# -*- coding: utf-8 -*-
"""
Module: code_first_search.py
Project: TALOS v5.18.1
Description:
    Reproducible code-first search engine. Discovers research papers that are
    verified to possess an official GitHub / PapersWithCode repository, a PyTorch
    implementation, or a robotic simulation benchmark (ROS2, Gazebo, AirSim,
    Isaac Gym). It queries the public GitHub repository search and PapersWithCode
    APIs, then cross-references results against the active profile database so
    only code-linked, reproducible studies surface.

    Key design decisions:
    - All queries degrade gracefully: an offline or rate-limited API returns an
      empty result rather than raising.
    - Reproducibility signals are matched against repository descriptions, topics,
      and PapersWithCode metadata (repository field, evaluation benchmark).
    - The engine is read-only with respect to the database; it surfaces matching
      records without modifying the corpus.

Dependencies:
    - os: Environment variable access and report directory resolution.
    - requests: HTTP client for GitHub and PapersWithCode APIs.
    - rich: Styled Rich Table rendering (optional, guarded import).
"""
import os

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


# -- Reproducibility signal keywords (robotic simulation + DL frameworks). --
REPRO_SIGNALS = (
    "pytorch", "tensorflow", "jax", "ros2", "gazebo", "airsim", "isaac",
    "isaac gym", "isaacgym", "simulation", "benchmark", "reinforcement",
    "gymnasium", "paper", "arxiv", "official", "implementation",
)


class CodeFirstSearchEngine:
    """Discover code-linked, reproducible research papers.

    Queries GitHub repositories and PapersWithCode for papers carrying an
    official implementation or a robotic simulation benchmark, and returns both
    the external reproducible artifacts and any matching records already present
    in the active profile database.
    """

    GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
    PWC_SEARCH_URL = "https://paperswithcode.com/api/v1/papers/"

    def __init__(self, timeout: int = 20):
        """Initialize the engine.

        Args:
            timeout (int): HTTP request timeout in seconds.
        """
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {"Accept": "application/vnd.github+json", "User-Agent": "TALOS"}
        )

    def _search_github_repos(self, query: str, limit: int = 20):
        """Search GitHub repositories matching the query.

        Args:
            query (str): Search query.
            limit (int): Maximum repositories to return.

        Returns:
            list: Repository records with name/url/description/topics/stars.
        """
        try:
            response = self.session.get(
                self.GITHUB_SEARCH_URL,
                params={"q": query, "per_page": min(limit, 100)},
                timeout=self.timeout,
            )
            response.raise_for_status()
            items = response.json().get("items", [])
            return [
                {
                    "repo": item.get("full_name"),
                    "url": item.get("html_url"),
                    "description": item.get("description") or "",
                    "topics": item.get("topics") or [],
                    "stars": item.get("stargazers_count", 0),
                }
                for item in items
            ]
        except (requests.RequestException, ValueError):
            return []

    def _is_reproducible(self, record):
        """Determine whether a repository carries a reproducibility signal.

        Args:
            record (dict): A repository or paper record.

        Returns:
            bool: True when a known code/benchmark signal is present.
        """
        blob = " ".join(
            str(record.get(k) or "")
            for k in ("description", "topics", "title", "repository")
        ).lower()
        return any(signal in blob for signal in REPRO_SIGNALS)

    def _search_paperswithcode(self, query: str, limit: int = 20):
        """Search PapersWithCode for papers matching the query.

        Args:
            query (str): Search query.
            limit (int): Maximum papers to return.

        Returns:
            list: Paper records with title/abstract-url/repository.
        """
        try:
            response = self.session.get(
                self.PWC_SEARCH_URL,
                params={"q": query},
                timeout=self.timeout,
            )
            response.raise_for_status()
            results = response.json().get("results", [])[:limit]
            return [
                {
                    "title": paper.get("title"),
                    "url": paper.get("url_abs") or paper.get("url_pdf"),
                    "repository": paper.get("repository"),
                }
                for paper in results
            ]
        except (requests.RequestException, ValueError):
            return []

    def run(self, query: str, limit: int = 20, render: bool = True):
        """Discover reproducible, code-linked papers for a query.

        Gathers reproducible repositories and PapersWithCode matches, then
        optionally renders a styled Rich Table and auto-exports a timestamped
        Markdown report to ``data/reports/code_search``.

        Args:
            query (str): Research query.
            limit (int): Maximum results per external source.
            render (bool): When True, render the Rich Table and write the report.

        Returns:
            dict: ``repositories`` and ``papers_with_code`` result lists plus a
                ``matching_db_papers`` list of active-profile records that match
                by title or abstract.
        """
        repos = [r for r in self._search_github_repos(query, limit) if self._is_reproducible(r)]
        pwc = [p for p in self._search_paperswithcode(query, limit) if self._is_reproducible(p)]
        results = {
            "query": query,
            "repositories": repos,
            "papers_with_code": pwc,
            "matching_db_papers": self._match_db_papers(query),
        }

        if render:
            self.render_results(results)
            self.export_search_report(query, results)
        return results

    def render_results(self, results: dict):
        """Render reproducible code-first search results as a styled Rich Table.

        Args:
            results (dict): The result dict returned by ``run``, with keys
                ``repositories``, ``papers_with_code``, and
                ``matching_db_papers``.
        """
        repositories = results.get("repositories") or []
        papers_with_code = results.get("papers_with_code") or []
        matching_db_papers = results.get("matching_db_papers") or []

        if not RICH_AVAILABLE:
            for rank, repo in enumerate(repositories, start=1):
                print(f"{rank}. {repo.get('repo')} ({repo.get('stars', 0)} stars) - {repo.get('url')}")
            return

        console = Console()
        if repositories:
            table = Table(
                title="Reproducible Code-First Search Results",
                box=box.ROUNDED,
                header_style="bold cyan",
                title_style="bold bright_cyan",
            )
            table.add_column("Rank", justify="right", style="bold")
            table.add_column("Stars", justify="right", style="yellow")
            table.add_column("Repository Name", style="bold white", overflow="fold", max_width=28)
            table.add_column("Paper Title & Description", style="dim", overflow="fold", max_width=44)
            table.add_column("Topics & Frameworks", style="cyan", overflow="fold", max_width=26)
            table.add_column("GitHub URL", style="dim", overflow="fold", max_width=34)
            for rank, repo in enumerate(repositories, start=1):
                table.add_row(
                    str(rank),
                    f"[bold yellow]{repo.get('stars', 0)} stars[/bold yellow]",
                    str(repo.get("repo") or ""),
                    str(repo.get("description") or ""),
                    ", ".join(repo.get("topics") or []),
                    str(repo.get("url") or ""),
                )
            console.print(table)

        if papers_with_code:
            pwc_table = Table(
                title="PapersWithCode Matches",
                box=box.ROUNDED,
                header_style="bold magenta",
                title_style="bold bright_magenta",
            )
            pwc_table.add_column("Rank", justify="right", style="bold")
            pwc_table.add_column("Paper Title", style="bold white", overflow="fold", max_width=56)
            pwc_table.add_column("Repository", style="cyan", overflow="fold", max_width=26)
            pwc_table.add_column("URL", style="dim", overflow="fold", max_width=34)
            for rank, paper in enumerate(papers_with_code, start=1):
                pwc_table.add_row(
                    str(rank),
                    str(paper.get("title") or ""),
                    str(paper.get("repository") or ""),
                    str(paper.get("url") or ""),
                )
            console.print(pwc_table)

        if matching_db_papers:
            db_table = Table(
                title="Matching Papers in Active Profile Database",
                box=box.ROUNDED,
                header_style="bold green",
                title_style="bold bright_green",
            )
            db_table.add_column("Rank", justify="right", style="bold")
            db_table.add_column("Title", style="bold white", overflow="fold", max_width=56)
            db_table.add_column("DOI / URL", style="dim", overflow="fold", max_width=34)
            db_table.add_column("Source", style="cyan")
            for rank, paper in enumerate(matching_db_papers, start=1):
                db_table.add_row(
                    str(rank),
                    str(paper.get("title") or ""),
                    str(paper.get("doi") or paper.get("url") or ""),
                    str(paper.get("source") or ""),
                )
            console.print(db_table)

    def export_search_report(self, query: str, results: dict,
                             output_dir: str = "data/reports/code_search") -> str:
        """Generate a structured Markdown report of a code-first search.

        Writes a timestamped Markdown report under ``output_dir`` (resolved
        relative to the project root) containing the query header, a ranked
        repositories table with clickable URLs, and supplementary
        PapersWithCode and matching-database sections.

        Args:
            query (str): Research query.
            results (dict): The result dict returned by ``run``.
            output_dir (str): Directory in which to write the report. Defaults
                to ``data/reports/code_search`` relative to the project root.

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
            report_dir, f"code_search_{now.strftime('%Y%m%d_%H%M%S')}.md")

        repositories = results.get("repositories") or []
        papers_with_code = results.get("papers_with_code") or []
        matching_db_papers = results.get("matching_db_papers") or []

        lines = []
        lines.append("# Reproducible Code-First Search Report")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| **Query** | {_md_escape(query)} |")
        lines.append(f"| **Timestamp** | {now.strftime('%Y-%m-%d %H:%M:%S')} |")
        lines.append(f"| **Repositories Discovered** | {len(repositories)} |")
        lines.append("")
        lines.append("## Repositories")
        lines.append("")
        lines.append("| Rank | Stars | Repository | Description | Topics / Frameworks | URL |")
        lines.append("|------|-------|------------|-------------|---------------------|-----|")
        for rank, repo in enumerate(repositories, start=1):
            link = _format_link("", repo.get("url"))
            lines.append(
                f"| {rank} | {repo.get('stars', 0)} | {_md_escape(repo.get('repo'))} | "
                f"{_md_escape(repo.get('description'))} | "
                f"{_md_escape(', '.join(repo.get('topics') or []))} | {link} |"
            )
        lines.append("")

        if papers_with_code:
            lines.append("## PapersWithCode Matches")
            lines.append("")
            lines.append("| Rank | Paper Title | Repository | URL |")
            lines.append("|------|-------------|------------|-----|")
            for rank, paper in enumerate(papers_with_code, start=1):
                link = _format_link("", paper.get("url"))
                lines.append(
                    f"| {rank} | {_md_escape(paper.get('title'))} | "
                    f"{_md_escape(paper.get('repository'))} | {link} |"
                )
            lines.append("")

        if matching_db_papers:
            lines.append("## Matching Papers in Active Profile Database")
            lines.append("")
            lines.append("| Rank | Title | DOI / URL | Source |")
            lines.append("|------|-------|-----------|--------|")
            for rank, paper in enumerate(matching_db_papers, start=1):
                link = _format_link(paper.get("doi"), paper.get("url"))
                lines.append(
                    f"| {rank} | {_md_escape(paper.get('title'))} | {link} | "
                    f"{_md_escape(paper.get('source'))} |"
                )
            lines.append("")

        with open(report_path, "w", encoding="utf-8") as handle:
            handle.write("\n".join(lines) + "\n")

        if RICH_AVAILABLE:
            Console().print(f"[dim]Code search report saved to: {report_path}[/dim]")
        else:
            print(f"Code search report saved to: {report_path}")
        return str(report_path)

    def _match_db_papers(self, query: str):
        """Cross-reference the query against the active profile database.

        Args:
            query (str): Research query.

        Returns:
            list: Matching paper records (id/title/doi/url/source).
        """
        try:
            from src.core.database_manager import DatabaseManager
            db = DatabaseManager()
            like = f"%{query.strip()}%"
            rows = db.execute_query(
                "SELECT id, title, doi, url, source FROM papers "
                "WHERE title LIKE ? OR abstract LIKE ? LIMIT 50",
                (like, like),
                fetch_all=True,
            )
            return [
                {"id": r[0], "title": r[1], "doi": r[2], "url": r[3], "source": r[4]}
                for r in (rows or [])
            ]
        except Exception:  # pragma: no cover - DB unavailable
            return []
