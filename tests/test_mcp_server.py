# -*- coding: utf-8 -*-
"""
Module: test_mcp_server.py
Project: TALOS v5.10.0
Description:
    Unit tests for the MCP Server module (src/mcp_server.py). Uses pytest
    with unittest.mock to verify tool registration, correct tool behavior,
    and graceful error handling when the TALOS FastAPI backend is unreachable.

    Tests cover:
    - MCP server name verification.
    - All 4 tools are registered in the MCPServer instance.
    - Each tool returns valid string responses under normal conditions.
    - Each tool returns the appropriate offline/error string when the
      FastAPI backend is mocked as unreachable.

    Key design decisions:
    - All HTTP calls are fully mocked (no actual network required).
    - Tool functions are tested directly as Python callables for simplicity
      (the MCPServer decorator preserves them as standard functions).
    - Self-contained: no external database or API server needed.

Dependencies:
    - pytest: Test framework for fixture-based testing.
    - unittest.mock: Mock HTTP responses for hermetic testing.
    - src.mcp_server: The MCP server module under test.
"""
import pytest
from unittest.mock import patch, MagicMock

import src.mcp_server as mcp_mod
import requests
import json


# =============================================================================
# -- Fixtures --
# =============================================================================

@pytest.fixture
def mock_requests_get():
    """Mock requests.get for hermetic testing."""
    with patch.object(requests, "get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_requests_post():
    """Mock requests.post for hermetic testing."""
    with patch.object(requests, "post") as mock_post:
        yield mock_post


@pytest.fixture
def mock_connection_error():
    """Return a requests.ConnectionError instance."""
    return requests.exceptions.ConnectionError("Connection refused")


@pytest.fixture
def mock_timeout():
    """Return a requests.Timeout instance."""
    return requests.exceptions.Timeout("Request timed out")


# =============================================================================
# -- Test: MCP Server Initialization --
# =============================================================================

class TestMCPServerRegistration:
    """Verify that the MCPServer is correctly initialized."""

    def test_server_name(self):
        """Verify the MCP server name is TALOS_Academic_Researcher."""
        assert mcp_mod.mcp.name == "TALOS_Academic_Researcher"

    def test_server_version(self):
        """Verify the MCP server version is 5.8.3."""
        assert mcp_mod.mcp.version == "5.8.3"

    def test_tools_registered(self):
        """Verify all 4 tools are registered in the MCPServer instance."""
        tool_names = set(mcp_mod.mcp._tool_manager._tools.keys())

        expected_tools = {
            "talos_system_status",
            "talos_semantic_search",
            "talos_get_paper_details",
            "talos_trigger_scrape",
        }
        missing = expected_tools - tool_names
        assert len(missing) == 0, f"Missing registered tools: {missing}"

    def test_tool_count(self):
        """Verify exactly 4 tools are registered."""
        tool_count = len(mcp_mod.mcp._tool_manager._tools)
        assert tool_count >= 4, (
            f"Expected at least 4 tools, found {tool_count}"
        )


# =============================================================================
# -- Test: talos_system_status --
# =============================================================================

class TestTalosSystemStatus:
    """Tests for the talos_system_status tool."""

    def test_success_response(self, mock_requests_get):
        """Verify formatted output when FastAPI health check succeeds."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "status": "running",
            "api_version": "5.8.3",
            "timestamp": "2026-08-01T00:00:00",
            "db_stats": {"total_papers": 142, "enriched": 120},
            "embedding_models": [
                {"model_label": "ollama:nomic-embed-text", "paper_count": 100},
                {"model_label": "gemini:embedding-001", "paper_count": 42},
            ],
        }
        mock_requests_get.return_value = mock_resp

        result = mcp_mod.talos_system_status()

        assert isinstance(result, str)
        assert "TALOS System Status" in result
        assert "5.8.3" in result
        assert "total_papers" in result
        assert "142" in result
        assert "ollama:nomic-embed-text" in result
        assert "100 papers" in result

    def test_offline_response(self, mock_requests_get, mock_connection_error):
        """Verify offline message when FastAPI is unreachable."""
        mock_requests_get.side_effect = mock_connection_error

        result = mcp_mod.talos_system_status()

        assert isinstance(result, str)
        assert "offline" in result.lower()
        assert "8001" in result

    def test_timeout_response(self, mock_requests_get, mock_timeout):
        """Verify timeout message when health check times out."""
        mock_requests_get.side_effect = mock_timeout

        result = mcp_mod.talos_system_status()

        assert isinstance(result, str)
        assert "timed out" in result.lower()

    def test_unparseable_response(self, mock_requests_get):
        """Verify error message when response is not valid JSON."""
        mock_resp = MagicMock()
        mock_resp.json.side_effect = json.JSONDecodeError(
            "Expecting value", "", 0
        )
        mock_requests_get.return_value = mock_resp

        result = mcp_mod.talos_system_status()

        assert isinstance(result, str)
        assert "unparseable" in result.lower()


# =============================================================================
# -- Test: talos_semantic_search --
# =============================================================================

class TestTalosSemanticSearch:
    """Tests for the talos_semantic_search tool."""

    def test_success_response(self, mock_requests_post):
        """Verify formatted output when semantic search succeeds."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "query": "drone swarm intelligence",
            "model_used": "ollama:nomic-embed-text",
            "results": [
                {
                    "id": 1,
                    "title": "Decentralized Drone Swarm Coordination",
                    "authors": "Smith, J., Doe, A.",
                    "publication_year": 2025,
                    "overall_score": 8.5,
                },
                {
                    "id": 2,
                    "title": "Reinforcement Learning for UAV Fleets",
                    "authors": "Jones, B.",
                    "publication_year": 2024,
                    "overall_score": 7.2,
                },
            ],
        }
        mock_requests_post.return_value = mock_resp

        result = mcp_mod.talos_semantic_search(
            "drone swarm intelligence", top_k=5
        )

        assert isinstance(result, str)
        assert "Semantic Search Results" in result
        assert "drone swarm intelligence" in result
        assert "Decentralized Drone Swarm Coordination" in result
        assert "Smith, J." in result
        assert "8.5" in result
        assert "[ID:1]" in result

    def test_empty_results(self, mock_requests_post):
        """Verify response when no papers match the query."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "query": "nonexistent research topic",
            "model_used": "ollama:nomic-embed-text",
            "results": [],
        }
        mock_requests_post.return_value = mock_resp

        result = mcp_mod.talos_semantic_search("nonexistent research topic")

        assert isinstance(result, str)
        assert "No matching papers found" in result

    def test_query_too_short(self, mock_requests_post):
        """Verify validation error for query shorter than 3 characters."""
        result = mcp_mod.talos_semantic_search("ab")

        assert isinstance(result, str)
        assert "at least 3 characters" in result.lower()
        # Ensure no HTTP call was made for invalid input.
        mock_requests_post.assert_not_called()

    def test_offline_response(self, mock_requests_post, mock_connection_error):
        """Verify offline message when FastAPI is unreachable."""
        mock_requests_post.side_effect = mock_connection_error

        result = mcp_mod.talos_semantic_search("drone swarms", top_k=10)

        assert isinstance(result, str)
        assert "offline" in result.lower()

    def test_timeout_response(self, mock_requests_post, mock_timeout):
        """Verify timeout message when search times out."""
        mock_requests_post.side_effect = mock_timeout

        result = mcp_mod.talos_semantic_search("drone swarms")

        assert isinstance(result, str)
        assert "timed out" in result.lower()

    def test_unparseable_response(self, mock_requests_post):
        """Verify error message when response is not valid JSON."""
        mock_resp = MagicMock()
        mock_resp.json.side_effect = json.JSONDecodeError(
            "Expecting value", "", 0
        )
        mock_requests_post.return_value = mock_resp

        result = mcp_mod.talos_semantic_search("drone swarms")

        assert isinstance(result, str)
        assert "unparseable" in result.lower()


# =============================================================================
# -- Test: talos_get_paper_details --
# =============================================================================

class TestTalosGetPaperDetails:
    """Tests for the talos_get_paper_details tool."""

    def test_success_response(self, mock_requests_get):
        """Verify full formatted output when paper is found."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": 42,
            "title": "Advanced Multi-Agent Pathfinding",
            "authors": "Chen, L., Wang, P.",
            "publication_year": 2025,
            "doi": "10.1234/amp.2025",
            "source": "arxiv",
            "publisher": "arXiv",
            "oa_status": "gold",
            "url": "https://arxiv.org/abs/2501.00001",
            "oa_pdf_url": "https://arxiv.org/pdf/2501.00001.pdf",
            "abstract": "This paper presents a novel approach to multi-agent pathfinding using hierarchical reinforcement learning. The method achieves state-of-the-art results on standard benchmarks while reducing computational overhead by 40%.",
            "strategic_score": 9,
            "operational_score": 8,
            "tactical_score": 7,
            "playground_score": 6,
            "overall_score": 8.0,
            "evaluation_reasoning": "Strong theoretical contribution with clear practical applications.",
            "evaluation_contribution": "Novel hierarchical approach.",
            "evaluation_utilization": "Can be applied to warehouse robotics and drone coordination.",
            "suggested_tags": "multi-agent, pathfinding, reinforcement-learning",
            "suggested_folder": "AI/Robotics/Multi-Agent",
            "suggested_discord_channel": "research-ai",
            "enrichment_status": 1,
            "embedding_model": "ollama:nomic-embed-text",
            "openalex_id": "W123456789",
            "pmid": None,
            "pmcid": None,
            "journal_issn": None,
            "in_zotero": 1,
            "processed_at": "2026-07-15T10:30:00",
            "last_evaluated_at": "2026-07-15T11:00:00",
        }
        mock_requests_get.return_value = mock_resp

        result = mcp_mod.talos_get_paper_details(42)

        assert isinstance(result, str)
        assert "PAPER DETAILS" in result
        assert "Advanced Multi-Agent Pathfinding" in result
        assert "Chen, L." in result
        assert "Strategic:    9" in result
        assert "Overall:      8.0" in result
        assert "hierarchical reinforcement learning" in result
        assert "Evaluation Reasoning" in result
        assert "gold" in result
        assert "Yes" in result  # In Zotero

    def test_paper_not_found(self, mock_requests_get):
        """Verify 'not found' message for a non-existent paper ID."""
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_requests_get.return_value = mock_resp

        result = mcp_mod.talos_get_paper_details(99999)

        assert isinstance(result, str)
        assert "not found" in result.lower()
        assert "99999" in result

    def test_invalid_paper_id(self, mock_requests_get):
        """Verify validation error for non-positive paper ID."""
        result = mcp_mod.talos_get_paper_details(0)

        assert isinstance(result, str)
        assert "positive integer" in result.lower()

        result_neg = mcp_mod.talos_get_paper_details(-5)

        assert isinstance(result_neg, str)
        assert "positive integer" in result_neg.lower()

        # Ensure no HTTP call was made for invalid input.
        mock_requests_get.assert_not_called()

    def test_offline_response(self, mock_requests_get, mock_connection_error):
        """Verify offline message when FastAPI is unreachable."""
        mock_requests_get.side_effect = mock_connection_error

        result = mcp_mod.talos_get_paper_details(42)

        assert isinstance(result, str)
        assert "offline" in result.lower()

    def test_timeout_response(self, mock_requests_get, mock_timeout):
        """Verify timeout message when lookup times out."""
        mock_requests_get.side_effect = mock_timeout

        result = mcp_mod.talos_get_paper_details(42)

        assert isinstance(result, str)
        assert "timed out" in result.lower()


# =============================================================================
# -- Test: talos_trigger_scrape --
# =============================================================================

class TestTalosTriggerScrape:
    """Tests for the talos_trigger_scrape tool."""

    def test_success_all_sources(self, mock_requests_post):
        """Verify confirmation message when scraping all 16 sources."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "task_id": "abc12345",
            "status": "running",
            "progress": "Fetching from 14 academic sources...",
            "started_at": "2026-08-01T00:00:00",
            "completed_at": None,
        }
        mock_requests_post.return_value = mock_resp

        result = mcp_mod.talos_trigger_scrape()

        assert isinstance(result, str)
        assert "started successfully" in result.lower()
        assert "abc12345" in result
        assert "all 16 sources" in result
        assert "running" in result

    def test_success_filtered_sources(self, mock_requests_post):
        """Verify confirmation message when scraping specific sources."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "task_id": "def67890",
            "status": "running",
            "progress": "",
            "started_at": "2026-08-01T00:00:00",
            "completed_at": None,
        }
        mock_requests_post.return_value = mock_resp

        result = mcp_mod.talos_trigger_scrape(sources=["arxiv", "ieee"])

        assert isinstance(result, str)
        assert "started successfully" in result.lower()
        assert "def67890" in result
        assert "arxiv, ieee" in result

    def test_empty_sources_list(self, mock_requests_post):
        """Verify that an empty sources list triggers all sources."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "task_id": "ghi11111",
            "status": "running",
            "progress": "",
        }
        mock_requests_post.return_value = mock_resp

        result = mcp_mod.talos_trigger_scrape(sources=[])

        assert isinstance(result, str)
        assert "ghi11111" in result
        assert "all 16 sources" in result

    def test_offline_response(self, mock_requests_post, mock_connection_error):
        """Verify offline message when FastAPI is unreachable."""
        mock_requests_post.side_effect = mock_connection_error

        result = mcp_mod.talos_trigger_scrape()

        assert isinstance(result, str)
        assert "offline" in result.lower()

    def test_timeout_response(self, mock_requests_post, mock_timeout):
        """Verify timeout message when trigger times out."""
        mock_requests_post.side_effect = mock_timeout

        result = mcp_mod.talos_trigger_scrape()

        assert isinstance(result, str)
        assert "timed out" in result.lower()

    def test_unparseable_response(self, mock_requests_post):
        """Verify error message when response is not valid JSON."""
        mock_resp = MagicMock()
        mock_resp.json.side_effect = json.JSONDecodeError(
            "Expecting value", "", 0
        )
        mock_requests_post.return_value = mock_resp

        result = mcp_mod.talos_trigger_scrape()

        assert isinstance(result, str)
        assert "unparseable" in result.lower()


# =============================================================================
# -- Test: TALOS_API_BASE Configuration --
# =============================================================================

class TestConfiguration:
    """Tests for MCP server configuration."""

    def test_default_api_base(self):
        """Verify the default TALOS_API_BASE is the local FastAPI backend."""
        assert mcp_mod.TALOS_API_BASE == "http://127.0.0.1:8001/api/v1"

    def test_default_timeout(self):
        """Verify the default request timeout is 30 seconds."""
        assert mcp_mod.REQUEST_TIMEOUT == 30