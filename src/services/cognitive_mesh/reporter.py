# -*- coding: utf-8 -*-
"""
Module: reporter.py
Project: TALOS v5.21.0
Description:
    Dual Intelligence Reporter for the Cognitive Mesh in-tree microservice. It
    renders a MarketIntelligenceReport into two deliverables under
    ``data/reports/llm_intelligence/``: a Markdown market-intelligence summary
    and a 100 percent standalone, zero-dependency, responsive Dark Theme HTML
    dashboard. The HTML embeds all CSS and vanilla JavaScript inline (no
    external CDN script or stylesheet links), satisfying the air-gapped mandate.

    Key design decisions:
    - Both reports share a single source of truth (the MarketIntelligenceReport
      DTO) so the Markdown and HTML can never drift.
    - The HTML dashboard exposes client-side filter buttons and colored VRAM
      badges (green for local fit, amber for cloud, blue for frontier) driven
      by a tiny inline script with zero external dependencies.
    - The output directory is created idempotently; filenames are date-stamped
      as ``llm_market_intelligence_YYYYMMDD.{md,html}``.

Dependencies:
    - pathlib, datetime, html (stdlib): path handling, timestamps, and escaping.
    - typing: type annotations (List, Dict, Any, Tuple).
    - src.services.cognitive_mesh.dto: MarketIntelligenceReport / ScavengedModel.
"""

import html as _html
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.services.cognitive_mesh.dto import MarketIntelligenceReport, ScavengedModel


class IntelligenceReporter:
    """Render dual market-intelligence reports (Markdown and standalone HTML)."""

    DEFAULT_OUTPUT_DIR = Path("data/reports/llm_intelligence")

    def generate_reports(
        self,
        report_data: MarketIntelligenceReport,
        output_dir: Path = DEFAULT_OUTPUT_DIR,
    ) -> Tuple[Path, Path]:
        """Render and persist both the Markdown and HTML deliverables.

        Args:
            report_data (MarketIntelligenceReport): The scavenging result.
            output_dir (Path): Target directory for the generated files.

        Returns:
            tuple[Path, Path]: The (markdown_path, html_path) pair.
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y%m%d")
        md_path = output_dir / f"llm_market_intelligence_{date_str}.md"
        html_path = output_dir / f"llm_market_intelligence_{date_str}.html"
        md_path.write_text(self._render_markdown(report_data), encoding="utf-8")
        html_path.write_text(self._render_html(report_data), encoding="utf-8")
        return md_path, html_path

    # ------------------------------------------------------------------
    # -- Markdown report ------------------------------------------------
    # ------------------------------------------------------------------

    def _render_markdown(self, report: MarketIntelligenceReport) -> str:
        lines: List[str] = []
        lines.append("# LLM Market Intelligence Report")
        lines.append("")
        lines.append(f"- Generated: {report.generated_at}")
        lines.append(f"- Discovery window: {report.window_days} days")
        lines.append(f"- Sources queried: {', '.join(report.sources_queried) or 'none'}")
        lines.append(f"- Sources failed: {', '.join(report.sources_failed) or 'none'}")
        lines.append(f"- Offline fallback: {report.offline_fallback}")
        lines.append("")
        lines.append("## Executive Summary")
        lines.append("")
        lines.append(
            f"The autonomous scavenger scanned {report.total_models_scanned} "
            f"models across {len(report.sources_queried)} sources and reconciled "
            f"them against the RTX 4070 (12 GB VRAM) budget. "
            f"{report.local_optimal_count} models fit locally, "
            f"{report.cloud_cost_effective_count} are cost-effective through "
            f"cloud APIs, and {report.frontier_reasoning_count} are frontier "
            f"reasoning architectures reserved for deep scientific audit."
        )
        lines.append("")
        lines.append("## Summary Statistics")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("| --- | --- |")
        lines.append(f"| Total Models Scanned | {report.total_models_scanned} |")
        lines.append(f"| Active Providers | {report.active_providers} |")
        lines.append(
            f"| Average Price per 1M Tokens (USD) | "
            f"{report.average_price_per_1m_usd:.4f} |"
        )
        lines.append(f"| Local Optimal (RTX 4070) | {report.local_optimal_count} |")
        lines.append(
            f"| Cloud Cost-Effective | {report.cloud_cost_effective_count} |"
        )
        lines.append(f"| Frontier Reasoning | {report.frontier_reasoning_count} |")
        lines.append("")
        lines.append("## Discovered Models")
        lines.append("")
        lines.append(
            "| Model | Developer | Parameters | Context | Pricing ($/1M) | "
            "MMLU-Pro | HumanEval | TTFT (ms) | Recommended Role | VRAM Class |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        for model in report.models:
            price = (
                f"{model.pricing_prompt_per_1m_usd + model.pricing_completion_per_1m_usd:.4f}"
                if (model.pricing_prompt_per_1m_usd or model.pricing_completion_per_1m_usd)
                else "-"
            )
            lines.append(
                f"| {self._md_cell(model.model)} | {self._md_cell(model.developer)} "
                f"| {model.parameter_count_label or '-'} | {model.context_window or '-'} "
                f"| {price} | {model.mmlu_pro or '-'} | {model.human_eval or '-'} "
                f"| {model.ttft_ms or '-'} | {model.recommended_role or '-'} "
                f"| {model.vram_class} |"
            )
        lines.append("")
        lines.append("## Hardware Recommendations (RTX 4070, 12 GB VRAM)")
        lines.append("")
        lines.append(
            "The active local runtime prefers GGUF Q4_K_M / Q8_0 quantized "
            "models at or below 14B parameters, or FP16 models at or below 7B "
            "parameters, bounded by threading.Semaphore(2) concurrency. The "
            "following local-optimal models are recommended for air-gapped "
            "operation:"
        )
        lines.append("")
        local_models = [m for m in report.models if m.vram_class == "LOCAL_OPTIMAL"]
        if local_models:
            for model in local_models[:10]:
                lines.append(
                    f"- {model.model} ({model.recommended_role or 'unclassified'})"
                )
        else:
            lines.append("- No local-optimal models discovered in this window.")
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _md_cell(value: Any) -> str:
        text = "" if value is None else str(value)
        return text.replace("|", "\\|")

    # ------------------------------------------------------------------
    # -- HTML report ----------------------------------------------------
    # ------------------------------------------------------------------

    def _render_html(self, report: MarketIntelligenceReport) -> str:
        cards = "\n".join(self._render_card(m) for m in report.models)
        timestamp = report.generated_at or datetime.now().strftime("%Y-%m-%d")
        stats = (
            f'<div class="stat"><span class="stat-num">'
            f'{report.total_models_scanned}</span>'
            f'<span class="stat-label">Models Scanned</span></div>'
            f'<div class="stat"><span class="stat-num">'
            f'{report.active_providers}</span>'
            f'<span class="stat-label">Active Providers</span></div>'
            f'<div class="stat"><span class="stat-num">'
            f'{report.average_price_per_1m_usd:.2f}</span>'
            f'<span class="stat-label">Avg Price /1M Tokens</span></div>'
        )
        return (
            "<!DOCTYPE html>\n"
            '<html lang="en">\n'
            "<head>\n"
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            "<title>LLM Market Intelligence</title>\n"
            f"<style>{_HTML_CSS}</style>\n"
            "</head>\n"
            "<body>\n"
            '<header class="hero">\n'
            "<h1>LLM Market Intelligence</h1>\n"
            f'<p class="subtitle">Autonomous Model Scavenger Report &middot; '
            f"{_html.escape(timestamp)}</p>\n"
            "</header>\n"
            '<section class="stats">\n'
            f"{stats}\n"
            "</section>\n"
            '<section class="filters" role="toolbar" aria-label="Model filters">\n'
            '<button class="filter active" data-filter="all" '
            'onclick="filterModels(\'all\')">All Models</button>\n'
            '<button class="filter" data-filter="LOCAL_OPTIMAL" '
            'onclick="filterModels(\'LOCAL_OPTIMAL\')">Local RTX 4070 '
            "(&lt;12GB)</button>\n"
            '<button class="filter" data-filter="CLOUD_COST_EFFECTIVE" '
            'onclick="filterModels(\'CLOUD_COST_EFFECTIVE\')">Cloud '
            "High-Throughput</button>\n"
            '<button class="filter" data-filter="FRONTIER_REASONING" '
            'onclick="filterModels(\'FRONTIER_REASONING\')">Deep '
            "Reasoning</button>\n"
            "</section>\n"
            '<main class="grid">\n'
            f"{cards}\n"
            "</main>\n"
            f"<script>{_HTML_JS}</script>\n"
            "</body>\n"
            "</html>\n"
        )

    @staticmethod
    def _render_card(model: ScavengedModel) -> str:
        label, cls = _badge(model.vram_class)
        price = (
            model.pricing_prompt_per_1m_usd + model.pricing_completion_per_1m_usd
        )
        price_text = f"${price:.2f}" if price else "-"
        return (
            f'<article class="card" data-vram="{model.vram_class}">\n'
            '<div class="card-head">\n'
            f"<h3>{_html.escape(model.model or 'Unnamed')}</h3>\n"
            f'<span class="badge {cls}">{label}</span>\n'
            "</div>\n"
            f'<p class="dev">{_html.escape(model.developer or "Unknown")}</p>\n'
            "<ul>\n"
            f"<li>Parameters: {model.parameter_count_label or '-'}</li>\n"
            f"<li>Context: {model.context_window or '-'} tokens</li>\n"
            f"<li>Pricing: {price_text} /1M</li>\n"
            f"<li>MMLU-Pro: {model.mmlu_pro or '-'}</li>\n"
            f"<li>HumanEval: {model.human_eval or '-'}</li>\n"
            f"<li>TTFT: {model.ttft_ms or '-'} ms</li>\n"
            f"<li>Role: {_html.escape(model.recommended_role or '-')}</li>\n"
            "</ul>\n"
            "</article>\n"
        )


def _badge(vram_class: str) -> Tuple[str, str]:
    """Map a VRAM class to a (label, css-class) badge pair.

    Args:
        vram_class (str): LOCAL_OPTIMAL, CLOUD_COST_EFFECTIVE, or
            FRONTIER_REASONING.

    Returns:
        tuple[str, str]: The human-readable label and CSS badge class.
    """
    if vram_class == "LOCAL_OPTIMAL":
        return "Local VRAM Fit", "badge-local"
    if vram_class == "FRONTIER_REASONING":
        return "Frontier", "badge-frontier"
    return "Cloud API", "badge-cloud"


# -- Embedded Dark Theme CSS (zero external dependencies) ----------------------
_HTML_CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  background: #0b1020; color: #e6ebf4;
  font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
  line-height: 1.5; padding: 2rem 1.5rem;
}
.hero { text-align: center; margin-bottom: 2rem; }
.hero h1 { font-size: 2rem; letter-spacing: 0.02em; color: #7fd1ff; }
.subtitle { color: #8a97b0; margin-top: 0.4rem; }
.stats {
  display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center;
  margin-bottom: 2rem;
}
.stat {
  background: #141b30; border: 1px solid #24314f; border-radius: 12px;
  padding: 1rem 1.5rem; min-width: 160px; text-align: center;
}
.stat-num { display: block; font-size: 1.6rem; font-weight: 700; color: #7fd1ff; }
.stat-label { color: #8a97b0; font-size: 0.85rem; text-transform: uppercase; }
.filters { display: flex; flex-wrap: wrap; gap: 0.6rem; justify-content: center; margin-bottom: 2rem; }
.filter {
  background: #141b30; color: #c4cde0; border: 1px solid #2c3a5c;
  border-radius: 999px; padding: 0.5rem 1.1rem; cursor: pointer;
  font-size: 0.9rem; transition: all 0.15s ease;
}
.filter:hover { border-color: #7fd1ff; }
.filter.active { background: #1d4f7a; border-color: #7fd1ff; color: #ffffff; }
.grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.2rem; max-width: 1200px; margin: 0 auto;
}
.card {
  background: #121829; border: 1px solid #23304c; border-radius: 14px;
  padding: 1.2rem; transition: transform 0.15s ease, border-color 0.15s ease;
}
.card:hover { transform: translateY(-3px); border-color: #7fd1ff; }
.card-head { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; }
.card-head h3 { font-size: 1.05rem; color: #e6ebf4; word-break: break-word; }
.dev { color: #8a97b0; font-size: 0.85rem; margin: 0.4rem 0 0.8rem; }
.card ul { list-style: none; font-size: 0.9rem; color: #c4cde0; }
.card li { padding: 0.15rem 0; }
.badge { font-size: 0.72rem; font-weight: 700; padding: 0.25rem 0.6rem; border-radius: 999px; white-space: nowrap; }
.badge-local { background: #0f3d2e; color: #6ee7a8; border: 1px solid #1f7a52; }
.badge-cloud { background: #4a3410; color: #f3c46b; border: 1px solid #8a6a1f; }
.badge-frontier { background: #102a4a; color: #6fb8ff; border: 1px solid #2a6aa8; }
@media (max-width: 640px) {
  body { padding: 1rem 0.8rem; }
  .hero h1 { font-size: 1.5rem; }
}
"""

# -- Embedded vanilla JavaScript (zero external dependencies) ------------------
_HTML_JS = """
function filterModels(cls) {
  var buttons = document.querySelectorAll('.filter');
  buttons.forEach(function (b) {
    b.classList.toggle('active', b.getAttribute('data-filter') === cls);
  });
  document.querySelectorAll('.card').forEach(function (card) {
    var match = cls === 'all' || card.getAttribute('data-vram') === cls;
    card.style.display = match ? '' : 'none';
  });
}
"""



