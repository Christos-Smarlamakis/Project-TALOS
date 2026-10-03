# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  For commercial licensing, please contact the author.
"""
Module: talos.py
Project: TALOS v5.21.0
Description:
    Main entry point for the TALOS TUI (Text User Interface). Provides a
    Rich-powered terminal dashboard with a dynamic status table showing
    Conda environment, API port, Synapse bus, execution mode, active
    LLM tiers, and the current active research focus from config.json.
    Unified 6-group hierarchical menu covering 100% of the executable
    codebase: Configuration & Profiles, Research Search & Ingestion,
    Advanced Analysis & Visualizations, DRL Agents/Daemons & GWO Swarm,
    Database Maintenance & Data Tools, and System Health, Diagnostics &
    CI/CD. Every prompt uses the canonical TALOS_QUESTIONARY_STYLE theme.

    v5.17.0: Two-Tier Hierarchical Swarm Architecture & Forensic Quality
    Engine -- the Tier-2 Forensic Quality Swarm (src/prisma/quality_swarm.py)
    decouples thematic screening (Tier-1) from forensic quality auditing:
    four specialized skill auditors (Theory/Operational/Benchmark/OpenScience)
    load profile-compiled, domain-specialized skills and synthesize the
    Kitchenham S_qual consensus with inter-auditor Fleiss kappa. CLI gains
    --appraise-quality [--swarm] and --compile-skills.

    v5.17.1: PRISMA Quality Appraisal UX Transparency & Force Re-Appraisal
    Engine -- appraise_candidates_batch gains force_reappraise and eliminates
    the silent exit when every candidate is already appraised, re-displaying the
    persisted 2D Evidence Quadrant distribution instead; CLI gains
    --appraise-quality [--swarm] [--force] and TUI Option 15 prompts before a
    deliberate re-audit.

    v5.18.0: Ethical Academic PDF Harvester, Smart Section Slicing & SQLite
    FTS5 Engine -- src/ingestion/pdf_harvester/ resolves and downloads legal
    Open Access / preprint full-text PDFs into data/fulltext_cache/ (magic-bytes
    validation, atomic writes, SHA-256, polite rate limiting), section_extractor
    caches Methodology/Experiments/Code/Limitations windows for the Tier-2
    Quality Swarm, and src/search/fulltext_search.py indexes cached bodies with
    SQLite FTS5. CLI gains --download-pdfs, --fts, and --open-pdf.

    v5.18.1: Autonomous Chaos Hardening, Fault Isolation & Dead Code
    Decommissioning -- headless/non-interactive TTY hardening in
    src/analysis/citation_analyzer.py, a fault-tolerant optional-dependency
    import guard in src/ingestion/sources/pubmed_source.py, and the safe
    decommissioning of the legacy src/ingestion/pdf_downloader.py module.

    v5.18.2: Net2Net DRL Checkpoint Repair, Win32 Close-to-Tray & Desktop
    Provisioner -- confirmation of the 18-source / 25-dim DDDQN tensor surgery
    on models/dddqn_trained.pth, a Win32 close-to-tray window-procedure hook
    that minimizes the daemon console (SW_HIDE) instead of terminating it, a
    1-click Desktop Shortcut provisioner (--create-shortcut), and an
    interactive autostart profile-target selector (--profile).

    v5.18.3: DRL Dual-Checkpoint Net2Net Surgery & Daemon Profile Provisioning
    Engine -- genuine Net2Net input tensor expansion on BOTH checkpoint
    locations (models/dddqn_trained.pth and src/ai/models/dddqn_trained.pth),
    widening lstm1.weight_ih_l0 to [512, 25] and the advantage head to [19, 32]
    to permanently eliminate the RuntimeError: Expected 23, got 25; the 24/7
    daemon dynamically synchronizes its banner and execution to the active
    profile (uav_mission_planning) via interactive Questionary selection.

    v5.18.4: Self-Healing Ingestion Gateway & Autostart Profile Provisioning --
    a top-level src/ingestion/resilient_gateway.py wraps all 18 academic source
    adapters with fast-fail circuit breaking (401/403/Quota) and automatic
    OpenAlex publisher mirroring for IEEE, Elsevier, and Springer; the daemon
    autostart flow promotes profile selection to the first mandatory prompt.

    v5.18.5: Hierarchical Evaluation Engine, Cognitive LLM Router Quota Latching
    & Clean Ingestion Lifecycle -- a centralized two-tier escalation engine
    (src/core/hierarchical_evaluator.py) runs a fast 8B screening sieve and
    escalates papers scoring S_rel >= 6.0 to the heavy 14B/cloud reasoning tier;
    the AI manager latches cloud providers returning HTTP 402/401 so they are
    bypassed with zero network attempts in favor of DeepSeek; the Science.gov
    adapter isolates DNS failures and DBLP sanitizes Boolean queries; and the
    daemon sets an official emoji-free dynamic console title.

    v5.21.0: Cognitive Mesh In-Tree Microservice & Autonomous LLM Scavenger
    Agent -- the extraction-ready src/services/cognitive_mesh/ package (dto,
    registry, router, benchmarks, scavenger, reporter, server, client), the
    autonomous ModelScavengerAgent foraging Hugging Face / OpenRouter / Ollama,
    dual MD/HTML market-intelligence reporting, and a Cognitive Mesh FastAPI
    mini-server mounted in main_api.py under /api/v1/cognitive.

    v5.20.0: Cognitive Meta-Router, SOTA LLM Dynamic Discovery & Enterprise
    Console Runbooks -- a decoupled src/core/cognitive_router.py (4 strategies,
    circuit breaker, quota latching, Semaphore(2)), a 16-provider registry,
    src/core/model_benchmark_client.py + --discover-llms, and the 6-zone
    docs/ARCHITECTURE_MAP.md.

    v5.19.0: Two-Stage Rigor Decoupling Engine & Cognitive SOTA Role Matcher --
    src/core/hierarchical_evaluator.py now executes a Stage-2 Dual-Audit (Faceted
    Deep Relevance Calibration S_rel_calibrated + Kitchenham 2007 S_qual via
    PrismaQualityAppraiser) and maps each study onto the 2D Evidence Quadrant;
    src/core/hardware_advisor.py gains get_role_based_matrix() / render_role_matrix()
    / apply_recommended_models() (four-role SOTA matcher); daily_search,
    historic_search and talos_service are unified through the engine; and the
    CLI gains --apply-models for 1-click model adoption.

    v5.16.2: Pluggable Provider Registry & Hardware-Aware Model Advisor -- a
    modular adapter-based provider registry (src/core/provider_registry.py)
    implements the Open-Closed Principle so new inference backends (NVIDIA NIM,
    Anthropic, custom edge servers) register as data without touching core
    routing loops; a hardware-aware model advisor
    (src/core/hardware_advisor.py) reuses VRAM/GPU telemetry to compute a
    4-bit-quantization parameter budget and recommend a role-based model stack
    with a best-effort SOTA discovery radar (Qwen 3/4, Llama 4). Exposed via
    --hardware-advisor / --recommend-models and a Configuration & Profiles menu
    entry.

    v5.16.1: Unified Profile Architecture & Workspace Synchronization Engine --
    ProfileManager is established as the strict single source of truth for all
    profile operations (anchored to repo-root _profiles/), the active PhD
    workspace is consolidated into the canonical uav_mission_planning profile,
    and local AI inference is unified on port 11434 (retiring the phantom 11435
    fast-edge warning path).

    v5.16.0: PRISMA Quality Appraisal & Dual-Axis Scientific Rigor Engine
    (Kitchenham 2007 Standard) -- a standardized six-question, three-point
    quality rubric (src/prisma/quality_appraisal.py) decouples Semantic
    Relevance (S_rel) from Methodological Quality (S_qual) and maps each study
    onto a 2D Evidence Decision Plane (Elite Foundational, Idea Mine,
    Methodological Exemplar, Noise); batch appraisal via --appraise-quality,
    SQLite schema expansion (quality_score / quality_rubric_json /
    evidence_quadrant), and BibTeX dual-filter export (--min-quality /
    --quadrant); README.md gains Kitchenham IEEE citations [11]-[12].

    v5.15.5: Dual-Surface Interactive Help System & Scientific Foundations
    Canon -- a rich four-panel console manual (src/utils/help_system.py)
    served via --help and TUI Option 7, plus an interactive zero-CDN Web
    Manual at http://localhost:8001/help (templates/help_manual.html) with
    live search, click-to-copy, and a dark/print-mode toggle; README.md gains
    a formal IEEE-style Scientific References & Theoretical Foundations
    section ([1]-[10]).

    v5.15.4: DRL Action-Space Expansion to 18 Sources & Net2Net Checkpoint
    Migration -- the DRL environment scales to 18 academic sources (action
    space 17 -> 19, observation space 23 -> 25 dims) by registering NASA NTRS
    and HAL/Inria in ALL_KNOWN_SOURCES; a Net2Net tensor-surgery utility
    (scripts/migrate_d3qn_checkpoint.py) widens both the DuelingLSTM advantage
    head (15 -> 19) and its LSTM input layer (21 -> 25) in
    models/dddqn_trained.pth, preserving all trained weights exactly while
    optimistically initialising the four newly introduced source heads; and
    Scopus/Elsevier XML-JSON author normalisation locks in the $, @name and
    @surname fields with clean 4-author + et al. truncation.

    v5.15.3: Session Circuit Breaker, Robust Author Extraction & Daemon
    Lifecycle Hardening -- a process-lifetime session circuit breaker in
    AIManager latches the CPU edge tier (11435) offline after the first
    failure (zero subsequent probes or fallback log spam), a multi-key author
    normalizer (normalize_authors) eliminates "Unknown Authors" false
    positives, the daemon emits clean single-line [EVAL] telemetry, and
    SynapseClient buffers events silently in standalone quiet mode.

    v5.15.2: Universal Search Hub UX & Reporting Harmonization --
    src/search/code_first_search.py and src/search/citation_snowballing.py gain
    styled Rich Table rendering (render_results / render_genealogy) and
    timestamped Markdown report export (data/reports/code_search and
    data/reports/snowball), eliminating raw JSON dumps from the TUI and CLI.

    v5.15.1: Persistent Vector Cache & Accelerated Neural Embedding Engine --
    src/core/database_manager.py adds the idempotent ``paper_embeddings`` SQLite
    table with get_cached_embeddings() / save_embeddings_batch() helpers;
    NeuralVectorSearchEngine now performs zero-redundancy incremental indexing
    behind a live rich.progress.Progress bar, vectorized NumPy matrix cosine
    similarity (<50ms retrieval), and styled Rich Table result presentation.

    v5.15.0: Universal Scientific Search Hub & Neural Graph Discovery Engine --
    src/search/ adds the CitationSnowballEngine (backward/forward citation graph
    traversal), NeuralVectorSearchEngine (local nomic-embed-text dense retrieval
    with cosine similarity), and CodeFirstSearchEngine (reproducible GitHub /
    PapersWithCode / benchmark discovery); src/ingestion/sources/ modularizes the
    18 source adapters behind a unified SOURCE_REGISTRY, exposed via the
    --snowball / --vector-search / --code-search CLI flags and the Group 2
    Universal Search Hub TUI menu.

    v5.14.2: BibTeX Scientific Exporter & 18-Source Aerospace Ingestion (Feature
    Freeze) -- src/utils/bibtex_exporter.py exports curated papers to a
    standard-compliant .bib library, and the official NASA NTRS and HAL/Inria
    REST harvesters (src/ingestion/nasa_ntrs_source.py, hal_inria_source.py)
    expand the academic ingestion mesh from 16 to 18 sources, exposed via the
    --export-bib CLI flag and the Group 5 Database Maintenance menu.

    v5.14.1: Multi-Agent Peer-Review Swarm & Consensus Engine --
    src/prisma/swarm_evaluators.py adds a 3-agent specialized review swarm
    (Algorithmic / Empirical Rigor / Swarm Operational NATO reviewers) with
    automated Cohen's Kappa inter-rater reliability and a Chain-of-Thought
    consensus arbiter, exposed via the --prisma --swarm CLI flag and the
    Group 3 Advanced Analysis & Visualizations menu screening-mode prompt.

    v5.14.0: Stanford DSPy PRISMA-ScR Pipeline & Declarative Synthesis Engine --
    src/prisma/ adds typed declarative PRISMA-ScR signatures, a PlanEval
    pipeline (PrismaPlanner / PrismaEvaluator / PrismaEligibilityJudge /
    PrismaExecutor), a PRISMA 2020 Mermaid flowchart generator, and a scoping
    review synthesizer, exposed via the --prisma CLI flag and the Group 3
    Advanced Analysis & Visualizations menu.

    v5.13.1: System Diagnostics Analyzer & Operational Integrity Engine --
    src/utils/system_diagnostics.py adds an 8-point pre-flight health check
    (Python environment, SQLite integrity, local AI runtime, port
    availability, filesystem permissions, environment credentials, daemon
    status, and network endpoints) rendered as a Rich health report with
    one-line remediation guidance, exposed via the --diagnostics / --doctor
    CLI flags and the Group 6 System Health TUI menu.

    v5.13.0: Full-Stack Concurrent Multi-Threaded Engine & High-Throughput
    Harvester -- historic_search.py joins daily_search.py in the 16-source
    ThreadPoolExecutor ingestion mesh, and the AIManager gains a concurrent
    batch cognitive evaluation pool (8 cloud workers / 2 VRAM-guarded local
    workers behind a bounded semaphore) with batched SQLite WAL commits in
    database re-evaluation.

    v5.12.4: Concurrent Ingestion Mesh & Multi-Profile Research Onboarding --
    the Research Setup Wizard gains a Step 0 profile target gate (reconfigure
    the active profile, switch to an existing isolated profile, or instantiate
    a fresh isolated workspace), and daily_search.py harvests all 16 sources
    concurrently via ThreadPoolExecutor (max_workers=16) with a real-time Rich
    Live telemetry table, reducing harvest latency from ~35-45s to ~3-4s.

    v5.12.3: Research Pivot Modernization & Setup Wizard TUI Integration --
    the Research Setup Wizard is promoted to the first entry of the
    Configuration & Profiles menu ("Full Onboarding & Reconfiguration"),
    the Research Pivot Wizard gains canonical REPO_ROOT-anchored subprocess
    paths with strict returncode verification, and the lingering mythological
    codenames (PYTHIA, CHIRON) are eliminated from the TUI in favour of
    ISO/IEC 25010 functional terminology.

    v5.12.2: Self-Healing AI Manager & Heuristic Search Optimizer -- the core
    AIManager gains a fast pre-flight Ollama probe with detached background
    spawn, silent provider trimming (STANDBY_NO_KEY), secure on-demand .env
    key injection, and a google.genai GA SDK migration; the Research Setup
    Wizard strips English stopwords from heuristic boolean queries so IEEE
    Xplore, Scopus, and arXiv fallback queries return records instead of zero
    hits.

    v5.12.1: Research Wizard Query Transparency & CLI Fast-Dispatch Engine --
    Step 1 renders a styled Rich query-preview table (top primary sources with
    their compiled boolean queries) plus inclusion/exclusion criteria and a
    Questionary confirmation before persisting config.json; talos.py gains
    lightweight CLI fast-dispatch flags (--wizard, --daily, --stats, --help).

    v5.12.0: Research Setup Wizard, Local Cognitive Input Validation with
    Failsafe Heuristic Bypass & ISO/IEC 25010 Usability Milestone -- a 4-step
    English-first onboarding wizard (src/utils/research_setup_wizard.py) with
    local AI runtime auto-spawn, 2-second scope validation timeout,
    deterministic heuristic fallback, and first-run sentinel automation.

    v5.11.3: Ecosystem Integrity, Deprecation Elimination & Dependency
    Alignment -- OpenReview V2 search_notes dispatch ladder, Fast-Edge (11435)
    batch circuit breaker, FastAPI lifespan migration, Gemini FutureWarning
    suppression, multi-path GWO artifact status check, and dependency-map
    verifier repair; also formally seals the 7 pre-demo concurrency hardening
    fixes (non-blocking SSE, cached DB singleton, headless workers, scrape
    lock, top_k clamp, payload guards, GWO monitor resilience).

    v5.11.2: Zero-Click Windows Pre-Flight Onboarding Wizard -- run_talos.bat
    gains a progress-aware 5-step setup engine with silent Miniconda3
    bootstrap and a sub-1-second fast-path bypass for daily launches.

    v5.11.1: TUI Sub-Menu Sanitization & Complete Hierarchy Audit -- corrected
    the Questionary choice-list duplication in the Configuration & Profiles
    sub-menu and standardized sequential numbering across every sub-menu.

    v5.11.0: Live Telemetry HUD Console, Win32 Close-to-Tray, Cross-Platform
    Linux Bootstrap & Full-Title History Engine -- bottom-right glassmorphism
    telemetry console in the 3D visualizer, native close-to-tray window hook,
    full title/authors [EVAL] telemetry with English error sanitization, a
    persistent JSONL evaluation history recorder with a Rich TUI viewer, and a
    zero-touch Miniconda/talosenv bootstrap in run_talos.sh.

    v5.10.16: Zero-Risk Performance Optimization & Academic LaTeX/BibTeX Engine --
    enabled SQLite WAL mode and PRAGMA tuning, added online snapshotting before
    destructive maintenance, introduced pooled HTTP sessions across ingestion
    sources, memoized deterministic routing helpers, and shipped a zero-dependency
    BibTeX/LaTeX academic export engine.

    v5.10.14: Autonomous Execution Matrix with Privacy Guardrails & DeepSeek V4
    Cognitive Integration -- new auto_dynamic network strategy with interactive
    Rich Privacy Safeguard consent, runtime resolution to strict_local /
    local_first / cloud_first, and DeepSeek V4 Pro cognitive thinking injection.

    v5.10.13: Desktop Control Hub, Self-Healing Infrastructure, Active Profile
    Persistence & Environment Canon Overhaul -- system tray control hub with
    self-healing API auto-bootstrap, single point of truth database persistence,
    and a professional section-by-section environment configuration redesign.

    v5.10.12: Autonomous Daemon Hardening, 3D Laser Telemetry & Interactive
    Visualizer Tools -- 60 FPS animated laser beams with traveling photon
    pulses, raycaster click-to-fire nodes, PNG snapshot, fullscreen and help
    overlays, 1000ms AJAX state polling, active-profile DB resolution, and a
    SQLite VACUUM optimizer.

    v5.10.11: Vendored Three.js 3D Knowledge Constellation & Live Telemetry
    Engine -- superseded the experimental raw WebGL 1.0 visualizer with a
    production-grade Three.js architecture locally vendored in
    static/js/three.min.js. Adds Health Aura Sprites, Academic Print Theme,
    and a 1.5-second live polling bridge over the existing SSE stream.

    v5.10.10: Enterprise TUI Overhaul & Academic Aesthetics -- unified
    questionary prompt style across the entire CLI (Cyan/Teal #00ced1 selection
    colors, bright-white category separators, IEEE blue #4a9eff question mark)
    for publication-ready IEEE screenshots. Style canonicalized in
    src/utils/ui_theme.py and imported by every prompt-using module.

    v5.10.7: OPTICA Bridge Integration -- TALOS now acts as an API client
    to the sister Project OPTICA microservice (port 8002), offloading heavy
    cnsplots/PyVis graphics. Added src/integration/optica_client.py and the
    "Data Visualizations (via OPTICA)" TUI menu option.

    v5.10.6: Daemon OS Autostart & Orchestrator -- added the Windows
    Startup hook installer (src/utils/daemon_autostart.py), interactive
    daemon network strategy configuration, and daemon_target_sources.
    v5.10.5: Universal Dynamic Model Provisioner & Self-Healing Redundancy
    Engine -- added the ModelProvisioner (src/utils/model_provisioner.py) with
    3-tier local path resolution, JIT auto-pull for Ollama and HuggingFace Hub,
    and a self-healing fallback cascade; integrated into the SETUP routine and
    the Model Manager TUI.

    v5.10.4: Dynamic Model Discovery Engine & SYNAPSE Protocol
    Interoperability -- added ModelDiscoveryEngine
    (src/ai/llm/model_discovery.py) with an air-gapped JSON benchmark registry
    (data/model_benchmarks.json), dynamic relative quality scoring Q_p, and the
    SYNAPSE GET /api/v1/synapse/status endpoint plus model_discovered and
    router_decision event types.

    v5.10.1: DRL Environment Scaling & Retraining -- the TALOS DRL agent
    environment scaled to a 23-dimensional state space (16 source usage
    ratios + 2 streaks + 4 provider ratios) and a 17-action space (16 sources
    + sleep). DDDQN auto-reconstructs networks for the new dimensions.

    v5.10.2: LLM Router Sub-Agent, Bi-Level GWO Reward Shaping & Interactive
    16-Source Checkbox TUI -- added the LLMRouterSubAgent provider-selection
    delegate, the GWOLLMRouterRewardShaper optimizer, and renamed
    gwo_rl_optimizer.py to gwo_foraging_hyperparameter_tuner.py. Options 3a/3b
    now prompt a questionary checkbox over all 16 academic sources.

    v5.10.3: Hierarchical DRL Orchestration (Daemon & Foraging Sub-Agent
    Integration) -- the LLMRouterSubAgent is now invoked directly by the live
    DRL foraging orchestrator, the 24/7 autonomous daemon, and the
    daily/historic search pipelines for optimal provider selection.

    v5.10.0: Academic Ingestion Expansion -- OpenReview and OpenAIRE source
    agents added (16-source ingestion). OpenReview peer-review decisions and
    OpenAIRE grant/funding metadata are appended to abstracts.

    v5.9.18: Universal Cloud Mesh -- Model Manager Cloud Configuration expanded
    to a nine-provider registry (Gemini primary + 8-provider OpenAI-compatible
    redundancy cascade: NVIDIA NIM, Groq, Cerebras, GitHub Models, Mistral,
    OpenRouter, DeepSeek, Hugging Face).

    v5.9.12: Vendored Graphify AST Knowledge Graph integrated via
    src/analysis/graphify_adapter.py. Main menu reorganized into five
    visually-grouped Rich categories. Version bumped from 5.9.9.

    v5.9.0: Autonomous Red Tester (RL-Driven Chaos Engineering) integrated
    as menu option 8. Runs a Non-Stationary Epsilon-Greedy Multi-Armed Bandit
    that stress-tests TALOS components via subprocess, diagnoses crashes with
    LLM-as-a-Judge (Fast Edge tier), saves Markdown reports, and displays
    Rich Q-table (Component Fragility) with Spinners, Panels, and Tables.

    v5.8.9: Active Research Focus row in status table (reads
    user_research_goal from config.json, truncated at 65 chars). Option 4
    refactored into interactive View & Pivot Research Focus workflow with
    inline Query Translator execution, raw goal preview panel, and
    boolean query display.

    v5.8.5: Universal TUI Beautification -- all sub-menu launches, diagnostic
    outputs, and informational prompts wrapped in styled Rich Panels with
    color-coded borders. New _build_info_panel() and _build_results_table()
    helpers for consistent Sci-Fi terminal aesthetics. Elite paper scores
    (>=7) highlighted in gold. Query Translator and baseline reports
    display contextual descriptions before subprocess launch. Fixed model name
    display in status panel -- full raw configuration strings printed directly
    without split(":") truncation.

    v5.8.4: Full Rich TUI refactoring (Console, Panel, Table, Box, Text).
    Model Manager integrated as menu option 1 via direct import.
    Zero emojis protocol enforced across all Rich-formatted output.

Dependencies:
    - config.settings: Single source of truth for TALOS_VERSION.
    - src.core.profile_manager: Profile switching and retrieval.
    - src.ai.llm.model_manager: Multi-tier AI model management TUI.
    - src.ai.testing.red_tester: RL-driven chaos engineering daemon.
    - src.analysis.graphify_adapter: Vendored Graphify AST knowledge graph.
    - rich: Terminal UI beautification (Console, Panel, Table, Box, Text).
    - questionary: Terminal UI interactive prompts.
    - python-dotenv: Environment variable loading.
"""
import questionary
from src.utils.ui_theme import TALOS_QUESTIONARY_STYLE

import os
import subprocess
import sys
import time
import tempfile
import stat
from dotenv import load_dotenv
load_dotenv()

import shutil

from config.settings import TALOS_VERSION, TALOS_API_PORT

# -- v5.9.17: Enterprise logging --
from src.utils.logger import get_logger
logger = get_logger(__name__)

# -- v5.9.8: Clickable Terminal Hyperlinks --
def _make_clickable_path(path_str: str) -> str:
    """Convert a file path to a Rich terminal hyperlink for CTRL+CLICK navigation.

    Args:
        path_str: Absolute or relative file path.

    Returns:
        Rich [link=file:///...] formatted string with forward slashes.
    """
    abs_path = os.path.abspath(path_str).replace("\\", "/")
    return f"[link=file:///{abs_path}]{path_str}[/link]"
from config.settings import TALOS_NETWORK_STRATEGY, TALOS_HARDWARE_STRATEGY, TALOS_EXECUTION_MODE
from config.settings import FAST_EDGE_MODEL, HEAVY_REASONING_MODEL
from config.settings import CLOUD_PROVIDER, GEMINI_FLASH_MODEL, DEEPSEEK_MODEL_CHAT
from config.settings import SYNAPSE_BUS_URL
from src.core.profile_manager import (
    ProfileManager,
    get_active_profile_name, save_current_state_to_profile, set_active_profile_name,
)
from src.utils.evaluation_history import read_evaluation_history

# -- Rich imports for the gorgeous terminal dashboard --
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
from rich.align import Align

console = Console()

# -- v5.11.1: Enable Windows VT100 (ANSI) virtual terminal processing --
def _enable_windows_vt100():
    """Enable ANSI/VT100 virtual terminal processing on Windows STDOUT.

    prompt_toolkit emits cursor-positioning and screen-redraw escape
    sequences that Windows ConHost ignores unless
    ENABLE_VIRTUAL_TERMINAL_PROCESSING is set. Without it, menu renders
    overwrite prior text without erasing, producing ghost-text artifacts.
    """
    if sys.platform != "win32":
        return
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        h_out = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
        out_mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(h_out, ctypes.byref(out_mode))
        # ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004) | ENABLE_PROCESSED_OUTPUT (0x0001)
        out_mode.value |= 0x0004 | 0x0001
        kernel32.SetConsoleMode(h_out, out_mode)
    except Exception:
        pass

_enable_windows_vt100()

USE_LOCAL_MODEL = False

# -- v5.9.2: Dynamic Focus Summarization --
# If config.json lacks active_focus_summary but has queries/goal, an LLM
# call generates a 6-10 word summary at startup and saves it.
def _maybe_generate_focus_summary(config_path="config.json"):
    """Generate a 6-10 word active_focus_summary via Fast Edge LLM if missing.

    Reads config.json. If active_focus_summary is absent but either
    user_research_goal or any *_query keys contain text, fires a Fast Edge
    LLM call with a spinner to summarize the research focus into a concise
    title, saves it back to config.json, and displays it.

    Args:
        config_path: Path to config.json.
    """
    import json as _json
    try:
        with open(config_path, "r", encoding="utf-8") as _f:
            _cfg = _json.load(_f)
    except Exception:
        return

    # -- Requirement: skip if summary already exists --
    if _cfg.get("active_focus_summary", "").strip():
        return

    # -- Build context from existing goal or queries --
    goal = (_cfg.get("user_research_goal") or
            _cfg.get("phd_focus_system_prompt") or "").strip()
    queries = []
    for k, v in sorted(_cfg.items()):
        if k.endswith("_query") and isinstance(v, str) and v.strip():
            queries.append(f"{k.replace('_query','')}: {v[:120]}")
    if not goal and not queries:
        return  # Nothing to summarize -- skip

    # -- Build a summary prompt --
    context_bits = []
    if goal:
        context_bits.append(f"Research goal: {goal[:300]}")
    if queries:
        context_bits.append("Search queries: " + "; ".join(queries[:5]))
    summary_prompt = (
        "You are a research archivist. Summarize the following research project "
        "into a single, concise title of 6 to 10 words. Return ONLY the title, "
        "with no additional text, quotes, or formatting.\n\n" +
        "\n".join(context_bits)
    )

    # -- Spinner + LLM call --
    console.print("\n[cyan]Generating Research Focus Summary...[/cyan]", end="")
    try:
        from src.core.ai_manager import AIManager
        mgr = AIManager({})
        result = mgr._execute_request(
            summary_prompt,
            model_type="flash",
            response_format="text",
            tier="fast",
        )
        if result and isinstance(result, str):
            title = result.strip().strip('"').strip("'")
            # Sanitize: enforce 6-10 words, truncate if longer
            words = title.split()
            if len(words) > 10:
                title = " ".join(words[:10])
            if len(words) >= 3:  # Only accept if at least 3 words
                _cfg["active_focus_summary"] = title
                with open(config_path, "w", encoding="utf-8") as _f:
                    _json.dump(_cfg, _f, indent=2, ensure_ascii=False)
                console.print(f"\r[green]Research Focus: [bold bright_green]{title}[/bold bright_green][/green]")
            else:
                console.print("\r[dim]Focus summary too short -- skipping.[/dim]")
        else:
            console.print("\r[dim]Focus summary: LLM unavailable -- skipping.[/dim]")
    except Exception:
        console.print("\r[dim]Focus summary: LLM error -- skipping.[/dim]")

# -- Script-name -> relative-path map (for run_script) -------------------------
# Maps the script filename to its package subdirectory under src/.
_SCRIPT_MAP = {
    # -- Ingestion --
    "daily_search.py":            "ingestion",
    "historic_search.py":         "ingestion",
    "grey_literature_miner.py":   "ingestion",
    "zotero_connector.py":        "ingestion",
    "metadata_enricher.py":       "ingestion",
    "data_enricher.py":           "ingestion",
    # -- DRL --
    "drl_trainer.py":             "ai/drl",
    "train_agent.py":             "ai/drl",
    "talos_live_agent.py":        "ai/drl",
    "talos_service.py":           "ai/drl",
    # -- Optimizers --
    "gwo_foraging_hyperparameter_tuner.py": "ai/optimizers",
    "gwo_llm_router_reward_shaper.py": "ai/optimizers",
    "gwo_live_dashboard.py":      "ai/optimizers",
    # -- Embeddings --
    "embedding_generator.py":     "ai/embeddings",
    "db_embedding_upgrade.py":    "ai/embeddings",
    # -- LLM --
    "query_translator.py":        "ai/llm",
    "model_manager.py":           "ai/llm",
    "model_discovery.py":         "ai/llm",
    "research_pivot.py":          "ai/llm",
    # -- Analysis --
    "citation_analyzer.py":       "analysis",
    "author_profiler.py":         "analysis",
    "author_trajectory_analyzer.py": "analysis",
    "trend_analyzer.py":          "analysis",
    "architecture_intelligence_report.py": "analysis",
    "knowledge_path_generator.py": "analysis",
    "recommender.py":             "analysis",
    "generate_baseline_report.py": "analysis",
    "generate_architecture_graph.py": "analysis",
    "graphify_adapter.py":        "analysis",
    # -- Utils --
    "db_stats.py":                "utils",
    "recalculate_scores.py":      "utils",
    "reevaluate_database.py":     "utils",
    "migrate_database_schema.py": "utils",
    "api_health_check.py":        "utils",
    "generate_docs.py":           "utils",
    "verify_dependency_map.py":   "utils",
    "interactive_dashboard.py":   "utils",
    "model_provisioner.py":       "utils",
    "daemon_autostart.py":        "utils",
    "academic_export.py":         "utils",
    "research_setup_wizard.py":   "utils",
    # -- Core (profile manager is imported directly, but can also be run) --
    "profile_manager.py":         "core",
    # -- API --
    "talos_service_api.py":       "api",
    # -- Testing --
    "red_tester.py":              "ai/testing",
    # -- Integration --
    "optica_client.py":           "integration",
}

def safe_select(message, choices, style=TALOS_QUESTIONARY_STYLE, **kwargs):
    """Safe questionary.select wrapper preventing Windows prompt_toolkit redraw bugs."""
    sys.stdout.flush()
    prompt_msg = message.strip() if (message and message.strip()) else "Select option:"
    kwargs.pop("instruction", None)
    kwargs.pop("use_indicator", None)
    try:
        return questionary.select(
            prompt_msg,
            choices=choices,
            style=style,
            use_indicator=False,
            use_shortcuts=False,
            pointer="> ",
            **kwargs
        ).ask()
    except (KeyboardInterrupt, Exception):
        sys.stdout.flush()
        return None

def safe_pause(msg="Press Enter to return..."):
    """Pause prompt that swallows Ctrl+C so a stray interrupt at a pause
    prompt returns to the menu instead of killing the whole TUI."""
    try:
        console.input(msg)
    except (KeyboardInterrupt, EOFError):
        console.print()

# -- v5.10.10: Universal Navigation Instructions --
NAV_SELECT  = "(Use arrow keys to navigate, Enter to confirm, Ctrl+C to return)"
NAV_CHECK   = "(Space to toggle, Enter to confirm, Ctrl+C to return)"
NAV_TEXT    = "(Enter to confirm, Ctrl+C to cancel)"
NAV_CONFIRM = "(y/n, Enter to confirm)"

# -- v5.14.2: Canonical 18-source list for the interactive checkbox TUI --
ALL_ACADEMIC_SOURCES = [
    "arxiv", "ieee", "semantic_scholar", "springer", "openalex", "dblp",
    "elsevier", "core", "crossref", "openarchives", "pubmed", "scigov",
    "osti", "plos", "openreview", "openaire", "nasa_ntrs", "hal_inria",
]


def prompt_source_selection():
    """Prompt the user to select academic sources via a checkbox.

    Returns:
        list of str | None: Selected source names, or None if cancelled.
    """
    try:
        return questionary.checkbox(
            "Select academic sources:",
            choices=[questionary.Choice(name, checked=True)
                     for name in ALL_ACADEMIC_SOURCES],
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()
    except KeyboardInterrupt:
        return None

def _resolve_script_path(script_name):
    """Resolve a script filename to its full path inside src/<subdir>/.

    Args:
        script_name: The filename (e.g. "db_stats.py") to resolve.

    Returns:
        str: Absolute path to the script under src/.

    Raises:
        FileNotFoundError: If the script is not present in _SCRIPT_MAP.
    """
    project_root = os.path.dirname(os.path.abspath(__file__))
    subdir = _SCRIPT_MAP.get(script_name)
    if subdir is None:
        raise FileNotFoundError(
            f"Script '{script_name}' is not mapped in _SCRIPT_MAP. "
            f"Add its src/ subdirectory to _SCRIPT_MAP in talos.py."
        )
    return os.path.join(project_root, 'src', subdir, script_name)

def _build_info_panel(title, message, border_style="bright_blue"):
    """Build a styled Rich Panel for informational messages.

    Args:
        title: Panel title string.
        message: Body text (str or list of str).
        border_style: Rich border style color.

    Returns:
        A rich.panel.Panel ready for console.print().
    """
    if isinstance(message, str):
        body = Text(message, style="white")
    else:
        body = Text()
        for i, line in enumerate(message):
            body.append(line)
            if i < len(message) - 1:
                body.append("\n")
    return Panel(
        Align.center(body),
        title=f"[bold]{title}[/bold]",
        border_style=border_style,
        box=box.ROUNDED,
        padding=(1, 2),
    )


def _build_results_table(papers, title="Search Results"):
    """Build a styled Rich Table for paper search results.

    Columns: ID (cyan), Title (white/bold), Source (magenta),
             Year (yellow), Overall Score (emerald/bold).
    Elite papers (overall_score >= 7) are highlighted in gold.

    Args:
        papers: List of dicts with keys id, title, source,
                publication_year, overall_score.
        title: Table title string.

    Returns:
        A rich.table.Table ready for display.
    """
    table = Table(
        title=f"[bold bright_cyan]{title}[/bold bright_cyan]",
        box=box.ROUNDED,
        border_style="bright_blue",
        show_lines=True,
        header_style="bold bright_cyan",
    )
    table.add_column("ID", style="dim cyan", width=6, no_wrap=True)
    table.add_column("Title", style="white", width=50, overflow="fold")
    table.add_column("Source", style="magenta", width=16)
    table.add_column("Year", style="yellow", width=6, justify="right")
    table.add_column("Score", style="bold emerald", width=8, justify="right")

    for p in papers:
        score = p.get("overall_score", 0)
        try:
            score_f = float(score)
        except (TypeError, ValueError):
            score_f = 0.0
        score_str = f"{score_f:.1f}"
        # Highlight elite papers (score >= 7) in gold
        if score_f >= 7:
            score_style = "[bold gold1]"
            row_style = None
            score_str_display = f"{score_style}{score_str}[/bold gold1]"
        else:
            score_style = ""
            row_style = None
            score_str_display = score_str
        title_text = str(p.get("title", "N/A"))[:100]
        table.add_row(
            str(p.get("id", "?")),
            title_text,
            str(p.get("source", "N/A")),
            str(p.get("publication_year", "N/A")),
            score_str_display,
        )
    return table


def run_script(script_name, python_exe, args=None, capture=False):
    """Launch a TALOS script as a subprocess.

    The script is resolved from the _SCRIPT_MAP (src/<subdir>/<name>).
    All TALOS_* environment variables are forwarded to the child process.
    """
    script_path = _resolve_script_path(script_name)
    command = [python_exe, script_path] + (args or [])
    launch_panel = _build_info_panel(
        f"Launching: {script_name}",
        f"[dim]Command: {' '.join(command)}[/dim]",
        border_style="cyan",
    )
    console.print(launch_panel)
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if USE_LOCAL_MODEL: env["TALOS_USE_LOCAL"] = "1"
    if os.environ.get("TALOS_MODELS_VERIFIED"): env["TALOS_MODELS_VERIFIED"] = "1"
    if os.environ.get("TALOS_ALLOW_CLOUD_FALLBACK"): env["TALOS_ALLOW_CLOUD_FALLBACK"] = "1"
    if os.environ.get("TALOS_ALLOW_LOCAL_FALLBACK"): env["TALOS_ALLOW_LOCAL_FALLBACK"] = "1"
    if os.environ.get("HF_MODEL_NAME"): env["HF_MODEL_NAME"] = os.environ["HF_MODEL_NAME"]
    try:
        if capture:
            result = subprocess.run(command, check=True, capture_output=True, text=True, encoding="utf-8", env=env)
            logger.info("%s", result.stdout)
            console.print(f"\n[dim green]--- '{script_name}' completed. ---[/dim green]")
            return result
        else:
            subprocess.run(command, check=True, env=env)
            console.print(f"\n[dim green]--- '{script_name}' completed. ---[/dim green]")
            return True
    except KeyboardInterrupt:
        console.print(f"\n[yellow]--- '{script_name}' cancelled by user. ---[/yellow]")
        return False
    except subprocess.CalledProcessError as e:
        if "interactive_dashboard.py" in script_name and e.returncode in [1, 2, -2, 3221225786]:
            console.print(f"\n[dim green]--- Dashboard server terminated by user. ---[/dim green]")
            return True
        console.print(f"\n[red]--- Error: {e} ---[/red]")
        return None
    except Exception as e:
        console.print(f"\n[red]--- Error: {e} ---[/red]")
        return None

def check_first_run(python_exe):
    config_path = "config.json"
    template_path = "config.template.json"
    if not os.path.exists(config_path):
        logger.info("Welcome to Project TALOS!")
        if os.path.exists(template_path):
            shutil.copy(template_path, config_path)
            logger.info("Created 'config.json' from the template.")
        else:
            logger.error("'config.template.json' not found.")
            return
        if not os.path.exists("_profiles"): os.makedirs("_profiles")
        # .ask() returns None on Ctrl+C -- treat as "no" (skip config).
        answer = questionary.confirm("Start configuration now?", default=True, style=TALOS_QUESTIONARY_STYLE, instruction=NAV_SELECT).ask()
        if answer:
            run_script("query_translator.py", python_exe)
            set_active_profile_name("default")
            save_current_state_to_profile("default")
            logger.info("Initial setup complete.")
        else:
            logger.info("Setup skipped. You can configure later via Profile & Settings.")
        time.sleep(2)

def author_tools_menu(python_exe):
    """Author-centric analysis tools: profiler, trajectory, and full report."""
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush()
    console.print(Panel("[bold cyan]Author & Researcher Tools[/bold cyan]\n[dim]Scientometric profiling and ORCID career trajectory mapping[/dim]", style="cyan", border_style="cyan"))
    choice = safe_select("Select author analysis tool:", choices=[
        "1. Author Profiler (Publication History)",
        "2. Author Trajectory Analyzer (ORCID Career Flow)",
        "3. Full Report (Profiler -> Trajectory)",
        "4. Back / Return to Previous Menu"
    ])
    if not choice or "Back" in choice: return
    if choice.startswith("1.") or choice.startswith("2."):
        aid = questionary.text("Enter author name or ORCID iD:", style=TALOS_QUESTIONARY_STYLE, instruction=NAV_SELECT).ask()
        scr = "author_profiler.py" if "1." in choice else "author_trajectory_analyzer.py"
        if aid: run_script(scr, python_exe, args=[aid.strip()])
    elif choice.startswith("3."):
        an = questionary.text("Enter author name:", style=TALOS_QUESTIONARY_STYLE, instruction=NAV_SELECT).ask()
        if an:
            result = run_script("author_profiler.py", python_exe, args=an.strip().split(), capture=True)
            if result and result.stdout:
                sel = next((l.split(":", 1)[1].strip() for l in result.stdout.splitlines() if l.startswith("SELECTED_ORCID_ID:")), None)
                if sel: run_script("author_trajectory_analyzer.py", python_exe, args=[sel])

def database_data_menu(python_exe):
    """Database maintenance, embeddings, scoring and enrichment sub-menu."""
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush()
    console.print(Panel("[bold cyan]Database Maintenance & Data Tools[/bold cyan]\n[dim]Database optimization, enrichment, and persistent storage utilities[/dim]", style="cyan", border_style="cyan"))
    choice = safe_select("Select database utility:", choices=[
        "1. Database Health & VACUUM Optimizer",
        "2. Database Schema Migration",
        "3. Recalculate Overall Scores",
        "4. Re-evaluate Database with LLM",
        "5. Batch Vector Embedding Generation",
        "6. Vector Embedding Schema Migration",
        "7. Metadata Enrichment",
        "8. Unpaywall Data Enricher",
        "9. Zotero Cloud Connector",
        "10. View Recent Evaluation History",
        "11. Export Curated Papers to BibTeX / LaTeX (.bib)",
        "12. Harvest Open Access Full-Text PDFs (12 Cascading Sources)",
        "13. Back / Return to Main Menu"
    ])
    if not choice or "Back" in choice: return
    if choice.startswith("1."): run_script("db_stats.py", python_exe, args=["--optimize"])
    elif choice.startswith("2."): run_script("migrate_database_schema.py", python_exe)
    elif choice.startswith("3."): run_script("recalculate_scores.py", python_exe)
    elif choice.startswith("4."): run_script("reevaluate_database.py", python_exe)
    elif choice.startswith("5."): run_script("embedding_generator.py", python_exe)
    elif choice.startswith("6."): run_script("db_embedding_upgrade.py", python_exe)
    elif choice.startswith("7."): run_script("metadata_enricher.py", python_exe)
    elif choice.startswith("8."): run_script("data_enricher.py", python_exe)
    elif choice.startswith("9."): run_script("zotero_connector.py", python_exe)
    elif choice.startswith("10."): _show_evaluation_history()
    elif choice.startswith("11."):
        from src.utils.bibtex_exporter import BibTeXExporter
        BibTeXExporter().export_and_render()
    elif choice.startswith("12."):
        try:
            from src.ingestion.pdf_harvester.harvester import AcademicPDFHarvester
            summary = AcademicPDFHarvester().harvest_candidates(min_relevance=7.0)
            _render_harvest_summary(summary)
        except Exception as e:
            console.print(f"[red]PDF harvest error: {e}[/red]")
        safe_pause()

def system_health_menu(python_exe):
    """System health, diagnostics, chaos engineering and CI/CD sub-menu."""
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush()
    console.print(Panel("[bold cyan]System Health, Diagnostics & CI/CD[/bold cyan]\n[dim]Stress testing, dependency verification, and test suites[/dim]", style="cyan", border_style="cyan"))
    project_root = os.path.dirname(os.path.abspath(__file__))
    choice = safe_select("Select health/CI operation:", choices=[
        "1. System Health & Diagnostic Analyzer",
        "2. Code Integrity Check",
        "3. API Backend Health Check",
        "4. Dependency Map & Import Audit",
        "5. DRL Agent Status",
        "6. Autonomous Red Tester (Chaos Engineering)",
        "7. 18-Language Documentation Builder",
        "8. System Capabilities Master Viewer",
        "9. Back / Return to Main Menu"
    ])
    if not choice or "Back" in choice: return
    if choice.startswith("1."):
        try:
            from src.utils.system_diagnostics import SystemDiagnosticsEngine
            SystemDiagnosticsEngine().run_and_render()
        except Exception as e:
            console.print(f"[red]Error running System Diagnostics Analyzer: {e}[/red]")
    elif choice.startswith("2."):
        tp = os.path.join(project_root, 'tests', 'test_system_integrity.py')
        if not os.path.exists(tp):
            tp = os.path.join(project_root, 'test_system_integrity.py')  # legacy fallback
        if os.path.exists(tp):
            r = subprocess.run([python_exe, tp], check=False, env=os.environ.copy())
            if r.returncode == 0:
                logger.info("All checks passed!")
            else:
                logger.warning("System Integrity verification exited with code %s.", r.returncode)
        else:
            logger.warning("System Integrity verification not found at tests/test_system_integrity.py")
    elif choice.startswith("3."):
        _probe_api_backend()
    elif choice.startswith("4."):
        mode = safe_select("Dependency audit mode:", choices=[
            "--ci (CI exit-code-only)", "--all (full report)", "Back"
        ])
        if mode is not None and "Back" not in mode:
            flag = "--ci" if "--ci" in mode else "--all"
            run_script("verify_dependency_map.py", python_exe, args=[flag])
    elif choice.startswith("5."):
        _show_drl_status(project_root)
    elif choice.startswith("6."):
        console.print(_build_info_panel(
            "Autonomous Red Tester (RL-Driven Chaos Engineering)",
            "Stress-tests TALOS system components using a Non-Stationary\n"
            "Epsilon-Greedy Multi-Armed Bandit. Diagnoses crashes with\n"
            "LLM-as-a-Judge (Fast Edge tier) and saves Markdown reports.",
            border_style="bright_magenta",
        ))
        cycles_str = questionary.text("Number of test cycles (default 10):", default="10", style=TALOS_QUESTIONARY_STYLE, instruction=NAV_TEXT).ask()
        cycles = 10
        if cycles_str is not None:
            try:
                cycles = int(cycles_str.strip()) if cycles_str.strip() else 10
            except ValueError:
                cycles = 10
                console.print("[yellow]Invalid input. Using default (10).[/yellow]")
        try:
            from src.ai.testing.red_tester import run_red_tester
            run_red_tester(cycles=cycles)
        except Exception as e:
            console.print(f"[red]Error running Autonomous Red Tester: {e}[/red]")
    elif choice.startswith("7."):
        console.print(_build_info_panel(
            "Codebase Documentation Generator (18 Languages)",
            "Uses LOCAL Ollama -- zero cloud cost, full privacy.\n"
            "Produces detailed Markdown docs for every code file selected.\n"
            "[dim]Supports: English, Greek, Chinese, Hindi, Spanish, Arabic, and 12 more.[/dim]",
            border_style="bright_blue",
        ))
        if questionary.confirm("Launch documentation generator?", default=True, style=TALOS_QUESTIONARY_STYLE, instruction=NAV_SELECT).ask():
            run_script("generate_docs.py", python_exe)
    elif choice.startswith("8."):
        _open_capabilities_viewer()
    console.print(); safe_pause("Press Enter...")

def api_keys_menu(python_exe):
    from dotenv import dotenv_values
    project_root = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(project_root, '.env')
    if not os.path.exists(env_path):
        ep = os.path.join(project_root, 'example.env')
        if os.path.exists(ep): shutil.copy(ep, env_path)
        else: open(env_path, 'w').close()
    ALL_KEYS = [
        ("Contact", [("MAILTO", "Contact Email")]),
        ("Premium AI", [("GEMINI_API_KEY", "Gemini"), ("DEEPSEEK_API_KEY", "DeepSeek"), ("HF_TOKEN", "HuggingFace")]),
        ("Academic", [("SEMANTIC_SCHOLAR_API_KEY", "Semantic Scholar"), ("IEEE_API_KEY", "IEEE"),
         ("ELSEVIER_API_KEY", "Scopus"), ("SPRINGER_API_KEY", "Springer"), ("CORE_API_KEY", "CORE"), ("OPENARCHIVES_API_KEY", "OpenArchives")]),
        ("Integrations", [("DISCORD_WEBHOOK_URL", "Discord"), ("ZOTERO_USER_ID", "Zotero ID"), ("ZOTERO_API_KEY", "Zotero Key"),
         ("ORCID_CLIENT_ID", "ORCID ID"), ("ORCID_CLIENT_SECRET", "ORCID Secret")]),
        ("Local", [("LOCAL_MODEL_NAME", "Chat Model"), ("LOCAL_EMBEDDING_MODEL", "Embedding Model")]),
    ]
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.flush()
        console.print(Panel("[bold cyan]API Keys Configuration[/bold cyan]\n[dim]Configure API credentials and verify provider connectivity[/dim]", style="cyan", border_style="cyan"))
        vals = dotenv_values(env_path)
        keys_table = Table(
            title="[bold bright_cyan]API Keys Management[/bold bright_cyan]",
            box=box.ROUNDED,
            border_style="cyan",
            header_style="bold bright_cyan",
        )
        keys_table.add_column("Key", style="cyan")
        keys_table.add_column("Status", style="yellow")
        keys_table.add_column("Category | Description", style="dim white")
        for cat, keys in ALL_KEYS:
            for k, d in keys:
                v = vals.get(k, "")
                s = "[green][SET][/green]" if v.strip() else "[red][NOT SET][/red]"
                keys_table.add_row(k, s, f"[magenta]{cat}[/magenta] | {d}")
        console.print(keys_table)
        console.print("\n[1] Edit key  [2] API Diagnostics  [3] Back / Return to Previous Menu")
        c = safe_select("Select API key operation:", [
            "1. Edit a key",
            "2. API Diagnostics",
            "3. Back / Return to Previous Menu"
        ])
        if not c or "Back" in c: return
        if c.startswith("1"):
            flat = []
            for cat, keys in ALL_KEYS:
                flat.append(f"--- {cat} ---")
                for k, d in keys:
                    v = vals.get(k, ""); s = "[SET]" if v.strip() else "[NOT SET]"
                    flat.append(f"{k}  {s}")
            flat.append("Cancel")
            sel = safe_select("Key:", choices=flat)
            if sel and not sel.startswith("---") and sel != "Cancel":
                k = sel.split()[0]; cv = vals.get(k, "")
                nv = questionary.text(f"New value for {k}:", default=cv, style=TALOS_QUESTIONARY_STYLE, instruction=NAV_SELECT).ask()
                if nv is not None:
                    from dotenv import set_key
                    try:
                        set_key(env_path, k, nv.strip())
                        os.environ[k] = nv.strip()
                        logger.info("[%s] updated.", k)
                    except Exception as e:
                        logger.error("Error: %s", e)
        elif c.startswith("2"):
            tp = _resolve_script_path("api_health_check.py")
            if os.path.exists(tp): subprocess.run([python_exe, tp], check=False)
        safe_pause("\nPress Enter...")

def _current_strategy_key():
    """Return the active ai_execution_strategy key for display, or 'unset'.

    Returns:
        str: The current strategy key (e.g. 'strict_local') or 'unset'.
    """
    try:
        from src.utils.ai_strategy_selector import _current_strategy
        return _current_strategy() or "unset"
    except Exception:
        return "unset"


def _launch_strategy_selector():
    """Launch the interactive AI execution strategy switcher in-process."""
    try:
        from src.utils.ai_strategy_selector import select_ai_execution_strategy
        select_ai_execution_strategy(None)
    except Exception as e:
        console.print(f"[red]Error launching strategy switcher: {e}[/red]")


def profile_settings_menu(python_exe):
    """Configuration & Profiles sub-menu: profiles, models, and API keys."""
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.stdout.flush()
        console.print(Panel("[bold cyan]Configuration & Profiles[/bold cyan]\n[dim]Manage research profiles, API keys, and model parameters[/dim]", style="cyan", border_style="cyan"))
        strategy_entry = f"3. AI Execution Strategy Switcher (Current: {_current_strategy_key()})"
        c = safe_select("Select profile setting:", choices=[
            "1. Research Setup Wizard (Full Onboarding & Reconfiguration)",
            "2. Manage Profiles",
            strategy_entry,
            "4. Research Pivot Wizard",
            "5. Research Goal (Query Translator / Cognitive Query Compiler)",
            "6. AI Model Management (2D Matrix)",
            "7. Model Discovery (Quality Scoring)",
            "8. Hardware-Aware Model Advisor (VRAM Budget & SOTA)",
            "9. Discover Top LLMs & Live Benchmarks",
            "10. Autonomous Model Scavenger & Market Intelligence (MD/HTML)",
            "11. Model Provisioning CLI",
            "12. API Keys Management",
            "13. API Key Diagnostics",
            "14. Create Desktop Shortcut (1-Click Launcher)",
            "15. Back / Return to Main Menu"
        ])
        if not c or "Back" in c: return
        if c == "1. Research Setup Wizard (Full Onboarding & Reconfiguration)": run_script("research_setup_wizard.py", python_exe)
        elif c == "2. Manage Profiles": run_script("profile_manager.py", python_exe)
        elif "AI Execution Strategy Switcher" in c: _launch_strategy_selector()
        elif c == "4. Research Pivot Wizard": run_script("research_pivot.py", python_exe)
        elif c == "5. Research Goal (Query Translator / Cognitive Query Compiler)": run_script("query_translator.py", python_exe)
        elif c == "6. AI Model Management (2D Matrix)":
            console.print("\n[bold bright_cyan]Launching AI Model Manager...[/bold bright_cyan]\n")
            try:
                from src.ai.llm.model_manager import main as mm_main
                mm_main()
            except Exception as e:
                console.print(f"[red]Error launching Model Manager: {e}[/red]")
        elif c == "7. Model Discovery (Quality Scoring)": _run_model_discovery()
        elif c == "8. Hardware-Aware Model Advisor (VRAM Budget & SOTA)": _run_hardware_advisor()
        elif c == "9. Discover Top LLMs & Live Benchmarks": _run_discover_llms()
        elif "Autonomous Model Scavenger" in c: _run_scavenge_models()
        elif c == "11. Model Provisioning CLI": run_script("model_provisioner.py", python_exe)
        elif c == "12. API Keys Management": api_keys_menu(python_exe)
        elif c == "13. API Key Diagnostics": run_script("api_health_check.py", python_exe)
        elif c == "14. Create Desktop Shortcut (1-Click Launcher)":
            from src.utils.desktop_shortcut import create_desktop_shortcut
            create_desktop_shortcut()
        safe_pause("\nPress Enter...")

# -- v5.9.15: Silent Fast Boot --
# The legacy startup model verifier (_verify_local_models) has been removed.
# Local model inspection and installation is now strictly on-demand via
# src/ai/llm/model_manager.py (Option 1: Configure AI Models).


# ---------------------------------------------------------------------------
# -- Rich TUI: Dynamic Status Table Builder --
# ---------------------------------------------------------------------------

def _read_active_focus():
    """Return the active research focus string from config.json.

    Resolution order: research_topic, then active_focus_summary, then
    user_research_goal. Returns an empty string when nothing is configured.

    Returns:
        str: The active research focus (may be empty).
    """
    try:
        import json as _json
        with open("config.json", "r", encoding="utf-8") as _f:
            _cfg = _json.load(_f)
        return (
            (_cfg.get("research_topic") or "").strip()
            or (_cfg.get("active_focus_summary") or "").strip()
            or (_cfg.get("user_research_goal") or "").strip()
        )
    except Exception:
        return ""


def _build_status_table():
    """Build and return a Rich Table with live system status information.

    Reads configuration from environment variables and config/settings.py
    to display:
      - Conda Environment / API Port / Synapse Bus
      - Active Execution Mode (Air-Gapped Local / Hybrid / Cloud)
      - Active Tiers: Fast Edge, Heavy Reasoning, Cloud Provider
      - Active Research Focus (from config.json user_research_goal)
    """
    # -- Detect Conda environment name (v5.9.3: sys.prefix fallback) --
    conda_env = os.environ.get("CONDA_DEFAULT_ENV")
    if not conda_env:
        if "envs" in sys.prefix:
            conda_env = os.path.basename(sys.prefix)
        elif hasattr(sys, "real_prefix") or sys.base_prefix != sys.prefix:
            conda_env = os.path.basename(sys.prefix)  # virtualenv fallback
        else:
            conda_env = "N/A"

    # -- v5.9.4: 2D Execution Matrix --
    net_strat = os.environ.get("TALOS_NETWORK_STRATEGY", TALOS_NETWORK_STRATEGY)
    hw_strat = os.environ.get("TALOS_HARDWARE_STRATEGY", TALOS_HARDWARE_STRATEGY)
    network_labels = {
        "strict_local": "Strict Local",
        "local_first":  "Local-First",
        "cloud_first":  "Cloud-First",
        "strict_cloud": "Strict Cloud",
    }
    hardware_labels = {
        "cpu_only":       "CPU Only",
        "gpu_only":       "GPU Only",
        "cpu_gpu_split":  "CPU+GPU Split",
    }
    net_display = network_labels.get(net_strat, net_strat)
    hw_display = hardware_labels.get(hw_strat, hw_strat)
    mode_display = f"{net_display} / {hw_display}"

    # -- Fast Edge model: use raw configuration string directly --
    fast_edge = os.environ.get("FAST_EDGE_MODEL", FAST_EDGE_MODEL)

    # -- Heavy Reasoning model: use raw configuration string directly --
    heavy_model = os.environ.get("HEAVY_REASONING_MODEL", HEAVY_REASONING_MODEL)

    # -- Cloud provider: display raw provider name + raw model name --
    cloud_prov = os.environ.get("TALOS_CLOUD_PROVIDER", CLOUD_PROVIDER)
    if cloud_prov == "gemini":
        gemini_model = os.environ.get("GEMINI_FLASH_MODEL", GEMINI_FLASH_MODEL)
        cloud_display = f"Gemini ({gemini_model})"
    elif cloud_prov == "deepseek":
        deepseek_model = os.environ.get("DEEPSEEK_MODEL_CHAT", DEEPSEEK_MODEL_CHAT)
        cloud_display = f"DeepSeek ({deepseek_model})"
    else:
        cloud_display = str(cloud_prov) if cloud_prov else "None"

    # -- Synapse bus URL shorthand --
    synapse_short = "localhost:8000" if "8000" in SYNAPSE_BUS_URL else SYNAPSE_BUS_URL

    # -- Build the table --
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Key", style="dim cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Conda Environment", f"[bold bright_cyan]{conda_env}[/bold bright_cyan]")
    table.add_row("API Port", f"[bold green]{TALOS_API_PORT}[/bold green]")
    table.add_row("Synapse Bus", f"[dim green]{synapse_short}[/dim green]")
    table.add_row("", "")
    table.add_row("Execution Mode", f"[bold yellow]{net_display} / {hw_display}[/bold yellow]")
    table.add_row("", "")
    table.add_row("Fast Edge Tier", f"[bright_cyan]{fast_edge}[/bright_cyan]")
    table.add_row("Heavy Reasoning Tier", f"[bright_magenta]{heavy_model}[/bright_magenta]")
    table.add_row("Cloud Provider", f"[bright_blue]{cloud_display}[/bright_blue]")
    table.add_row("", "")
    # -- Active Research Focus (from config.json) --
    focus = _read_active_focus()
    focus_display = (
        f"[bold bright_green]{focus}[/bold bright_green]"
        if focus else "[dim]Not configured[/dim]"
    )
    table.add_row("Active Research Focus", focus_display)

    return table


# ---------------------------------------------------------------------------
# -- Interactive View & Pivot Research Focus (v5.8.9) --
# ---------------------------------------------------------------------------

def _view_and_pivot_research_focus(python_exe, project_root):
    """Display current research goal and offer interactive pivot workflow.

    Shows a cyan-bordered Panel with the raw research goal text from
    config.json plus a preview of existing boolean queries (if any).
    The user may then either pivot to a new goal (running Query Translator
    in-place), view all 14 generated queries, or return to the main menu.

    Args:
        python_exe: Path to the Python executable.
        project_root: Absolute path to the project root directory.
    """
    os.system('cls' if os.name == 'nt' else 'clear')

    # -- Read current goal and queries from config.json --
    current_goal = ""
    queries = {}
    try:
        import json as _json
        with open("config.json", "r", encoding="utf-8") as _f:
            _cfg = _json.load(_f)
        current_goal = _cfg.get("user_research_goal") or _cfg.get("phd_focus_system_prompt", "")
        # Collect any keys ending in _query as boolean queries
        for k, v in _cfg.items():
            if k.endswith("_query") and isinstance(v, str) and v.strip():
                queries[k] = v
    except Exception:
        current_goal = "[Error reading config.json]"

    # -- Build the goal preview panel --
    goal_body = Text()
    if current_goal.strip():
        goal_body.append("Current Research Goal:\n\n", style="bold white")
        goal_body.append(current_goal.strip(), style="bright_green")
    else:
        goal_body.append("No research goal configured.", style="dim yellow")

    goal_panel = Panel(
        goal_body,
        title="[bold]Active Research Focus[/bold]",
        border_style="cyan",
        box=box.ROUNDED,
        padding=(1, 2),
    )
    console.print(goal_panel)
    console.print("")

    # -- Show query preview if queries exist --
    if queries:
        query_text = Text()
        query_text.append(f"Boolean Queries Defined: {len(queries)} of 14\n\n", style="bold bright_cyan")
        for i, (k, v) in enumerate(sorted(queries.items())):
            short_name = k.replace("_query", "")
            short_val = v[:80] + ("..." if len(v) > 80 else "")
            query_text.append(f"[dim]{short_name}:[/dim] {short_val}\n")
            if i >= 4:  # Show first 5, then ...
                remaining = len(queries) - i - 1
                if remaining > 0:
                    query_text.append(f"\n[dim]... and {remaining} more. Select 'View All Queries' below to see full list.[/dim]")
                break
        query_panel = Panel(
            query_text,
            title="[bold]Query Preview[/bold]",
            border_style="bright_blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
        console.print(query_panel)
        console.print("")

    # -- Interactive menu --
    pivot_choice = safe_select("View & Pivot Research Focus:", choices=[
        "1. Pivot to New Research Goal (Run Query Translator)",
        "2. View All 14 Generated Boolean Queries",
        "3. Return to Main Menu",
    ])

    if pivot_choice is None or "3." in pivot_choice:
        return

    if "1." in pivot_choice:
        # -- Prompt for new goal --
        new_goal = questionary.text(
            "Enter your new research goal (natural language):",
            default=current_goal.strip() if current_goal.strip() else "",
            style=TALOS_QUESTIONARY_STYLE,
        ).ask()
        if new_goal is None or not new_goal.strip():
            console.print("\n[yellow]Pivot cancelled -- no goal provided.[/yellow]")
            safe_pause()
            return

        # -- Update config.json with the new goal --
        try:
            import json as _json
            with open("config.json", "r", encoding="utf-8") as _f:
                _cfg = _json.load(_f)
            _cfg["user_research_goal"] = new_goal.strip()
            # Clear old queries so the Cognitive Query Compiler regenerates them fresh
            for k in list(_cfg.keys()):
                if k.endswith("_query"):
                    _cfg[k] = ""
            with open("config.json", "w", encoding="utf-8") as _f:
                _json.dump(_cfg, _f, indent=2, ensure_ascii=False)
            console.print("\n[green][SUCCESS][/green] Research goal updated. Launching Cognitive Query Compiler...\n")
        except Exception as e:
            console.print(f"\n[red]Error updating config.json: {e}[/red]")
            safe_pause()
            return

        # -- Run Query Translator in-process (same as run_script but with
        #    confirmation first) --
        info = _build_info_panel(
            "Cognitive Query Compiler -- Query Translator",
            "Translates your natural-language research goal into optimized\n"
            "boolean search queries for all 18 academic APIs.\n"
            "[dim]Uses the AI Manager with Research Architect persona.[/dim]",
            border_style="bright_magenta",
        )
        console.print(info)
        if questionary.confirm("Proceed with Query Translation?", default=True, style=TALOS_QUESTIONARY_STYLE, instruction=NAV_SELECT).ask():
            run_script("query_translator.py", python_exe)
            # -- Show success panel --
            success = _build_info_panel(
                "Research Focus Pivot Complete",
                f"New goal set and queries regenerated.\n"
                f"[bright_green]{new_goal.strip()[:100]}[/bright_green]",
                border_style="green",
            )
            console.print(success)
        safe_pause()

    elif "2." in pivot_choice:
        # -- View all generated boolean queries --
        os.system('cls' if os.name == 'nt' else 'clear')
        try:
            import json as _json
            with open("config.json", "r", encoding="utf-8") as _f:
                _cfg = _json.load(_f)
            q_table = Table(
                title="[bold bright_cyan]All Generated Boolean Queries[/bold bright_cyan]",
                box=box.ROUNDED,
                border_style="cyan",
                show_lines=True,
                header_style="bold bright_cyan",
            )
            q_table.add_column("#", style="dim cyan", width=4, justify="right")
            q_table.add_column("API Source", style="bright_magenta", width=20)
            q_table.add_column("Boolean Query", style="white", width=60, overflow="fold")
            count = 0
            for k in sorted(_cfg.keys()):
                if k.endswith("_query"):
                    count += 1
                    v = _cfg[k]
                    q_table.add_row(str(count), k.replace("_query", ""), v if v else "[dim](empty)[/dim]")
            if count == 0:
                q_table.add_row("", "[dim yellow]No queries defined.[/dim yellow]", "")
            console.print(q_table)
        except Exception as e:
            console.print(f"[red]Error reading config.json: {e}[/red]")
        safe_pause()


def _configure_daemon_autostart(project_root):
    """Interactive pre-flight configuration for the 24/7 daemon.

    Prompts first for the target research profile (mandatory), then the daemon
    network strategy and target sources, and finally an optional Windows OS
    autostart hook. Persists the strategy to .env and, together with the
    sources and the selected profile, into the isolated profile config under
    ``_profiles/<profile>/config.json``.

    Args:
        project_root (str): Absolute path to the project root.
    """
    from dotenv import set_key

    env_path = os.path.join(project_root, '.env')
    if not os.path.exists(env_path):
        console.print("[yellow]No .env file found -- creating an empty one.[/yellow]")
        open(env_path, 'w', encoding='utf-8').close()

    # -- 0. Target research profile (first mandatory prompt) --
    profiles = ProfileManager().list_profiles()
    active = ProfileManager().get_active_profile_name()
    target_profile = questionary.select(
        "Select target research profile for the 24/7 background daemon:",
        choices=profiles,
        default=active if active in profiles else (profiles[0] if profiles else "default"),
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if not target_profile:
        console.print("[yellow]Autostart configuration cancelled.[/yellow]")
        return

    # -- 1. Network strategy --
    strategy = questionary.select(
        "Select Daemon Network Strategy (Redundancy):",
        choices=[
            questionary.Choice("local_first (Recommended) -- local primary, auto-fallback to cloud", "local_first"),
            questionary.Choice("strict_local -- air-gapped, never cloud", "strict_local"),
            questionary.Choice("cloud_first -- cloud primary, auto-fallback to local", "cloud_first"),
            questionary.Choice("strict_cloud -- cloud only, never local", "strict_cloud"),
        ],
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if strategy:
        try:
            set_key(env_path, "TALOS_NETWORK_STRATEGY", strategy)
            os.environ["TALOS_NETWORK_STRATEGY"] = strategy
            console.print(f"[green][OK] TALOS_NETWORK_STRATEGY set to {strategy}.[/green]")
        except Exception as e:
            console.print(f"[red][ERROR] Could not update .env: {e}[/red]")

    # -- 2. Target sources --
    selected_sources = prompt_source_selection()
    if selected_sources is None:
        console.print("[dim]Source selection cancelled.[/dim]")
        sources = None
    else:
        sources = selected_sources or list(ALL_ACADEMIC_SOURCES)

    # -- 2b. Persist profile + strategy + sources into the profile config --
    try:
        from src.utils.daemon_autostart import persist_daemon_config
        persist_daemon_config(target_profile, strategy=strategy, sources=sources)
    except Exception as e:
        console.print(f"[red][ERROR] Could not persist daemon config into profile: {e}[/red]")

    # -- 3. Autostart hook --
    install_hook = questionary.confirm(
        "Install Windows Autostart Hook?",
        default=False,
        style=TALOS_QUESTIONARY_STYLE,
    ).ask()
    if install_hook:
        try:
            from src.utils.daemon_autostart import install_windows_autostart
            result = install_windows_autostart(profile_name=target_profile)
            if result:
                console.print(f"[green][OK] Autostart hook installed: {result}[/green]")
            else:
                console.print("[yellow][WARN] Autostart hook could not be installed.[/yellow]")
        except Exception as e:
            console.print(f"[red][ERROR] Autostart installation failed: {e}[/red]")


def _launch_daemon_in_new_console(project_root, python_exe):
    """Spawn the 24/7 autonomous daemon in a detached console window.

    On Windows the daemon is launched with subprocess.CREATE_NEW_CONSOLE so it
    owns a fresh console window while the main TUI stays interactive. On
    non-Windows platforms the existing synchronous run_script() path is kept.

    Args:
        project_root (str): Absolute path to the project root.
        python_exe (str): Path to the active Python interpreter (used as the
            fallback launcher on non-Windows platforms).
    """
    daemon_script = os.path.join(
        project_root, "src", "ai", "drl", "talos_service.py"
    )
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    if USE_LOCAL_MODEL:
        env["TALOS_USE_LOCAL"] = "1"

    if sys.platform == "win32":
        try:
            subprocess.Popen(
                [sys.executable, daemon_script],
                cwd=project_root,
                env=env,
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
        except OSError as exc:
            console.print(f"[red][ERROR] Daemon launch failed: {exc}[/red]")
            return
        console.print(_build_info_panel(
            "Autonomous Research Daemon Launched",
            "[INIT] Autonomous Research Daemon launched in a new console window.\n"
            "Main TUI remains active. Return to the main menu is immediate.",
            border_style="green",
        ))
    else:
        run_script("talos_service.py", python_exe)


def _launch_visualizer():
    """Auto-start FastAPI on port 8001 and open the WebGL visualizer.

    The routine first checks the local TCP port. If the backend is offline,
    it starts Uvicorn as a silent non-blocking subprocess and polls for up to
    three seconds. The browser opens only after the service accepts connections.
    """
    import socket
    import webbrowser

    host = "127.0.0.1"
    port = 8001
    viz_url = f"http://{host}:{port}/api/v1/visualizer/live"

    def _port_is_listening():
        """Return True when the local FastAPI TCP port accepts connections."""
        try:
            with socket.create_connection((host, port), timeout=0.25):
                return True
        except OSError:
            return False

    console.print(_build_info_panel(
        "3D Knowledge Constellation Visualizer",
        "Vendored Three.js r128 constellation with 60 FPS animated\n"
        "laser beams, traveling photon pulses, interactive click-to-fire\n"
        "nodes, PNG snapshot, fullscreen, help overlay, and glassmorphism\n"
        "HUD. Live 1000ms AJAX polling + Offline Conference Replay.\n\n"
        f"Access URL: {viz_url}",
        border_style="bright_cyan",
    ))

    if not _port_is_listening():
        console.print(
            "[cyan][INIT] FastAPI backend offline. Auto-bootstrapping "
            "microservice on port 8001 in background...[/cyan]"
        )
        project_root = os.path.dirname(os.path.abspath(__file__))
        try:
            subprocess.Popen(
                [
                    sys.executable,
                    "-m",
                    "uvicorn",
                    "src.api.main_api:app",
                    "--host",
                    host,
                    "--port",
                    str(port),
                ],
                cwd=project_root,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            console.print(f"[red][ERROR] FastAPI bootstrap failed: {exc}[/red]")
            return

        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            if _port_is_listening():
                break
            time.sleep(0.15)

    if not _port_is_listening():
        console.print(
            "[red][ERROR] FastAPI did not become reachable on port 8001 "
            "within three seconds.[/red]"
        )
        return

    webbrowser.open(viz_url)
    console.print(_build_info_panel(
        "Visualizer Online",
        "FastAPI is listening on port 8001.\n"
        "The default browser has been opened.\n\n"
        f"{viz_url}",
        border_style="green",
    ))


def _generate_optica_plots():
    """Drive the OPTICA visualization bridge from the TALOS TUI.

    Prompts the user for a plot type and a journal template, then delegates
    the heavy rendering work to the Project OPTICA microservice (port 8002).
    The result (or a graceful error) is rendered in a Rich panel.
    """
    # -- Plot type selection --
    plot_choice = safe_select(
        "Select a visualization to generate (via OPTICA):",
        choices=[
            "opex_dashboard (OPEX & Scores Multi-Panel)",
            "semantic_topology (Elite Semantic Graph)",
        ],
    )
    if plot_choice is None:
        return
    plot_type = plot_choice.split(" ")[0]

    # -- Journal template selection --
    journal_template = safe_select(
        "Select the journal template:",
        choices=["nature", "science", "cell"],
    )
    if journal_template is None:
        return

    info = _build_info_panel(
        "Data Visualizations (via OPTICA)",
        "Offloading graphics rendering to Project OPTICA (port 8002).\n"
        f"[dim]Plot: {plot_type} | Journal template: {journal_template}[/dim]",
        border_style="bright_magenta",
    )
    console.print(info)

    # -- Lazy import: keep the OPTICA client out of the startup path --
    try:
        from src.integration.optica_client import OpticaClient
        result = OpticaClient().request_plot(plot_type, journal_template)
    except Exception as exc:  # pragma: no cover - defensive
        result = {
            "ok": False,
            "error": f"Failed to reach OPTICA: {exc}",
            "output_path": None,
        }

    # -- Render the result in a Rich panel --
    if result.get("ok"):
        output_path = result.get("output_path") or result.get("path")
        body = "OPTICA plot generated successfully."
        if output_path:
            body += f"\n\n[bold green]Output:[/bold green] {output_path}"
        console.print(Panel(
            body,
            title="[bold]OPTICA Bridge[/bold]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        ))
    else:
        error_msg = result.get("error", "OPTICA is unreachable.")
        console.print(Panel(
            f"[bold red]OPTICA request failed.[/bold red]\n\n{error_msg}\n\n"
            "[dim]Ensure Project OPTICA is running on port 8002 and retry.[/dim]",
            title="[bold]OPTICA Bridge[/bold]",
            border_style="red",
            box=box.ROUNDED,
            padding=(1, 2),
        ))


def _show_drl_status(project_root):
    """Display DRL model and GWO hyperparameter status in a Rich panel.

    Reads models/dddqn_trained.pth and probes the GWO artifact paths:
    models/gwo_foraging_hyperparameters.json, models/gwo_llm_router_reward_weights.json,
    and the legacy models/gwo_parameters.json (v5.11.3 multi-path check).

    Args:
        project_root: Absolute path to the project root directory.
    """
    mp = os.path.join(project_root, "models", "dddqn_trained.pth")
    # -- v5.11.3: multi-path GWO artifact detection (current + router + legacy) --
    gwo_candidates = [
        os.path.join(project_root, "models", "gwo_foraging_hyperparameters.json"),
        os.path.join(project_root, "models", "gwo_llm_router_reward_weights.json"),
        os.path.join(project_root, "models", "gwo_parameters.json"),  # legacy path
    ]
    gp = next((p for p in gwo_candidates if os.path.exists(p)), None)
    t = Table(show_header=False, box=box.SIMPLE, border_style="cyan")
    t.add_column("Parameter", style="dim cyan")
    t.add_column("Value", style="white")
    if os.path.exists(mp):
        t.add_row("DRL Model", f"[green]Present ({os.path.getsize(mp)/1024:.0f} KB)")
    else:
        t.add_row("DRL Model", "[red]Not found")
    if gp:
        t.add_row("GWO Tuning", "[bold green]Present[/bold green]")
        # -- Detailed metrics are rendered only for the foraging artifact. --
        if os.path.basename(gp) == "gwo_foraging_hyperparameters.json":
            try:
                import json
                with open(gp, "r", encoding="utf-8") as f:
                    p = json.load(f)
                t.add_row("Learning Rate", f"[yellow]{p['learning_rate']:.6e}")
                t.add_row("Gamma", f"[yellow]{p['gamma']:.4f}")
                t.add_row("Epsilon Decay", f"[yellow]{p['epsilon_decay']:.6f}")
                t.add_row("Best Fitness", f"[magenta]{p['best_fitness']:.1f}")
                t.add_row("Best Reward", f"[green]{p['best_avg_reward']:.1f}")
            except (OSError, ValueError, KeyError):
                pass  # -- artifact mid-write or unexpected schema; status row suffices --
    else:
        t.add_row("GWO Tuning", "[yellow]Default Baseline Active[/yellow] [dim](Run Opt 4.6 to tune)[/dim]")
    console.print(Panel(
        t,
        title="[bold]DRL Agent Status[/bold]",
        border_style="cyan",
        box=box.ROUNDED,
    ))


def _show_evaluation_history(limit=30):
    """Render the most recent daemon evaluations in a Rich table.

    Reads data/history/daemon_evaluations.jsonl and displays the latest N
    records with columns: #, Timestamp, Title, Authors, Source, Score, Verdict.

    Args:
        limit (int): Maximum number of records to display (default 30).
    """
    records = read_evaluation_history(limit=limit)
    if not records:
        console.print(Panel(
            "[yellow]No evaluation history recorded yet.[/yellow]\n"
            "[dim]Run the DRL live agent or the 24/7 daemon to populate the history.[/dim]",
            title="[bold]Evaluation History[/bold]",
            border_style="yellow",
            box=box.ROUNDED,
        ))
        safe_pause()
        return

    t = Table(box=box.SIMPLE_HEAVY, border_style="cyan", expand=True)
    t.add_column("#", style="dim", justify="right", no_wrap=True)
    t.add_column("Timestamp", style="dim cyan", no_wrap=True)
    t.add_column("Title", style="bold white", overflow="fold")
    t.add_column("Authors", style="italic white", overflow="fold")
    t.add_column("Source", style="cyan", no_wrap=True)
    t.add_column("Score", style="bold white", justify="right", no_wrap=True)
    t.add_column("Verdict", justify="center", no_wrap=True)

    for i, rec in enumerate(records, start=1):
        score = float(rec.get("score", 0.0) or 0.0)
        verdict = rec.get("verdict", "REJECT")
        if verdict == "ELITE":
            verdict_cell = "[bold gold1]ELITE[/bold gold1]"
        elif verdict == "ACCEPT":
            verdict_cell = "[bold green]ACCEPT[/bold green]"
        else:
            verdict_cell = "[bold red]REJECT[/bold red]"
        t.add_row(
            str(i),
            str(rec.get("timestamp", "--")),
            str(rec.get("title", "Unknown Title")),
            str(rec.get("authors", "Unknown Authors")),
            str(rec.get("source", "unknown")),
            f"{score:.1f}",
            verdict_cell,
        )

    console.print(Panel(
        t,
        title=f"[bold]Evaluation History (last {len(records)})[/bold]",
        border_style="cyan",
        box=box.ROUNDED,
    ))
    safe_pause()


def _run_hardware_advisor():
    """Render the Hardware-Aware Model Advisor + 4-role SOTA matrix (v5.19.0)."""
    from src.core.hardware_advisor import HardwareModelAdvisor
    advisor = HardwareModelAdvisor()
    advisor.render_recommendations()
    advisor.render_role_matrix()
    # -- 1-click adoption of the recommended 4-role model stack. --
    try:
        import questionary
        if questionary.confirm(
            "Adopt the recommended 4-role SOTA model stack "
            "(writes active profile config.json)?",
            default=False,
        ).ask():
            advisor.apply_recommended_models()
    except Exception:
        pass


def _run_discover_llms():
    """Render the SOTA LLM discovery matrix (v5.20.0)."""
    from src.core.model_benchmark_client import run_discover_llms
    run_discover_llms(online=True)


def _render_scavenge_summary(report):
    """Render a Rich summary table for the Autonomous Model Scavenger result.

    Args:
        report (MarketIntelligenceReport): The aggregate scavenging report.
    """
    from rich.table import Table
    from rich import box
    table = Table(
        title=f"Autonomous Model Scavenger Summary (window {report.window_days} days)",
        box=box.ROUNDED,
        border_style="bright_cyan",
        header_style="bold bright_cyan",
        expand=False,
    )
    table.add_column("Metric", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="bold white", no_wrap=True)
    table.add_row("Total Models Scanned", str(report.total_models_scanned))
    table.add_row("Active Providers", str(report.active_providers))
    table.add_row("Average Price /1M Tokens", f"${report.average_price_per_1m_usd:.4f}")
    table.add_row("Local Optimal (RTX 4070)", str(report.local_optimal_count))
    table.add_row("Cloud Cost-Effective", str(report.cloud_cost_effective_count))
    table.add_row("Frontier Reasoning", str(report.frontier_reasoning_count))
    table.add_row("Sources Queried", ", ".join(report.sources_queried) or "none")
    table.add_row("Offline Fallback", str(report.offline_fallback))
    console.print(table)


def _run_scavenge_models(days: int = 30, report_only: bool = False):
    """Run the Autonomous Model Scavenger and emit dual market intelligence reports.

    Args:
        days (int): Discovery window in days.
        report_only (bool): When True, skip the Rich console summary table.

    Returns:
        int: Process exit code (0 on success).
    """
    from src.services.cognitive_mesh.scavenger import ModelScavengerAgent
    from src.services.cognitive_mesh.reporter import IntelligenceReporter
    console.print(_build_info_panel(
        "Autonomous Model Scavenger & Market Intelligence",
        f"Foraging Hugging Face, OpenRouter, and Ollama (window: {days} days)...\n"
        "[dim]Air-gapped offline fallback to cached benchmarks is guaranteed.[/dim]",
        border_style="bright_cyan",
    ))
    report = ModelScavengerAgent().scavenge_market(window_days=days)
    if not report_only:
        _render_scavenge_summary(report)
    md_path, html_path = IntelligenceReporter().generate_reports(report)
    console.print(f"[green][OK] Markdown report: {md_path}[/green]")
    console.print(f"[green][OK] HTML dashboard : {html_path}[/green]")
    return 0


def _run_model_discovery():
    """Run the Model Discovery Engine in-process and render a Rich table."""
    console.print(_build_info_panel(
        "Model Discovery Engine",
        "Discovering active models across the local Ollama tier and optional cloud providers.\n"
        "[dim]Air-gapped fallback registry guarantees offline operation.[/dim]",
        border_style="bright_blue",
    ))
    try:
        from src.ai.llm.model_discovery import get_discovery_engine
        engine = get_discovery_engine()
        report = engine.discover_active_models(online=True)
        active = report.get("active_models", [])
        mode = report.get("mode", "unknown")
        summary = Text(f"Discovery mode: {mode} | Active models: {len(active)}", style="bright_cyan")
        console.print(Panel(
            Align.center(summary),
            title="[bold]Model Discovery[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
        ))
        if active:
            t = Table(show_header=True, box=box.SIMPLE, border_style="cyan")
            t.add_column("Model", style="white")
            t.add_column("Provider", style="dim cyan")
            t.add_column("SWE-bench", style="yellow")
            t.add_column("MMLU-Pro", style="yellow")
            t.add_column("Context", style="dim")
            t.add_column("Pricing", style="magenta")
            for m in active:
                t.add_row(
                    str(m.get("name")),
                    str(m.get("provider", "unknown")),
                    f"{m.get('swe_bench_score')}" if m.get("swe_bench_score") is not None else "-",
                    f"{m.get('mmlu_pro_score')}" if m.get("mmlu_pro_score") is not None else "-",
                    str(m.get("context_window") or "-"),
                    str(m.get("pricing_tier", "unknown")),
                )
            console.print(t)
        else:
            console.print("[yellow]No active models discovered.[/yellow]")
    except Exception as exc:
        console.print(f"[red]Model Discovery failed: {exc}[/red]")


def _probe_api_backend():
    """Probe the local TALOS FastAPI backend on port 8001."""
    import socket
    host, port = "127.0.0.1", 8001
    console.print(_build_info_panel(
        "API Backend Health Check",
        f"Probing TALOS FastAPI backend at http://{host}:{port} ...",
        border_style="bright_blue",
    ))
    try:
        with socket.create_connection((host, port), timeout=2.0):
            reachable = True
    except OSError:
        reachable = False
    status = "[green]REACHABLE[/green]" if reachable else "[red]UNREACHABLE[/red]"
    console.print(Panel(
        f"API Backend: {status}  (http://{host}:{port})",
        title="[bold]Health Check[/bold]",
        border_style="green" if reachable else "red",
        box=box.ROUNDED,
        padding=(1, 2),
    ))


def _open_capabilities_viewer():
    """Auto-bootstrap the FastAPI backend and open the capabilities reference."""
    import socket
    import webbrowser
    host, port = "127.0.0.1", 8001
    url = f"http://{host}:{port}/api/v1/capabilities"
    console.print(_build_info_panel(
        "System Capabilities Master Viewer",
        "Serves the ultra-detailed capabilities whitepaper via the local FastAPI backend.",
        border_style="bright_cyan",
    ))
    try:
        with socket.create_connection((host, port), timeout=0.25):
            listening = True
    except OSError:
        listening = False
    if not listening:
        project_root = os.path.dirname(os.path.abspath(__file__))
        try:
            subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "src.api.main_api:app", "--host", host, "--port", str(port)],
                cwd=project_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            console.print(f"[red][ERROR] FastAPI bootstrap failed: {exc}[/red]")
            return
        deadline = time.monotonic() + 3.0
        while time.monotonic() < deadline:
            try:
                with socket.create_connection((host, port), timeout=0.25):
                    listening = True
                    break
            except OSError:
                time.sleep(0.15)
    if not listening:
        console.print("[red][ERROR] FastAPI did not become reachable on port 8001.[/red]")
        return
    webbrowser.open(url)
    console.print(_build_info_panel("Capabilities Viewer Online", f"Opened {url}", border_style="green"))


def _open_d3_architecture_graph(python_exe, project_root):
    """Regenerate the D3 architecture graph and open it in the browser."""
    console.print(_build_info_panel(
        "Dynamic D3 Architecture Graph",
        "Regenerates the dependency graph from the live codebase and opens the interactive D3 viewer.",
        border_style="bright_cyan",
    ))
    run_script("generate_architecture_graph.py", python_exe)
    import webbrowser, socket
    port = 8765
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.settimeout(0.5)
        if s.connect_ex(('127.0.0.1', port)) != 0:
            sd = os.path.join(project_root, "templates")
            subprocess.Popen([python_exe, "-m", "http.server", str(port), "--bind", "127.0.0.1", "--directory", sd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        s.close()
    except Exception:
        pass
    webbrowser.open(f"http://localhost:{port}/architecture_graph.html")


def _launch_gwo_dashboard(python_exe):
    """Launch the GWO 3D Swarm live dashboard on Dash port 8050."""
    import webbrowser, socket
    console.print(_build_info_panel(
        "GWO Live Dashboard",
        "Real-Time 3D Swarm Hunt\n"
        "Starts a Dash server at http://localhost:8050\n"
        "Shows live 3D scatter plot of GWO wolf pack convergence.\n"
        "Auto-refreshes every 3 seconds.",
        border_style="bright_magenta",
    ))
    dash_running = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        if s.connect_ex(('127.0.0.1', 8050)) == 0:
            dash_running = True
        s.close()
    except Exception:
        pass
    if not dash_running:
        logger.info("Starting Dash server...")
        script_path = _resolve_script_path("gwo_live_dashboard.py")
        subprocess.Popen([python_exe, script_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
    webbrowser.open("http://localhost:8050")
    logger.info("Dashboard opened in browser.")


def search_ingestion_menu(python_exe):
    """Research search and ingestion sub-menu (Universal Search Hub)."""
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush()
    console.print(Panel("[bold cyan]Universal Search Hub[/bold cyan]\n[dim]Daily harvesting, deep archives, citation graphs, dense retrieval, and reproducible code[/dim]", style="cyan", border_style="cyan"))
    choice = safe_select("Select search operation:", choices=[
        "1. Daily Concurrent Harvester (18 APIs in Parallel)",
        "2. Historical Deep Window Search (Days Window)",
        "3. Autonomous Citation Snowballing Search (Graph Traversal)",
        "4. Neural Vector Semantic Search (Local nomic-embed-text)",
        "5. Reproducible Code-First Search (GitHub / Benchmark Linked)",
        "6. PRISMA-ScR Swarm Declarative Pipeline (Stanford DSPy)",
        questionary.Separator(),
        "7. Grey Literature Miner",
        "8. Zotero Cloud Sync",
        "9. Interactive Dashboard (Flask)",
        "10. SQLite FTS5 Full-Text Search (Search Inside PDF Bodies)",
        questionary.Separator(),
        "11. Back / Return to Main Menu"
    ])
    if not choice or "Back" in choice: return
    if choice.startswith("1."):
        selected = prompt_source_selection()
        if selected is None:
            console.print("[dim]Source selection cancelled.[/dim]")
        elif not selected:
            console.print("[yellow]No sources selected.[/yellow]")
        else:
            run_script("daily_search.py", python_exe, args=["--sources"] + selected)
    elif choice.startswith("2."):
        if questionary.confirm("This may take a long time. Proceed?", default=False, style=TALOS_QUESTIONARY_STYLE, instruction=NAV_CONFIRM).ask():
            selected = prompt_source_selection()
            if selected is None:
                console.print("[dim]Source selection cancelled.[/dim]")
            elif not selected:
                console.print("[yellow]No sources selected.[/yellow]")
            else:
                run_script("historic_search.py", python_exe, args=["--sources"] + selected)
    elif choice.startswith("3."):
        seed = questionary.text("Seed paper (DOI, database ID, or title):", style=TALOS_QUESTIONARY_STYLE).ask()
        if seed and seed.strip():
            try:
                from src.search.citation_snowballing import CitationSnowballEngine
                CitationSnowballEngine().run(seed.strip())
            except Exception as e:
                console.print(f"[red]Citation snowballing error: {e}[/red]")
        safe_pause()
    elif choice.startswith("4."):
        query = questionary.text("Research query (semantic):", style=TALOS_QUESTIONARY_STYLE).ask()
        if query and query.strip():
            try:
                from src.search.neural_vector_search import NeuralVectorSearchEngine
                NeuralVectorSearchEngine().run(query.strip())
            except Exception as e:
                console.print(f"[red]Neural vector search error: {e}[/red]")
        safe_pause()
    elif choice.startswith("5."):
        query = questionary.text("Research query (code-first):", style=TALOS_QUESTIONARY_STYLE).ask()
        if query and query.strip():
            try:
                from src.search.code_first_search import CodeFirstSearchEngine
                CodeFirstSearchEngine().run(query.strip())
            except Exception as e:
                console.print(f"[red]Code-first search error: {e}[/red]")
        safe_pause()
    elif choice.startswith("6."):
        mode_choice = safe_select("Select Screening Mode:", choices=[
            "1. Fast Single Screener",
            "2. Rigorous Multi-Agent Review Swarm (3-Agent Consensus & Cohen's Kappa)",
            "3. Cancel / Back"
        ])
        if not mode_choice or "Cancel" in mode_choice or "Back" in mode_choice:
            return
        evaluation_mode = "swarm" if mode_choice.startswith("2.") else "single"
        try:
            from src.prisma.dspy_modules import PrismaExecutor
            PrismaExecutor(evaluation_mode=evaluation_mode).run_interactive()
        except Exception as e:
            console.print(f"[red]PRISMA pipeline error: {e}[/red]")
        safe_pause()
    elif choice.startswith("7."):
        run_script("grey_literature_miner.py", python_exe)
    elif choice.startswith("8."):
        run_script("zotero_connector.py", python_exe)
    elif choice.startswith("9."):
        run_script("interactive_dashboard.py", python_exe)
    elif choice.startswith("10."):
        query = questionary.text("Full-text query (SQLite FTS5):", style=TALOS_QUESTIONARY_STYLE).ask()
        if query and query.strip():
            try:
                from src.search.fulltext_search import FullTextSearchEngine
                FullTextSearchEngine().run(query.strip())
            except Exception as e:
                console.print(f"[red]FTS5 search error: {e}[/red]")
        safe_pause()


def analysis_visualization_menu(python_exe):
    """Advanced analysis and visualization sub-menu."""
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush()
    console.print(Panel("[bold cyan]Advanced Analysis & Visualizations[/bold cyan]\n[dim]Explore knowledge constellations, citation graphs, and bibliometrics[/dim]", style="cyan", border_style="cyan"))
    project_root = os.path.dirname(os.path.abspath(__file__))
    ap = get_active_profile_name()
    pdb = ProfileManager().get_active_db_path()
    rdb = os.path.join(project_root, 'data', 'talos_research.db')
    tdb = pdb if os.path.exists(pdb) else rdb
    choice = safe_select("Select analysis tool:", choices=[
        "1. 3D Knowledge Constellation Visualizer",
        "2. Graphify AST Knowledge Graph",
        "3. Dynamic D3 Architecture Graph",
        "4. OPTICA Scientific Visualizations",
        "5. Knowledge Path Generator",
        "6. Citation Network Analyzer",
        "7. Strategic Reading Recommender",
        "8. Author Profiler & ORCID Trajectory",
        "9. Scientometrics & Trend Analyzer",
        "10. Architecture Intelligence Report",
        "11. Baseline Report (Standard)",
        "12. Baseline Report (Academic -- 600 DPI)",
        "13. Academic Export (BibTeX & LaTeX Tables)",
        "14. PRISMA-ScR Declarative Synthesis Pipeline (Stanford DSPy Engine)",
        "15. PRISMA Scientific Quality Appraisal & 2D Quadrant Analysis (Kitchenham 2007)",
        "16. Back / Return to Main Menu"
    ])
    if not choice or "Back" in choice: return
    if choice.startswith("1."): _launch_visualizer()
    elif choice.startswith("2."): run_script("graphify_adapter.py", python_exe)
    elif choice.startswith("3."): _open_d3_architecture_graph(python_exe, project_root)
    elif choice.startswith("4."): _generate_optica_plots()
    elif choice.startswith("5."): run_script("knowledge_path_generator.py", python_exe)
    elif choice.startswith("6."): run_script("citation_analyzer.py", python_exe)
    elif choice.startswith("7."): run_script("recommender.py", python_exe)
    elif choice.startswith("8."): author_tools_menu(python_exe)
    elif choice.startswith("9."): run_script("trend_analyzer.py", python_exe, args=[tdb])
    elif choice.startswith("10."):
        if questionary.confirm("Start now? (may take 60s)", default=True, style=TALOS_QUESTIONARY_STYLE, instruction=NAV_SELECT).ask():
            run_script("architecture_intelligence_report.py", python_exe)
    elif choice.startswith("11."):
        console.print(_build_info_panel(
            "Baseline Report (Standard)",
            "Generates a standard baseline report with score distribution,\n"
            "quad-layer averages, source distribution, and embedding coverage.",
            border_style="green",
        ))
        run_script("generate_baseline_report.py", python_exe)
    elif choice.startswith("12."):
        console.print(_build_info_panel(
            "Baseline Report (Academic -- 600 DPI)",
            "Generates a publication-quality academic baseline report\n"
            "with serif fonts, 600 DPI plots, and muted color palette\n"
            "suitable for IEEE/Springer journals.",
            border_style="yellow",
        ))
        run_script("generate_baseline_report.py", python_exe, args=["--academic"])
    elif choice.startswith("13."):
        console.print(_build_info_panel(
            "Academic Export (BibTeX & LaTeX Tables)",
            "Exports the elite literature set (overall_score >= 7) as\n"
            "BibTeX (.bib) and a publication-ready LaTeX longtable (.tex)\n"
            "for Overleaf and Zotero interoperability.",
            border_style="green",
        ))
        run_script("academic_export.py", python_exe, args=["--elite", "--bib", "--tex"])
    elif choice.startswith("14."):
        console.print(_build_info_panel(
            "PRISMA-ScR Declarative Synthesis Pipeline (Stanford DSPy Engine)",
            "Runs the 4-phase PRISMA 2020 scoping review pipeline (Identification,\n"
            "Screening, Eligibility, Included) with Chain-of-Thought screening,\n"
            "live record counters, a PRISMA 2020 Mermaid flowchart, and\n"
            "publication-grade Markdown/LaTeX scoping review drafts.",
            border_style="magenta",
        ))
        mode_choice = safe_select("Select Screening Mode:", choices=[
            "1. Fast Single Screener",
            "2. Rigorous Multi-Agent Review Swarm (3-Agent Consensus & Cohen's Kappa)",
            "3. Cancel / Back"
        ])
        if not mode_choice or "Cancel" in mode_choice or "Back" in mode_choice:
            return
        evaluation_mode = "swarm" if mode_choice.startswith("2.") else "single"
        try:
            from src.prisma.dspy_modules import PrismaExecutor
            PrismaExecutor(evaluation_mode=evaluation_mode).run_interactive()
        except Exception as e:
            console.print(f"[red]PRISMA pipeline error: {e}[/red]")
        safe_pause()
    elif choice.startswith("15."):
        console.print(_build_info_panel(
            "PRISMA Scientific Quality Appraisal & 2D Quadrant Analysis (Kitchenham 2007)",
            "Runs the standardized Kitchenham et al. (2007) six-question quality\n"
            "appraisal on candidate papers (overall_score >= 7.0 by default),\n"
            "decouples semantic relevance (S_rel) from methodological rigor\n"
            "(S_qual), and maps every study onto the 2D Evidence Decision Plane\n"
            "(Elite Foundational, Idea Mine, Methodological Exemplar, Noise).\n"
            "v5.17.0: the Forensic Multi-Skill Quality Swarm dispatches four\n"
            "specialized auditors (Theory, Operational, Benchmarks, Open Science)\n"
            "over profile-compiled skills and reports inter-auditor Fleiss kappa.\n"
            "v5.17.1: --force re-appraises already-appraised candidates; "
            "otherwise the existing quadrant distribution is re-displayed.",
            border_style="cyan",
        ))
        # -- v5.17.0: Two-Tier appraisal mode selection. --
        mode_choice = questionary.select(
            "Select Appraisal Mode:",
            choices=[
                "1. Fast Single Screener (one structured prompt per paper)",
                "2. Forensic Multi-Skill Quality Swarm (4 Auditors + S_qual)",
            ],
            style=TALOS_QUESTIONARY_STYLE, instruction=NAV_TEXT,
        ).ask()
        if not mode_choice:
            return
        appraisal_mode = "swarm" if mode_choice.startswith("2.") else "single"
        min_raw = questionary.text(
            "Minimum relevance threshold (overall_score, default 7.0):",
            default="7.0",
            style=TALOS_QUESTIONARY_STYLE, instruction=NAV_TEXT,
        ).ask()
        try:
            min_score = float(min_raw) if min_raw else 7.0
        except ValueError:
            min_score = 7.0
        try:
            from src.prisma.quality_appraisal import PrismaQualityAppraiser
            from src.core.database_manager import DatabaseManager
            appraiser = PrismaQualityAppraiser(appraisal_mode=appraisal_mode)
            # -- v5.17.1: UX transparency -- detect whether any uncached
            # candidates remain so an already-appraised corpus prompts instead
            # of silently exiting. --
            db = DatabaseManager()
            total_row = db.execute_query(
                "SELECT COUNT(*) FROM papers WHERE overall_score >= ?",
                (min_score,), fetch_one=True,
            )
            total_candidates = int((total_row or (0,))[0])
            unappraised_row = db.execute_query(
                "SELECT COUNT(*) FROM papers WHERE overall_score >= ? "
                "AND quality_score IS NULL",
                (min_score,), fetch_one=True,
            )
            unappraised = int((unappraised_row or (0,))[0])
            force_reappraise = False
            if total_candidates > 0 and unappraised == 0:
                force_reappraise = bool(questionary.confirm(
                    "All candidate papers are already appraised. "
                    "Force re-appraise with selected mode?",
                    default=False,
                    style=TALOS_QUESTIONARY_STYLE,
                    instruction=NAV_TEXT,
                ).ask())
            appraiser.run(
                min_relevance=min_score,
                force_reappraise=force_reappraise,
            )
        except Exception as e:
            console.print(f"[red]Quality appraisal error: {e}[/red]")
        safe_pause()


def drl_gwo_menu(python_exe):
    """DRL agents, daemons and GWO swarm sub-menu."""
    os.system('cls' if os.name == 'nt' else 'clear')
    sys.stdout.flush()
    console.print(Panel("[bold cyan]DRL Agents, Daemons & GWO Swarm[/bold cyan]\n[dim]Autonomous foraging, reinforcement learning, and swarm optimization[/dim]", style="cyan", border_style="cyan"))
    project_root = os.path.dirname(os.path.abspath(__file__))
    choice = safe_select("Select DRL/GWO operation:", choices=[
        "1. 24/7 Autonomous Daemon (new console)",
        "2. Live DRL Agent (API Fetching)",
        "3. Configure Daemon Autostart",
        "4. Train DRL Agent (Simulated)",
        "5. Offline DRL Training (Real DB Scores)",
        "6. GWO Hyperparameter Tuner",
        "7. GWO LLM Router Reward Shaper",
        "8. GWO 3D Swarm Live Dashboard",
        "9. DRL Agent Status",
        "10. Back / Return to Main Menu"
    ])
    if not choice or "Back" in choice: return
    if choice.startswith("1."):
        _launch_daemon_in_new_console(project_root, python_exe)
    elif choice.startswith("2."):
        run_script("talos_live_agent.py", python_exe, args=["--verbose"])
    elif choice.startswith("3."):
        _configure_daemon_autostart(project_root)
    elif choice.startswith("4."):
        episodes = questionary.text(
            "Number of episodes:", default="500",
            validate=lambda t: t.isdigit() and int(t) > 0,
            style=TALOS_QUESTIONARY_STYLE, instruction=NAV_TEXT,
        ).ask()
        if episodes:
            run_script("drl_trainer.py", python_exe, args=["--episodes", episodes])
    elif choice.startswith("5."):
        episodes = questionary.text(
            "Number of episodes:", default="500",
            validate=lambda t: t.isdigit() and int(t) > 0,
            style=TALOS_QUESTIONARY_STYLE, instruction=NAV_TEXT,
        ).ask()
        iters = questionary.text(
            "Number of iterations:", default="100",
            validate=lambda t: t.isdigit() and int(t) > 0,
            style=TALOS_QUESTIONARY_STYLE, instruction=NAV_TEXT,
        ).ask()
        if episodes and iters:
            run_script("train_agent.py", python_exe, args=["--episodes", episodes, "--iters", iters])
    elif choice.startswith("6."):
        wolves = questionary.text(
            "Number of wolves:", default="12",
            validate=lambda t: t.isdigit() and int(t) > 0,
            style=TALOS_QUESTIONARY_STYLE, instruction=NAV_TEXT,
        ).ask()
        iterations = questionary.text(
            "Number of iterations:", default="30",
            validate=lambda t: t.isdigit() and int(t) > 0,
            style=TALOS_QUESTIONARY_STYLE, instruction=NAV_TEXT,
        ).ask()
        live = questionary.confirm("Enable live mode?", default=False, style=TALOS_QUESTIONARY_STYLE, instruction=NAV_CONFIRM).ask()
        if wolves and iterations:
            args = ["--wolves", wolves, "--iterations", iterations]
            if live:
                args.append("--live")
            run_script("gwo_foraging_hyperparameter_tuner.py", python_exe, args=args)
    elif choice.startswith("7."):
        wolves = questionary.text(
            "Number of wolves:", default="12",
            validate=lambda t: t.isdigit() and int(t) > 0,
            style=TALOS_QUESTIONARY_STYLE, instruction=NAV_TEXT,
        ).ask()
        iterations = questionary.text(
            "Number of iterations:", default="30",
            validate=lambda t: t.isdigit() and int(t) > 0,
            style=TALOS_QUESTIONARY_STYLE, instruction=NAV_TEXT,
        ).ask()
        if wolves and iterations:
            run_script("gwo_llm_router_reward_shaper.py", python_exe, args=["--wolves", wolves, "--iterations", iterations])
    elif choice.startswith("8."):
        _launch_gwo_dashboard(python_exe)
    elif choice.startswith("9."):
        _show_drl_status(project_root)


def main_menu():
    python_exe = sys.executable or "python"
    project_root = os.path.dirname(os.path.abspath(__file__))
    check_first_run(python_exe)
    time.sleep(1)
    global USE_LOCAL_MODEL

    # -- v5.9.2: Silent Initialization --
    # TALOS now reads TALOS_USE_LOCAL from .env directly via config/settings.py
    # and AIManager. The legacy interactive LOCAL/CLOUD prompt has been purged.
    USE_LOCAL_MODEL = os.environ.get("TALOS_USE_LOCAL", "").lower() in ("1", "true", "yes")
    # -- v5.9.15: Silent Fast Boot -- skip model verification at startup.
    # Model checks are on-demand only (Model Manager, Option 1).
    os.environ["TALOS_MODELS_VERIFIED"] = "1"

    # -- v5.9.2: Dynamic Focus Summarization --
    # If config.json lacks active_focus_summary but has queries/goal,
    # automatically generate a 6-10 word title via Fast Edge LLM.
    _maybe_generate_focus_summary()

    # -- v5.12.0: First-run Research Setup Wizard sentinel --
    # When the onboarding sentinel is absent, auto-invoke the wizard exactly
    # once before the dashboard renders. When present, this is a single file
    # existence check (sub-0.3s) so daily launches stay fast.
    sentinel_path = os.path.join(project_root, "data", ".talos_onboarded")
    if not os.path.exists(sentinel_path):
        run_script("research_setup_wizard.py", python_exe)

    while True:
        os.system('cls' if os.name == 'nt' else 'clear')

        # -- Build the Rich dashboard header --
        ap = get_active_profile_name()

        # -- Title banner --
        title_text = Text()
        title_text.append("TALOS", style="bold bright_cyan")
        title_text.append(f" v{TALOS_VERSION}", style="bold cyan")
        title_text.append(f"  |  Profile: [{ap}]", style="bold bright_cyan")

        # -- Active Research Focus line (v5.16.1) --
        focus_value = _read_active_focus()
        focus_text = Text()
        focus_text.append("Active Research Focus: ", style="dim white")
        focus_text.append(
            focus_value if focus_value else "Not configured",
            style="bold bright_green" if focus_value else "dim",
        )

        # -- v5.9.7: IEEE Computer Society WEIGD Fund badge --
        ieee_badge = Text()
        ieee_badge.append(" IEEE CS ", style="bold white on #006699")
        ieee_badge.append(" WEIGD FUND RECIPIENT 2026 ", style="bold white on #002855")

        # -- Database stats line --
        db_line = ""
        try:
            from src.core.database_manager import DatabaseManager
            db = DatabaseManager(); s = db.get_database_statistics()
            db_line = f"Papers: {s['total_papers']}  |  Elite: {s['elite_papers']}"
        except Exception:
            pass

        # -- VRAM line --
        vram_line = ""
        try:
            from src.core.hardware import detect_vram_gb
            v = detect_vram_gb()
            if v: vram_line = f"VRAM: {v:.0f} GB"
        except Exception:
            pass

        # Status panel
        status_table = _build_status_table()

        # -- Assemble the full header panel --
        header_content = Table(show_header=False, box=None, padding=(0, 0))
        header_content.add_column(justify="center")
        header_content.add_row(title_text)
        header_content.add_row(focus_text)
        header_content.add_row(ieee_badge)
        header_content.add_row("")
        if db_line or vram_line:
            stats_parts = []
            if db_line: stats_parts.append(db_line)
            if vram_line: stats_parts.append(vram_line)
            header_content.add_row(Text(" | ".join(stats_parts), style="dim white"))
        header_content.add_row("")
        header_content.add_row(status_table)

        header_panel = Panel(
            Align.center(header_content),
            border_style="#006699",
            box=box.ROUNDED,
            padding=(1, 2),
        )

        console.print(header_panel)

        # -- v5.10.15: Unified 6-group hierarchical menu (100% coverage) --
        choice = safe_select("Select operation:", choices=[
            questionary.Separator("  [ 1. CONFIGURATION & PROFILES ]"),
            "  1. Configuration & Profiles",
            questionary.Separator("  [ 2. RESEARCH SEARCH & INGESTION ]"),
            "  2. Research Search & Ingestion",
            questionary.Separator("  [ 3. ADVANCED ANALYSIS & VISUALIZATIONS ]"),
            "  3. Advanced Analysis & Visualizations",
            questionary.Separator("  [ 4. DRL AGENTS, DAEMONS & GWO SWARM ]"),
            "  4. DRL Agents, Daemons & GWO Swarm",
            questionary.Separator("  [ 5. DATABASE MAINTENANCE & DATA TOOLS ]"),
            "  5. Database Maintenance & Data Tools",
            questionary.Separator("  [ 6. SYSTEM HEALTH, DIAGNOSTICS & CI/CD ]"),
            "  6. System Health, Diagnostics & CI/CD",
            questionary.Separator(),
            "  7. Help & Command Reference Manual",
            "  8. Exit",
        ])
        if choice is None or "Exit" in choice: break
        fm = "Press Enter to return..."

        # -- Route to the selected sub-menu (v5.10.15: unified hierarchy) --
        if " 1." in choice:
            profile_settings_menu(python_exe)
        elif " 2." in choice:
            search_ingestion_menu(python_exe)
        elif " 3." in choice:
            analysis_visualization_menu(python_exe)
        elif " 4." in choice:
            drl_gwo_menu(python_exe)
        elif " 5." in choice:
            database_data_menu(python_exe)
        elif " 6." in choice:
            system_health_menu(python_exe)
        elif " 7." in choice:
            from src.utils.help_system import render_help_manual
            render_help_manual(interactive=True)

        if choice and "Exit" not in choice:
            safe_pause(fm)

    # -- Exit sequence --
    console.print("\n[dim]TALOS Command Center Closing...[/dim]\n")


# ---------------------------------------------------------------------------
# -- v5.12.1: CLI Fast-Dispatch Engine --
# ---------------------------------------------------------------------------

def _cli_help_table():
    """Render the four-panel TALOS command reference manual.

    Delegates to ``src.utils.help_system.render_help_manual(interactive=False)``
    so the CLI --help fast-dispatch path and the TUI Option 7 share a single
    canonical manual definition.

    Returns:
        A rich.console.Group renderable ready for console.print().
    """
    from src.utils.help_system import render_help_manual
    return render_help_manual(interactive=False)


def _parse_strategy_flag(argv):
    """Detect the --strategy / --mode flag and its optional mode argument.

    Args:
        argv (list[str]): Command-line arguments following the script name.

    Returns:
        tuple[bool, str or None]: (flag_present, target_strategy_or_None).
    """
    for i, arg in enumerate(argv):
        if arg in ("--strategy", "--mode"):
            target = None
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                target = argv[i + 1]
            return True, target
    return False, None


def _flag_value(argv, flag):
    """Return the argument following a flag, or None when absent.

    Args:
        argv (list[str]): Command-line arguments following the script name.
        flag (str): The flag whose following argument is requested.

    Returns:
        str or None: The value after the flag, or None.
    """
    for i, arg in enumerate(argv):
        if arg == flag and i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            return argv[i + 1]
    return None


def _render_harvest_summary(summary):
    """Render a Rich summary table for the Open Access PDF harvest result.

    Args:
        summary (dict): Output of ``AcademicPDFHarvester.harvest_candidates``.
    """
    from rich.table import Table
    from rich import box
    table = Table(
        title="Open Access PDF Harvest Summary",
        box=box.ROUNDED,
        border_style="bright_cyan",
        header_style="bold bright_cyan",
        expand=False,
    )
    table.add_column("Metric", style="bold cyan", no_wrap=True)
    table.add_column("Value", style="bold white", no_wrap=True)
    table.add_row("Candidates", str(summary.get("candidates", 0)))
    table.add_row("Downloaded", str(summary.get("downloaded", 0)))
    table.add_row("Unavailable", str(summary.get("unavailable", 0)))
    table.add_row("Failed", str(summary.get("failed", 0)))
    console.print(table)
    for result in summary.get("results", []):
        status = result.get("status", "")
        color = "green" if status == "DOWNLOADED" else ("yellow" if status == "UNAVAILABLE" else "red")
        source = f" [{result.get('source')}]" if result.get("source") else ""
        console.print(f"  [{color}]{status}[/{color}] (id={result.get('id')}) {str(result.get('title') or '')[:70]}{source}")


def _open_local_pdf(paper_id):
    """Open a downloaded local PDF in the default system viewer.

    Args:
        paper_id (str): The database id of the paper whose PDF should open.
    """
    if not paper_id:
        console.print("[yellow]Usage: python talos.py --open-pdf <paper_id>[/yellow]")
        return
    from src.core.database_manager import DatabaseManager
    db = DatabaseManager()
    row = db.execute_query(
        "SELECT local_pdf_path, title FROM papers WHERE id = ?",
        (paper_id,),
        fetch_one=True,
    )
    if not row:
        console.print(f"[red]Paper {paper_id} not found.[/red]")
        return
    path, title = row[0], row[1]
    if not path or not os.path.exists(path):
        console.print(f"[yellow]No downloaded PDF for paper {paper_id} "
                      f"({title or 'untitled'}). Run --download-pdfs first.[/yellow]")
        return
    try:
        if os.name == "nt":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
        console.print(f"[green]Opened local PDF: {path}[/green]")
    except OSError as exc:
        console.print(f"[red]Failed to open PDF: {exc}[/red]")


def _handle_cli_flags(argv):
    """Dispatch CLI fast-path flags and return True when one was handled.

    Args:
        argv (list[str]): Command-line arguments following the script name.

    Returns:
        bool: True when a recognized flag was dispatched (the caller exits 0),
        False when the interactive main menu should launch instead.
    """
    python_exe = sys.executable or "python"
    if "--help" in argv or "-h" in argv:
        console.print(_cli_help_table())
        return True
    if "--wizard" in argv:
        run_script("research_setup_wizard.py", python_exe)
        return True
    if "--daily" in argv:
        run_script("daily_search.py", python_exe)
        return True
    if "--stats" in argv:
        run_script("db_stats.py", python_exe)
        return True
    # -- v5.13.1: System Diagnostics Analyzer (--diagnostics / --doctor / -d). --
    if any(flag in argv for flag in ("--diagnostics", "--doctor", "-d")):
        from src.utils.system_diagnostics import SystemDiagnosticsEngine
        SystemDiagnosticsEngine().run_and_render()
        return True
    # -- v5.14.1: PRISMA-ScR Declarative Synthesis Pipeline (--prisma [--swarm]). --
    if "--prisma" in argv:
        from src.prisma.dspy_modules import PrismaExecutor
        mode = "swarm" if "--swarm" in argv else "single"
        PrismaExecutor(evaluation_mode=mode).run_interactive()
        return True
    # -- v5.14.2: BibTeX Scientific Exporter (--export-bib [min_score]). --
    if "--export-bib" in argv:
        from src.utils.bibtex_exporter import BibTeXExporter
        threshold = 7.0
        for i, arg in enumerate(argv):
            if arg == "--export-bib" and i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                try:
                    threshold = float(argv[i + 1])
                except ValueError:
                    threshold = 7.0
                break
        BibTeXExporter().export_and_render(min_score=threshold)
        return True
    # -- v5.17.0: Profile Skill Compiler (--compile-skills [--force]). --
    if "--compile-skills" in argv:
        from src.prisma.quality_swarm import SkillCompiler
        profile = _flag_value(argv, "--profile")
        path = SkillCompiler().compile_profile_skills(
            profile_name=profile,
            force_recompile="--force" in argv,
        )
        console.print(f"[green][OK] Profile auditor skills compiled under: {path}[/green]")
        return True
    # -- v5.16.0/v5.17.0/v5.17.1: PRISMA Quality Appraisal
    # (--appraise-quality [--min-score] [--swarm] [--force]). --
    if "--appraise-quality" in argv:
        from src.prisma.quality_appraisal import PrismaQualityAppraiser
        min_score = 7.0
        raw = _flag_value(argv, "--min-score")
        if raw:
            try:
                min_score = float(raw)
            except ValueError:
                min_score = 7.0
        mode = "swarm" if "--swarm" in argv else "single"
        PrismaQualityAppraiser(appraisal_mode=mode).run(
            min_relevance=min_score,
            force_reappraise="--force" in argv,
        )
        return True
    # -- v5.16.2 / v5.19.0: Hardware-Aware Model Advisor + 4-Role SOTA Matcher
    # -- (--hardware-advisor / --recommend-models / --apply-models). --
    if any(flag in argv for flag in ("--hardware-advisor", "--recommend-models")):
        from src.core.hardware_advisor import HardwareModelAdvisor
        advisor = HardwareModelAdvisor()
        advisor.render_recommendations()
        advisor.render_role_matrix()
        return True
    if "--apply-models" in argv:
        from src.core.hardware_advisor import HardwareModelAdvisor
        HardwareModelAdvisor().apply_recommended_models()
        return True
    # -- v5.20.0: SOTA LLM discovery (--discover-llms [--offline]). --
    if "--discover-llms" in argv:
        from src.core.model_benchmark_client import run_discover_llms
        run_discover_llms(online="--offline" not in argv)
        return True
    # -- v5.21.0: Autonomous Model Scavenger
    # -- (--scavenge-models [--days N] [--report-only]). --
    if "--scavenge-models" in argv:
        days = 30
        raw = _flag_value(argv, "--days")
        if raw:
            try:
                days = int(raw)
            except ValueError:
                days = 30
        _run_scavenge_models(days=days, report_only="--report-only" in argv)
        return True
    # -- v5.15.0: Universal Search Hub fast-dispatch flags. --
    if "--snowball" in argv:
        seed = _flag_value(argv, "--snowball")
        if not seed:
            console.print("[yellow]Usage: python talos.py --snowball <seed_doi|title|db_id>[/yellow]")
            return True
        from src.search.citation_snowballing import CitationSnowballEngine
        CitationSnowballEngine().run(seed.strip())
        return True
    if "--vector-search" in argv:
        query = _flag_value(argv, "--vector-search")
        if not query:
            console.print("[yellow]Usage: python talos.py --vector-search <query>[/yellow]")
            return True
        from src.search.neural_vector_search import NeuralVectorSearchEngine
        NeuralVectorSearchEngine().run(query.strip())
        return True
    if "--code-search" in argv:
        query = _flag_value(argv, "--code-search") or "reinforcement learning robotics"
        from src.search.code_first_search import CodeFirstSearchEngine
        CodeFirstSearchEngine().run(query.strip())
        return True
    # -- v5.12.2: AI execution strategy switcher (--strategy / --mode). --
    flag_present, strategy_target = _parse_strategy_flag(argv)
    if flag_present:
        from src.utils.ai_strategy_selector import select_ai_execution_strategy
        if not select_ai_execution_strategy(strategy_target):
            sys.exit(1)
        return True
    # -- v5.18.0: Ethical Academic PDF Harvester (--download-pdfs [--min-score]). -- #
    if "--download-pdfs" in argv:
        from src.ingestion.pdf_harvester.harvester import AcademicPDFHarvester
        min_score = 7.0
        raw = _flag_value(argv, "--min-score")
        if raw:
            try:
                min_score = float(raw)
            except ValueError:
                min_score = 7.0
        summary = AcademicPDFHarvester().harvest_candidates(min_relevance=min_score)
        _render_harvest_summary(summary)
        return True
    # -- v5.18.0: SQLite FTS5 full-text search (--fts "<query>"). -- #
    if "--fts" in argv:
        query = _flag_value(argv, "--fts")
        if not query:
            console.print("[yellow]Usage: python talos.py --fts \"<query>\"[/yellow]")
            return True
        from src.search.fulltext_search import FullTextSearchEngine
        FullTextSearchEngine().run(query.strip())
        return True
    # -- v5.18.0: Open a downloaded local PDF (--open-pdf [paper_id]). -- #
    if "--open-pdf" in argv:
        _open_local_pdf(_flag_value(argv, "--open-pdf"))
        return True
    # -- v5.18.2: 1-click Desktop Shortcut provisioner (--create-shortcut). -- #
    if "--create-shortcut" in argv:
        from src.utils.desktop_shortcut import create_desktop_shortcut
        if not create_desktop_shortcut():
            sys.exit(1)
        return True
    return False


if __name__ == "__main__":
    # -- v5.12.1: CLI fast-dispatch flags (--wizard/--daily/--stats/--help) --
    # -- run headless and exit cleanly; no flags -> interactive main menu. --
    try:
        if _handle_cli_flags(sys.argv[1:]):
            sys.exit(0)
        main_menu()
    except KeyboardInterrupt:
        console.print("\n\n[dim]TALOS Closing...[/dim]\n")
        sys.exit(0)
