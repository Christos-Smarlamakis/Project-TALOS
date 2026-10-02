# -*- coding: utf-8 -*-
"""
Module: citation_snowballing.py
Project: TALOS v5.18.0
Description:
    Autonomous citation snowballing engine. Starting from a seed paper (DOI, title,
    or database ID), it traverses the academic citation graph in two directions:
    backward snowballing walks the referenced literature of the seed, while forward
    snowballing walks the papers that cite the seed and were published in 2024-2026.
    Discovered nodes are filtered for research relevance via the PRISMA evaluator
    (local ``llama3.1:8b``) and imported into the active profile database. The
    engine also emits a structured citation genealogy graph.

    Key design decisions:
    - OpenAlex is the primary graph provider (keyless, rich citation edges);
      Crossref and Semantic Scholar serve as graceful secondary sources.
    - All network calls are wrapped in try/except so an offline node returns an
      empty result set instead of raising (air-gapped safe).
    - Relevance filtering degrades to a deterministic keyword pass when the local
      LLM is unavailable.

Dependencies:
    - os: Environment variable access.
    - re: DOI normalization.
    - requests: HTTP client for OpenAlex / Crossref / Semantic Scholar.
"""
import os
import re

import requests

try:
    from rich.console import Console
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:  # pragma: no cover - rich not installed
    RICH_AVAILABLE = False


def _md_escape(text):
    """Escape Markdown table-breaking characters in a cell value.

    Args:
        text (str): Raw cell text.

    Returns:
        str: A single-line, pipe-escaped Markdown-safe string.
    """
    if text is None:
        return ""
    return str(text).replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def _format_link(doi, url):
    """Build a Markdown clickable link from a DOI or URL.

    Args:
        doi (str): DOI identifier (e.g. ``10.1109/...``).
        url (str): Direct URL.

    Returns:
        str: Markdown link, or an empty string when neither is present.
    """
    doi = str(doi or "").strip()
    url = str(url or "").strip()
    if doi:
        href = doi if doi.startswith(("http://", "https://")) else f"https://doi.org/{doi}"
        return f"[{_md_escape(doi)}]({href})"
    if url:
        return f"[{_md_escape(url)}]({url})"
    return ""


class CitationSnowballEngine:
    """Traverse the citation graph around a seed paper and import relevant nodes.

    Attributes:
        ai_manager: Optional AIManager for LLM-backed relevance filtering.
        db_manager: Optional DatabaseManager for seed resolution and import.
        session: Shared HTTP session.
        timeout: HTTP request timeout in seconds.
    """

    OPENALEX_BASE = "https://api.openalex.org"
    CROSSREF_BASE = "https://api.crossref.org/works"
    S2_BASE = "https://api.semanticscholar.org/graph/v1"

    def __init__(self, ai_manager=None, db_manager=None, timeout: int = 25):
        """Initialize the engine.

        Args:
            ai_manager: Optional AIManager instance for relevance filtering.
            db_manager: Optional DatabaseManager instance.
            timeout (int): HTTP request timeout in seconds.
        """
        self.ai_manager = ai_manager
        self.db_manager = db_manager
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "TALOS/5.17.0"})

    # -- OpenAlex primitives ----------------------------------------------------
    def _get_json(self, url, params=None):
        """Perform a GET request and return parsed JSON, or None on failure.

        Args:
            url (str): Request URL.
            params (dict, optional): Query parameters.

        Returns:
            dict or None: Parsed JSON body, or None on any request error.
        """
        try:
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            return None

    def _work_by_doi(self, doi: str):
        """Fetch an OpenAlex work by its DOI.

        Args:
            doi (str): Normalized DOI string.

        Returns:
            dict or None: The OpenAlex work object.
        """
        if not doi:
            return None
        url = f"{self.OPENALEX_BASE}/works/https://doi.org/{doi}"
        return self._get_json(url)

    def _works_by_ids(self, openalex_ids, limit: int = 25):
        """Fetch multiple OpenAlex works by their canonical IDs.

        Args:
            openalex_ids (list): OpenAlex work ID strings (e.g. ``W123...``).
            limit (int): Maximum works to return.

        Returns:
            list: OpenAlex work objects.
        """
        if not openalex_ids:
            return []
        ids = "|".join(openalex_ids[:200])
        url = f"{self.OPENALEX_BASE}/works"
        data = self._get_json(url, params={"filter": f"ids:{ids}", "per-page": limit})
        return (data or {}).get("results", [])

    def _citing_works(self, work_id: str, year_from: int, year_to: int, limit: int = 50):
        """Fetch works that cite a given work within a year window.

        Args:
            work_id (str): OpenAlex work ID (e.g. ``W123...``).
            year_from (int): Inclusive start year.
            year_to (int): Inclusive end year.
            limit (int): Maximum works to return.

        Returns:
            list: OpenAlex work objects.
        """
        url = f"{self.OPENALEX_BASE}/works"
        params = {
            "filter": f"cites:{work_id},from_publication_date:{year_from}-01-01,"
                      f"to_publication_date:{year_to}-12-31",
            "per-page": limit,
        }
        data = self._get_json(url, params=params)
        return (data or {}).get("results", [])

    # -- Normalization ----------------------------------------------------------
    @staticmethod
    def _reconstruct_abstract(inverted_index):
        """Reconstruct a plain-text abstract from OpenAlex's inverted index.

        Args:
            inverted_index (dict): Word -> list of positions mapping.

        Returns:
            str: Reconstructed abstract text.
        """
        if not isinstance(inverted_index, dict):
            return ""
        positions = {}
        for word, pos_list in inverted_index.items():
            for pos in pos_list:
                positions[pos] = word
        return " ".join(positions[i] for i in sorted(positions))

    @staticmethod
    def _normalize_openalex_work(work):
        """Map an OpenAlex work onto the canonical TALOS paper dict.

        Args:
            work (dict): OpenAlex work object.

        Returns:
            dict: {doi, url, title, authors_str, publication_year, abstract, source}.
        """
        authors = [
            a.get("author", {}).get("display_name", "")
            for a in (work.get("authorships") or [])
        ]
        doi = str(work.get("doi") or "").replace("https://doi.org/", "")
        return {
            "doi": doi,
            "url": work.get("doi") or work.get("id") or "",
            "title": work.get("title") or work.get("display_name") or "",
            "authors_str": ", ".join(a for a in authors if a),
            "publication_year": work.get("publication_year"),
            "abstract": CitationSnowballEngine._reconstruct_abstract(
                work.get("abstract_inverted_index")
            ),
            "source": "OpenAlex",
        }

    def _normalize_crossref_item(self, item):
        """Map a Crossref reference item onto the canonical paper dict.

        Args:
            item (dict): Crossref reference object.

        Returns:
            dict: {doi, url, title, authors_str, publication_year, abstract, source}.
        """
        title = item.get("title") or [""]
        return {
            "doi": str(item.get("DOI") or "").lower(),
            "url": f"https://doi.org/{item.get('DOI')}" if item.get("DOI") else "",
            "title": title[0] if isinstance(title, list) and title else str(title),
            "authors_str": "",
            "publication_year": item.get("year"),
            "abstract": "",
            "source": "Crossref",
        }

    def _crossref_references(self, doi: str, limit: int = 25):
        """Fetch a seed's cited references from Crossref.

        Args:
            doi (str): Seed DOI.
            limit (int): Maximum references to return.

        Returns:
            list: Canonical paper dicts.
        """
        data = self._get_json(f"{self.CROSSREF_BASE}/{doi}")
        if not data:
            return []
        references = (data.get("message") or {}).get("reference") or []
        return [
            self._normalize_crossref_item(ref)
            for ref in references[:limit]
        ]

    def _semantic_scholar_edges(self, doi: str, kind: str, limit: int = 25):
        """Fetch citation edges from Semantic Scholar.

        Args:
            doi (str): Seed DOI.
            kind (str): ``references`` (backward) or ``citations`` (forward).
            limit (int): Maximum edges to return.

        Returns:
            list: Canonical paper dicts.
        """
        try:
            paper_id = f"DOI:{doi}"
            data = self._get_json(
                f"{self.S2_BASE}/paper/{paper_id}/{kind}",
                params={"fields": "title,abstract,year,externalIds,url", "limit": limit},
            )
            out = []
            for edge in ((data or {}).get("data") or []):
                paper = edge.get("citedPaper") or edge.get("citingPaper") or {}
                ext = paper.get("externalIds") or {}
                out.append({
                    "doi": str(ext.get("DOI") or "").lower(),
                    "url": paper.get("url") or "",
                    "title": paper.get("title") or "",
                    "authors_str": "",
                    "publication_year": paper.get("year"),
                    "abstract": paper.get("abstract") or "",
                    "source": "Semantic Scholar",
                })
            return out
        except (requests.RequestException, ValueError):
            return []

    def _dedupe(self, papers):
        """Deduplicate a list of papers by DOI, then URL, then title.

        Args:
            papers (list): Canonical paper dicts.

        Returns:
            list: Deduplicated papers preserving order.
        """
        seen_doi, seen_url, seen_title = set(), set(), set()
        out = []
        for paper in papers:
            doi = (paper.get("doi") or "").strip().lower()
            url = (paper.get("url") or "").strip()
            title = (paper.get("title") or "").strip().lower()
            if doi and doi in seen_doi:
                continue
            if url and url in seen_url:
                continue
            if title and title in seen_title:
                continue
            if doi:
                seen_doi.add(doi)
            if url:
                seen_url.add(url)
            if title:
                seen_title.add(title)
            out.append(paper)
        return out

    # -- Relevance filtering ----------------------------------------------------
    def _filter_relevant(self, papers, criteria=None):
        """Filter discovered nodes by research relevance.

        Uses the PRISMA evaluator (LLM-backed when ``ai_manager`` is present,
        otherwise deterministic) and keeps only nodes screened as INCLUDE.

        Args:
            papers (list): Canonical paper dicts.
            criteria (list, optional): Inclusion criteria strings.

        Returns:
            list: Papers screened as relevant.
        """
        inclusion = criteria or []
        relevant = []
        evaluator = None
        try:
            from src.prisma.dspy_modules import PrismaEvaluator
            evaluator = PrismaEvaluator(ai_manager=self.ai_manager, evaluation_mode="single")
        except Exception:
            evaluator = None

        for paper in papers:
            title = paper.get("title") or ""
            abstract = paper.get("abstract") or ""
            if evaluator is not None:
                try:
                    result = evaluator.screen(title, abstract, inclusion_criteria=inclusion)
                    if getattr(result, "decision", "UNCERTAIN") == "INCLUDE":
                        paper["relevance_decision"] = "INCLUDE"
                        relevant.append(paper)
                        continue
                except Exception:
                    pass
            if self._deterministic_relevant(title, abstract):
                paper["relevance_decision"] = "INCLUDE"
                relevant.append(paper)
        return relevant

    @staticmethod
    def _deterministic_relevant(title: str, abstract: str) -> bool:
        """Keyword-based relevance heuristic for air-gapped operation.

        Args:
            title (str): Paper title.
            abstract (str): Paper abstract.

        Returns:
            bool: True when the text contains a robotics / RL signal keyword.
        """
        signals = (
            "reinforcement", "multi-agent", "multi agent", "swarm", "uav",
            "robot", "robotic", "drone", "deep learning", "neural", "graph",
            "mission", "planning", "cooperative",
        )
        blob = f"{title} {abstract}".lower()
        return any(signal in blob for signal in signals)

    # -- Import -----------------------------------------------------------------
    def _import_papers(self, papers):
        """Import relevant papers into the active profile database.

        Args:
            papers (list): Canonical paper dicts to import.

        Returns:
            int: Number of papers successfully inserted.
        """
        if not papers:
            return 0
        try:
            from src.core.database_manager import DatabaseManager
            db = self.db_manager or DatabaseManager()
        except Exception:
            return 0

        imported = 0
        for paper in papers:
            try:
                if db.paper_exists_by_doi(paper.get("doi")) or db.paper_exists_by_url(paper.get("url")):
                    continue
                evaluation = {
                    "scores": {"strategic": 0, "operational": 0, "tactical": 0, "playground": 0},
                    "overall_score": 0.0,
                    "reasoning": "Discovered via citation snowballing (v5.17.0).",
                    "tags": ["snowballing"],
                }
                db.add_paper(paper, evaluation)
                imported += 1
            except Exception:
                continue
        return imported

    # -- Seed resolution --------------------------------------------------------
    def resolve_seed(self, seed: str):
        """Resolve a seed identifier (DOI, DB ID, or title) to a paper dict.

        Args:
            seed (str): Seed DOI, numeric database ID, or title.

        Returns:
            dict or None: {doi, url, title, ...} for the seed.
        """
        seed = (seed or "").strip()
        if not seed:
            return None

        # Numeric database ID.
        if seed.isdigit():
            try:
                from src.core.database_manager import DatabaseManager
                db = self.db_manager or DatabaseManager()
                row = db.execute_query(
                    "SELECT doi, url, title, abstract FROM papers WHERE id = ?",
                    (int(seed),),
                    fetch_one=True,
                )
                if row:
                    return {"doi": row[0], "url": row[1], "title": row[2], "abstract": row[3]}
            except Exception:
                pass

        # DOI (matches "10.xxxx/..." possibly prefixed with a URL).
        match = re.search(r"10\.\d{4,9}/[^\s]+", seed)
        doi = match.group(0).rstrip(".,;") if match else None
        if doi:
            work = self._work_by_doi(doi)
            if work:
                paper = self._normalize_openalex_work(work)
                paper["doi"] = doi
                return paper
            return {"doi": doi, "url": f"https://doi.org/{doi}", "title": seed, "abstract": ""}

        # Title lookup via Crossref.
        data = self._get_json(self.CROSSREF_BASE, params={"query.bibliographic": seed, "rows": 1})
        items = ((data or {}).get("message") or {}).get("items") or []
        if items:
            return self._normalize_crossref_item(items[0])
        return {"doi": "", "url": "", "title": seed, "abstract": ""}

    # -- Snowball traversal -----------------------------------------------------
    @staticmethod
    def _short_id(openalex_id: str) -> str:
        """Extract the short OpenAlex work ID from a full URL.

        Args:
            openalex_id (str): Full OpenAlex URL or short ID.

        Returns:
            str: Short ID (e.g. ``W123...``).
        """
        return str(openalex_id).rsplit("/", 1)[-1]

    def backward_snowball(self, seed: dict, depth: int = 1, limit: int = 25):
        """Walk cited references of a seed (backward direction).

        Args:
            seed (dict): Seed paper dict.
            depth (int): Traversal depth (1 = direct references only).
            limit (int): Maximum references per node.

        Returns:
            list: Canonical paper dicts for referenced literature.
        """
        collected = []
        frontier = [seed]
        for _ in range(max(1, depth)):
            next_frontier = []
            for node in frontier:
                doi = node.get("doi")
                refs = []
                if doi:
                    refs += self._crossref_references(doi, limit)
                    refs += self._semantic_scholar_edges(doi, "references", limit)
                    work = self._work_by_doi(doi)
                    if work:
                        openalex_ids = [
                            self._short_id(w) for w in (work.get("referenced_works") or [])
                        ]
                        refs += [
                            self._normalize_openalex_work(w)
                            for w in self._works_by_ids(openalex_ids, limit)
                        ]
                refs = self._dedupe(refs)
                collected.extend(refs)
                next_frontier.extend(refs[:limit])
            frontier = next_frontier
        return self._dedupe(collected)

    def forward_snowball(self, seed: dict, year_from: int = 2024, year_to: int = 2026, limit: int = 50):
        """Walk citing papers of a seed within a publication window.

        Args:
            seed (dict): Seed paper dict.
            year_from (int): Inclusive start year.
            year_to (int): Inclusive end year.
            limit (int): Maximum citing works.

        Returns:
            list: Canonical paper dicts for citing literature.
        """
        doi = seed.get("doi")
        collected = []
        if doi:
            collected += self._semantic_scholar_edges(doi, "citations", limit)
        work = self._work_by_doi(doi) if doi else None
        if work:
            collected += [
                self._normalize_openalex_work(w)
                for w in self._citing_works(self._short_id(work.get("id")), year_from, year_to, limit)
            ]
        return self._dedupe(collected)

    # -- Genealogy graph --------------------------------------------------------
    @staticmethod
    def generate_genealogy(seed: dict, backward, forward):
        """Build a structured citation genealogy graph.

        Args:
            seed (dict): Seed paper dict.
            backward (list): Backward (referenced) papers.
            forward (list): Forward (citing) papers.

        Returns:
            dict: {seed, nodes, edges} describing the graph.
        """
        seed_title = seed.get("title") or seed.get("doi") or "seed"
        nodes = [{"id": "seed", "label": seed_title, "role": "seed", "doi": seed.get("doi")}]
        edges = []
        for i, paper in enumerate(backward):
            node_id = f"backward-{i}"
            nodes.append({
                "id": node_id,
                "label": paper.get("title") or paper.get("doi") or "?",
                "role": "referenced",
                "doi": paper.get("doi"),
            })
            edges.append({"source": node_id, "target": "seed", "relation": "cited_by_seed"})
        for i, paper in enumerate(forward):
            node_id = f"forward-{i}"
            nodes.append({
                "id": node_id,
                "label": paper.get("title") or paper.get("doi") or "?",
                "role": "citing",
                "doi": paper.get("doi"),
            })
            edges.append({"source": "seed", "target": node_id, "relation": "cites_seed"})
        return {"seed": seed, "nodes": nodes, "edges": edges}

    def render_genealogy(self, results: dict):
        """Render the citation genealogy as a styled Rich Table.

        Args:
            results (dict): The result dict returned by ``run``, with keys
                ``backward``, ``forward``, and ``relevant``.
        """
        backward = results.get("backward") or []
        forward = results.get("forward") or []

        if not RICH_AVAILABLE:
            for rank, paper in enumerate(backward, start=1):
                print(f"Backward {rank}. {paper.get('title')} ({paper.get('publication_year')})")
            for rank, paper in enumerate(forward, start=1):
                print(f"Forward {rank}. {paper.get('title')} ({paper.get('publication_year')})")
            return

        relevant_keys = set()
        for paper in results.get("relevant") or []:
            key = (paper.get("doi") or "").strip().lower()
            if not key:
                key = (paper.get("title") or "").strip().lower()
            if key:
                relevant_keys.add(key)

        def _relevance(paper):
            key = (paper.get("doi") or "").strip().lower()
            if not key:
                key = (paper.get("title") or "").strip().lower()
            if key and key in relevant_keys:
                return "[green]Relevant[/green]"
            return "[dim]-[/dim]"

        table = Table(
            title="Citation Snowballing Genealogy Graph",
            box=box.ROUNDED,
            header_style="bold cyan",
            title_style="bold bright_cyan",
        )
        table.add_column("Traversal", style="bold")
        table.add_column("Depth", justify="right", style="cyan")
        table.add_column("Title", style="bold white", overflow="fold", max_width=46)
        table.add_column("Year / Source", style="cyan")
        table.add_column("DOI / URL", style="dim", overflow="fold", max_width=26)
        table.add_column("Relevance Score", style="magenta")

        depth = results.get("depth", 1)
        for paper in backward:
            table.add_row(
                "Backward",
                str(depth),
                str(paper.get("title") or ""),
                f"{paper.get('publication_year') or ''} / {paper.get('source') or ''}".strip(" /"),
                str(paper.get("doi") or paper.get("url") or ""),
                _relevance(paper),
            )
        for paper in forward:
            table.add_row(
                "Forward",
                "1",
                str(paper.get("title") or ""),
                f"{paper.get('publication_year') or ''} / {paper.get('source') or ''}".strip(" /"),
                str(paper.get("doi") or paper.get("url") or ""),
                _relevance(paper),
            )
        Console().print(table)

    def export_snowball_report(self, seed: str, results: dict,
                               output_dir: str = "data/reports/snowball") -> str:
        """Generate a structured Markdown report of a citation snowballing run.

        Writes a timestamped Markdown report under ``output_dir`` (resolved
        relative to the project root) with the seed header, backward and
        forward traversal tables, and direct clickable links.

        Args:
            seed (str): Seed DOI, database ID, or title.
            results (dict): The result dict returned by ``run``.
            output_dir (str): Directory in which to write the report. Defaults
                to ``data/reports/snowball`` relative to the project root.

        Returns:
            str: Absolute path to the generated Markdown report.
        """
        import datetime

        project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", ".."))
        report_dir = output_dir
        if not os.path.isabs(report_dir):
            report_dir = os.path.join(project_root, report_dir)
        os.makedirs(report_dir, exist_ok=True)

        now = datetime.datetime.now()
        report_path = os.path.join(
            report_dir, f"snowball_{now.strftime('%Y%m%d_%H%M%S')}.md")

        seed_paper = results.get("seed") or {}
        backward = results.get("backward") or []
        forward = results.get("forward") or []
        depth = results.get("depth", 1)
        year_window = results.get("year_window", "2024-2026")
        nodes = len(backward) + len(forward)

        seed_label = seed_paper.get("title") or seed_paper.get("doi") or seed

        lines = []
        lines.append("# Citation Snowballing Report")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| **Seed Paper Identifier** | {_md_escape(seed_label)} |")
        lines.append(f"| **Traversal Depth** | {depth} |")
        lines.append(f"| **Timestamp** | {now.strftime('%Y-%m-%d %H:%M:%S')} |")
        lines.append(f"| **Nodes Discovered** | {nodes} |")
        lines.append("")
        lines.append("## Backward Snowballing (Cited References)")
        lines.append("")
        lines.append("| Rank | Title | Authors | Year | DOI / URL |")
        lines.append("|------|-------|---------|------|-----------|")
        for rank, paper in enumerate(backward, start=1):
            link = _format_link(paper.get("doi"), paper.get("url"))
            lines.append(
                f"| {rank} | {_md_escape(paper.get('title'))} | "
                f"{_md_escape(paper.get('authors_str'))} | "
                f"{paper.get('publication_year') or ''} | {link} |"
            )
        lines.append("")
        lines.append(f"## Forward Snowballing (Citing Recent Literature {year_window})")
        lines.append("")
        lines.append("| Rank | Title | Authors | Year | DOI / URL |")
        lines.append("|------|-------|---------|------|-----------|")
        for rank, paper in enumerate(forward, start=1):
            link = _format_link(paper.get("doi"), paper.get("url"))
            lines.append(
                f"| {rank} | {_md_escape(paper.get('title'))} | "
                f"{_md_escape(paper.get('authors_str'))} | "
                f"{paper.get('publication_year') or ''} | {link} |"
            )
        lines.append("")

        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")

        if RICH_AVAILABLE:
            Console().print(f"[dim]Snowball report saved to: {report_path}[/dim]")
        else:
            print(f"Snowball report saved to: {report_path}")
        return str(report_path)

    # -- End-to-end orchestration ----------------------------------------------
    def run(self, seed: str, depth: int = 1, year_from: int = 2024, year_to: int = 2026,
            import_to_db: bool = True, criteria=None, render: bool = True):
        """Run the full citation snowballing workflow.

        Traverses the citation graph around the seed, filters relevant nodes,
        imports them, and (when ``render``) presents a styled Rich genealogy
        table plus a timestamped Markdown report under ``data/reports/snowball``.

        Args:
            seed (str): Seed DOI, database ID, or title.
            depth (int): Backward traversal depth.
            year_from (int): Forward citation window start year.
            year_to (int): Forward citation window end year.
            import_to_db (bool): Whether to import relevant nodes into the DB.
            criteria (list, optional): Inclusion criteria for relevance filtering.
            render (bool): When True, render the genealogy table and report.

        Returns:
            dict: {seed, backward, forward, relevant, genealogy, imported,
                depth, year_window}.
        """
        seed_paper = self.resolve_seed(seed)
        if not seed_paper:
            return {"error": f"Could not resolve seed: {seed}"}

        backward = self.backward_snowball(seed_paper, depth=depth)
        forward = self.forward_snowball(seed_paper, year_from=year_from, year_to=year_to)

        combined = self._dedupe(backward + forward)
        relevant = self._filter_relevant(combined, criteria=criteria)

        imported = self._import_papers(relevant) if import_to_db else 0

        results = {
            "seed": seed_paper,
            "backward": backward,
            "forward": forward,
            "relevant": relevant,
            "genealogy": self.generate_genealogy(seed_paper, backward, forward),
            "imported": imported,
            "depth": depth,
            "year_window": f"{year_from}-{year_to}",
        }

        if render:
            self.render_genealogy(results)
            self.export_snowball_report(seed, results)
        return results

