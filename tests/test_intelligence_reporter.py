# -*- coding: utf-8 -*-
"""
Module: test_intelligence_reporter.py
Project: TALOS v5.21.0
Description:
    Unit tests for the Dual Intelligence Reporter
    (src/services/cognitive_mesh/reporter.py). Verifies that both the Markdown
    and the standalone HTML dashboard are written to the output directory, that
    the HTML embeds zero external script/stylesheet/CDN dependencies, and that
    the interactive filter controls and VRAM badges are present.
"""

from src.services.cognitive_mesh.dto import MarketIntelligenceReport, ScavengedModel
from src.services.cognitive_mesh.reporter import IntelligenceReporter


def _sample_report():
    return MarketIntelligenceReport(
        generated_at="2026-10-03T00:00:00Z",
        window_days=30,
        sources_queried=["huggingface", "openrouter", "ollama"],
        models=[
            ScavengedModel(
                model="qwen2.5:14b",
                developer="Ollama",
                parameter_count_b=14.0,
                parameter_count_label="14B",
                source="ollama",
                vram_class="LOCAL_OPTIMAL",
                recommended_role="Kitchenham Rigor",
            ),
            ScavengedModel(
                model="openai/gpt-6.1-sol",
                developer="OpenRouter",
                parameter_count_b=None,
                context_window=1050000,
                source="openrouter",
                vram_class="FRONTIER_REASONING",
                recommended_role="Kitchenham Rigor",
                pricing_prompt_per_1m_usd=6.0,
                pricing_completion_per_1m_usd=12.0,
            ),
        ],
        total_models_scanned=2,
        active_providers=5,
        average_price_per_1m_usd=9.0,
        local_optimal_count=1,
        cloud_cost_effective_count=0,
        frontier_reasoning_count=1,
    )


class TestIntelligenceReporter:
    def test_generates_md_and_html(self, tmp_path):
        reporter = IntelligenceReporter()
        md_path, html_path = reporter.generate_reports(
            _sample_report(), output_dir=tmp_path
        )
        assert md_path.exists()
        assert html_path.exists()
        assert md_path.suffix == ".md"
        assert html_path.suffix == ".html"

    def test_html_has_zero_external_dependencies(self, tmp_path):
        reporter = IntelligenceReporter()
        _, html_path = reporter.generate_reports(
            _sample_report(), output_dir=tmp_path
        )
        content = html_path.read_text(encoding="utf-8")
        assert "<script src=" not in content
        assert '<link rel="stylesheet"' not in content
        assert "http://" not in content
        assert "https://" not in content

    def test_html_contains_filters_and_badges(self, tmp_path):
        reporter = IntelligenceReporter()
        _, html_path = reporter.generate_reports(
            _sample_report(), output_dir=tmp_path
        )
        content = html_path.read_text(encoding="utf-8")
        assert "Local RTX 4070" in content
        assert "Deep Reasoning" in content
        assert "data-vram" in content
        assert "badge-local" in content
        assert "badge-frontier" in content

    def test_markdown_contains_summary_table(self, tmp_path):
        reporter = IntelligenceReporter()
        md_path, _ = reporter.generate_reports(
            _sample_report(), output_dir=tmp_path
        )
        content = md_path.read_text(encoding="utf-8")
        assert "## Executive Summary" in content
        assert "## Discovered Models" in content
        assert "Total Models Scanned" in content
