# -*- coding: utf-8 -*-
"""
Module: mcp_server.py
Project: TALOS v5.9.15
Description:
    Official MCP (Model Context Protocol) Server for the TALOS Ecosystem.
    This module exposes TALOS capabilities as MCP tools via stdio transport,
    enabling AI coding assistants (Cherry Studio, Claude Desktop, etc.) to
    interact with the TALOS research platform through structured tool calls.

    Architecture: Clean decoupling -- this MCP server makes HTTP requests to
    the TALOS FastAPI backend running at the configurable base URL (default:
    http://127.0.0.1:8001/api/v1). No direct database or AI manager access.

    Exposes 4 tools:
    - talos_system_status: Health check with DB stats and embedding models.
    - talos_semantic_search: Natural-language vector search across papers.
    - talos_get_paper_details: Full paper record including AI evaluation.
    - talos_trigger_scrape: Launch background academic scraping pipeline.

    Key design decisions:
    - MCPServer from mcp.server.mcpserver for stdio-based MCP transport (v2.0.0).
    - requests library for synchronous HTTP calls to the FastAPI backend.
    - TALOS_API_BASE env var for configurable API location (air-gapped safe).
    - Graceful error handling: all tools return descriptive error strings
      rather than raising exceptions, ensuring LLM-friendly responses.
    - JSON text formatting for paper results to optimize LLM comprehension.

Dependencies:
    - mcp.server.mcpserver: MCPServer class for tool registration and stdio.
    - requests: HTTP client for communicating with the TALOS FastAPI backend.
    - os: Environment variable access for TALOS_API_BASE configuration.
    - json: Serialization of request bodies to the FastAPI backend.
    - typing: Type hints for tool function signatures.
"""
import os
import json
from typing import Optional, List

import requests
from mcp.server.mcpserver import MCPServer

# -- Configuration ---------------------------------------------------------
TALOS_API_BASE: str = os.environ.get(
    "TALOS_API_BASE",
    "http://127.0.0.1:8001/api/v1",
).rstrip("/")

REQUEST_TIMEOUT: int = int(os.environ.get("TALOS_MCP_TIMEOUT", "30"))

# -- MCP Server Initialization ---------------------------------------------
mcp = MCPServer(name="TALOS_Academic_Researcher", version="5.8.3")


# =============================================================================
# TOOL: talos_system_status
# =============================================================================

@mcp.tool()
def talos_system_status() -> str:
    """Query the TALOS FastAPI backend health endpoint and return a formatted
    summary of database statistics and available embedding models.

    Returns:
        str: Human-readable summary of system health, or an error message if
             the FastAPI backend is unreachable.
    """
    try:
        resp = requests.get(
            f"{TALOS_API_BASE}/health",
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        return "TALOS FastAPI Core is offline on port 8001."
    except requests.exceptions.Timeout:
        return "TALOS FastAPI Core health check timed out (port 8001)."
    except requests.exceptions.RequestException as e:
        return f"TALOS FastAPI Core health check failed: {str(e)}"
    except json.JSONDecodeError:
        return "TALOS FastAPI Core returned an unparseable response."

    # -- Build formatted output --------------------------------------------
    lines: List[str] = []
    lines.append("=== TALOS System Status ===")
    lines.append(f"API Version: {data.get('api_version', 'unknown')}")
    lines.append(f"Status: {data.get('status', 'unknown')}")
    lines.append(f"Timestamp: {data.get('timestamp', 'unknown')}")
    lines.append("")

    # -- Database statistics -----------------------------------------------
    db_stats = data.get("db_stats", {})
    lines.append("--- Database Statistics ---")
    if isinstance(db_stats, dict):
        for key, value in db_stats.items():
            lines.append(f"  {key}: {value}")
    else:
        lines.append(f"  {db_stats}")
    lines.append("")

    # -- Embedding models --------------------------------------------------
    embedding_models = data.get("embedding_models", [])
    lines.append("--- Available Embedding Models ---")
    if embedding_models:
        for model in embedding_models:
            if isinstance(model, dict):
                label = model.get("model_label", "unknown")
                count = model.get("paper_count", 0)
                lines.append(f"  {label}: {count} papers")
            else:
                lines.append(f"  {model}")
    else:
        lines.append("  No embedding models found.")

    return "\n".join(lines)


# =============================================================================
# TOOL: talos_semantic_search
# =============================================================================

@mcp.tool()
def talos_semantic_search(query: str, top_k: int = 5) -> str:
    """Perform a semantic (vector-based) search across the TALOS paper database.

    The query is embedded using the configured AI provider and matched against
    stored paper embeddings via cosine similarity.

    Args:
        query: Natural-language research question or topic (min 3 characters).
        top_k: Maximum number of results to return (default 5, range 1-200).

    Returns:
        str: Formatted list of matching papers with ID, title, authors, year,
             and overall relevance score, or an error message.
    """
    # -- Validate inputs ---------------------------------------------------
    query = query.strip()
    if len(query) < 3:
        return "Error: query must be at least 3 characters long."
    top_k = max(1, min(top_k, 200))

    # -- Call FastAPI backend ----------------------------------------------
    try:
        resp = requests.post(
            f"{TALOS_API_BASE}/search/semantic",
            json={"query": query, "top_k": top_k},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        return "TALOS FastAPI Core is offline on port 8001."
    except requests.exceptions.Timeout:
        return "TALOS FastAPI Core semantic search timed out."
    except requests.exceptions.RequestException as e:
        return f"Semantic search request failed: {str(e)}"
    except json.JSONDecodeError:
        return "TALOS FastAPI Core returned an unparseable response."

    # -- Format results ----------------------------------------------------
    results = data.get("results", [])
    model_used = data.get("model_used", "unknown")

    if not results:
        return (
            f"Semantic search completed (model: {model_used}). "
            f"No matching papers found for query: \"{query}\""
        )

    lines: List[str] = []
    lines.append(f"Semantic Search Results (model: {model_used})")
    lines.append(f"Query: \"{query}\"")
    lines.append(f"Found {len(results)} paper(s):")
    lines.append("-" * 60)

    for i, paper in enumerate(results, 1):
        pid = paper.get("id", "?")
        title = paper.get("title", "Untitled")
        authors = paper.get("authors", "Unknown")
        year = paper.get("publication_year", "?")
        score = paper.get("overall_score", 0.0)
        lines.append(
            f"{i}. [ID:{pid}] {title}"
        )
        lines.append(f"   Authors: {authors}")
        lines.append(f"   Year: {year} | Score: {score:.1f}")
        lines.append("")

    return "\n".join(lines)


# =============================================================================
# TOOL: talos_get_paper_details
# =============================================================================

@mcp.tool()
def talos_get_paper_details(paper_id: int) -> str:
    """Retrieve the complete record for a specific paper by its database ID.

    Includes all metadata, abstract, AI evaluation scores, reasoning,
    suggested tags, and Open Access links.

    Args:
        paper_id: The integer database ID of the paper to retrieve.

    Returns:
        str: Full paper record as formatted text with sections for metadata,
             evaluation, and enrichment data, or an error message.
    """
    if paper_id < 1:
        return "Error: paper_id must be a positive integer."

    # -- Call FastAPI backend ----------------------------------------------
    try:
        resp = requests.get(
            f"{TALOS_API_BASE}/papers/{paper_id}",
            timeout=REQUEST_TIMEOUT,
        )
        if resp.status_code == 404:
            return f"Paper with ID {paper_id} not found in the TALOS database."
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        return "TALOS FastAPI Core is offline on port 8001."
    except requests.exceptions.Timeout:
        return "TALOS FastAPI Core paper lookup timed out."
    except requests.exceptions.RequestException as e:
        return f"Paper lookup request failed: {str(e)}"
    except json.JSONDecodeError:
        return "TALOS FastAPI Core returned an unparseable response."

    # -- Build formatted output --------------------------------------------
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append(f"PAPER DETAILS - ID: {paper_id}")
    lines.append("=" * 70)
    lines.append("")

    # -- Basic metadata ----------------------------------------------------
    lines.append("--- Basic Metadata ---")
    lines.append(f"  Title:       {data.get('title', 'Untitled')}")
    lines.append(f"  Authors:     {data.get('authors', 'Unknown')}")
    lines.append(f"  Year:        {data.get('publication_year', '?')}")
    lines.append(f"  DOI:         {data.get('doi', 'N/A')}")
    lines.append(f"  Source:      {data.get('source', 'N/A')}")
    lines.append(f"  Publisher:   {data.get('publisher', 'N/A')}")
    lines.append(f"  OA Status:   {data.get('oa_status', 'N/A')}")
    lines.append(f"  URL:         {data.get('url', 'N/A')}")
    lines.append(f"  OA PDF URL:  {data.get('oa_pdf_url', 'N/A')}")
    lines.append("")

    # -- Abstract ----------------------------------------------------------
    abstract = data.get("abstract", "")
    if abstract:
        lines.append("--- Abstract ---")
        lines.append(abstract)
        lines.append("")

    # -- AI Evaluation Scores ----------------------------------------------
    lines.append("--- AI Evaluation Scores ---")
    lines.append(f"  Strategic:    {data.get('strategic_score', 0)}/10")
    lines.append(f"  Operational:  {data.get('operational_score', 0)}/10")
    lines.append(f"  Tactical:     {data.get('tactical_score', 0)}/10")
    lines.append(f"  Playground:   {data.get('playground_score', 0)}/10")
    lines.append(f"  Overall:      {data.get('overall_score', 0.0):.1f}/10")
    lines.append("")

    # -- Evaluation Reasoning ----------------------------------------------
    reasoning = data.get("evaluation_reasoning", "")
    if reasoning:
        lines.append("--- Evaluation Reasoning ---")
        lines.append(reasoning)
        lines.append("")

    contribution = data.get("evaluation_contribution", "")
    if contribution:
        lines.append("--- Research Contribution ---")
        lines.append(contribution)
        lines.append("")

    utilization = data.get("evaluation_utilization", "")
    if utilization:
        lines.append("--- Practical Utilization ---")
        lines.append(utilization)
        lines.append("")

    # -- Suggested Classification ------------------------------------------
    tags = data.get("suggested_tags", "")
    folder = data.get("suggested_folder", "")
    channel = data.get("suggested_discord_channel", "")
    if tags or folder or channel:
        lines.append("--- Suggested Classification ---")
        if tags:
            lines.append(f"  Tags:            {tags}")
        if folder:
            lines.append(f"  Folder:          {folder}")
        if channel:
            lines.append(f"  Discord Channel: {channel}")
        lines.append("")

    # -- Enrichment & Identifiers ------------------------------------------
    lines.append("--- Enrichment & Identifiers ---")
    lines.append(f"  Enrichment Status: {data.get('enrichment_status', 0)}")
    lines.append(f"  Embedding Model:   {data.get('embedding_model', 'N/A')}")
    lines.append(f"  OpenAlex ID:       {data.get('openalex_id', 'N/A')}")
    lines.append(f"  PMID:              {data.get('pmid', 'N/A')}")
    lines.append(f"  PMCID:             {data.get('pmcid', 'N/A')}")
    lines.append(f"  Journal ISSN:      {data.get('journal_issn', 'N/A')}")
    lines.append(f"  In Zotero:         {'Yes' if data.get('in_zotero', 0) else 'No'}")
    lines.append(f"  Processed At:      {data.get('processed_at', 'N/A')}")
    lines.append(f"  Last Evaluated:    {data.get('last_evaluated_at', 'N/A')}")
    lines.append("")
    lines.append("=" * 70)

    return "\n".join(lines)


# =============================================================================
# TOOL: talos_trigger_scrape
# =============================================================================

@mcp.tool()
def talos_trigger_scrape(sources: Optional[List[str]] = None) -> str:
    """Trigger the TALOS academic scraping pipeline to fetch new papers from
    configured sources. The scrape runs in the background on the FastAPI server.

    Args:
        sources: Optional list of source names to query (e.g. ['arxiv', 'ieee']).
                 If None or empty, all 14 configured sources are queried.

    Returns:
        str: Confirmation message with the background task ID, or an error
             message if the scrape could not be started.
    """
    # -- Build request body ------------------------------------------------
    request_body: dict = {}
    if sources is not None and len(sources) > 0:
        request_body["source_filter"] = sources

    # -- Call FastAPI backend ----------------------------------------------
    try:
        resp = requests.post(
            f"{TALOS_API_BASE}/scrape/trigger",
            json=request_body,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.exceptions.ConnectionError:
        return "TALOS FastAPI Core is offline on port 8001."
    except requests.exceptions.Timeout:
        return "TALOS FastAPI Core scrape trigger timed out."
    except requests.exceptions.RequestException as e:
        return f"Scrape trigger request failed: {str(e)}"
    except json.JSONDecodeError:
        return "TALOS FastAPI Core returned an unparseable response."

    # -- Format response ---------------------------------------------------
    task_id = data.get("task_id", "unknown")
    status = data.get("status", "unknown")
    progress = data.get("progress", "")

    source_info = ", ".join(sources) if sources else "all 14 sources"
    lines: List[str] = []
    lines.append("Background scrape task started successfully.")
    lines.append(f"  Task ID: {task_id}")
    lines.append(f"  Status:  {status}")
    lines.append(f"  Sources: {source_info}")
    if progress:
        lines.append(f"  Progress: {progress}")
    lines.append("")
    lines.append(f"Monitor progress via GET /api/v1/tasks/{task_id} or use the TALOS dashboard.")

    return "\n".join(lines)


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    mcp.run_stdio_async()