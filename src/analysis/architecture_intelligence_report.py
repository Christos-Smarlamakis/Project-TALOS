# -*- coding: utf-8 -*-
"""
Module: architecture_intelligence_report.py (v1.0)
Project: TALOS v4.11.0
Description:
    Feeds PROJECT_MAP.md, dependency audit JSON, and architecture graph data
    to an LLM (Gemini Pro) to generate a comprehensive Architecture
    Intelligence Report in both English and Greek.

    Usage:
        python scripts/architecture_intelligence_report.py

    Outputs:
        reports/architecture_intelligence_report_en.md  — English report
        reports/architecture_intelligence_report_gr.md  — Greek report
"""
import os
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import json
import time
from pathlib import Path
from datetime import datetime

# Add project root to path for core imports
PROJECT_ROOT = Path(_P) if _P else Path(os.getcwd())
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.ai_manager import AIManager

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_MAP_PATH = PROJECT_ROOT / "PROJECT_MAP.md"
AUDIT_JSON_PATH = PROJECT_ROOT / "data" / "reports" / "audits" / "dependency_audit.json"
GRAPH_JSON_PATH = PROJECT_ROOT / "templates" / "architecture_graph_data.json"
REPORTS_DIR = PROJECT_ROOT / "data" / "reports"

# Timestamp-based filenames for history tracking
_TIMESTAMP = datetime.now().strftime("%Y-%m-%d_%H-%M")
REPORT_EN_PATH = REPORTS_DIR / f"architecture_intelligence_report_en_{_TIMESTAMP}.md"
REPORT_GR_PATH = REPORTS_DIR / f"architecture_intelligence_report_gr_{_TIMESTAMP}.md"


def load_config():
    """Load config.json using canonical project root resolution."""
    config_path = PROJECT_ROOT / "config.json"
    if not config_path.exists():
        config_path = PROJECT_ROOT / "config.template.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def collect_data():
    """Gather all source data for the intelligence report."""
    print("Collecting architecture data...")
    
    data = {}
    
    # 1. PROJECT_MAP.md
    if PROJECT_MAP_PATH.exists():
        data["project_map"] = PROJECT_MAP_PATH.read_text(encoding="utf-8")
        print(f"  PROJECT_MAP.md: {len(data['project_map'])} chars")
    else:
        print("  WARNING: PROJECT_MAP.md not found")
        data["project_map"] = "PROJECT_MAP.md not available"
    
    # 2. Audit JSON
    if AUDIT_JSON_PATH.exists():
        with open(AUDIT_JSON_PATH, "r", encoding="utf-8") as f:
            audit = json.load(f)
        data["audit"] = json.dumps(audit, indent=2, ensure_ascii=False)
        print(f"  Audit: {audit.get('matched', 0)} matched, {audit.get('stale', 0)} stale, {audit.get('missing', 0)} missing")
    else:
        print("  WARNING: Audit JSON not found (run verify_dependency_map.py first)")
        data["audit"] = "Audit data not available. Run: python scripts/verify_dependency_map.py --all"
    
    # 3. Graph JSON (summary only — full would be too large)
    if GRAPH_JSON_PATH.exists():
        with open(GRAPH_JSON_PATH, "r", encoding="utf-8") as f:
            graph = json.load(f)
        # Extract summary statistics, don't send all 318 edges
        summary = {
            "stats": graph.get("stats", {}),
            "generated_at": graph.get("generated_at", ""),
            "nodes_by_layer": {},
        }
        for el in graph.get("elements", []):
            if el["group"] == "nodes":
                layer = el["data"]["layer"]
                summary["nodes_by_layer"][layer] = summary["nodes_by_layer"].get(layer, 0) + 1
        data["graph"] = json.dumps(summary, indent=2, ensure_ascii=False)
        print(f"  Graph: {summary['stats'].get('nodes', 0)} nodes, {summary['stats'].get('edges', 0)} edges")
    else:
        print("  WARNING: Graph JSON not found (run generate_architecture_graph.py first)")
        data["graph"] = "Graph data not available."
    
    return data


def build_prompt(data, language):
    """Build the prompt for the LLM based on target language."""
    
    lang_instruction = {
        "en": "Write the ENTIRE report in ENGLISH. Use professional, clear technical English.",
        "gr": "Γράψε ΟΛΟΚΛΗΡΗ την αναφορά στα ΕΛΛΗΝΙΚΑ. Χρησιμοποίησε άψογα επαγγελματικά ελληνικά με τεχνικούς όρους όπου χρειάζεται."
    }
    
    prompt = f"""You are a senior software architect with 20 years of experience reviewing large Python projects.

Below are three datasets from Project TALOS, a research intelligence platform:

---
DATASET 1: PROJECT_MAP (complete architecture documentation)
---
{data["project_map"][:15000]}

---
DATASET 2: DEPENDENCY AUDIT (AST vs documentation comparison)
---
{data["audit"][:5000]}

---
DATASET 3: ARCHITECTURE GRAPH (nodes and edges summary)
---
{data["graph"][:3000]}

---

{lang_instruction.get(language, lang_instruction["en"])}

Generate a comprehensive Architecture Intelligence Report with the following sections:

## 1. Architecture Health Index (A-F Grade)
Grade each dimension: coupling, cohesion, documentation coverage, test coverage evidence, external dependency risk.

## 2. Critical Risks & Single Points of Failure
Identify modules that, if broken, would bring down the entire system. Note missing fallbacks.

## 3. Refactoring Priority List
Top 10 modules that need attention, ranked by urgency. Explain WHY each one needs refactoring.

## 4. Dependency Health Matrix
Rate each external API/service (Gemini, DeepSeek, HuggingFace, Ollama, Discord, Zotero, Unpaywall, ORCID) on: criticality, reliability, fallback availability.

## 5. Documentation Gaps
What's documented in PROJECT_MAP but missing from code, and vice versa.

## 6. Onboarding Guide
For a new developer joining the project: where to look to understand X, what to modify to add a new Y.

## 7. Evolution & Growth Summary
How the architecture has grown, what patterns emerge, what the next logical steps would be.

## 8. Recommendations Summary
Top 5 actionable recommendations in priority order.

Format the report as clean Markdown with tables, bullet points, and clear section headers.
Use ✅, ⚠️, ❌ icons for status indicators.
Use technical depth — this is for fellow engineers.

Begin your response IMMEDIATELY with the report. No preamble."""
    
    return prompt


def generate_report(data, language, config):
    """Generate the report for the specified language using AIManager's provider chain.

    The AIManager automatically tries providers in priority order:
    local (Ollama) → HuggingFace (free) → Gemini → DeepSeek
    with circuit breaker and automatic fallback.
    """
    lang_label = {"en": "English", "gr": "Greek"}
    print(f"\nGenerating {lang_label.get(language, language)} report...")
    
    prompt = build_prompt(data, language)
    
    try:
        # Use AIManager with its built-in provider chain and fallback
        ai = AIManager(config)
        result_text = ai._execute_request(prompt, model_type="pro", response_format="text")
        
        if result_text:
            report = result_text.strip()
            return report
        else:
            print("  ERROR: All AI providers failed (local, HuggingFace, Gemini, DeepSeek).")
            print("  Check .env for at least one of: GEMINI_API_KEY, DEEPSEEK_API_KEY, HF_TOKEN, or TALOS_USE_LOCAL=1")
            return None
            
    except Exception as e:
        print(f"  ERROR generating report: {e}")
        return None


def main():
    print("=" * 60)
    print("  Project TALOS — Architecture Intelligence Report")
    print("=" * 60)
    print()
    
    # Ensure reports directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load config
    config = load_config()
    
    # Collect data
    data = collect_data()
    
    if not data.get("project_map") or data["project_map"] == "PROJECT_MAP.md not available":
        print("\nERROR: PROJECT_MAP.md is required. Cannot continue.")
        sys.exit(1)
    
    # Generate English report
    en_report = generate_report(data, "en", config)
    if en_report:
        header_en = f"# Project TALOS — Architecture Intelligence Report\n\n"
        header_en += f"> **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        header_en += f"> **Language:** English\n"
        header_en += f"> **Data sources:** PROJECT_MAP.md, dependency_audit.json, architecture_graph_data.json\n\n"
        header_en += "---\n\n"
        
        with open(REPORT_EN_PATH, "w", encoding="utf-8") as f:
            f.write(header_en + en_report)
        print(f"\n  English report saved: {REPORT_EN_PATH}")
    else:
        print("\n  Failed to generate English report.")
    
    # Wait briefly to avoid rate limiting
    time.sleep(2)
    
    # Generate Greek report
    gr_report = generate_report(data, "gr", config)
    if gr_report:
        header_gr = f"# Project TALOS — Αναφορά Αρχιτεκτονικής Νοημοσύνης\n\n"
        header_gr += f"> **Ημερομηνία:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        header_gr += f"> **Γλώσσα:** Ελληνικά\n"
        header_gr += f"> **Πηγές:** PROJECT_MAP.md, dependency_audit.json, architecture_graph_data.json\n\n"
        header_gr += "---\n\n"
        
        with open(REPORT_GR_PATH, "w", encoding="utf-8") as f:
            f.write(header_gr + gr_report)
        print(f"  Greek report saved: {REPORT_GR_PATH}")
    else:
        print("\n  Failed to generate Greek report.")
    
    print()
    print("=" * 60)
    print("  Report generation complete.")
    print(f"  EN: {REPORT_EN_PATH}")
    print(f"  GR: {REPORT_GR_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()