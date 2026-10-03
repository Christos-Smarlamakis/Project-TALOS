# -*- coding: utf-8 -*-
"""
Module: resolvers.py
Project: TALOS v5.18.3
Description:
    Cascading Open Access (OA) and preprint URL resolver for the Ethical
    Academic PDF Harvester. Given a paper metadata dictionary, ``resolve_oa_url``
    walks an ordered chain of legal resolver strategies and returns the first
    viable ``(pdf_url, resolver_source)`` tuple, or ``None`` when no legal
    full-text link can be located.

    The cascade is organised in three tiers:

    1. Direct preprint repositories (deterministic, keyless URL construction):
       Cornell arXiv, IEEE TechRxiv, HAL/Inria, and NASA NTRS.
    2. Publisher Open Access APIs (legal, publisher-sanctioned endpoints):
       Elsevier ScienceDirect OA API (keyed), PLOS direct, and PubMed Central.
    3. Meta-resolvers (aggregated OA location indices): Unpaywall, OpenAlex,
       Semantic Scholar, CORE, Crossref OA, and SSRN.

    Every network-backed resolver degrades gracefully: connection errors, HTTP
    failures, and malformed payloads are swallowed and the cascade simply
    advances to the next strategy. The module enforces the polite academic
    User-Agent mandated by the release specification so every request is
    attributable and policy-compliant.

    Key design decisions:
    - Resolver order favours keyless, deterministic endpoints first so the
      harvester remains functional in an air-gapped profile with no API keys.
    - Each resolver returns a ``(url, source)`` pair rather than fetching the
      PDF itself, keeping network I/O and integrity validation in the harvester.
    - Identifier extraction tolerates heterogeneous upstream schemas (doi, url,
      openalex_id, pmcid, pmid) so no single canonical field is assumed.

Dependencies:
    - os: environment variable access for optional API keys.
    - re: identifier extraction from DOIs and URLs.
    - requests: HTTP client for the network-backed resolver tiers.
    - typing: Optional / Tuple return annotations.
"""

import os
import re

import requests

from typing import Optional, Tuple

# -- Polite academic User-Agent (University of the Peloponnese). -- #
ACADEMIC_USER_AGENT = (
    "TALOS-Academic-Research-Bot/5.18.3 "
    "(University of the Peloponnese; mailto:c.smarlamakis@uop.gr)"
)

# -- Shared request timeout for network-backed resolvers (seconds). -- #
_RESOLVER_TIMEOUT = 10


def _headers() -> dict:
    """Return the standard polite request headers for resolver probes."""
    return {"User-Agent": ACADEMIC_USER_AGENT}


def _http_get_json(url: str, params: Optional[dict] = None,
                   timeout: int = _RESOLVER_TIMEOUT) -> Optional[dict]:
    """Fetch a JSON document with graceful error handling.

    Args:
        url (str): Endpoint URL.
        params (dict, optional): Query-string parameters.
        timeout (int): Request timeout in seconds.

    Returns:
        Optional[dict]: Decoded JSON payload, or None on any failure.
    """
    try:
        response = requests.get(url, headers=_headers(), params=params,
                                timeout=timeout)
        if response.status_code != 200:
            return None
        return response.json()
    except (requests.RequestException, ValueError):
        return None


def _doi(paper: dict) -> Optional[str]:
    """Return the normalized DOI (lowercased) from a paper dictionary."""
    raw = paper.get("doi") or paper.get("DOI")
    if not raw:
        return None
    return str(raw).strip().lower()


def _url(paper: dict) -> Optional[str]:
    """Return the primary URL from a paper dictionary, if present."""
    raw = paper.get("url") or paper.get("pdf_url") or paper.get("oa_pdf_url")
    return str(raw).strip() if raw else None

# ---------------------------------------------------------------------------
# -- Tier 1: Direct preprint repositories (deterministic, keyless) -- #
# ---------------------------------------------------------------------------

def _resolve_arxiv(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve a Cornell arXiv PDF from an arXiv id embedded in DOI or URL.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "arXiv")`` or None.
    """
    arxiv_id = None
    doi = _doi(paper) or ""
    m = re.search(r"10\.48550/arxiv\.([0-9]{4}\.[0-9]{4,5}(v[0-9]+)?)", doi)
    if m:
        arxiv_id = m.group(1)
    else:
        url = _url(paper) or ""
        m2 = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5}(v[0-9]+)?)", url)
        if m2:
            arxiv_id = m2.group(1)
    if not arxiv_id:
        return None
    return (f"https://arxiv.org/pdf/{arxiv_id}.pdf", "arXiv")


def _resolve_techrxiv(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve an IEEE TechRxiv PDF via its 10.36227/techrxiv DOI.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "IEEE TechRxiv")`` or None.
    """
    doi = _doi(paper) or ""
    if "10.36227" not in doi:
        return None
    return (f"https://www.techrxiv.org/doi/pdf/{doi}", "IEEE TechRxiv")


def _resolve_hal_inria(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve a HAL/Inria deposit PDF from a hal.science URL.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "HAL/Inria")`` or None.
    """
    url = _url(paper) or ""
    if "hal.science" not in url and "hal.inria.fr" not in url:
        return None
    base = url.split("#")[0].split("?")[0]
    if base.endswith("/document"):
        return (base, "HAL/Inria")
    return (base.rstrip("/") + "/document", "HAL/Inria")


def _resolve_nasa_ntrs(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve a NASA NTRS PDF via the citations API download manifest.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "NASA NTRS")`` or None.
    """
    url = _url(paper) or ""
    m = re.search(r"ntrs\.nasa\.gov/(?:citations/)?([0-9]+)", url)
    if not m:
        return None
    ntrs_id = m.group(1)
    manifest = _http_get_json(
        f"https://ntrs.nasa.gov/api/citations/{ntrs_id}/downloads"
    )
    if not manifest:
        return None
    if isinstance(manifest, dict):
        downloads = manifest.get("downloads", [])
    elif isinstance(manifest, list):
        downloads = manifest
    else:
        return None
    for entry in downloads:
        name = entry.get("filename") or entry.get("original") or entry.get("name")
        link = entry.get("links", {}).get("pdf") or entry.get("link")
        if link and str(name or "").lower().endswith(".pdf"):
            return (link, "NASA NTRS")
    return None

# ---------------------------------------------------------------------------
# -- Tier 2: Publisher Open Access APIs -- #
# ---------------------------------------------------------------------------

def _resolve_elsevier_oa(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve an Elsevier ScienceDirect OA full-text link via the OA API.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "Elsevier ScienceDirect OA")``
            or None.
    """
    api_key = os.getenv("ELSEVIER_API_KEY", "")
    doi = _doi(paper)
    if not api_key or not doi:
        return None
    url = f"https://api.elsevier.com/content/article/doi/{doi}"
    headers = _headers()
    headers["X-ELS-APIKey"] = api_key
    headers["Accept"] = "application/json"
    try:
        response = requests.get(url, headers=headers, timeout=_RESOLVER_TIMEOUT)
        if response.status_code != 200:
            return None
        data = response.json()
        link = (
            data.get("full-text-retrieval-response", {})
                .get("coredata", {})
                .get("prism:url")
        )
        if link:
            return (str(link), "Elsevier ScienceDirect OA")
    except (requests.RequestException, ValueError):
        return None
    return None


def _resolve_plos(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve a PLOS PDF (fully Open Access publisher) from its DOI.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "PLOS")`` or None.
    """
    doi = _doi(paper) or ""
    if not doi.startswith("10.1371/"):
        return None
    return (f"https://journals.plos.org/plosone/article/file?id={doi}&type=printable", "PLOS")


def _resolve_pmc(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve a PubMed Central OA PDF via the PMC id or PMID.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "PubMed Central")`` or None.
    """
    pmcid = str(paper.get("pmcid") or "").strip()
    if pmcid.lower().startswith("pmc"):
        pmcid = pmcid[3:]
    if pmcid:
        return (f"https://pmc.ncbi.nlm.nih.gov/articles/PMC{pmcid}/pdf/", "PubMed Central")
    pmid = str(paper.get("pmid") or "").strip()
    if pmid:
        return (f"https://pmc.ncbi.nlm.nih.gov/articles/PMID{pmid}/pdf/", "PubMed Central")
    return None

# ---------------------------------------------------------------------------
# -- Tier 3: Meta-resolvers (aggregated OA location indices) -- #
# ---------------------------------------------------------------------------

def _resolve_unpaywall(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve the best OA location via the Unpaywall API (Piwowar et al. 2018).

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "Unpaywall")`` or None.
    """
    doi = _doi(paper)
    if not doi:
        return None
    email = os.getenv("UNPAYWALL_EMAIL", "") or os.getenv("MAILTO", "")
    params = {"email": email} if email else None
    data = _http_get_json(f"https://api.unpaywall.org/v2/{doi}", params=params)
    if not data:
        return None
    best = data.get("best_oa_location") or {}
    pdf_url = best.get("url_for_pdf") or best.get("url")
    if pdf_url:
        return (str(pdf_url), "Unpaywall")
    return None


def _resolve_openalex(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve the OpenAlex ``best_oa_location`` from the works endpoint.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "OpenAlex")`` or None.
    """
    doi = _doi(paper)
    openalex_id = str(paper.get("openalex_id") or "").strip()
    if openalex_id:
        url = f"https://api.openalex.org/works/{openalex_id}"
    elif doi:
        url = f"https://api.openalex.org/works/doi:{doi}"
    else:
        return None
    data = _http_get_json(url)
    if not data:
        return None
    oa = data.get("open_access") or {}
    if oa.get("is_oa") and oa.get("oa_url"):
        return (str(oa["oa_url"]), "OpenAlex")
    best = data.get("best_oa_location") or {}
    pdf_url = best.get("pdf_url") or best.get("landing_page_url")
    if pdf_url:
        return (str(pdf_url), "OpenAlex")
    return None


def _resolve_semantic_scholar(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve the Semantic Scholar ``openAccessPdf`` field.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "Semantic Scholar")`` or None.
    """
    doi = _doi(paper)
    if not doi:
        return None
    data = _http_get_json(
        f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}",
        params={"fields": "openAccessPdf,isOpenAccess"},
    )
    if not data:
        return None
    pdf = data.get("openAccessPdf") or {}
    pdf_url = pdf.get("url")
    if pdf_url:
        return (str(pdf_url), "Semantic Scholar")
    return None


def _resolve_core(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve a full-text link via the CORE v3 search API.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "CORE")`` or None.
    """
    doi = _doi(paper)
    if not doi:
        return None
    data = _http_get_json(
        "https://api.core.ac.uk/v3/search/works",
        params={"q": f"doi:\"{doi}\"", "limit": 1},
    )
    if not data:
        return None
    results = data.get("results") or []
    if not results:
        return None
    download = results[0].get("downloadUrl")
    if download:
        return (str(download), "CORE")
    return None

def _resolve_crossref_oa(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve a Crossref OA link via the works API ``link`` field.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "Crossref OA")`` or None.
    """
    doi = _doi(paper)
    if not doi:
        return None
    data = _http_get_json(f"https://api.crossref.org/works/{doi}")
    if not data:
        return None
    message = data.get("message") or {}
    for link in message.get("link", []) or []:
        if link.get("content-type") == "application/pdf":
            url = link.get("URL")
            if url:
                return (str(url), "Crossref OA")
    return None


def _resolve_ssrn(paper: dict) -> Optional[Tuple[str, str]]:
    """Resolve an SSRN preprint PDF from an ssrn.com URL.

    Args:
        paper (dict): Paper metadata.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, "SSRN")`` or None.
    """
    url = _url(paper) or ""
    m = re.search(r"ssrn\.com/(?:abstract=|delivery\.php\?id=)([0-9]+)", url)
    if not m:
        return None
    ssrn_id = m.group(1)
    return (f"https://papers.ssrn.com/sol3/Delivery.cfm/{ssrn_id}.pdf", "SSRN")


# ---------------------------------------------------------------------------
# -- Public cascade entry point -- #
# ---------------------------------------------------------------------------

_RESOLVER_CHAIN = (
    _resolve_arxiv,
    _resolve_techrxiv,
    _resolve_hal_inria,
    _resolve_nasa_ntrs,
    _resolve_elsevier_oa,
    _resolve_plos,
    _resolve_pmc,
    _resolve_unpaywall,
    _resolve_openalex,
    _resolve_semantic_scholar,
    _resolve_core,
    _resolve_crossref_oa,
    _resolve_ssrn,
)


def resolve_oa_url(paper_dict: dict) -> Optional[Tuple[str, str]]:
    """Resolve a legal Open Access or preprint PDF URL for a paper.

    Walks the ordered cascade of direct preprint repositories, publisher OA
    APIs, and meta-resolvers, returning the first viable ``(pdf_url,
    resolver_source)`` pair. Returns ``None`` when no legal full-text link is
    resolvable (the harvester then marks the candidate ``UNAVAILABLE``).

    Args:
        paper_dict (dict): Paper metadata. Accepted keys include ``doi``, ``url``,
            ``pdf_url``, ``oa_pdf_url``, ``openalex_id``, ``pmcid``, and ``pmid``.

    Returns:
        Optional[Tuple[str, str]]: ``(pdf_url, resolver_source)``, or None when
            every resolver in the cascade fails.
    """
    if not isinstance(paper_dict, dict):
        return None
    for resolver in _RESOLVER_CHAIN:
        try:
            result = resolver(paper_dict)
        except Exception:
            # -- A single resolver must never abort the cascade. -- #
            result = None
        if result:
            return result
    return None




