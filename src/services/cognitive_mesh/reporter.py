# -*- coding: utf-8 -*-
"""
Module: reporter.py
Project: TALOS v5.25.3
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
    - v5.23.0 adds the four-tier AccessTier taxonomy: each model carries a
      colored access-tier badge (LOCAL_NO_KEY, CLOUD_ZERO_CONFIG_FREE,
      CLOUD_FREE_TIER_WITH_KEY, CLOUD_PAID_API), tier filter buttons, and a
      dedicated zero-config free models section.
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
        lines.append("# TALOS Model Scout Intelligence Report")
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
        lines.append(f"| Local No-Key Models | {report.local_no_key_count} |")
        lines.append(
            f"| Cloud Zero-Config Free Models | {report.cloud_zero_config_free_count} |"
        )
        lines.append(
            f"| Cloud Free Tier (Key) Models | {report.cloud_free_tier_with_key_count} |"
        )
        lines.append(f"| Cloud Paid API Models | {report.cloud_paid_api_count} |")
        lines.append("")
        lines.append("## Executive Optimal Selection Matrix & FinOps")
        lines.append("")
        lines.append(
            "Champion models are selected per execution budget and costed at the "
            "estimated USD spend to process 1,000 papers. Abstract screening "
            "assumes 2,000 prompt / 500 completion tokens per paper; full-text "
            "Kitchenham audit assumes 12,000 prompt / 3,000 completion tokens "
            "per paper."
        )
        lines.append("")
        lines.append(
            "| Budget | Champion Model | Developer | Role | Parameters | "
            "MMLU-Pro | Screening /1k | Audit /1k |"
        )
        lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for champ in self._select_champions(report):
            model_cell = (
                f"[{self._md_cell(champ['model'])}]({champ['url']})"
                if champ.get("url") else self._md_cell(champ["model"])
            )
            lines.append(
                f"| {self._md_cell(champ['budget'])} | {model_cell} "
                f"| {self._md_cell(champ['developer'])} | {self._md_cell(champ['role'])} "
                f"| {champ['params']} | {champ['mmlu_pro'] or '-'} | "
                f"${champ['screening_cost_1k']:.2f} | ${champ['audit_cost_1k']:.2f} |"
            )
        lines.append("")
        lines.append("## Discovered Models")
        lines.append("")
        lines.append(
            "| Model | Developer | Parameters | Context | Pricing ($/1M) | "
            "MMLU-Pro | HumanEval | TTFT (ms) | Recommended Role | VRAM Class | "
            "Access Tier |"
        )
        lines.append(
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"
        )
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
                f"| {model.vram_class} | {model.access_tier} |"
            )
        lines.append("")
        lines.append("## Zero-Config Free Models (Air-Gapped Ready)")
        lines.append("")
        lines.append(
            "Models in the LOCAL_NO_KEY or CLOUD_ZERO_CONFIG_FREE access tiers "
            "require no API key and no paid cloud account. They are the preferred "
            "dynamic-failover targets when paid endpoints are latched or "
            "rate-limited."
        )
        lines.append("")
        free_models = [
            m for m in report.models
            if m.access_tier in ("LOCAL_NO_KEY", "CLOUD_ZERO_CONFIG_FREE")
        ]
        if free_models:
            for model in free_models[:20]:
                lines.append(
                    f"- {model.model} [{model.access_tier}] "
                    f"({model.recommended_role or 'unclassified'})"
                )
        else:
            lines.append("- No zero-config free models discovered in this window.")
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
    # -- Executive decision matrix & FinOps (v5.21.1) -------------------
    # ------------------------------------------------------------------

    @staticmethod
    def _finops_cost(
        prompt_usd: float, completion_usd: float, screening: bool
    ) -> float:
        """Estimate USD cost to process 1,000 papers for a given model.

        Abstract screening assumes 2,000 prompt tokens and 500 completion tokens
        per paper; a full-text Kitchenham audit assumes 12,000 prompt tokens and
        3,000 completion tokens per paper.

        Args:
            prompt_usd (float): Prompt price per 1M tokens.
            completion_usd (float): Completion price per 1M tokens.
            screening (bool): True for screening, False for full-text audit.

        Returns:
            float: Estimated USD cost per 1,000 papers.
        """
        if screening:
            prompt_tokens, completion_tokens = 2000, 500
        else:
            prompt_tokens, completion_tokens = 12000, 3000
        cost = (
            prompt_tokens * prompt_usd + completion_tokens * completion_usd
        ) / 1_000_000.0
        return round(cost * 1000.0, 2)

    @classmethod
    def _select_champions(cls, report: MarketIntelligenceReport) -> List[Dict[str, Any]]:
        """Select champion models for the three execution budgets.

        The Local champion is the highest-quality LOCAL_OPTIMAL model (zero
        marginal cost). The Cloud champion is the cheapest CLOUD_COST_EFFECTIVE
        model meeting a quality floor. The Frontier champion is the
        highest-quality FRONTIER_REASONING model.

        Args:
            report (MarketIntelligenceReport): The scavenged report.

        Returns:
            list[dict]: Champion descriptors with per-1k-paper cost estimates.
        """
        def pick(models: List[ScavengedModel], key, reverse: bool):
            ranked = sorted(
                [m for m in models if (key(m) or 0) > 0],
                key=key, reverse=reverse,
            )
            return ranked[0] if ranked else None

        local = pick(
            [m for m in report.models if m.vram_class == "LOCAL_OPTIMAL"],
            lambda m: m.mmlu_pro, True,
        )
        cloud_pool = [m for m in report.models if m.vram_class == "CLOUD_COST_EFFECTIVE"]
        cloud = None
        if cloud_pool:
            qualified = [m for m in cloud_pool if m.mmlu_pro >= 50.0] or cloud_pool
            cloud = min(
                qualified,
                key=lambda m: (
                    (m.pricing_prompt_per_1m_usd or 0)
                    + (m.pricing_completion_per_1m_usd or 0)
                ) or 10**9,
            )
        frontier = pick(
            [m for m in report.models if m.vram_class == "FRONTIER_REASONING"],
            lambda m: m.mmlu_pro, True,
        )

        def champion(budget: str, model: ScavengedModel) -> Dict[str, Any]:
            if model is None:
                return {
                    "budget": budget, "model": "-", "developer": "-", "role": "-",
                    "params": "-", "mmlu_pro": 0.0, "prompt_usd": 0.0,
                    "completion_usd": 0.0, "screening_cost_1k": 0.0,
                    "audit_cost_1k": 0.0, "source": "", "url": "",
                }
            prompt_usd = model.pricing_prompt_per_1m_usd or 0.0
            completion_usd = model.pricing_completion_per_1m_usd or 0.0
            return {
                "budget": budget, "model": model.model,
                "developer": model.developer or "-",
                "role": model.recommended_role or "-",
                "params": model.parameter_count_label or "-",
                "mmlu_pro": model.mmlu_pro, "prompt_usd": prompt_usd,
                "completion_usd": completion_usd,
                "screening_cost_1k": cls._finops_cost(
                    prompt_usd, completion_usd, True
                ),
                "audit_cost_1k": cls._finops_cost(
                    prompt_usd, completion_usd, False
                ),
                "source": model.source or "",
                "url": cls._get_model_canonical_url(model),
            }

        return [
            champion("Local RTX 4070 (Air-Gapped)", local),
            champion("Cloud Cost-Optimized", cloud),
            champion("Frontier Maximum Rigor", frontier),
        ]

    # ------------------------------------------------------------------
    # -- HTML report ----------------------------------------------------
    # ------------------------------------------------------------------

    def _render_html(self, report: MarketIntelligenceReport) -> str:
        cards = "\n".join(self._render_card(m) for m in report.models)
        champion_cards = self._render_champion_cards(report)
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
            "<title>TALOS Model Scout Intelligence</title>\n"
            f"<style>{_HTML_CSS}</style>\n"
            "</head>\n"
            "<body>\n"
            '<header class="hero">\n'
            "<h1>TALOS Model Scout Intelligence</h1>\n"
            f'<p class="subtitle">Autonomous Model Scout Report &middot; '
            f"{_html.escape(timestamp)}</p>\n"
            "</header>\n"
            '<section class="stats">\n'
            f"{stats}\n"
            "</section>\n"
            '<section class="champions">\n'
            f"{champion_cards}\n"
            "</section>\n"
            '<section class="search" role="search" aria-label="Model search">\n'
            '<input type="text" id="model-search" '
            'placeholder="Search by model name or developer..." '
            'oninput="searchModels(this.value)">\n'
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
            '<button class="filter" data-filter="LOCAL_NO_KEY" '
            'onclick="filterModels(\'LOCAL_NO_KEY\')">Local No-Key</button>\n'
            '<button class="filter" data-filter="CLOUD_ZERO_CONFIG_FREE" '
            'onclick="filterModels(\'CLOUD_ZERO_CONFIG_FREE\')">Zero-Config '
            "Free</button>\n"
            '<button class="filter" data-filter="CLOUD_FREE_TIER_WITH_KEY" '
            'onclick="filterModels(\'CLOUD_FREE_TIER_WITH_KEY\')">Free Tier '
            "(Key)</button>\n"
            '<button class="filter" data-filter="CLOUD_PAID_API" '
            'onclick="filterModels(\'CLOUD_PAID_API\')">Paid API</button>\n'
            "</section>\n"
            '<main class="grid">\n'
            f"{cards}\n"
            "</main>\n"
            f"<script>{_HTML_JS}</script>\n"
            "</body>\n"
            "</html>\n"
        )

    @staticmethod
    def _get_model_canonical_url(model: ScavengedModel) -> str:
        """Resolve the canonical external catalog URL for a scavenged model.

        Maps the discovery ``source`` to its authoritative model-catalog entry so
        every model card and Markdown row can link directly to the upstream
        record in a new browser tab.

        Args:
            model (ScavengedModel): The scavenged model record.

        Returns:
            str: The canonical URL, or an empty string when the source is not a
                supported external catalog (e.g. internal benchmark records).
        """
        model_id = (model.model or "").strip()
        source = (model.source or "").strip().lower()
        if not model_id:
            return ""
        if source == "huggingface":
            return f"https://huggingface.co/{model_id}"
        if source == "openrouter":
            return f"https://openrouter.ai/models/{model_id}"
        if source == "ollama":
            base_name = model_id.split(":")[0]
            return f"https://ollama.com/library/{base_name}"
        return ""

    @staticmethod
    def _render_card(model: ScavengedModel) -> str:
        label, cls = _badge(model.vram_class)
        tier_label, tier_cls = _tier_badge(model.access_tier)
        price = (
            model.pricing_prompt_per_1m_usd + model.pricing_completion_per_1m_usd
        )
        price_text = f"${price:.2f}" if price else "-"
        searchable = _html.escape(
            f"{model.model or ''} {model.developer or ''}".lower(), quote=True
        )
        url = IntelligenceReporter._get_model_canonical_url(model)
        if url:
            model_title = (
                f'<a href="{_html.escape(url, quote=True)}" target="_blank" '
                f'rel="noopener noreferrer" class="model-title-link">'
                f"{_html.escape(model.model or 'Unnamed')}</a>"
            )
        else:
            model_title = f'<h3>{_html.escape(model.model or "Unnamed")}</h3>'
        return (
            f'<article class="card" data-vram="{model.vram_class}" '
            f'data-tier="{model.access_tier}" '
            f'data-search="{searchable}">\n'
            '<div class="card-head">\n'
            f"{model_title}\n"
            '<div class="card-badges">\n'
            f'<span class="badge {cls}">{label}</span>\n'
            f'<span class="badge {tier_cls}">{tier_label}</span>\n'
            "</div>\n"
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

    @staticmethod
    def _render_champion_cards(report: MarketIntelligenceReport) -> str:
        """Render the three champion summary cards for the executive matrix.

        Args:
            report (MarketIntelligenceReport): The scavenged report.

        Returns:
            str: Concatenated HTML champion cards.
        """
        cards: List[str] = []
        for champ in IntelligenceReporter._select_champions(report):
            price = champ["prompt_usd"] + champ["completion_usd"]
            price_text = f"${price:.2f}/1M" if price else "Local (0 cost)"
            cards.append(
                '<article class="champion-card">\n'
                f'<h3>{_html.escape(champ["budget"])}</h3>\n'
                f'<p class="champ-model">{_html.escape(champ["model"])}</p>\n'
                f'<p class="dev">{_html.escape(champ["developer"])} &middot; '
                f'{_html.escape(champ["role"])} &middot; '
                f'{_html.escape(champ["params"])}</p>\n'
                "<ul>\n"
                f"<li>MMLU-Pro: {champ['mmlu_pro'] or '-'}</li>\n"
                f"<li>Pricing: {price_text}</li>\n"
                f"<li>Screening (1k papers): ${champ['screening_cost_1k']:.2f}</li>\n"
                f"<li>Full-text audit (1k papers): ${champ['audit_cost_1k']:.2f}</li>\n"
                "</ul>\n"
                "</article>\n"
            )
        return "\n".join(cards)


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


def _tier_badge(tier: str) -> Tuple[str, str]:
    """Map an AccessTier to a (label, css-class) badge pair.

    Args:
        tier (str): LOCAL_NO_KEY, CLOUD_ZERO_CONFIG_FREE,
            CLOUD_FREE_TIER_WITH_KEY, or CLOUD_PAID_API.

    Returns:
        tuple[str, str]: The human-readable label and CSS badge class.
    """
    if tier == "LOCAL_NO_KEY":
        return "Local (No Key)", "badge-tier-local"
    if tier == "CLOUD_ZERO_CONFIG_FREE":
        return "Zero-Config Free", "badge-tier-free"
    if tier == "CLOUD_FREE_TIER_WITH_KEY":
        return "Free Tier (Key)", "badge-tier-freetier"
    return "Paid API", "badge-tier-paid"


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
.card-head { display: block; width: 100%; }
.card-head h3 { font-size: 1.05rem; color: #e6ebf4; word-break: break-word; }
.model-title-link {
  display: block; width: 100%; word-break: break-word; overflow-wrap: break-word;
  line-height: 1.35; font-size: 1.05rem; font-weight: 700; color: #38bdf8;
  text-decoration: none; margin-bottom: 8px;
}
.model-title-link:hover { text-decoration: underline; color: #7fd1ff; }
.card-badges { display: flex; flex-wrap: wrap; gap: 6px; width: 100%; }
.dev { color: #8a97b0; font-size: 0.85rem; margin: 0.4rem 0 0.8rem; }
.card ul { list-style: none; font-size: 0.9rem; color: #c4cde0; }
.card li { padding: 0.15rem 0; }
.badge { font-size: 0.72rem; font-weight: 700; padding: 0.25rem 0.6rem; border-radius: 999px; white-space: nowrap; }
.badge-local { background: #0f3d2e; color: #6ee7a8; border: 1px solid #1f7a52; }
.badge-cloud { background: #4a3410; color: #f3c46b; border: 1px solid #8a6a1f; }
.badge-frontier { background: #102a4a; color: #6fb8ff; border: 1px solid #2a6aa8; }
.badge-tier-local { background: #0d2b1f; color: #9ef0c0; border: 1px solid #1f7a52; }
.badge-tier-free { background: #1b2c14; color: #c6f68f; border: 1px solid #4a7a2f; }
.badge-tier-freetier { background: #241f0a; color: #f5d98a; border: 1px solid #8a7a2f; }
.badge-tier-paid { background: #3a1020; color: #f79ec0; border: 1px solid #8a2f4a; }
.champions { display: flex; flex-wrap: wrap; gap: 1rem; justify-content: center; margin-bottom: 2rem; max-width: 1200px; margin-left: auto; margin-right: auto; }
.champion-card { background: #101a2e; border: 1px solid #2a3a5c; border-radius: 14px; padding: 1.1rem 1.3rem; min-width: 260px; flex: 1 1 260px; }
.champion-card h3 { color: #7fd1ff; font-size: 1rem; margin-bottom: 0.5rem; }
.champ-model { color: #e6ebf4; font-weight: 700; font-size: 1.05rem; word-break: break-word; }
.champion-card ul { list-style: none; font-size: 0.88rem; color: #c4cde0; }
.champion-card li { padding: 0.15rem 0; }
.search { text-align: center; margin-bottom: 1.5rem; }
#model-search { width: min(480px, 90%); padding: 0.65rem 1rem; border-radius: 999px; border: 1px solid #2c3a5c; background: #141b30; color: #e6ebf4; font-size: 0.95rem; outline: none; }
#model-search:focus { border-color: #7fd1ff; }
@media (max-width: 640px) {
  body { padding: 1rem 0.8rem; }
  .hero h1 { font-size: 1.5rem; }
}
"""

# -- Embedded vanilla JavaScript (zero external dependencies) ------------------
_HTML_JS = """
var activeFilter = 'all';
var activeQuery = '';
function applyFilters() {
  document.querySelectorAll('.card').forEach(function (card) {
    var vram = card.getAttribute('data-vram');
    var tier = card.getAttribute('data-tier');
    var text = (card.getAttribute('data-search') || '').toLowerCase();
    var match = activeFilter === 'all' || vram === activeFilter || tier === activeFilter;
    var textMatch = activeQuery === '' || text.indexOf(activeQuery) !== -1;
    card.style.display = (match && textMatch) ? '' : 'none';
  });
}
function filterModels(cls) {
  activeFilter = cls;
  var buttons = document.querySelectorAll('.filter');
  buttons.forEach(function (b) {
    b.classList.toggle('active', b.getAttribute('data-filter') === cls);
  });
  applyFilters();
}
function searchModels(q) {
  activeQuery = (q || '').toLowerCase().trim();
  applyFilters();
}
"""



