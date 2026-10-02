# Changelog - Project TALOS

All notable changes to the TALOS project will be documented in this file. The project adheres to [Semantic Versioning](https://semver.org/).

## [v5.18.0] - 2026-10-02 -- Ethical Academic PDF Harvester, Smart Section Slicing & SQLite FTS5 Engine

### Added

- **Ethical Academic PDF Harvester** (`src/ingestion/pdf_harvester/`): a modular, air-gapped subsystem that resolves and downloads legal Open Access / preprint full-text PDFs into the gitignored `data/fulltext_cache/` directory. The package comprises `resolvers.py` (the cascading resolver), `harvester.py` (the six-layer fault-tolerant download pipeline), and `section_extractor.py` (local text extraction and smart section slicing).

- **Cascading Open Access resolver** (`resolvers.py:resolve_oa_url`): an ordered chain of thirteen legal resolvers spanning (1) direct preprint repositories -- Cornell arXiv, IEEE TechRxiv (`10.36227/techrxiv`), HAL/Inria, NASA NTRS; (2) publisher OA APIs -- Elsevier ScienceDirect OA (`ELSEVIER_API_KEY`), PLOS, PubMed Central; and (3) meta-resolvers -- Unpaywall, OpenAlex `best_oa_location`, Semantic Scholar `openAccessPdf`, CORE, Crossref OA, and SSRN. Each resolver returns a `(pdf_url, resolver_source)` tuple and fails soft so the cascade never aborts.

- **Six-layer download pipeline** (`harvester.py:AcademicPDFHarvester`): `%PDF-` magic-bytes validation (first five bytes), atomic temporary-file writing (`tmp_<id>.pdf` -> `<id>.pdf` via `os.replace`), SHA-256 integrity hashing, a 20 second timeout, a 50 MB size cap, and a 1.5 second polite inter-request delay under the academic User-Agent `TALOS-Academic-Research-Bot/5.18.0 (University of the Peloponnese; mailto:c.smarlamakis@uop.gr)`.

- **`harvest_candidates(min_relevance=7.0, active_profile=None)`**: queries the active profile SQLite database for candidates with `overall_score >= min_relevance`, downloads sequentially, and persists `local_pdf_path`, `pdf_sha256`, and `pdf_status` ('DOWNLOADED' | 'UNAVAILABLE' | 'FAILED').

- **Smart section slicing** (`section_extractor.py:PDFSectionExtractor`): local `pypdf` extraction (with a printable-byte fallback parser) caches four evidence windows under `data/fulltext_cache/<id>/` -- `methodology.txt`, `experiments.txt`, `code_availability.txt`, and `limitations.txt` -- for the Tier-2 Quality Swarm.

- **SQLite FTS5 full-text engine** (`src/search/fulltext_search.py:FullTextSearchEngine`): creates the `papers_fts(paper_id, title, fulltext_content)` virtual table, indexes cached bodies incrementally, and executes sub-millisecond FTS5 `MATCH` queries with BM25 ranking and `snippet(papers_fts, 2, '<b>', '</b>', '...', 15)` highlighting. Results render in a styled Rich Table (`box.ROUNDED`, title "SQLite FTS5 Full-Text Search Results") with matched sentences and best-effort page estimates.

- **CLI & TUI integration** (`talos.py`): `--download-pdfs [--min-score 7.0]`, `--fts "<query>"`, and `--open-pdf [paper_id]` (opens the local PDF in the default system viewer); the Universal Search Hub (Group 2) gains "SQLite FTS5 Full-Text Search" and the Database & Data menu (Group 5) gains "Harvest Open Access Full-Text PDFs (12 Cascading Sources)".

- **Rule 10 private dossier** (`docs/internal/academic/07_ETHICAL_OPEN_ACCESS_PDF_HARVESTING_FTS.md`): a seven-section confidential academic dossier documenting the EU Directive 2019/790 TDM framework, magic-bytes/SHA-256/BM25 mathematics, plain-language explanation, code traceability matrix, engineering adaptations, and pre-compiled PhD/publication excerpts.

### Changed

- **SmartSectionSlicer cached-section integration** (`src/prisma/quality_swarm.py`): the Tier-2 slicer now reads real cached PDF section text whenever a local PDF has been harvested (a `full_text`-absent fallback to `data/fulltext_cache/<id>/*.txt`), preserving the existing title-plus-abstract fallback and all prior tests.

- **Database schema** (`src/core/database_manager.py`): added `papers.local_pdf_path`, `papers.pdf_sha256`, and `papers.pdf_status` columns (idempotent migration).

- **Dependency map verifier** (`src/utils/verify_dependency_map.py`): `pypdf` added to the `EXTERNAL_PACKAGES` whitelist.

- **Version strings synchronized to 5.18.0** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata/lifespan/description, `talos.py` docstring/banner, `run_talos.bat`, `run_talos.sh`, `tests/test_multi_tier.py` version assertion), `docker-compose.yml` (`talos:5.18.0`), `CITATION.cff` (version 5.18.0, date-released 2026-10-02), `config.template.json`, tray/visualizer/wizard/strategy/diagnostics/bibtex/help metadata, all `src/prisma/` and `src/search/` docstrings, and all 19 canonical documentation files (dated 2026-10-02).

- **ROADMAP.md**: current version advanced to v5.18.0 (Complete, 2026-10-02); CORTEX & n8n orchestration advanced to v5.19.0.

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_pdf_harvester.py -q` (8 passed -- mocked `%PDF-` / atomic write / SHA-256); `pytest tests/test_fulltext_search.py -q` (4 passed -- FTS5 virtual table + snippet MATCH); `pytest tests/test_quality_swarm.py tests/test_quality_appraisal.py -q` (34 passed -- backward compatible); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.18.0); `python talos.py --help` documents `--download-pdfs`, `--fts`, `--open-pdf`; dossier 07 conforms to the 7-section standard with 0 U+FFFD glyphs; `python src/utils/verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.17.1] - 2026-10-02 -- PRISMA Quality Appraisal UX Transparency & Force Re-Appraisal Engine

### Added

- **Force re-appraisal engine** (`src/prisma/quality_appraisal.py`): `appraise_candidates_batch()` gains a backward-compatible `force_reappraise: bool = False` parameter. When `True`, the batch selects every candidate paper matching `overall_score >= min_relevance` (ignoring whether `quality_score` is already populated), prints a yellow force-re-appraisal notice, and overwrites `quality_score`, `quality_rubric_json`, and `evidence_quadrant` in SQLite WAL.

- **Idempotent quadrant-distribution fallback**: when `force_reappraise=False` and every candidate already carries a `quality_score`, the appraiser no longer exits silently. It renders an informative Rich panel ("All {n} candidate papers ... have already been appraised. Displaying existing 2D Evidence Quadrant distribution."), re-projects the persisted `evidence_quadrant` values onto the 2D Evidence Decision Plane, and returns without re-computing.

### Changed

- **CLI & TUI integration** (`talos.py`): `--appraise-quality` now accepts `--force` (`python talos.py --appraise-quality [--min-score 7.0] [--swarm] [--force]`); TUI Group 3 Option 15 detects an already-appraised corpus and prompts "All candidate papers are already appraised. Force re-appraise with selected mode?" (default `No`), falling back to a clean quadrant table when declined.

- **Dual-Surface Help** (`src/utils/help_system.py`, `templates/help_manual.html`): Panel 1 and Card 6 now document `--appraise-quality [--swarm] [--force]` with a dedicated force re-appraisal command and a v5.17.1 UX-transparency explanation.

- **Version strings synchronized to 5.17.1** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata/lifespan/description, `talos.py` docstring/banner, `run_talos.bat`, `run_talos.sh`, `tests/test_multi_tier.py` version assertion), `docker-compose.yml` (`talos:5.17.1`), `CITATION.cff` (version 5.17.1, date-released 2026-10-02), `config.template.json`, tray/visualizer/wizard/strategy/diagnostics/bibtex/help metadata, all `src/prisma/` and `src/search/` docstrings, and all 19 canonical documentation files (dated 2026-10-02).

- **ROADMAP.md**: current version advanced to v5.17.1 (Complete, 2026-10-02); CORTEX & n8n orchestration retained at v5.18.0.

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_quality_appraisal.py -q` (17 passed -- backward compatible); `pytest tests/test_quality_swarm.py -q` (17 passed); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.17.1); `python talos.py --help` documents `--appraise-quality [--swarm] [--force]`; `python src/utils/verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.17.0] - 2026-10-02 -- Two-Tier Hierarchical Swarm Architecture & Forensic Quality Engine

### Added

- **Two-Tier Hierarchical Swarm Architecture** (`src/prisma/quality_swarm.py`, 1,261 lines): formal decoupling of Tier-1 Thematic Screening (`swarm_evaluators.py`: three reviewer personas emitting INCLUDE/EXCLUDE/UNCERTAIN votes for study selection) from Tier-2 Forensic Quality Auditing (new: four specialized skill auditors scoring the Kitchenham 2007 rubric on admitted candidates). Tier-1 answers "is this study on-topic?"; Tier-2 answers "is this study methodologically trustworthy?".

- **Four specialized forensic skill auditors**: `TheoryAuditor` (Q1: formal problem formulation, hypotheses, scope), `OperationalAuditor` (Q2: environmental realism, physical disturbances, communication latency, operational rules/safety bounds), `BenchmarkAuditor` (Q3-Q4: 2-3 modern SOTA baselines under identical conditions, >= 5 random seeds, confidence intervals, p-values, ablations), and `OpenScienceAuditor` (Q5-Q6: public code repository, open benchmark simulator/dataset, explicit limitations and failure boundaries). Each auditor emits typed Pydantic-v2 results with ternary scores snapped onto the strict {0.0, 0.5, 1.0} grid via the shared `_normalize_ternary` invariant, plus a named forensic critique (`theory_critique`, `operational_critique`, `benchmark_critique`, `openscience_critique`).

- **Domain-Agnostic Core Templates & Profile-Compiled Skills pattern** (`src/prisma/skills/templates/` + `SkillCompiler`): four canonical invariant templates (`theory_auditor.template.md`, `empirical_auditor.template.md`, `openscience_auditor.template.md`, `operational_auditor.template.md`) containing zero domain-specific criteria -- only `{{RESEARCH_DOMAIN}}` and `{{DOMAIN_CONSTRAINTS}}` placeholders. `SkillCompiler.compile_profile_skills(profile_name, force_recompile)` injects the active profile's `research_topic`, `inclusion_criteria`, and `exclusion_criteria`, optionally refines each skill with the hardware-advised heavy model (`HardwareModelAdvisor.get_recommendations()`: `qwen2.5:14b` locally, `deepseek-reasoner` / `gemini-2.5-flash` on the Cloud Mesh, guarded by a minimum-length and schema-retention check), and writes the compiled `.md` files into `_profiles/<profile>/skills/`. A zero-cost fast path returns immediately when compiled skills already exist; deterministic placeholder injection is the guaranteed air-gapped lower bound.

- **SmartSectionSlicer**: heading-regex extraction of canonical paper sections (Code/Data Availability, Methodology, Experiments/Results, Discussion/Limitations) with per-auditor target maps (OpenScience receives Code Availability + Limitations; Benchmark receives Experiments + Methodology; etc.), word-capped to ~300-500 words per auditor, with a title-plus-abstract fallback when no full text is available -- minimizing the per-auditor token footprint while quadrupling evidential focus.

- **KitchenhamQualitySynthesizer**: dispatches the four auditors concurrently via `ThreadPoolExecutor` bounded by `QUALITY_SWARM_SEMAPHORE = threading.Semaphore(2)` locally (Constitution III, `llama3.1:8b` 2GB headroom) or `max_workers=4` on `cloud_first`/`strict_cloud`; auto-compiles missing profile skills; merges the six ternary scores into the canonical `KitchenhamRubric` (invariant `S_qual = (10/6) * sum(Q_i)`); computes the inter-auditor Fleiss agreement `kappa_qual` over banded auditor ratings (LOW/MID/HIGH at 0.375/0.75 thresholds, reusing `swarm_evaluators.calculate_cohens_kappa`); maps the 2D Decision Quadrant (ELITE_FOUNDATIONAL, IDEA_MINE, METHODOLOGICAL_EXEMPLAR, METHODOLOGICAL_NOISE); and synthesizes the unified forensic audit narrative in a `SwarmQualityVerdict` dataclass.

- **Appraiser swarm mode** (`src/prisma/quality_appraisal.py`): `PrismaQualityAppraiser(appraisal_mode='single'|'swarm')`; `QualityAppraisalResult` gains backward-compatible fields `appraisal_mode` (default `'single'`), `swarm_kappa`, `auditor_critiques`. In swarm mode the batch auto-compiles profile skills first, delegates each paper to `KitchenhamQualitySynthesizer`, and persists the extended payload (rubric + mode + kappa + critiques) into the existing `quality_score` / `quality_rubric_json` / `evidence_quadrant` SQLite columns -- zero schema changes. The Rich quadrant summary reports the mean inter-auditor kappa in swarm mode.

- **CLI & TUI integration** (`talos.py`, `src/utils/help_system.py`, `templates/help_manual.html`): new fast-dispatch flags `--appraise-quality [--min-score 7.0] [--swarm]` and `--compile-skills [--force] [--profile name]`; TUI Group 3 Option 15 gains the interactive "Select Appraisal Mode: 1. Fast Single Screener | 2. Forensic Multi-Skill Quality Swarm (4 Auditors + S_qual)" prompt; Panel 1 of the help manual and the web manual Card 6 document the Two-Tier architecture with click-to-copy commands.

- **Rule 10 private academic dossier 06** (`docs/internal/academic/06_TWO_TIER_HIERARCHICAL_SWARM_QUALITY.md`): seven-section confidential dossier with metadata and BibTeX (Du et al. ICML 2024 multi-agent debate; Chan et al. ICLR 2024 ChatEval; Kitchenham & Charters 2007 EBSE-2007-01; Page et al. BMJ 2021 PRISMA 2020), the formal two-tier/task-decomposition/Fleiss-kappa mathematical framework with an attention-dilution bound theorem, an ELI5 section, a 1:1 code traceability matrix, engineering adaptations, version lineage, and pre-compiled PhD Chapter 2/3 and HOU ICBE 2026 excerpts.

- **Hermetic test suite** (`tests/test_quality_swarm.py`, 17 tests): ternary audit-model coercion, slicer section targeting and word caps, compiler injection/idempotency/force-recompile gates, end-to-end swarm consensus on mocked backends (Q1-Q6, S_qual = 8.3333, quadrant, kappa, narrative), deterministic no-backend degradation, worker-budget resolution, and appraiser swarm-mode integration.

### Changed

- **Version strings synchronized to 5.17.0** across the 6 core code files (`config/settings.py` TALOS_VERSION, `src/api/main_api.py` FastAPI metadata/lifespan/description, `talos.py` docstring/banner, `run_talos.bat`, `run_talos.sh`, `tests/test_multi_tier.py` version assertion), `docker-compose.yml` (`talos:5.17.0`), `CITATION.cff` (version 5.17.0, date-released 2026-10-02), `config.template.json`, tray/visualizer/wizard/strategy/diagnostics/bibtex/help metadata, all `src/prisma/` and `src/search/` docstrings, and all 19 canonical documentation files (dated 2026-10-02).

- **ROADMAP.md**: current version advanced to v5.17.0 (Complete, 2026-10-02); CORTEX & n8n orchestration re-scoped to v5.18.0.

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_quality_swarm.py -q` (17 passed, hermetic); `pytest tests/test_quality_appraisal.py -q` (17 passed -- full backward compatibility of the single mode); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.17.0); `python talos.py --compile-skills` compiles `_profiles/uav_mission_planning/skills/*.md` with the UAV/DRL/ST-GAT domain injected; `python talos.py --help` documents `--appraise-quality [--swarm]` and `--compile-skills`; dossier 06 conforms to the 7-section standard with 0 U+FFFD glyphs; `python src/utils/verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.16.2] - 2026-10-02 -- Pluggable Provider Registry & Hardware-Aware Model Advisor

### Added

- **Pluggable Provider Registry** (`src/core/provider_registry.py`): a modular adapter catalogue implementing the Open-Closed Principle (open for extension, closed for modification). `ProviderDescriptor` (a dataclass value object) captures the canonical `name`, `base_url`, optional `api_key_env`, `default_model`, latency `category` (`local_gpu` / `local_cpu` / `cloud_reasoning` / `cloud_fast` / `cloud_heavy`), an `is_openai_compatible` flag, and a dynamically evaluated `is_active` flag. `ProviderRegistry` pre-registers the local Ollama runtime plus nine cloud providers (NVIDIA NIM, DeepSeek, Gemini, Groq, Cerebras, Mistral, Hugging Face, OpenRouter, Anthropic) and exposes a stable four-method API (`register`, `get`, `list_all`, `list_active`). Adding any future provider (a custom NVIDIA NIM instance, Anthropic Claude, or a custom edge server) is now a pure data operation -- no core evaluation loop is ever edited. `is_active` is re-evaluated truthfully at query time: cloud providers are active when their key is present in the environment, while local Ollama is active when its port answers a lightweight TCP probe.
- **Hardware-Aware Model Advisor** (`src/core/hardware_advisor.py`): `HardwareModelAdvisor` reuses the existing VRAM telemetry (`detect_vram_gb()` via nvidia-smi) and augments it with Torch CUDA introspection (device name and `total_memory`), psutil system RAM, and a battery-based laptop-CPU heuristic -- all guarded so CPU-only hosts degrade gracefully. `get_hardware_profile()` returns `{has_cuda, device_name, total_vram_gb, system_ram_gb, is_laptop_cpu}`. `calculate_vram_budget()` applies a piecewise 4-bit-quantization formula (`VRAM >= 11.0 GB -> 14B`, `5.5 <= VRAM < 11.0 -> 8B`, `VRAM < 5.5 / CPU -> 3B`) and `get_recommendations()` returns a role-based stack (`screening_local`, `reasoning_local`, `reasoning_cloud`, `fast_cloud`) sized to the detected budget.
- **SOTA online radar** (`scan_sota_models(timeout=1.5)`): a lightweight, non-blocking scan over a static verified radar plus live Ollama tags and an OpenRouter probe, surfacing newer releases (Qwen 3/4, Llama 4) that fit within the detected budget. When offline it degrades to the static verified list and never raises.
- **Unit tests** (`tests/test_provider_registry.py`, `tests/test_hardware_advisor.py`): 18 hermetic tests covering registry registration/retrieval, dynamic `is_active` evaluation, the VRAM budget arithmetic, role-based recommendations, and the SOTA radar budget filter.

### Changed

- **Zero-regression AIManager decoupling** (`src/core/ai_manager.py`): the manager now instantiates and consumes `ProviderRegistry` through two additive, read-only helpers -- `list_active_providers()` and `get_provider_descriptor(name)` -- layered on top of the unchanged `OPENAI_COMPATIBLE_REGISTRY`, the existing SDK initialization loops, and the existing circuit-breaker state. All public method contracts (`evaluate_paper_json`, `analyze_generic_text`, `batch_evaluate_papers`, `_resolve_strategies`) remain 100% backward compatible.
- **CLI & TUI integration** (`talos.py`, `src/utils/help_system.py`): `_handle_cli_flags()` dispatches `--hardware-advisor` / `--recommend-models` (renders the Hardware Profile, Parameter Budget, Recommended Stack, and SOTA radar as styled Rich tables, exit 0); the Configuration & Profiles menu gains Option 8 "Hardware-Aware Model Advisor (VRAM Budget & SOTA)" (later options renumbered); Panel 1 of the four-panel help manual documents the new flag.
- **Version strings synchronized to 5.16.2** across the 6 core code files, `docker-compose.yml` (`talos:5.16.2`), `CITATION.cff` (5.16.2, 2026-10-02), tray/visualizer/wizard/strategy/diagnostics metadata, `src/prisma/` and `src/search/` docstrings, and all 19 canonical documentation files (dated 2026-10-02).

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_provider_registry.py tests/test_hardware_advisor.py -q` (18 passed, hermetic); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.16.2); `python talos.py --recommend-models` renders the Rich advisor table on an RTX 4070 (12 GB -> 14B budget) and exits 0; `verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.16.1] - 2026-10-02 -- Unified Profile Architecture & Workspace Synchronization Engine

### Added

- **Unified Profile Manager Single Source of Truth** (`src/core/profile_manager.py`): the legacy module-level path logic is replaced by a canonical `ProfileManager` class anchored strictly to the repository-root `_profiles/` directory via `Path(__file__).resolve().parents[2]`. The class exposes the complete profile state machine -- `get_profiles_dir()`, `get_active_profile_name()`, `set_active_profile(name)` (validate, scaffold, write the active marker, and synchronize config), `list_profiles()`, `create_profile(name, seed_config)`, `get_active_db_path()`, and `get_active_config_path()` -- eliminating every relative-path resolution bug that previously produced phantom databases and stale active-profile markers. A module-level singleton plus thin backward-compatible aliases (`get_active_profile_name`, `set_active_profile_name`, `save_current_state_to_profile`, `load_profile_to_root`) preserve all existing callers.
- **DatabaseManager delegation** (`src/core/database_manager.py`): `get_active_profile_db_path()` now delegates directly to `ProfileManager.get_active_db_path()` so the daemon, the offline DRL environment, the OPTICA bridge, and the daily digest share one canonical path resolver.
- **Research wizard & TUI profile helpers** (`src/utils/research_setup_wizard.py`, `talos.py`): every profile-path helper (`_profiles_dir`, `_active_profile_file`, `_list_profiles`, `_get_active_profile`, `_set_active_profile`, `_validate_profile_name`) now consumes `ProfileManager` directly, and the `analysis_visualization_menu()` database path resolves through `ProfileManager().get_active_db_path()`.

### Changed

- **Canonical PhD workspace migration**: the populated research corpus (5,472 papers, 114 elite papers with `overall_score > 7`, 325 quality-appraised papers) is consolidated into the canonical `uav_mission_planning` profile under `_profiles/uav_mission_planning/`, and `_profiles/active_profile.txt` now points to it. Root `config.json` and the profile config lock in `research_topic: "Drone Mission Planning (Task Allocation-Path Planning) with DRL and ST-GAT"`, which the TUI banner renders as `Profile: [uav_mission_planning]` / `Active Research Focus: ...`.
- **Local AI runtime unification (retire phantom port 11435)**: `config/settings.py` introduces `FAST_EDGE_URL` defaulting to `http://127.0.0.1:11434/v1` (with `FAST_EDGE_BASE_URL` retained as a backward-compatible alias), `src/core/ai_manager.py` routes the fast edge tier directly to the verified Ollama runtime on 11434, and `src/utils/system_diagnostics.py` / `src/utils/help_system.py` / `templates/help_manual.html` document port 11434 as the Universal Local AI Runtime (GPU/CPU). All phantom 11435 warning paths and port probes are removed.
- **TUI banner** (`talos.py`): the dashboard header now renders both the active profile and the active research focus line.

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.16.1); `ProfileManager` get/set/switch/list smoke test; `python talos.py --diagnostics` renders cleanly without 11435; `verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.16.0] - 2026-10-01 -- PRISMA Quality Appraisal & Dual-Axis Scientific Rigor Engine (Kitchenham 2007 Standard)

### Added

- **PRISMA Quality Appraisal engine** (`src/prisma/quality_appraisal.py`): a standardized six-question, three-point categorical quality rubric formalizing the Kitchenham et al. (2007) guidelines for systematic literature reviews. The typed Pydantic-v2 schema (`KitchenhamRubric`) enforces each question onto the strict {0.0, 0.5, 1.0} grid (aims clarity, context realism, baseline rigor, statistical validity, open reproducibility, limitations and negative results) with a permissive ternary normalizer (`_normalize_ternary`) that snaps drifted local-LLM outputs back onto the grid. `QualityAppraisalResult` binds the normalized methodological-quality score, the rubric, and the evidence quadrant.

- **Formal decoupling of Semantic Relevance ($S_{rel}$) from Methodological Quality ($S_{qual}$)**: the quality score is computed strictly as `S_qual = (sum(Q_i) / 6.0) * 10.0`, independently of the four-layer `overall_score`. `map_evidence_quadrant()` projects every study onto a 2D Evidence Decision Plane with orthogonal thresholds ($\tau_{rel}=7.0$, $\tau_{qual}=7.5$), yielding four quadrants: `ELITE_FOUNDATIONAL`, `IDEA_MINE`, `METHODOLOGICAL_EXEMPLAR`, and `METHODOLOGICAL_NOISE`.

- **Batch quality appraisal** (`PrismaQualityAppraiser.appraise_candidates_batch`, CLI `--appraise-quality [--min-score 7.0]`): queries the active-profile SQLite database for papers with `overall_score >= min_relevance AND quality_score IS NULL`, appraises them concurrently via `ThreadPoolExecutor` (bounded by `threading.Semaphore(2)` on local GPU, 8 workers on the Cloud Mesh), persists each result, and renders a Rich quadrant-distribution table (`render_quadrant_summary`).

- **SQLite schema expansion** (`src/core/database_manager.py`): idempotent `ALTER TABLE` adds `quality_score REAL`, `quality_rubric_json TEXT`, and `evidence_quadrant TEXT` columns to the `papers` table, with a new `update_paper_quality()` helper for WAL-safe concurrent persistence.

- **BibTeX dual-filter export** (`src/utils/bibtex_exporter.py`): `export_library()` gains `min_quality` and `quadrant` parameters, building `overall_score >= ? AND (quality_score >= ? OR quality_score IS NULL)` (plus an optional quadrant predicate). Each generated entry now emits a `note` field in the form `{TALOS Relevance: 9.2/10, Scientific Quality: 8.3/10 (Kitchenham 2007: High Rigor), Quadrant: ELITE_FOUNDATIONAL}`.

- **Kitchenham IEEE citations [11]-[12]** (`README.md`): Section 5 (English) and the mirrored Greek section append the formal Kitchenham and Charters (2007) EBSE technical report and the Kitchenham et al. (2009) Information and Software Technology systematic-review citations.

- **Rule 10 private academic dossier** (`docs/internal/academic/05_PRISMA_QUALITY_APPRAISAL_KITCHENHAM.md`): a seven-section confidential dossier implementing the dual-layer traceability standard, with metadata and BibTeX for Kitchenham (2007/2009), Higgins (2011/2019) Cochrane Risk of Bias, and PRISMA 2020 item 11; LaTeX equations; an ELI5 explanation; a 1:1 code traceability matrix; engineering adaptations; version lineage; and pre-compiled PhD/ICBE 2026 excerpts.

### Changed

- **Dual-Surface Help System** (`src/utils/help_system.py` and `templates/help_manual.html`): Panel 1 documents `--appraise-quality [--min-score 7.0]` and the dual-threshold `--export-bib`; Panel 4 documents the `quality_score` / `evidence_quadrant` database fields; the Web Manual gains a new interactive card with click-to-copy commands and a four-quadrant visual explanation.

- **CLI & TUI integration** (`talos.py`): `_handle_cli_flags()` dispatches `--appraise-quality`; `analysis_visualization_menu()` (Group 3) gains Option 15 "PRISMA Scientific Quality Appraisal & 2D Quadrant Analysis (Kitchenham 2007)" (Back renumbered to Option 16).

- **Version strings synchronized to 5.16.0** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata/lifespan/description, `talos.py` docstring/banner, `run_talos.bat`, `run_talos.sh`, `tests/test_multi_tier.py` version assertion), `docker-compose.yml` (`talos:5.16.0`), `CITATION.cff` (version 5.16.0, date-released 2026-10-01), tray/visualizer/wizard/strategy/diagnostics metadata, `src/prisma/` and `src/search/` docstrings, and all 19 canonical documentation files (dated 2026-10-01).

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_quality_appraisal.py -q` (17 passed, hermetic); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.16.0); `python talos.py --appraise-quality --min-score 7.0` renders the Rich quadrant table; `python talos.py --help` shows `--appraise-quality`; BibTeX `min_quality=7.5` dual-filter export; `GET /help` renders the updated HTML manual; README [11]/[12] present in EN and GR; dossier has 0 U+FFFD glyphs; `verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.15.5] - 2026-10-01 -- Dual-Surface Interactive Help System & Scientific Foundations Canon

### Added

- **Dual-Surface Interactive Help System** (`src/utils/help_system.py`): a rich four-panel console command reference manual (Panel 1 -- categorized CLI Fast-Dispatch Flags; Panel 2 -- Interactive Controls & Navigation; Panel 3 -- Port Mapping & Services Architecture; Panel 4 -- Generated Reports & Storage Artifacts). `render_help_manual(interactive=False)` returns a `rich.console.Group` renderable consumed by `python talos.py --help`, while `render_help_manual(interactive=True)` prints the panels and prompts the user to either open the Web Manual in a browser or return to the menu (ISO/IEC 25010 Context of Use compliance). Zero emojis across every heading and cell.

- **Interactive Web HTML Manual** (`templates/help_manual.html` plus `GET /help` and `GET /manual` redirect in `src/api/main_api.py`): a self-contained, zero-CDN, responsive page matching the TALOS academic dark theme, served at `http://localhost:8001/help`. Features a live search filter bar, click-to-copy buttons on every CLI command, structured cards (CLI Commands, Research Search Paradigms, Ports & Services, Directory Layout), and a dark/print-mode toggle. The API endpoint count rises from 23 to 25.

- **Formal IEEE Scientific References & Theoretical Foundations** (`README.md`): Section 5 in the English guide and the mirrored "Επιστημονικές Αναφορές & Θεωρητικό Υπόβαθρο" section in the Greek guide, presenting ten strictly-formatted IEEE citations ([1]-[10]) covering Stanford DSPy, Net2Net, PRISMA 2020, PRISMA-ScR, Cohen's Kappa, Fleiss' Kappa, citation snowballing, Nomic Embed, Dueling DQN, and Double Q-Learning.

### Changed

- **TUI & CLI integration** (`talos.py`): `_cli_help_table()` now delegates to `help_system.render_help_manual(interactive=False)`, and the main menu gains Option 7 "Help & Command Reference Manual" (Exit renumbered to Option 8).

- **Version strings synchronized to 5.15.5** across the 6 core code files, `docker-compose.yml` (`talos:5.15.5`), `CITATION.cff` (version 5.15.5, date-released 2026-10-01), tray/visualizer/wizard/diagnostics metadata, `src/prisma/` and `src/search/` docstrings, and all 19 canonical documentation files (dated 2026-10-01).

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.5); `python talos.py --help` (4-panel Rich manual, exit 0); `GET /help` (HTMLResponse 200) and `GET /manual` (307 redirect); `verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.15.4] - 2026-10-01 -- DRL Action-Space Expansion to 18 Sources & Net2Net Checkpoint Migration

### Added

- **DRL Action-Space Expansion to 18 Sources** (`src/ai/drl/talos_env.py`): `ALL_KNOWN_SOURCES` grows from 16 to 18 academic sources by appending `nasa_ntrs` and `hal_inria`, completing the 18-source autonomous foraging action space. The Gymnasium action space scales from `Discrete(17)` to `Discrete(19)` -- actions 0..17 query the 18 sources, action 18 is the sleep/cooldown action -- and the observation space scales from 23 to 25 dimensions (1 normalized hour + 18 source usage ratios + 2 streaks + 4 provider ratios). `_load_source_list()` now guarantees the full canonical 18-source list is always present, and the module docstring, `_build_obs()`, and `get_default_state_space()`/`get_default_action_space()` are synchronized to the 25-dim / 19-action baseline. The companion DRL modules (`drl_agent.py`, `drl_networks.py`, `live_agent_sources.py`, `live_agent_orchestrator.py`) and the `TestDRLEnvironment` test class were likewise re-baselined to 18 sources.

- **Net2Net Checkpoint Migration Utility** (`scripts/migrate_d3qn_checkpoint.py`): a one-shot Net2Net (Net2WiderNet) tensor-surgery utility that migrates `models/dddqn_trained.pth` to the 18-source action space while preserving every trained weight bit-for-bit. It performs two complementary widening operations. First, the DuelingLSTM advantage head `A.weight` / `A.bias` is widened to `[19, 32]` / `[19]`: surviving source rows are copied exactly, the four newly introduced source heads (`openaire`, `openreview`, `nasa_ntrs`, `hal_inria`) are initialized with the mean of the top-5 existing source rows (ranked by L2 norm) plus a +0.05 optimistic exploratory bias, and the sleep row is re-indexed to position 18. Second, the LSTM input layer `lstm1.weight_ih_l0` is widened to `[512, 25]` by name-based column remapping: existing source columns are copied by name, the four new source columns are initialized with a column-mean prior (the standard replicate-then-specialise Net2WiderNet strategy), and the two streak columns plus the four provider columns are shifted to their new trailing positions. The checkpoint metadata dictionary is updated in place (`state_dim=25`, `action_dim=19`, `source_names=18`), and the result is verified by a strict `DuelingLSTM(25, 19).load_state_dict()` load with zero tensor-mismatch errors. A safety backup `models/dddqn_trained.pth.bak` is created on first run. Note: inspection revealed the legacy checkpoint was trained on 14 sources (state_dim=21, action_dim=15), not the 16 sources assumed by the prior documentation, so the migration name-based approach expands 15 -> 19 actions and 21 -> 25 state dimensions and is robust to any legacy ordering.

- **18-Source Profile Synchronization** (`config.json`, `config.template.json`, `_profiles/default_drones/config.json`): `nasa_ntrs` and `hal_inria` were added to the `max_results_config` surfaces and query-key sets (with new `nasa_ntrs_query` / `hal_inria_query` keys, plus -- in the drone profile -- the previously-missing `openreview_query` / `openaire_query` and the `core`/`scigov` result caps), so the daemon detects and reports 18 configured and working sources on startup.

### Changed

- **Scopus/Elsevier XML-JSON Author Normalization** (`src/utils/evaluation_history.py`): the canonical `normalize_authors()` resolver now explicitly locks in the Scopus/Elsevier XML-JSON author forms -- the `$`-wrapped value nodes, the `@name` / `@surname` attribute pairs, and the `given_name` / `surname` fallback -- with a clean 4-author + "et al." truncation for long author lists, backed by dedicated unit coverage (`tests/test_session_circuit_breaker.py`).

- **Version strings synchronized to 5.15.4** across the 6 core code files, `docker-compose.yml` (`talos:5.15.4`), `CITATION.cff` (version 5.15.4, date-released 2026-10-01), tray/visualizer/wizard/diagnostics metadata, `src/prisma/` and `src/search/` docstrings, and all 19 canonical documentation files (dated 2026-10-01).

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.4); DRL model load verification (`DuelingLSTM(25, 19)` strict load, zero tensor mismatch); daemon source detection (Configured sources: 18, Working sources: 18); `verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.15.3] - 2026-09-29 -- Session Circuit Breaker, Robust Author Extraction & Daemon Lifecycle Hardening

### Added

- **Session-Level Circuit Breaker** (`src/core/ai_manager.py`): a process-lifetime latch `AIManager.fast_tier_offline` (default `False`) replaces the prior per-batch memo as the primary fast-tier guard. The first connection-refused/timeout on the CPU Edge endpoint (`FAST_EDGE_BASE_URL`, port 11435) latches the tier offline and emits a single one-time notice (`[INFO] Fast CPU tier (11435) offline. Latching direct local GPU routing for this session.`), after which every subsequent fast-tier request in the batch and daemon loop bypasses port 11435 with ZERO network attempts, ZERO timeout latency, and ZERO warning logs, routing directly to local GPU Ollama (`LOCAL_GPU_MODEL` at port 11434). The legacy `_fast_edge_offline_memo` is retained as a synonym so existing diagnostics and documentation references never break.
- **Robust Multi-Key Author Extraction** (`src/utils/evaluation_history.py:normalize_authors(paper)`): a single canonical resolver handling every author representation produced across the 18-source ingestion mesh -- `authors_str` (flat string), `authors` as a list of dicts (`{"name": ...}` from OpenAlex/Semantic Scholar, `{"author": {"display_name": ...}}` from OpenAlex raw, `{"full_name": ...}` from IEEE), `authors` as a list of strings, `authors` as a comma/semicolon-delimited string, and the singular legacy `author` key. It never returns "Unknown Authors" when any standard key holds data. Consumed by both `src/ai/drl/talos_service.py` and `src/ai/drl/live_agent_orchestrator.py`.
- **Silent Standalone SYNAPSE Buffering** (`src/integration/synapse_client.py`): a Standalone Quiet Mode state machine (`synapse_available`) latches the bus offline on the first connection-refused probe (port 8000) and buffers every subsequent event silently to bounded in-memory storage plus best-effort JSONL (`data/synapse_buffer.jsonl`) with a single one-time notice (`[INFO] SYNAPSE bus offline (port 8000). Operating in standalone quiet mode (local event buffering active).`), eliminating all per-paper emission warnings.

### Changed

- **Clean Daemon Evaluation Telemetry** (`src/ai/drl/talos_service.py`): the daemon loop now emits a single clean, uncluttered Rich block per real evaluation -- `[EVAL] <Full Title> | Authors: <Extracted Authors> | Score: <X.X>/10 | [<DECISION>] -> DB` -- gated on a resolved title so empty/simulated steps stay silent; no interstitial connection warnings clutter the console.
- **Version strings synchronized to 5.15.3** across the 6 core code files, `docker-compose.yml` (`talos:5.15.3`), `CITATION.cff` (version 5.15.3, date-released 2026-09-29), tray/visualizer/wizard/diagnostics metadata, `src/prisma/` and `src/search/` docstrings, and all 19 canonical documentation files (dated 2026-09-29).

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.3); `pytest tests/test_session_circuit_breaker.py -q` (12 passed: 10 author-normalization + 2 circuit-breaker latching); `verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.15.2] - 2026-09-28 -- Universal Search Hub UX & Reporting Harmonization

### Added

- **Code-First Search Rich Table & Markdown report** (`src/search/code_first_search.py`): `render_results()` renders reproducible repositories in a styled `box.ROUNDED` table ("Reproducible Code-First Search Results") with Rank, Stars (rendered as `[bold yellow]N stars[/bold yellow]`, zero emoji), Repository Name, Paper Title & Description, Topics & Frameworks, and GitHub URL columns, plus supplementary PapersWithCode and matching-database tables; `export_search_report()` writes a timestamped `code_search_YYYYMMDD_HHMMSS.md` report under `data/reports/code_search/` with clickable URLs, and `run(..., render=True)` auto-invokes both.
- **Citation Snowballing Rich genealogy & Markdown report** (`src/search/citation_snowballing.py`): `render_genealogy()` renders the citation graph in a `box.ROUNDED` table ("Citation Snowballing Genealogy Graph") with Traversal (Backward/Forward), Depth, Title, Year / Source, DOI / URL, and Relevance Score columns; `export_snowball_report()` writes a timestamped `snowball_YYYYMMDD_HHMMSS.md` report under `data/reports/snowball/` with Backward (Cited References) and Forward (Citing Recent Literature 2024-2026) tables and clickable links; `run(..., render=True)` auto-invokes both.

### Changed

- **TUI/CLI raw JSON dumps eliminated** (`talos.py`): `--code-search` and `--snowball` fast-dispatch flags plus the Group 2 Universal Search Hub menu options 3 (Snowballing) and 5 (Code-First) now invoke the engines' `run()` methods directly, which render their dedicated Rich tables and report paths without printing redundant raw JSON (the dead `_render_search_result()` helper was removed).
- **Version strings synchronized to 5.15.2** across the 6 core code files, `docker-compose.yml` (`talos:5.15.2`), `CITATION.cff` (version 5.15.2), tray/visualizer/wizard/diagnostics metadata, `src/prisma/` and `src/search/` docstrings, and all 19 canonical documentation files (dated 2026-09-28).

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.2); `python talos.py --code-search "spatio temporal graph neural networks"` (Rich Table + `data/reports/code_search/` report); `python talos.py --snowball "10.1109/TTE.2026.3665346"` (Rich genealogy + `data/reports/snowball/` report); `verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.15.1] - 2026-09-28 -- Persistent Vector Cache & Accelerated Neural Embedding Engine

### Added

- **Persistent SQLite Vector Cache** (`src/core/database_manager.py`): idempotent `paper_embeddings` table (BLOB-encoded float32 vectors, per-model index, `ON DELETE CASCADE` foreign key) plus `get_cached_embeddings(model_name)` and `save_embeddings_batch(records)` helpers, enabling zero-redundancy incremental indexing across runs.
- **Real-time `rich.progress.Progress` telemetry** (`src/search/neural_vector_search.py`): a live progress bar with percentage, completed/total papers, and ETA (`{task.time_remaining}`) for the uncached abstract delta, embedded concurrently via `ThreadPoolExecutor` and persisted in batches of 64.
- **NumPy vectorized matrix cosine similarity** (`src/search/neural_vector_search.py`): `_matrix_rank()` assembles a single N x 768 document matrix and computes `S_C(q, D) = (q . D^T) / (||q|| ||D||)` in one vectorized pass, reducing query latency from minutes to under 50ms.
- **Rich Table presentation** (`src/search/neural_vector_search.py`): `render_results()` renders top-K results in a styled `box.ROUNDED` table ("Neural Vector Semantic Search Results") with Rank, Similarity (%), Title, Year / Source, DOI / URL, and Key Abstract Match Snippet columns; JSON output preserved via `run(..., render=False)`.

### Changed

- **Version strings synchronized to 5.15.1** across the 6 core code files, `docker-compose.yml` (`talos:5.15.1`), `CITATION.cff` (version 5.15.1), tray/visualizer/wizard/diagnostics metadata, `src/prisma/` docstrings, and all 19 canonical documentation files (dated 2026-09-28).

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.1); `pytest tests/test_neural_vector_search.py -q` (mock `nomic-embed-text` embeddings, exit 0); persistent cache round-trip smoke test (`get_cached_embeddings` / `save_embeddings_batch`); `verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan (0 U+FFFD).

## [v5.15.0] - 2026-09-28 -- Universal Scientific Search Hub & Neural Graph Discovery Engine

### Added

- **Modular ingestion subpackage** (`src/ingestion/sources/`): all 18 source adapters (`arxiv`, `ieee`, `semantic_scholar`, `springer`, `openalex`, `dblp`, `elsevier`, `core`, `crossref`, `openarchives`, `pubmed`, `scigov`, `osti`, `plos`, `openreview`, `openaire`, `nasa_ntrs`, `hal_inria`) relocated under a unified `SOURCE_REGISTRY` exposed by `src/ingestion/sources/__init__.py`; `daily_search.py` and `historic_search.py` import the canonical registry from the new subpackage.
- **Citation Snowballing Engine** (`src/search/citation_snowballing.py`): `CitationSnowballEngine` traverses the citation graph backward (referenced works via OpenAlex/Crossref/Semantic Scholar) and forward (citing works 2024-2026), filters nodes via `PrismaEvaluator`/local `llama3.1:8b`, generates a structured genealogy graph, and imports relevant papers into the active-profile DB.
- **Neural Vector Search** (`src/search/neural_vector_search.py`): `NeuralVectorSearchEngine` encodes queries and abstracts with the local `nomic-embed-text` Ollama model (port 11434) and ranks by cosine similarity `S_C(u,v) = (u . v) / (||u|| ||v||)`, with a deterministic lexical fallback offline.
- **Code-First Search** (`src/search/code_first_search.py`): `CodeFirstSearchEngine` discovers reproducible, code-linked papers (GitHub / PapersWithCode / PyTorch / ROS2 / Gazebo / AirSim / Isaac Gym benchmarks) and cross-references the active-profile DB.
- **CLI & TUI integration** (`talos.py`): `--snowball [seed]`, `--vector-search [query]`, and `--code-search [query]` fast-dispatch flags plus a restructured Group 2 "Universal Search Hub" menu (6 core options + preserved grey literature / Zotero / dashboard tools).
- **Rule 10 dossier 04** (`docs/internal/academic/04_NEURAL_GRAPH_SEARCH_PARADIGMS.md`): 7-section confidential academic dossier (Jalali & Wohlin 2012, Nomic Embed 2024, DPR) with a full code traceability matrix.

### Changed

- **Version strings synchronized to 5.15.0** across the 6 core code files, `docker-compose.yml`, `CITATION.cff`, tray/visualizer/wizard/diagnostics metadata, `src/prisma/` docstrings, and all 19 canonical documentation files.

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.15.0); `pytest tests/test_neural_vector_search.py -q` (mock `nomic-embed-text` embeddings, exit 0); ingestion modularization smoke test; dossier conforms to the 7-section standard with 0 U+FFFD; `verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan.

## [v5.14.2] - 2026-09-28 -- BibTeX Scientific Exporter, 18-Source Aerospace Ingestion & Feature Freeze

### Added

- **BibTeX Scientific Exporter** (`src/utils/bibtex_exporter.py`): new `BibTeXExporter` class exporting curated papers from the active-profile SQLite database to a standard-compliant `.bib` library (default `data/exports/talos_library.bib`). Generates `AuthorYearTitleKeyword` cite keys (for example `Smarlamakis2026Cooperative`), sanitizes all LaTeX reserved characters, emits `@article`/`@inproceedings` entries with title, author, journal/booktitle, year, doi, url, abstract, keywords, and a `note` carrying the TALOS evaluation score, and renders a Rich confirmation panel via `render_export_summary()`. `export_library()` accepts `min_score`, `only_prisma_included`, and `active_profile`; a standalone `__main__` and `export_and_render()` are included.
- **NASA NTRS Harvester** (`src/ingestion/nasa_ntrs_source.py`): `NasaNtrsSource` querying the official `https://ntrs.nasa.gov/api/citations/search` REST endpoint (pure JSON, no API key) for aerospace technical reports (NASA TM/TP/CR), flight control, avionics, and autonomous swarm research, with landing-page URLs and DOI extraction.
- **HAL/Inria Harvester** (`src/ingestion/hal_inria_source.py`): `HalInriaSource` querying `https://api.archives-ouvertes.fr/search/` (Solr-style JSON, no API key) for CNRS/Inria/ONERA robotics, multi-agent reinforcement learning, and French/EU PhD theses.
- **Rule 10 dossier 03** (`docs/internal/academic/03_GREY_LITERATURE_AEROSPACE_EXPANSION.md`): 7-section confidential academic dossier (gitignored) implementing the dual-layer traceability standard.

### Changed

- **18-source ingestion mesh:** `SOURCE_REGISTRY` in `daily_search.py` and `historic_search.py` now registers `nasa_ntrs` and `hal_inria` (16 -> 18 sources); `max_workers` raised to 18; `ALL_ACADEMIC_SOURCES` (checkbox TUI) and `_ALL_VISUALIZER_SOURCES` (API health map) expanded; `OPEN_ACADEMIC_ENDPOINTS` in `system_diagnostics.py` probes both new endpoints.
- **Persisted PRISMA decision:** `papers.prisma_decision` nullable column added idempotently in `database_manager.create_table()` so the exporter can filter INCLUDE studies.
- **Version strings synchronized to 5.14.2** across the 6 core code files, `docker-compose.yml`, `CITATION.cff`, tray/visualizer/wizard metadata, `src/prisma/` docstrings, and all 19 canonical documentation files.

### Verification

- `python -m compileall src config tests talos.py` (0 errors); `pytest tests/test_system_integrity.py -q`; `pytest tests/test_multi_tier.py -k test_talos_version` (5.14.2); `python talos.py --export-bib` (exit 0); source-factory mock tests (18 sources); dossier conforms to 7-section standard with 0 U+FFFD; `verify_dependency_map.py --ci` (exit 0); `bash -n run_talos.sh`; strict UTF-8 scan.

## [v5.14.1] - 2026-09-28 -- Multi-Agent Peer-Review Swarm & Consensus Engine

### Added

- **Multi-agent peer-review swarm** (`src/prisma/swarm_evaluators.py`): three specialized reviewer personas -- `AlgorithmicReviewer` (mathematical formulation, HMADRL / Dec-POMDPs / QMIX DRL algorithms, ST-GNNs / ST-GAT graph neural networks, theoretical soundness), `EmpiricalReviewer` (Gazebo / AirSim / Isaac Gym simulation environments, ablation studies, benchmark rigor, real flight tests, quantitative metrics), and `OperationalReviewer` (swarm scalability, communication topology and latency, physical collision avoidance, NATO / CJCSI operational constraints). Each persona emits a typed `ReviewerVerdict` (agent name, INCLUDE / EXCLUDE / UNCERTAIN vote, 0.0-10.0 score, 0.0-1.0 confidence, and key critiques).
- **Automated inter-rater reliability** (`calculate_cohens_kappa` / `cohens_kappa_pairwise`): Fleiss' multi-rater generalization of Cohen's Kappa `kappa = (p_o - p_e) / (1 - p_e)` over the three votes, plus a classical pairwise two-rater kappa for auditing the agreement matrix.
- **Chain-of-Thought consensus arbiter** (`SwarmConsensusArbiter.adjudicate`): unanimous verdicts (3-0 or 0-3) short-circuit to an instant high-confidence decision; split verdicts (2-1 / 1-2 / 1-1-1) invoke a Chain-of-Thought adjudication over the dissenting critiques, falling back to a 2-1 majority (or UNCERTAIN on a 1-1-1 tie) when the LLM is unreachable. Returns a `ConsensusVerdict` carrying the final decision, a confidence-weighted consensus score, the Cohen's Kappa, and a multi-perspective synthesis narrative.
- **PRISMA pipeline integration** (`src/prisma/dspy_modules.py` + `dspy_signatures.py`): `PrismaEvaluator` gains an `evaluation_mode` parameter (`'single'` fast baseline vs `'swarm'` rigorous 3-agent consensus); the swarm path dispatches the three personas concurrently via `ThreadPoolExecutor` bounded by the `threading.Semaphore(2)` VRAM guard (2 workers local, 3 workers cloud mesh) and records Cohen's Kappa and per-agent critiques in `PrismaScreeningSignature` (`consensus_mode`, `swarm_kappa`, `agent_verdicts`). `PrismaExecutor.run()` logs consensus statistics (mean Cohen's Kappa) during the Screening phase.
- **CLI & TUI integration** (`talos.py`): `--prisma --swarm` fast-dispatch flag and a Group 3 "Select Screening Mode" prompt (1. Fast Single Screener | 2. Rigorous Multi-Agent Review Swarm).
- **Rule 10 academic dossier** (`docs/internal/academic/02_MULTI_AGENT_CONSENSUS_SWARM.md`): 7-section confidential dossier implementing the dual-layer traceability standard.

### Changed

- **Version strings synchronized to 5.14.1** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata/lifespan log/description, `talos.py` docstring and release note, `run_talos.bat` title/banner/logs, `run_talos.sh` header/banner/logs, `tests/test_multi_tier.py` version assertion), plus `docker-compose.yml` (`talos:5.14.1`), `CITATION.cff` (version 5.14.1, date-released 2026-09-28), the user-facing strings in `src/utils/tray_icon.py`, `src/utils/evaluation_history.py`, `src/utils/research_setup_wizard.py`, `src/utils/ai_strategy_selector.py`, `src/utils/system_diagnostics.py`, and `templates/live_foraging_visualizer.html`, the `src/prisma/` module docstrings, and all 19 canonical documentation files.

### Verification

- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.14.1).
- `python talos.py --help` lists `--prisma [--swarm]`.
- Swarm evaluator unit exercise (3-agent review + Cohen's Kappa) completed with exit 0.
- `python src/utils/verify_dependency_map.py --ci` returned exit 0.
- `bash -n run_talos.sh` passed with zero syntax errors.
- Strict UTF-8 decode scan across all modified files: zero U+FFFD replacement glyphs.

## [v5.14.0] - 2026-09-28 -- Stanford DSPy PRISMA-ScR Pipeline & Declarative Synthesis Engine

### Added

- **Declarative PRISMA-ScR signatures** (`src/prisma/dspy_signatures.py`): typed, Pydantic-v2 schema models mirroring the Stanford DSPy `dspy.Signature` paradigm -- `PrismaPlanSignature` (topic/scope -> search facets, boolean strategy, methodological inclusion and exclusion criteria), `PrismaScreeningSignature` (title/abstract + criteria -> INCLUDE/EXCLUDE/UNCERTAIN decision, bounded relevance score, exclusion reason, methodology tags, chain-of-thought), `PrismaEligibilitySignature` (deep assessment -> ELIGIBLE/INELIGIBLE decision + swarm algorithm type / learning paradigm / network architecture), and `PrismaSynthesisSignature` (included-studies summary -> thematic taxonomy, methodological distribution, gaps, narrative). A robust `extract_json_payload()` recovery helper parses fenced or prose-prefixed local-model JSON.
- **PlanEval pipeline modules** (`src/prisma/dspy_modules.py`): `PrismaPlanner` (multi-database search protocol synthesis), `PrismaEvaluator` (structured Chain-of-Thought screening over the multi-tier `AIManager`), `PrismaEligibilityJudge` (full-record methodological suitability), and `PrismaExecutor` (end-to-end 4-phase orchestrator with live record counters N_identified / N_dedup / N_screened / N_excluded / N_eligible / N_included). Every LLM-backed step degrades gracefully to deterministic keyword rules for air-gapped operation.
- **PRISMA 2020 Mermaid flowchart generator** (`src/prisma/mermaid_generator.py`): `generate_prisma_mermaid(counts)` emits a standard-compliant `flowchart TD` with exact `(n = ...)` labels across Identification/Screening/Eligibility/Included, plus `mermaid_to_markdown()` and `mermaid_to_html()` export wrappers.
- **Scoping review synthesizer** (`src/prisma/scoping_review_synthesizer.py`): `synthesize_scoping_review()` and `synthesize_scoping_review_latex()` produce seven-section publication-grade drafts per PRISMA-ScR guidelines.
- **CLI & TUI integration** (`talos.py`): `--prisma` fast-dispatch flag and Group 3 option "PRISMA-ScR Declarative Synthesis Pipeline (Stanford DSPy Engine)".
- **Rule 10 academic dossier** (`docs/internal/academic/01_STANFORD_DSPY_PRISMA_PIPELINE.md`): 7-section confidential dossier implementing the dual-layer traceability standard.

### Changed

- **Version strings synchronized to 5.14.0** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata/lifespan log/description, `talos.py` docstring and release note, `run_talos.bat` title/banner/logs, `run_talos.sh` header/banner/logs, `tests/test_multi_tier.py` version assertion), plus `docker-compose.yml` (`talos:5.14.0`), `CITATION.cff` (version 5.14.0, date-released 2026-09-28), and the user-facing strings in `src/utils/tray_icon.py`, `src/utils/evaluation_history.py`, `src/utils/research_setup_wizard.py`, `src/utils/ai_strategy_selector.py`, `src/utils/system_diagnostics.py`, and `templates/live_foraging_visualizer.html`, and all 19 canonical documentation files.

### Verification

- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.14.0).
- `python talos.py --help` lists `--prisma`.
- `python src/utils/verify_dependency_map.py --ci` returned exit 0.
- `bash -n run_talos.sh` passed with zero syntax errors.
- Strict UTF-8 decode scan across all modified files: zero U+FFFD replacement glyphs.

## [v5.13.1] - 2026-09-28 -- System Diagnostics Analyzer & Operational Integrity Engine

### Added

- **System Diagnostics Analyzer** (`src/utils/system_diagnostics.py`): new `SystemDiagnosticsEngine` conforming to ISO/IEC 25010 Diagnosability and Fault Tolerance. Executes an 8-point pre-flight health check in strict local-first order: `check_python_environment()` (Python 3.11.x + `talosenv` conda env), `check_database_integrity()` (`PRAGMA integrity_check` + WAL journal mode on the active profile DB), `check_local_ai_runtime()` (0.8s HTTP GET to Ollama `/api/tags` verifying `LOCAL_GPU_MODEL`), `check_port_availability()` (ports 8001/8000/11434/11435 conflict probe), `check_filesystem_permissions()` (read/write probes on `data/`, `_profiles/`, `logs/`), `check_environment_credentials()` (`.env` structure validation with secret redaction), `check_daemon_status()` (`talos_service.py` process detection), and `check_network_endpoints()` (concurrent probe of 7 zero-key open repositories -- arXiv, OpenAlex, Crossref, DBLP, PubMed (NCBI), OSTI (DOE), PLOS -- with per-endpoint latency and a 1.5s timeout, guarded for air-gapped operation).
- **Rich health report rendering** (`render_report()`): a `box.ROUNDED` Rich table titled "TALOS System Diagnostic Health Report" with Component / Target-Metric / Status (PASS green / WARN yellow / FAIL red) / Remediation Guidance columns, each failure carrying a one-line copy-paste remediation.
- **CLI fast-dispatch flags** (`talos.py`): `--diagnostics` (canonical ISO flag) and `--doctor` / `-d` (DevOps alias) run `SystemDiagnosticsEngine().run_and_render()` and exit cleanly.
- **TUI integration (Group 6)**: `system_health_menu()` gains Option 1 "System Health & Diagnostic Analyzer", with the remaining options renumbered 1-8 to 2-9.

### Changed

- **Version strings synchronized to 5.13.1** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata/lifespan log/description, `talos.py` docstring and release note, `run_talos.bat` title/banner/logs, `run_talos.sh` header/banner/logs, `tests/test_multi_tier.py` version assertion), plus `docker-compose.yml` (`talos:5.13.1`), `CITATION.cff` (version 5.13.1, date-released 2026-09-28), and the user-facing strings in `src/utils/tray_icon.py`, `src/utils/evaluation_history.py`, `src/utils/research_setup_wizard.py`, `src/utils/ai_strategy_selector.py`, and `templates/live_foraging_visualizer.html`.

### Verification

- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.13.1).
- `python talos.py --diagnostics` rendered the Rich health table and exited 0.
- `python talos.py --doctor` executed identically (exit 0).
- `python src/utils/verify_dependency_map.py --ci` returned exit 0.
- `bash -n run_talos.sh` passed with zero syntax errors.
- Strict UTF-8 decode scan across all modified files: zero U+FFFD replacement glyphs.

## [v5.13.0] - 2026-09-28 -- Full-Stack Concurrent Multi-Threaded Engine & High-Throughput Harvester

### Added

- **Concurrent Cognitive Evaluation Pool** (`src/core/ai_manager.py:batch_evaluate_papers()`): a multi-threaded batch evaluator that scores an arbitrary list of papers through the structured JSON evaluation schema of `evaluate_paper_json()`. Worker concurrency is resolved dynamically via `_resolve_eval_concurrency()` from the 2D Execution Matrix: the Cloud Mesh (DeepSeek, Gemini, Groq, and the OpenAI-compatible registry) runs `max_workers=8`, while local GPU (Ollama) runs `max_workers=2` bounded by a `threading.Semaphore(2)` to eliminate CUDA Out-Of-Memory risks. Results preserve input order as `(paper, evaluation_dict_or_None)` pairs.

- **Concurrent Historical Ingestion Mesh** (`src/ingestion/historic_search.py`): the sequential multi-year fetch loop is replaced with the same `ThreadPoolExecutor(max_workers=min(16, len(enabled_sources)))` model used by `daily_search.py`. Each source is isolated in `_harvest_single_source()` with per-thread stdout redirection (`contextlib.redirect_stdout`) and full exception guards, aggregated via `as_completed()` on the main thread, and deduplicated by DOI + SHA-1 normalized-title hash.

- **Real-time Rich Live telemetry for historical harvesting**: a Rich Live table renders per-source status (`WAITING` / `HARVESTING` / `COMPLETED` / `FAILED`) with Papers Found and Elapsed Time columns, followed by a Historical Ingestion Summary panel.

- **Concurrent database re-evaluation** (`src/utils/reevaluate_database.py`): the sequential re-evaluation loop now drives the concurrent evaluation pool and persists results through `_apply_evaluation_batch()`, which batches UPDATE statements on a single SQLite WAL connection with grouped commits.

- **Step 0 Profile Target Gate (Research Setup Wizard)**: the multi-profile onboarding surface retains the pre-flight Step 0 profile target selection (`reconfigure active / switch existing / create fresh isolated profile`), now covered by the v5.13.0 verification suite.

### Changed

- **Literature harvesting latency reduced 8x-10x**: concurrent multi-source harvesting cuts the total academic harvest from approximately 35-45 seconds down to approximately 3-4 seconds across both daily and historical pipelines.

- **LLM paper scoring accelerated 5x-8x**: the concurrent batch evaluation pool parallelizes cognitive scoring, with VRAM-aware worker throttling (Cloud 8 workers, Local GPU 2 workers).

- **Version strings synchronized to 5.13.0** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata and lifespan startup log, `talos.py` docstring and banner, `run_talos.bat` title/banner/logs, `run_talos.sh` header/banner/logs, `tests/test_multi_tier.py` version assertion), plus `docker-compose.yml` (`talos:5.13.0`), `CITATION.cff` (version 5.13.0, date-released 2026-09-28), and the user-facing strings in `src/utils/tray_icon.py`, `src/utils/evaluation_history.py`, `src/utils/research_setup_wizard.py`, `src/utils/ai_strategy_selector.py`, and `templates/live_foraging_visualizer.html`.

- **Roadmap realignment**: v5.13.0 now holds the Full-Stack Concurrent Multi-Threaded Engine; the Stanford DSPy PRISMA Pipeline milestone moves to v5.14.0 (Target: Christmas 2026 / Early 2027).

### Verification

- `python -m compileall src config tests talos.py daily_search.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.13.0).
- `python -m pytest tests/test_research_setup_wizard.py -q` passed.
- `python src/utils/verify_dependency_map.py --ci` returned exit 0.
- `bash -n run_talos.sh` passed with zero syntax errors.
- Strict UTF-8 decode scan across all modified files: zero U+FFFD replacement glyphs.

## [v5.12.4] - 2026-09-28 -- Concurrent Ingestion Mesh & Multi-Profile Research Onboarding

### Added

- **Step 0 Profile Target Selection** (`src/utils/research_setup_wizard.py:_step0_profile_selection()`): a pre-flight gate executed before the Research Topic step offers three mutually exclusive paths -- reconfigure the current active profile in place, switch to an existing isolated profile, or instantiate a fresh isolated workspace under `_profiles/<name>/` with its own `config.json` and a fresh `talos_research.db`. The header panel now displays `Target Profile: [<target_profile>]`, and the canonical `_profiles/active_profile.txt` marker drives the single-source-of-truth database resolver `get_active_profile_db_path()`.

- **Concurrent Academic Ingestion Mesh** (`src/ingestion/daily_search.py`): the sequential 16-source harvest loop is replaced with a `ThreadPoolExecutor(max_workers=min(16, len(enabled_scrapers)))` mesh. Each provider is isolated in `_harvest_single_source(scraper_name, query, criteria, date_limit, ...)` with strict per-thread exception isolation -- a timeout or HTTP error in one provider (e.g. Science.gov or OSTI) never aborts the overall process. Results are gathered via `concurrent.futures.as_completed()` and aggregated on the main thread.

- **Real-time Rich Live concurrency telemetry**: a Rich Live table tracks per-source status (`WAITING` / `HARVESTING` / `COMPLETED` / `FAILED`) with Papers Found and Elapsed Time columns, followed by a final summary panel reporting total harvest time, raw paper count, and unique deduplicated count.

- **DOI + normalized-title-hash deduplication**: `_deduplicate_papers()` keyed by DOI with a SHA-1 normalized-title fallback collapses cross-source duplicates on the main thread before database insertion.

### Changed

- **Harvest latency reduction**: concurrent harvesting cuts the total academic harvest from approximately 35-45 seconds down to approximately 3-4 seconds.

- **Environment Setup Guides documented**: `docs/ENVIRONMENT_SETUP_GUIDE.md` and `docs/ENVIRONMENT_SETUP_GUIDE_GR.md` are now the official English and Greek references for configuring the environment and credentials.

### Verification

- `python -m compileall src config tests talos.py daily_search.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.12.4).
- `python -m pytest tests/test_research_setup_wizard.py -q` passed (39 tests).
- `python src/utils/verify_dependency_map.py --ci` returned exit 0.
- `bash -n run_talos.sh` passed with zero syntax errors.
- Strict UTF-8 decode scan across all modified files: zero U+FFFD replacement glyphs.

## [v5.12.3] - 2026-09-27 -- Research Pivot Modernization & Setup Wizard TUI Integration

### Changed

- **Research Pivot canonical path resolution** (`src/ai/llm/research_pivot.py`): the broken `scripts/` subfolder resolution and the stale `src/ai/scripts/query_translator.py` path were removed. The wizard now anchors every subprocess invocation to `REPO_ROOT` (the directory containing `talos.py`) and resolves canonical scripts through a dedicated `_SCRIPT_MAP`: the Cognitive Query Compiler (`src/ai/llm/query_translator.py`), the database re-evaluation script (`src/utils/reevaluate_database.py` / `src/utils/recalculate_scores.py`), and the DRL training script (`src/ai/drl/train_agent.py`). Every subprocess is executed with `sys.executable` so the active Conda interpreter is used rather than an ambiguous system Python.

- **Strict subprocess returncode verification** (`research_pivot.py`): the wizard now captures `proc.returncode` for every child process and reports `YES` in the Pivot Summary only when the return code is exactly 0; any non-zero code is reported as `FAILED (Code X)` with the trailing output lines surfaced to the operator. Silent-failure reporting (including the previous `YES` on exit code 2) is eliminated.

- **Rule 9 codename elimination**: the lingering mythological codenames `PYTHIA` and `CHIRON` were removed from the Research Pivot Wizard and the Configuration & Profiles TUI menu and replaced with ISO/IEC 25010 functional terminology -- `PYTHIA` becomes the Cognitive Query Compiler and `CHIRON` becomes the Citation Graph Analyzer.

- **Research Setup Wizard TUI promotion** (`talos.py:profile_settings_menu()`): the wizard is promoted to option 1 as "Research Setup Wizard (Full Onboarding & Reconfiguration)", making it re-runnable at any time to re-tune the research scope, the 16 search queries, the inclusion/exclusion criteria, the historical search window, and the AI execution strategy. The Configuration & Profiles menu was renumbered accordingly (Manage Profiles, AI Execution Strategy Switcher, Research Pivot Wizard, Research Goal, AI Model Management, Model Discovery, Model Provisioning CLI, API Keys Management, API Key Diagnostics).

### Summary -- Research Setup Wizard Enhancements

- **5-tier AI execution strategy matrix**: `strict_local`, `local_first`, `cloud_first`, `strict_cloud`, and `auto_dynamic` persisted to `config.json` (`ai_execution_strategy`) and `.env` (`TALOS_NETWORK_STRATEGY`).
- **Day-based historical search window**: measured in days from today with presets and a custom positive-integer prompt (`days_to_search_historic`).
- **Cancellation flow integrity**: cancelling any step aborts the flow before any `config.json` write and guards the onboarding sentinel.
- **Thinking model parser**: local and cloud response parsers unwrap `reasoning_content` / `thinking` / `<think>` tags so thinking models never return empty strings.

### Verification

- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.12.3).
- `python -m pytest tests/test_research_setup_wizard.py -q` passed (28 tests).
- `python src/utils/verify_dependency_map.py --ci` returned exit 0.
- `bash -n run_talos.sh` passed with zero syntax errors.
- Strict UTF-8 decode scan across all modified files: zero U+FFFD replacement glyphs.

## [v5.12.2] - 2026-09-27 -- Self-Healing AI Manager, 5-Tier Strategy Matrix & Research Wizard Integrity Engine

### Added

- **Self-healing local Ollama probe & spawn** (`src/core/ai_manager.py:probe_local_ollama()` / `_ensure_local_ollama_runtime()`): a fast pre-flight liveness probe issues a lightweight `GET http://127.0.0.1:11434/api/tags` (0.8s timeout). When the runtime is offline, the manager consults the `auto_start_local_llm` config flag, offers a `TALOS_QUESTIONARY_STYLE` Questionary confirm ("Would you like TALOS to launch it in the background?", default True) in interactive CLI/Wizard sessions, spawns `ollama serve` detached (`CREATE_NEW_PROCESS_GROUP | DETACHED_PROCESS` on Windows), and polls the health endpoint for up to 3.0s (0.5s interval) before degrading gracefully.
- **Secure on-demand cloud key injection** (`_prompt_cloud_key()` / `_persist_env_key()` / `_register_cloud_provider_on_demand()` / `_ensure_cloud_credential_for_fallback()`): in interactive mode, when local inference fails and the operator consents to cloud fallback but the provider key is missing, TALOS renders a masked `questionary.password` prompt, validates the key, injects it into `os.environ`, appends it cleanly to the project `.env` (gitignored, dedup-safe), and registers the provider on the fly.
- **Heuristic query stopword cleaner** (`src/utils/research_setup_wizard.py:_extract_salient_terms()`): the offline rule-based query generator now strips English stopwords (`for`, `with`, `and`, `the`, etc.) and punctuation noise (unbalanced parentheses, stray hyphens) while preserving hyphenated compounds (`spatio-temporal`), capping the boolean query at 4-6 salient tokens so IEEE Xplore, Scopus, and arXiv fallback queries produce valid, executable Boolean syntax instead of zero-hit stopword chains. Three new hermetic tests lock the behavior.
- **5-Tier AI Execution Strategy Matrix** (`src/utils/research_setup_wizard.py:EXECUTION_STRATEGIES` / `src/utils/ai_strategy_selector.py`): Step 2 now offers the full five-tier hierarchy -- `strict_local` (100% air-gapped/offline), `local_first` (local GPU priority with cloud fallback on failure/OOM), `cloud_first` (cloud priority with local fallback on network failure), `strict_cloud` (0% GPU VRAM footprint to leave the workstation GPU free for concurrent PhD deep-learning runs), and `auto_dynamic` (autonomous 2D router adapting to VRAM and task complexity) -- persisted to `config.json` (`ai_execution_strategy`) and `.env` (`TALOS_NETWORK_STRATEGY`). Exposed via a new `--strategy [mode]` CLI flag and an "AI Execution Strategy Switcher" entry in the TUI.
- **Day-based historical search window** (`_step3_search_window()` / `_prompt_custom_days()`): Step 3 now measures the window in days from today with presets (30, 365, 1,095, 1,825, 3,650 days) plus a custom positive-integer prompt, persisting `days_to_search_historic` (replacing legacy start/end year fields).
- **Sentinel & cancellation integrity** (`_render_cancelled()`): cancelling any step (None or KeyboardInterrupt) now aborts the whole flow before any config.json write, eliminates `'N/A'` placeholders, and guards the `data/.talos_onboarded` sentinel.
- **Thinking/reasoning model resilience** (`src/core/ai_manager.py:_strip_thinking_tags()` / `_extract_assistant_content()`): the local and cloud response parsers unwrap `reasoning_content`, Ollama-native `thinking`, and `<think>...</think>` tags so thinking models (`gemma4:12b`, DeepSeek-R1) never return empty strings.
- **English-first cognitive mandate** (`LANGUAGE_AND_SYNTAX_MANDATE`): the LLM query/criteria generation prompt enforces strictly formal academic English in `inclusion_criteria` / `exclusion_criteria` and disallows hallucinated prefixes such as `topic:`.

### Changed

- **Provider trimming** (`src/core/ai_manager.py`): cloud providers (Gemini, NVIDIA, Groq, Cerebras, GitHub Models, Mistral, DeepSeek, HuggingFace, OpenRouter) are registered only when their API key is present and non-empty; missing keys are parked silently as `STANDBY_NO_KEY` in a new `provider_status` map instead of generating noisy runtime warning cascades or attempting network connections.
- **Google GenAI GA SDK migration** (`_execute_gemini_request()` / Gemini provider init): Gemini text generation now prefers the `google.genai` GA SDK (`genai_types.GenerateContentConfig`), falling back to the legacy `google.generativeai` path only when the GA SDK is unavailable -- eliminating the end-of-support `FutureWarning` path for new installs.
- **Local GPU baseline** (`config/settings.py`): `LOCAL_GPU_MODEL` now defaults to verified-installed `"llama3.1:8b"` (zero thinking/reasoning overhead) while gracefully accommodating `gemma4:12b` through the parser fix.
- **Version strings synchronized to 5.12.2** across the 6 core code files plus `docker-compose.yml` (`talos:5.12.2`), `CITATION.cff` (version 5.12.2, date-released 2026-09-27), the user-facing strings in `src/utils/tray_icon.py`, `src/utils/evaluation_history.py`, `templates/live_foraging_visualizer.html`, `src/utils/research_setup_wizard.py`, and all 19 canonical documentation files.

### Verification

- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.12.2).
- `python -m pytest tests/test_research_setup_wizard.py -q` passed (28 tests).
- `python src/utils/verify_dependency_map.py --ci` returned exit 0.
- `bash -n run_talos.sh` passed with zero syntax errors.
- Strict UTF-8 decode scan across all modified files: zero U+FFFD replacement glyphs.

## [v5.12.1] - 2026-09-27 -- Research Wizard Query Transparency & CLI Fast-Dispatch Engine

### Added

- **Wizard query-transparency table** (`src/utils/research_setup_wizard.py:_render_query_preview()`): after Step 1 compiles the 16 academic search queries, a rounded Rich Table (`box.ROUNDED`, title "Generated Academic Search Queries") previews the boolean query strings for the top primary sources (arXiv, IEEE Xplore, Scopus (Elsevier), OpenAlex, Semantic Scholar, Springer Link) alongside a summary of the compiled `inclusion_criteria` / `exclusion_criteria`.
- **User confirmation gate** (`_step1_research_topic()`): a Questionary confirmation ("Proceed with these compiled search parameters?", default `True`, `TALOS_QUESTIONARY_STYLE`) is rendered before the parameters are persisted to `config.json`; declining re-enters the research-scope prompt so the researcher can refine the topic, while cancelling aborts without persisting.
- **CLI fast-dispatch engine** (`talos.py:_handle_cli_flags()` / `_cli_help_table()`): lightweight `sys.argv` parsing in `if __name__ == "__main__"` adds `--wizard` (launch `research_setup_wizard.py`), `--daily` (launch `daily_search.py`), `--stats` (launch `db_stats.py`), and `--help` / `-h` (render a Rich flag-reference table). Each flag dispatches through the existing `run_script()` helper and exits cleanly with code 0; no flags preserve the interactive `main_menu()` flow.

### Changed

- **Version strings synchronized to 5.12.1** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata and lifespan startup log, `talos.py` docstring, `run_talos.bat` title/banner/init header/setup log, `run_talos.sh` header/banner/logs, `tests/test_multi_tier.py` version assertion), plus `docker-compose.yml` (`talos:5.12.1`), `CITATION.cff` (version 5.12.1, date-released 2026-09-27), the user-facing strings in `src/utils/tray_icon.py` (`TRAY_TITLE`), `src/utils/evaluation_history.py`, `templates/live_foraging_visualizer.html`, `src/utils/research_setup_wizard.py` (docstring/sentinel/header), and all 19 canonical documentation files.

### Verification

- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.12.1).
- `python talos.py --help` printed the CLI flag table cleanly and exited 0.
- `python src/utils/verify_dependency_map.py --ci` returned exit 0.
- `bash -n run_talos.sh` passed with zero syntax errors.
- Strict UTF-8 decode scan across all modified files: zero U+FFFD replacement glyphs.

## [v5.12.0] - 2026-09-27 -- Research Setup Wizard, Local Cognitive Input Validation with Failsafe Heuristic Bypass & ISO/IEC 25010 Usability Milestone

### Added

- **Research Setup Wizard** (`src/utils/research_setup_wizard.py`): a structured 4-step, English-first onboarding guide. Step 1 captures the research topic and performs local cognitive scope validation via the Fast Edge model (Llama-3.1-8B / Neutrino-8B) with a 2-second timeout and a deterministic rule-based heuristic bypass (minimum 3 words, sub-domain suggestions); Step 2 selects the AI execution strategy (`strict_local` or `local_first`) and writes it into `.env`; Step 3 selects the historical search window (Recent / Standard / Retrospective) and stores it in `config.json`; Step 4 optionally triggers a 10-paper test search, auto-bootstraps the FastAPI server, and opens the 3D visualizer.
- **Local AI runtime auto-spawn** (`_ensure_local_ai_runtime()`): probes ports 11434 (Ollama) and 11435 (Fast Edge) with a 0.8s timeout, silently spawns `ollama serve` when offline, then performs a bounded 2-second wait. When no runtime comes online, the wizard degrades gracefully to pure deterministic heuristics without blocking or crashing.
- **Query & criteria generation** (`_generate_queries_llm()` / `_generate_queries_heuristic()`): reuses `src.ai.llm.query_translator.flatten_json` to compile 16 English academic search queries plus `inclusion_criteria` / `exclusion_criteria`; offline mode applies deterministic English boolean/plain queries.
- **First-run sentinel automation** (`data/.talos_onboarded`): the sentinel is written only after successful completion; `talos.py:main_menu()` auto-invokes the wizard exactly once when the sentinel is absent and fast-boots in under 0.3s when present.
- **TUI integration**: `profile_settings_menu()` gains "2. Run Research Setup Wizard (Interactive Guide)" (subsequent options renumbered 1-10); `_SCRIPT_MAP` registers `research_setup_wizard.py` under `utils`.
- **Hermetic test suite** (`tests/test_research_setup_wizard.py`): covers sentinel detection/creation, cognitive heuristic validation, and strategy/window persistence.

### Changed

- **Version strings synchronized to 5.12.0** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata and lifespan startup log, `talos.py` docstring, `run_talos.bat` title/banner/init header/setup log, `run_talos.sh` header/banner/logs, `tests/test_multi_tier.py` version assertion), plus `docker-compose.yml` (`talos:5.12.0`), `CITATION.cff` (version 5.12.0, date-released 2026-09-27), the user-facing strings in `src/utils/tray_icon.py` (`TRAY_TITLE`), `src/utils/evaluation_history.py`, `templates/live_foraging_visualizer.html`, and all 19 canonical documentation files.
- **Roadmap realignment**: v5.12.0 now holds the Research Setup Wizard & Cognitive Onboarding; DSPy PRISMA shifted to v5.13.0, CORTEX & n8n to v5.14.0, Project ALEXANDRIA to v6.0.0+.

### Verification

- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.12.0).
- `python -m pytest tests/test_research_setup_wizard.py -q` passed.
- `python src/utils/verify_dependency_map.py --ci` returned exit 0.
- `bash -n run_talos.sh` passed with zero syntax errors.
- Strict UTF-8 decode scan across all modified files: zero U+FFFD replacement glyphs.

## [v5.11.3] - 2026-09-26 -- Ecosystem Integrity, Deprecation Elimination & Dependency Alignment

### Added
- **Formal release codification of the 7 pre-demo critical defect fixes** (HOU ICBE 2026): the stability hardening previously shipped as a same-version patch under v5.11.2 is now formally sealed under this release with its own version identity, changelog canon, timeline phase, and capabilities whitepaper section. This release gives the concurrency architecture a permanent, citable version anchor.
- **Ecosystem integrity hardening set** (5 additional fixes): OpenReview V2 `search_notes` dispatch, Fast-Edge (11435) batch circuit breaker, FastAPI lifespan migration with Gemini FutureWarning suppression, multi-path GWO artifact status check, and dependency-map verifier repair with canonical path corrections. Full details in the second Fixed section below.

### Fixed -- Pre-Demo Critical Defect Set (formally codified and re-verified)
1. **Non-blocking SSE event loop** (`src/api/main_api.py:visualizer_sse_stream`, L1340): `await asyncio.to_thread(_visualizer_event_queue.get, True, 1.0)` offloads the blocking queue read to a worker thread, keeping the single uvicorn event loop responsive while `/api/v1/visualizer/stream` clients are connected (previously all other endpoints were starved to roughly 1 Hz in Live SSE mode).
2. **Cached DatabaseManager singleton on visualizer polling** (`main_api.py:get_visualizer_demo_data` L1382, `get_visualizer_state` L1551): `_get_db()` replaces per-request `DatabaseManager(db_path=...)` construction, eliminating per-poll DDL re-runs and full embeddings-table unpickling on every 1-1.5 s poll. Both endpoints bind to the profile database active at server start; restart uvicorn after a mid-session profile switch.
3. **Headless background workers** (`main_api.py:_run_scrape_background` L749, `_run_evaluate_background` L972): `os.environ["TALOS_HEADLESS"] = "1"` is injected at task entry, so local-model connection failures can never reach the interactive `questionary` consent prompt in `AIManager._interactive_cloud_fallback()` from a BackgroundTasks thread.
4. **Scrape task concurrency lock** (`main_api.py` L185, L759, L790): module-level `_scrape_task_lock = threading.Lock()` brackets the process-global `sys.exit` monkey-patch/restore sequence (release inside `finally`), so concurrent scrape triggers serialize instead of permanently corrupting `sys.exit`.
5. **Semantic search bounds clamping** (`src/core/database_manager.py:semantic_search` L342-344): `top_k = min(top_k, len(self._embedding_ids))` with an early `return []` for `top_k <= 0`, preventing `ValueError: kth out of bounds` from `np.argpartition` when the model-filtered embedding count is smaller than the requested top_k.
6. **Visualizer payload guards** (`main_api.py:_record_beam_event` L442-446): the `count` field is cast inside `try/except (TypeError, ValueError)` defaulting to 0; a malformed external POST to `/api/v1/visualizer/events` can no longer trigger an unhandled 500.
7. **GWO progress monitor resilience** (`main_api.py:_run_gwo_background._poll_progress` L872): the history-file read handler is broadened to `except Exception: pass`; structurally unexpected `gwo_history.json` content (mid-write truncation, dict root causing `KeyError` on `history[-1]`) no longer kills the monitor thread.

### Fixed -- Ecosystem Integrity & Dependency Alignment
- **OpenReview V2 API dispatch** (`src/ingestion/openreview_source.py`, new `_query_notes()` helper; call sites in `fetch_new_papers` and `search_papers`): the legacy V1-style `client.get_notes(term=...)` call (unsupported by the V2 `OpenReviewClient`, raising `TypeError`) is replaced by a version-tolerant ladder -- `search_notes(term=...)` when the client exposes it, `get_notes(content={"title": ...})` otherwise, and a bare `get_notes(limit=...)` retry on `TypeError` for mixed client versions. Four new hermetic tests in `tests/test_openreview_source.py` pin the dispatch order, the pagination kwargs pass-through, and the fallback behavior.
- **Fast-Edge batch circuit breaker** (`src/core/ai_manager.py`): new instance memo `AIManager._fast_edge_offline_memo`. Once the CPU edge endpoint (`FAST_EDGE_BASE_URL`, port 11435) fails with a connection error (`ConnectionRefusedError` / `WinError 10061` / `NewConnectionError`, wrapped by `requests.exceptions.ConnectionError`), all subsequent fast-tier calls in the same batch skip the dead endpoint instantly and fall back to local GPU Ollama (port 11434), logging `[INFO] Fast tier (11435) marked offline for current batch. Immediate fallback to local GPU active.` -- no repeated connection timeouts.
- **FastAPI lifespan migration** (`src/api/main_api.py`): the deprecated `@app.on_event("startup")` handler is replaced by a modern `@asynccontextmanager` `lifespan` coroutine passed to `FastAPI(lifespan=...)`; startup warm-up/logging preserved verbatim, shutdown section is an explicit no-op; the `on_event` DeprecationWarning is fully eliminated.
- **Gemini FutureWarning suppression** (`src/core/ai_manager.py:_try_import_genai`): paired module-scoped and message-scoped `warnings.filterwarnings("ignore", category=FutureWarning, ...)` filters installed immediately before the lazy `google.generativeai` import, silencing the end-of-support notice without masking unrelated warnings.
- **GWO status multi-path check** (`talos.py:_show_drl_status`): GWO artifact detection now probes `models/gwo_foraging_hyperparameters.json`, `models/gwo_llm_router_reward_weights.json`, and the legacy `models/gwo_parameters.json`; renders `[bold green]Present[/bold green]` when any exists, else `[yellow]Default Baseline Active[/yellow] [dim](Run Opt 4.6 to tune)[/dim]`; detailed metric rows render only for the foraging artifact and are guarded against mid-write/schema errors.
- **Dependency map verifier repair** (`src/utils/verify_dependency_map.py`): `parse_section_7` now accepts both the English (`Dependency Graph`) and Greek (`Γράφος Εξαρτήσεων`) Section 7 headers -- the verifier parses the Greek master `docs/PROJECT_MAP.md` -- and tolerates language-tagged code fences (` ```text `); `EXTERNAL_PACKAGES` whitelist expanded (`atexit`, `asyncio`, `queue`, `html`, `ctypes`, `win32com`, `win32com.client`, `PIL`, `Pillow`, `pystray`, `urllib3`); stale generated-report footers corrected to `src/utils/verify_dependency_map.py -- TALOS v5.11.3`. `--ci` returns exit 0 again (previously exit 1 with "Could not extract Section 7" plus 12 false missing entries).
- **Canonical path corrections** (`.clinerules`, `docs/SYSTEM_CAPABILITIES_MASTER.md`, `docs/SYSTEM_CAPABILITIES_MASTER.html`): stale `scripts/verify_dependency_map.py` and `scripts/db_stats.py` references corrected to `src/utils/verify_dependency_map.py` and `src/utils/db_stats.py`.

### Changed
- **Version strings synchronized to 5.11.3** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata and lifespan startup log, `talos.py` docstring, `run_talos.bat` title/banner/init header/setup log, `run_talos.sh` header/banner/logs, `tests/test_multi_tier.py` version assertion), plus `docker-compose.yml` (`talos:5.11.3`), `CITATION.cff` (version 5.11.3, date-released 2026-09-26), the user-facing strings in `src/utils/tray_icon.py` (`TRAY_TITLE`), `src/utils/evaluation_history.py`, `templates/live_foraging_visualizer.html`, and all 19 canonical documentation files.
- **`pytest.ini` warning hygiene**: a `filterwarnings` block suppresses the `google.generativeai` end-of-support `FutureWarning` during test-suite runs (pytest overrides import-time warning filters with `simplefilter("always")`); the in-code filters in `_try_import_genai()` continue to cover normal runtime execution.

### Security & IP Protection
- **Relocated SOTA Tech Radar (EN & GR) into `docs/internal/`** to safeguard proprietary architectural roadmaps (PAIR-DRL, Colibrì 2.8T MoE streaming, Laya System 1, Tri-Tier routing, Headroom token compression) from public GitHub exposure. Both `docs/TECH_RADAR.md` and `docs/TECH_RADAR_GR.md` were moved to `docs/internal/` and reclassified as Confidential / Internal.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed with zero `on_event` deprecation warnings (lifespan migration verified).
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.11.3).
- `python -m pytest tests/test_multi_tier.py -q` full multi-tier regression passed.
- `python -m pytest tests/test_openreview_source.py -q` passed (V2 dispatch ladder tests included).
- `python src/utils/verify_dependency_map.py --ci` exited 0 (Section 7 parsed from the Greek master; 0 stale, 0 missing).
- `bash -n run_talos.sh` passed with zero syntax errors.
- Strict UTF-8 decode scan across all modified files: zero U+FFFD replacement glyphs.

## [v5.11.2] - 2026-09-26 -- Zero-Click Windows Pre-Flight Onboarding Wizard & Cross-Platform Packaging

### Added
- **Progress-aware pre-flight onboarding engine** (`run_talos.bat`, new `:AUTO_PREFLIGHT` routine): a five-step guided setup wizard (`[Step 1/5]` through `[Step 5/5]`) that runs automatically on first launch or whenever the environment is incomplete. It prints a reassuring header banner, per-step `[OK]` status ticks, and explicit time estimates so non-technical users never face a blank or frozen console:
  - **Step 1/5 -- Conda runtime check:** if no Conda installation is detected, the wizard downloads Miniconda3 (~85 MB) with `curl.exe -# -fS` (native Windows curl with a live progress bar) and installs it silently via `start /wait` with `/InstallationType=JustMe /RegisterPython=0 /S /D=%USERPROFILE%\miniconda3`. Fatal failures pause with a clear `[ERROR]` message and exit code 1 instead of crashing.
  - **Step 2/5 -- Isolated environment:** verifies or auto-creates the `talosenv` Conda environment (Python 3.11) using `conda info --envs | findstr` detection, then activates it in-session.
  - **Step 3/5 -- Configuration:** initializes `.env` from `example.env` when missing (or creates an empty one as a fallback).
  - **Step 4/5 -- Dependencies:** probes `import questionary, rich, fastapi`; on failure it upgrades pip, installs `requirements.txt` with live output, and runs `src/utils/frontend_provisioner.py`, clearly labelled as a one-time 2-3 minute operation.
  - **Step 5/5 -- Integrity:** final interpreter sanity check and a "100% ready" confirmation before handing off to the main menu.
- **`:DISCOVER_CONDA` subroutine** (`run_talos.bat`): scans the candidate roots (`%USERPROFILE%\miniconda3`, `%USERPROFILE%\anaconda3`, `C:\ProgramData\miniconda3`, `C:\ProgramData\anaconda3`, `%LOCALAPPDATA%\Continuum\anaconda3`) plus PATH (`where conda`) for `condabin\conda.bat`; sets `CONDA_BAT` and `CONDA_ROOT`, and back-fills the legacy `CONDA_ACTIVATE_PATH` (`Scripts\activate.bat`) so the existing `:ACTIVATE_CONDA` routine used by all 10 menu options continues to work unchanged.
- **Silent fast-path bypass gate** (`run_talos.bat` startup): before the wizard, four silent checks run with all output suppressed (`CONDA_BAT` defined, `CONDA_ROOT` defined, `.env` present, `<root>\envs\talosenv\python.exe -c "import questionary, rich, fastapi"` succeeds). When all four pass, the script jumps directly to `:MAIN_MENU` with zero wizard output, keeping daily startup under one second; any failure falls through to the full `:AUTO_PREFLIGHT` wizard.

### Changed
- **Batch hardening:** all literal parentheses inside parenthesized `if`/`else` code blocks are caret-escaped (`^( ... ^)`) to prevent premature block termination; the wizard ends with `goto :EOF` and the caller performs the `goto :MAIN_MENU` jump so the `call` stack stays clean. Strict CRLF line endings preserved (367 CRLF, 0 lone LF verified byte-level).
- **Version strings synchronized to 5.11.2** across the 6 core code files (`config/settings.py` `TALOS_VERSION`, `src/api/main_api.py` FastAPI metadata, `talos.py` docstring, `run_talos.bat` title/banner/setup log, `run_talos.sh` header/banner/logs, `tests/test_multi_tier.py` version assertion), plus `docker-compose.yml` (`talos:5.11.2`), `CITATION.cff` (version 5.11.2, date-released 2026-09-26), the user-facing strings in `src/utils/tray_icon.py` (`TRAY_TITLE`), `src/utils/evaluation_history.py`, `templates/live_foraging_visualizer.html`, and all 19 canonical documentation files.

### Verification
- `python -m compileall -q src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.11.2).
- `bash -n run_talos.sh` passed with zero syntax errors.
- `run_talos.bat` label/jump audit passed (all `call`/`goto` targets resolve); strict CRLF verified with zero lone LF; zero U+FFFD replacement glyphs across all modified files.

## [v5.11.1] - 2026-09-24 -- TUI Sub-Menu Sanitization & Complete Hierarchy Audit

### Fixed
- **Questionary choice-list corruption in `profile_settings_menu()`** (`talos.py`): replaced the string-based `safe_select()` choice list with explicit `questionary.Choice(title=..., value=...)` entries and a dedicated `__back__` sentinel, eliminating the duplication glitch and restoring strictly sequential 1-8 numbering plus a `[ Back / Return to Main Menu ]` option.
- **Routing corrections:** "1. Manage Profiles" dispatches to `run_script("profile_manager.py", ...)` and "5. Model Discovery (Quality Scoring)" to the in-process `_run_model_discovery()` helper (no silent subprocess no-op).

### Changed
- **Unified sub-menu styling:** every sub-menu in `talos.py` (`search_ingestion_menu`, `analysis_visualization_menu`, `drl_gwo_menu`, `database_data_menu`, `system_health_menu`, `author_tools_menu`, `api_keys_menu`) now uses a `[ Back / Return to Main Menu ]` label with clean sequential numbering and the canonical `TALOS_QUESTIONARY_STYLE` theme.
- **Version strings synchronized to 5.11.1** across the 6 core code files, `docker-compose.yml` (`talos:5.11.1`), `CITATION.cff` (date 2026-09-24), and the 19 canonical documentation files.

### Verification
- `python -m compileall -q src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.11.1).
- `bash -n run_talos.sh` passed with zero syntax errors.

### Fixed -- Pre-Demo Stability Hardening Patch (HOU ICBE 2026, same-version patch; no version bump)

- **Non-blocking SSE event loop** (`src/api/main_api.py:visualizer_sse_stream`, L1340): the blocking `_visualizer_event_queue.get(timeout=1.0)` call inside the async SSE generator was replaced with `await asyncio.to_thread(_visualizer_event_queue.get, True, 1.0)`. A connected `/api/v1/visualizer/stream` client no longer monopolizes the single uvicorn event loop (previously every other endpoint was starved to roughly 1 Hz while the visualizer's Live SSE mode was open).
- **Cached DatabaseManager singleton in visualizer polling endpoints** (`main_api.py:get_visualizer_demo_data` L1382, `get_visualizer_state` L1551): per-request `DatabaseManager(db_path=...)` constructions replaced with the cached `_get_db()` singleton, eliminating per-poll DDL re-runs and full embeddings-table unpickling on every 1-1.5 s poll. Operational note: both endpoints now bind to the profile database that was active at server start; restart uvicorn after a mid-session profile switch.
- **Headless background tasks** (`main_api.py:_run_scrape_background` L749, `_run_evaluate_background` L972): both tasks set `os.environ["TALOS_HEADLESS"] = "1"` at entry, so local-model connection failures can never reach the interactive `questionary` consent prompt in `AIManager._interactive_cloud_fallback()` from a BackgroundTasks thread (previously a hang hazard when the server console is a TTY).
- **Scrape task concurrency serialization** (`main_api.py` L185, L759, L790): new module-level `_scrape_task_lock = threading.Lock()`; the process-global `sys.exit` monkey-patch/restore sequence in `_run_scrape_background` is bracketed by `_scrape_task_lock.acquire()`/`release()` (release inside the existing `finally`), so concurrent scrape triggers serialize instead of racing the patch and permanently corrupting `sys.exit`.
- **Semantic search top_k bounds guard** (`src/core/database_manager.py:semantic_search` L342-344): `top_k` clamped to `min(top_k, len(self._embedding_ids))` with an early `return []` for `top_k <= 0`, preventing `ValueError: kth out of bounds` from `np.argpartition` when the model-filtered embedding count is smaller than the requested top_k.
- **Visualizer events payload hardening** (`main_api.py:_record_beam_event` L442-446): the `count` field is cast inside `try/except (TypeError, ValueError)` defaulting to 0; a malformed external POST to `/api/v1/visualizer/events` can no longer trigger an unhandled 500.
- **GWO progress monitor resilience** (`main_api.py:_run_gwo_background._poll_progress` L872): the file-read handler broadened from `except (json.JSONDecodeError, OSError)` to `except Exception`; structurally unexpected `gwo_history.json` content (e.g., a dict root causing `KeyError` on `history[-1]`) no longer kills the monitor thread.

### Verification (hardening patch)
- `python -m compileall -q src/api/main_api.py src/core/database_manager.py src/core/ai_manager.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.11.1).
- Extended regression (`pytest tests/ -k "visualizer or api or synapse"`): 28 passed, 0 failed.
- Runtime smoke checks: `main_api` imports cleanly (visualizer routes and `_scrape_task_lock` present); `semantic_search` verified with 2 embeddings at `top_k=50` and `top_k=0`.

## [v5.11.0] - 2026-09-23 -- Live Telemetry HUD Console, Win32 Close-to-Tray, Cross-Platform Linux Bootstrap & Full-Title History Engine

### Added
- **Live Telemetry HUD Console** (`templates/live_foraging_visualizer.html`): bottom-right glassmorphism stream (rgba(15,23,42,0.85) + backdrop blur + cyan border) with a 40-line ring buffer, auto-scroll, `[ACT]`/`[ROUTER]`/`[DATA]`/`[RECOVERY]`/`[WARNING]`/`[ERROR]`/`[EVAL]` color tags, `C`/`L` hotkey toggles, and automatic hide during PNG SNAPSHOT export.
- **Win32 Close-to-Tray Hook** (`src/utils/tray_icon.py`): `enable_close_to_tray()` subclasses the console window procedure via `ctypes` (GetWindowLongPtrW / SetWindowLongPtrW / CallWindowProcW), intercepting `WM_CLOSE` and `WM_SYSCOMMAND`/`SC_CLOSE` to call `ShowWindow(SW_HIDE)` instead of terminating the daemon; a module-level WNDPROC reference prevents garbage collection.
- **Full-Title & Authors Telemetry** (`src/ai/drl/live_agent_orchestrator.py`): [EVAL] telemetry now renders the complete title (no 55-character truncation) and a normalized author list over a two-line Rich structure; `src/core/ai_manager.py` adds `_sanitize_connection_error()` returning the locale-independent English message "Connection refused: target host or port is offline."
- **Persistent Evaluation History** (`src/utils/evaluation_history.py`): every evaluated paper is appended to `data/history/daemon_evaluations.jsonl` (timestamp, title, authors, source, score, verdict, provider); `talos.py` gains `_show_evaluation_history(limit=30)` (Rich table) surfaced as "View Recent Evaluation History".
- **Autonomous Linux Bootstrap** (`run_talos.sh`): `detect_or_install_conda()` (PATH + standard-directory detection, x86_64/aarch64 silent Miniconda3 download/install) and `ensure_talosenv()` (Python 3.11 `talosenv` create/activate); all menu options 2-9 execute inside `talosenv`.

### Changed
- **Version strings synchronized to 5.11.0** across the 6 core code files, `docker-compose.yml` (`talos:5.11.0`), and `CITATION.cff` (date 2026-09-23).

### Verification
- `python -m compileall -q src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.11.0).
- `bash -n run_talos.sh` passed with zero syntax errors.


## [v5.10.16] - 2026-08-28 -- Zero-Risk Performance Optimization & Academic LaTeX/BibTeX Engine

### Added
- **SQLite WAL Mode & PRAGMA Connection Factory** (`src/core/database_manager.py`): Added private `_apply_pragmas()` and `_connect()` helpers. Every connection now enables `journal_mode=WAL`, `busy_timeout=5000`, `cache_size=-64000`, `synchronous=NORMAL`, and `temp_store=MEMORY`. All 14 connection sites (`execute_query`, `execute_many`, `get_all_papers_for_dashboard`, `get_single_paper_details`, `get_papers_needing_embedding`, `get_all_embeddings`, `get_papers_by_ids`, `get_recent_core_papers`, `get_recent_elite_papers`, `get_embedding_model_stats`, `get_all_papers_as_dataframe`, `get_database_statistics`, `get_papers_for_enrichment`, `update_papers_enrichment_batch`) now route through `self._connect()`, enabling non-blocking concurrent reads between the FastAPI service (port 8001) and the 24/7 daemon.
- **Safe Online Snapshotting** (`src/utils/snapshot_manager.py`): New `snapshot_database()` uses `sqlite3.Connection.backup()` for consistent, timestamped online backups under `_profiles/<active>/backups/` with rolling retention (last 5). Wired immediately before `VACUUM` (`db_stats.py`), bulk re-scoring (`recalculate_scores.py`), and full re-evaluation (`reevaluate_database.py`).
- **HTTP Session Pooling** (`src/utils/http_client.py`): New `build_session()` factory returning a `requests.Session` with `urllib3` `HTTPAdapter` connection pooling and polite headers. Migrated all 13 `requests`-based ingestion sources and the local Ollama/Fast-edge HTTP paths in `AIManager` to persistent sessions (TCP/TLS keep-alive). The three library-client sources (Elsevier, OpenReview, PubMed) retain their native transports.
- **Academic Export Engine** (`src/utils/academic_export.py`): Zero-dependency exporter producing BibTeX (`.bib`) with collision-safe `AuthorYear` keys, publication-ready LaTeX longtables (`.tex`), and PRISMA candidate-set tables. Exposed as option 13 in the Advanced Analysis & Visualizations menu and registered in `_SCRIPT_MAP`.
- **Deterministic LRU Caching**: `@functools.lru_cache` applied to pure helpers -- `estimate_prompt_tokens` (4096), `relative_quality` (32), `detect_protocol` (512), `_sanitize` (1024), `_cloud_key_for` (512), and `_task_type` (32).

### Changed
- **Version strings synchronized to 5.10.16** across the 6 core code files (`config/settings.py`, `src/api/main_api.py`, `talos.py`, `run_talos.bat`, `run_talos.sh`, `tests/test_multi_tier.py`), `docker-compose.yml` (`talos:5.10.16`), and `CITATION.cff`.
- **Test seam adjusted**: `tests/test_openaire_source.py` now patches the source session (`src.session.get`) rather than the module-level `requests.get`, matching the pooled-session migration.

### Verification
- `python -m compileall -q src config tests talos.py` passed.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed (v5.10.16).
- `python -m pytest tests/test_openaire_source.py -q` passed (27 tests).


## [v5.10.15] - 2026-08-28 -- Universal TUI Feature Restoration & 100% Codebase Coverage

### Added
- **Unified 6-Group Hierarchical TUI** (`talos.py`): Reorganized `main_menu()` into six visually-grouped sections using Rich separators and the canonical `TALOS_QUESTIONARY_STYLE` -- (1) Configuration & Profiles, (2) Research Search & Ingestion, (3) Advanced Analysis & Visualizations, (4) DRL Agents, Daemons & GWO Swarm, (5) Database Maintenance & Data Tools, (6) System Health, Diagnostics & CI/CD, plus Exit.
- **Revived Dead Sub-Menus** (`talos.py`): `profile_settings_menu()`, `database_data_menu()`, and `system_health_menu()` reconnected as live, callable handlers from the main menu. New sub-menus `search_ingestion_menu()`, `analysis_visualization_menu()`, and `drl_gwo_menu()` extracted from the former flat menu.
- **100% Executable Module Coverage (45/45)**: Every orphaned module wired into the hierarchy, including Model Discovery (`model_discovery.py`), Model Provisioning (`model_provisioner.py`), GWO LLM Router Reward Shaper (`gwo_llm_router_reward_shaper.py`), Red Tester (`red_tester.py`), Daemon Autostart (`daemon_autostart.py`), and the OPTICA client.
- **GWO Swarm Suite** (`drl_gwo_menu`): Hyperparameter Tuner, LLM Router Reward Shaper, and 3D Swarm Live Dashboard (Dash port 8050) unified under one menu.
- **New Rich Helpers** (`talos.py`): `_show_drl_status()`, `_run_model_discovery()`, `_probe_api_backend()`, `_open_capabilities_viewer()`, `_open_d3_architecture_graph()`, `_launch_gwo_dashboard()`.

### Changed
- **Script Map Hardening**: `_SCRIPT_MAP` extended with six missing modules; `_resolve_script_path()` no longer silently falls back to `scripts/` and now raises a descriptive `FileNotFoundError` for unmapped scripts.
- **DRL Status**: `models/gwo_foraging_hyperparameters.json` inspection consolidated into `_show_drl_status()`.
- **Version strings synced across 6 core code files** (`config/settings.py`, `src/api/main_api.py`, `talos.py`, `run_talos.bat`, `run_talos.sh`, `tests/test_multi_tier.py`) plus `docker-compose.yml` (`talos:5.10.15`) and `CITATION.cff` to v5.10.15.
- **Roadmap re-aligned**: DSPy PRISMA Pipeline shifted to v5.10.16; CORTEX & n8n Gateway shifted to v5.10.17.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed with v5.10.15 assertion.

## [v5.10.14] - 2026-08-28 -- Autonomous Execution Matrix with Privacy Guardrails & DeepSeek V4 Cognitive Integration

### Added
- **Auto-Dynamic Orchestration (2D Execution Matrix 5th Strategy)** (`src/ai/llm/model_manager.py`): `select_execution_mode()` now offers Option 5 -- `auto_dynamic` -- "Autonomous strategy selection with Privacy Guardrails". The TUI table, questionary choices, label map, summary panel, and legacy `.env` compatibility keys were all extended to cover the new strategy.
- **Privacy Guardrail Resolution Engine** (`src/core/ai_manager.py`): `_resolve_strategies(model_type)` now collapses `auto_dynamic` into a concrete strategy at runtime. New private helpers `_is_network_online()`, `_detect_vram_gb()`, `_resolve_auto_dynamic()`, `_prompt_auto_dynamic_consent()`, and `_log_auto_matrix()` implement the deterministic policy: offline -> strict_local; online + non-deep task -> local_first; online + deep task + interactive consent -> cloud_first; refusal/offline -> strict_local; non-interactive -> local_first. A Rich Privacy Safeguard Panel compares Local GPU vs Cloud estimated service times before prompting for consent.
- **DeepSeek V4 Cognitive Integration** (`src/core/ai_manager.py`): `_execute_openai_compatible_request()` now injects `thinking={"type": "enabled"}` and `reasoning_effort="high"` when the provider is `deepseek` and the resolved model name contains `v4`.

### Changed
- **DeepSeek V4 default model** (`config/settings.py`): `DEEPSEEK_MODEL_CHAT` default changed from `deepseek-chat` to `deepseek-v4-pro`; the OpenAI-compatible registry now defaults to the V4 Pro cognitive tier.
- **DeepSeek V4 catalog** (`src/ai/llm/model_manager.py` + `src/ai/llm/model_discovery.py`): `DEEPSEEK_MODELS` now includes `deepseek-v4-pro` and `deepseek-v4-flash`; `DEFAULT_BENCHMARK_MODELS` adds both V4 variants (v4-pro SWE-bench 75.0 / MMLU-Pro 82.0).
- **HARD CONSTRAINT -- strict_local is never overridden**: `_resolve_strategies()` short-circuits `strict_local` before any auto-dynamic or cloud logic.
- **Version strings synced across 6 core code files** (`config/settings.py`, `src/api/main_api.py`, `talos.py`, `run_talos.bat`, `run_talos.sh`, `tests/test_multi_tier.py`) plus `docker-compose.yml` (`talos:5.10.14`) and `CITATION.cff` to v5.10.14.
- **Roadmap re-aligned**: DSPy PRISMA Pipeline shifted to v5.10.15; CORTEX & n8n Gateway shifted to v5.10.16.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed with v5.10.14 assertion.

## [v5.10.13] - 2026-08-28 -- Desktop Control Hub, Self-Healing Infrastructure, Active Profile Persistence & Environment Canon Overhaul

### Added
- **Desktop Control Hub System Tray** (`src/utils/tray_icon.py`): Expanded the pystray companion into a seven-item control surface -- Open 3D Visualizer, Open Reports Folder, Open System Log, Open API Docs (Swagger), Trigger Instant Search Cycle, Show / Hide Console Window, and Terminate Daemon. Tooltip retitled to `"TALOS v5.10.13 | Research Intelligence Mesh"`.
- **Self-Healing Auto-Bootstrap** (`src/utils/tray_icon.py`): New `_is_api_alive(port=8001)` probes `http://127.0.0.1:8001/api/v1/health` with a 0.6s timeout; new `_ensure_api_server()` dynamically locates the project root and spawns `uvicorn src.api.main_api:app --host 127.0.0.1 --port 8001` in a hidden background process (`subprocess.CREATE_NO_WINDOW` on Windows), polling until responsive (up to 3s). The Visualizer, Swagger, and instant-search actions self-heal the backend before opening.
- **Native OS Desktop Bridge** (`src/utils/tray_icon.py`): Cross-platform path openers (`os.startfile` on Windows, `open` on macOS, `xdg-open` on Linux) for the reports folder (`data/reports`) and the system log (`data/logs/talos_system.log`).

### Changed
- **Single Point of Truth Database Persistence (BREAKING)** (`src/core/database_manager.py`): `DatabaseManager.__init__` now defaults `db_path=None` to `get_active_profile_db_path()` (the active profile database at `_profiles/<active>/talos_research.db`). The previous `data/talos_research.db` canonical-priority and legacy `_resolve_profile_db` walk-up logic were removed. Migration: any component that previously relied on the `data/` database must now pass an explicit `db_path`, or the data will land in the active profile database.
- **Bi-directional 4-State Parabolic Telemetry & Synthetic ID Engine** (`src/api/main_api.py` + `src/integration/visualizer_bridge.py`): Documented the 4-state beam bridge (query_out / data_in / evaluation / error) that maps telemetry to per-source health and parabolic quadratic-bezier laser beams, plus the synthetic latest-evaluation override (`_live_eval_seq` / `_live_eval_state`) that mints strictly increasing ids so backlog re-evaluations keep the HUD advancing.
- **OpenAIRE nested XML/JSON title parsing unwrap** (`src/ingestion/openaire_source.py`): `_first()` now unwraps nested `$` / `#text` / `value` dictionary wrappers so a title such as `[{"$": "Some Title"}]` resolves to the plain string; `src/api/main_api.py` additionally strips surviving dict reprs.
- **Zero Emojis Protocol compliance** (`src/utils/db_stats.py`): Replaced emoji glyphs in the console metrics with plain-text bracketed markers (`[PAPERS]`, `[ELITE]`, `[AVG]`, `[OK]`, `[WARN]`, `[EMBED]`) so the statistics report runs on Greek Windows (cp1253) consoles without a UnicodeEncodeError.
- **Professional Environment Configuration redesign** (`example.env` + `.env`): Reconstructed both files into six commented sections -- (1) Execution Matrix & Network Strategy, (2) Local AI Model Tiers, (3) Universal Cloud Mesh (9 providers), (4) 16 Academic Ingestion APIs, (5) Ecosystem Integrations, (6) System Notifications. Existing `.env` secrets preserved verbatim.
- **Version strings synced across 6 core code files** (`config/settings.py`, `src/api/main_api.py`, `talos.py`, `run_talos.bat`, `run_talos.sh`, `tests/test_multi_tier.py`) plus `docker-compose.yml` (`talos:5.10.13`) and `CITATION.cff` to v5.10.13.
- **Roadmap re-aligned**: DSPy PRISMA Pipeline shifted to v5.10.14; CORTEX & n8n Gateway shifted to v5.10.15.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed with v5.10.13 assertion.
- `python src/utils/db_stats.py` confirmed paper counts in the active profile database.

## [v5.10.12] - 2026-08-27 -- Autonomous Daemon Hardening, 3D Laser Telemetry & Interactive Visualizer Tools

### Added
- **3D Animated Laser Beams & Photon Pulses** (`templates/live_foraging_visualizer.html`): `activeBeams` array with additive-blended glowing `THREE.Line` beams and traveling `SphereGeometry(0.12)` photon spheres (Cyan `#00ced1` / Gold `#f59e0b`) animated at 60 FPS; sine-envelope opacity, temporary target-node scale pulse, and aura intensification with full geometry/material disposal on completion.
- **Interactive Visualizer Tools**: raycaster click-to-fire on satellite nodes, SNAPSHOT (PNG download `TALOS_3D_Constellation.png` via `canvas.toDataURL`), FULLSCREEN toggle, THEME (dark / academic print), and a HELP modal with keyboard shortcuts (R/T/F/S/Space/1-3).
- **1000ms Pure AJAX State Poller**: cache-busted `GET /api/v1/visualizer/state?_t=` with strict no-store headers, refreshing all 16 health auras and count badges, and firing beams on new evaluation IDs.
- **SQLite Vacuum Optimizer** (`src/utils/db_stats.py`): `optimize_database(db_path)` running `PRAGMA integrity_check;` + `VACUUM;` with clean console metrics and a `--optimize` CLI flag.
- **System Tray Companion** (`src/utils/tray_icon.py` + `pystray` + `Pillow`): `launch_tray_icon_async()` renders a 16x16 navy/cyan "T" tray icon with Open 3D Visualizer, Show / Hide Console (Win32 `ShowWindow`), and Terminate Daemon actions, running in a non-blocking daemon thread; wired into `talos_service.py` startup with a graceful ImportError fallback.
- **New Console Window Daemon Launch** (`talos.py`): Option 11 now spawns `talos_service.py` via `subprocess.Popen(..., creationflags=subprocess.CREATE_NEW_CONSOLE)` on Windows so the 24/7 daemon owns a dedicated console while the TUI stays interactive.
- **Rich TrueColor DRL Telemetry** (`src/ai/drl/live_agent_orchestrator.py`): `Console(force_terminal=True)` with color-coded `[ACT]`, `[ROUTER]`, `[WARNING]`, `[RECOVERY]`, and `[EVAL]` badges; dynamic status badges `[ELITE  +]` / `[ACCEPT v]` / `[REJECT X]`.

### Changed
- **Version strings synced across 6 core code files** to v5.10.12; Docker image `talos:5.10.12`; CITATION.cff version and date updated.
- **Documentation synced across the canonical file set** to v5.10.12 (2026-08-27).
- **23 FastAPI endpoints** documented (E01-E23) across capabilities and project-map references.
- **Roadmap re-aligned**: DSPy PRISMA Pipeline shifted to v5.10.13; CORTEX & n8n Gateway shifted to v5.10.14.
- **Project Map structural repair**: `docs/PROJECT_MAP.md` and `docs/PROJECT_MAP_EN.md` re-encoded to UTF-8; broken markdown tables, misaligned columns, and corrupted box-drawing glyphs fixed; stale `scripts/` and `app.py` (Streamlit) paths replaced with the current `src/` layout; strict EN/GR parity restored (79 src/ modules, 23 endpoints).

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed with v5.10.12 assertion.

## [v5.10.11] - 2026-08-24 -- Vendored Three.js 3D Knowledge Constellation & Live Telemetry Engine

### Added
- **Vendored Three.js library** (`static/js/three.min.js`): Production-grade Three.js r128 (UMD, MIT license) bundle locally vendored and served from `/static/js/three.min.js` via a new idempotent `app.mount("/static", StaticFiles(directory="static"), name="static")` in `src/api/main_api.py`. Zero external CDN calls, 100% air-gapped compliant.
- **Three.js 3D Knowledge Constellation Visualizer** (`templates/live_foraging_visualizer.html`): Rebuilt from the v5.10.10 raw WebGL 1.0 prototype into a robust Three.js architecture. Features:
  - Dark Slate/Navy (`#0f1117`) background with Academic Print Mode (`renderer.setClearColor(0xffffff)` plus high-contrast white/navy HUD restyling) for publication screenshots.
  - Central gold (`#f39c12`) `THREE.IcosahedronGeometry` wireframe core rotating continuously.
  - 16 cyan (`#00ced1`) `THREE.SphereGeometry` satellite source nodes distributed via Fibonacci spherical coordinates (radius 4.5).
  - Dynamic Health Aura `THREE.Sprite` halos behind each node with soft radial-gradient `CanvasTexture`, color-mapped Green (`#10b981`, Healthy), Amber (`#f59e0b`, Cooldown), Red (`#ef4444`, Error/403), Cyan (`#06b6d4`, Standby).
  - Direct connection lines from the core to all 16 nodes plus a faint nearest-neighbor constellation mesh.
  - Animated energy laser pulse beam from the core to the target source node fading over 1.2 seconds via additive-blended `THREE.Line`.
  - Manual orbit camera controls (left-drag rotate, right-click pan, wheel zoom), THEME toggle, dual-mode switch (Live SSE Stream vs. Conference Offline Replay with Play/Pause and 1x/2x/5x speed), and a glassmorphism HUD card showing normalized title, ELITE/ACCEPT/REJECT score badge, DRL reward, and provider attribution.
- **Resilient live polling bridge**: 1.5-second `GET /api/v1/visualizer/demo-data` polling timer runs alongside the existing `/api/v1/visualizer/stream` SSE channel; new evaluations fire the laser, update the target node aura and counter badge, and refresh the HUD card.

### Changed
- **Version strings synced across 6 code files** (`config/settings.py`, `src/api/main_api.py`, `talos.py`, `run_talos.bat`, `run_talos.sh`, `tests/test_multi_tier.py`) to v5.10.11.
- **Documentation synced across 15 canonical files** to v5.10.11 (2026-08-24).
- **Roadmap re-aligned**: DSPy PRISMA Pipeline shifted to v5.10.12; CORTEX & n8n Gateway shifted to v5.10.13.
- **Legacy WebGL 1.0 visualizer (v5.10.10) documented as superseded** by the production Three.js implementation.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed with v5.10.11 assertion.

## [v5.10.10] - 2026-08-24 -- 3D Holographic Knowledge Constellation & Multi-Pipeline Live Visualizer

### Added
- **3D Holographic Knowledge Constellation Visualizer** (`templates/live_foraging_visualizer.html`): Single-file, air-gapped WebGL 1.0 interactive 3D visualizer with zero external network dependencies. Features: Deep Slate/Navy background (`#0f1117`) with ambient space particle field (800+ particles), IEEE blue (`#006699`) orbital ring grids on 3 inclination planes, rotating gold (`#f39c12`) icosahedron central TALOS core, 16 cyan (`#00ced1`) satellite source nodes positioned on orbital rings, animated energy pulse beams traveling along 3D vectors from core to target source, amber/red pulsating octahedron lockout cages, glassmorphism HUD overlay with real-time evaluation card, interactive camera controls (mouse-drag orbit, mouse-wheel zoom, middle-drag pan, reset view, 2D/3D projection toggle), dual-mode operation (Live SSE Stream vs. Conference Offline Replay), replay controls (Play/Pause, 1x/2x/5x Speed, timeline scrub), and score filter (All/Accepted/Elite).
- **FastAPI Visualizer Endpoints** (`src/api/main_api.py`):
  - `GET /api/v1/visualizer/live`: Serves the standalone visualizer HTML page via `HTMLResponse`.
  - `GET /api/v1/visualizer/stream`: Server-Sent Events (SSE) endpoint pushing live JSON payloads (`paper_evaluated`, `paper_discovered`, `agent_step`, `router_decision`) via `StreamingResponse` with 15-second heartbeat keep-alive.
  - `GET /api/v1/visualizer/demo-data`: Returns the 50 most recently evaluated papers from the database for offline conference replay mode.
  - In-memory `broadcast_visualizer_event()` helper using `queue.Queue` for thread-safe, non-blocking event publication from synchronous pipeline code.
- **Multi-Pipeline Event Hooking**:
  - `src/ingestion/daily_search.py`: Emits `paper_evaluated` events after both Flash pre-screening and Pro deep analysis phases with pipeline labels "Daily Search 16 APIs" and "Daily Search 16 APIs (Deep)".
  - `src/ingestion/historic_search.py`: Emits `paper_evaluated` events after Flash evaluation with pipeline label "Historic Archive Search".
  - `talos.py` `_menu_architecture_graphs()`: New option "3. 3D Knowledge Constellation Visualizer (Browser)" with FastAPI reachability check on port 8001, Rich info panel, and `webbrowser.open()` auto-launch.

### Changed
- **API endpoint count** increased from 19 to 22 total (100% ecosystem coverage + visualizer streaming).
- **Version strings synced across 6 code files** (`config/settings.py`, `src/api/main_api.py`, `talos.py`, `run_talos.bat`, `run_talos.sh`, `tests/test_multi_tier.py`) to v5.10.10.
- **Documentation synced across 15 canonical files** to v5.10.10 (2026-08-24).
- **Academic test suite formalization**: `tests/test_smoke.py` renamed to `tests/test_system_integrity.py`, formally designated the "TALOS Automated System Integrity Verification Suite" (ISO/IEC 25010 compliance) for IEEE publication and HOU ICBE presentation rigor.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest tests/test_system_integrity.py -q` passed.
- `python -m pytest tests/test_multi_tier.py -k test_talos_version` passed with v5.10.10 assertion.
## [v5.10.9] - 2026-08-23 -- Comprehensive TUI Feature Audit & Profile Management Restoration

### Added
- **Hierarchical TUI Refactoring** (`talos.py`): 16-option progressive-disclosure menu across six visual groups replacing the legacy flat menu. Each group opens a dedicated sub-menu with Back-to-Main-Menu navigation and Ctrl+C safety via `safe_select()`/`safe_pause()`.
  - **Core Configuration & Profiles** (Options 1-3): AI Model Manager, Profile Management (Switch/Create/View), Research Focus & Query Translation (PYTHIA/Pivot).
  - **Search & Ingestion Pipelines** (Option 4): Daily Search (16 APIs), Historical Archive Search, Grey Literature Miner, Batch PDF Downloader.
  - **Advanced Analysis & Insights** (Options 5-7): Literature & Scientometric Analysis (Citation Analyzer, Knowledge Path Generator, Recommender, Author Profiler, Trend Analyzer, Interactive Dashboard, DRL Training), Codebase Architecture Graphs (Graphify AST + Legacy D3.js), Data Visualizations (via OPTICA).
  - **Reinforcement Learning & Daemons** (Options 8-12): Autonomous Research Daemon, Live DRL Agent, Autonomous Red Tester, GWO Swarm Optimization (Foraging Tuner, LLM Router Shaper, 3D Live Dashboard), Configure Daemon & OS Autostart.
  - **System, Database & Diagnostics** (Options 13-15): Database Maintenance (Metadata Enrichment, Recalculate Scores, Re-evaluate Database, DB Health Stats), Baseline Reports (Standard/Academic 600 DPI), System Diagnostics (DRL Status, Docs Generator, API Health Check).
- **Profile Management restored as first-class TUI node** (`talos.py` `_manage_profiles()`): Switch active profile, create new profile with PYTHIA setup, view profile info (research goal, config size, database size), save current state to profile. All operations delegate to `src.core.profile_manager` functions.
- **Nine dedicated sub-menu handler functions** in `talos.py`: `_manage_profiles`, `_menu_research_focus`, `_menu_search_ingestion`, `_menu_literature_analysis`, `_menu_architecture_graphs`, `_menu_gwo_suite`, `_menu_database_maintenance`, `_menu_baseline_reports`, `_menu_system_diagnostics`.

### Changed
- **Profile Manager emoji cleanup** (`src/core/profile_manager.py`): All emoji characters in print statements replaced with plain-text bracketed markers (`[SAVED]`, `[LOADED]`, `[NEW]`, `[ACTIVE]`, `[Saving]`, `[Loading]`). Compliance with Constitution I (Zero Emojis Protocol).
- **Unified TUI theme** maintained across all new handlers: every `questionary` prompt in the 9 new sub-menu functions imports and passes `style=TALOS_QUESTIONARY_STYLE` from `src/utils.ui_theme`.
- **DSPy PRISMA pipeline** shifted to v5.10.11. CORTEX & n8n Gateway shifted to v5.10.12.
- **Version strings synced** across 6 code files and 15 canonical documentation files to v5.10.9.
## [v5.10.8] - 2026-08-22 -- Enterprise TUI Overhaul & Academic Aesthetics

### Added
- **Unified Questionary Theme** (`src/utils/ui_theme.py`): New canonical `TALOS_QUESTIONARY_STYLE` module defining the Enterprise TUI "Cyan/Teal & Bright White" palette. Category separators render in bright white (`bold fg:#ffffff`), the question mark in IEEE blue (`bold fg:#4a9eff`), and all selection/pointer/answer accents in cyan/teal (`bold fg:#00ced1`) with `noinherit` to suppress background inversion for publication-ready IEEE screenshots.

### Changed
- **Every interactive prompt themed** -- `talos.py`, `src/ai/llm/model_manager.py`, `src/ai/llm/research_pivot.py`, `src/ai/llm/query_translator.py`, `src/analysis/citation_analyzer.py`, `src/analysis/author_profiler.py`, `src/analysis/knowledge_path_generator.py`, `src/core/profile_manager.py`, `src/core/ai_manager.py`, `src/ai/drl/drl_trainer.py`, `src/ai/drl/talos_service.py`, `src/ingestion/grey_literature_miner.py`, `src/ingestion/metadata_enricher.py`, `src/ingestion/pdf_downloader.py`, `src/utils/generate_docs.py`, `src/utils/migrate_database_schema.py`, `src/utils/recalculate_scores.py`, and `src/utils/reevaluate_database.py` now import and pass `TALOS_QUESTIONARY_STYLE` to every `questionary.select`, `questionary.checkbox`, and `questionary.text` prompt.
- **Header panel border** -- the top-level Rich panel in `talos.py` now uses `border_style="#006699"` (IEEE blue) for an elegant academic frame.
- **DSPy PRISMA pipeline postponed** to v5.10.9 in favor of the Enterprise TUI Overhaul.
- **Version strings synced** across 5 code files and the 15 canonical documentation files to v5.10.8.

## [v5.10.7] - 2026-08-21 -- OPTICA Bridge Integration

### Added
- **OPTICA REST Client** (`src/integration/optica_client.py`): New `OpticaClient` class that lets TALOS act as an API client to the sister Project OPTICA microservice (port 8002), offloading heavy cnsplots/PyVis graphics rendering. `request_plot(plot_type, journal_template)` dynamically resolves the active profile database path via `get_active_profile_db_path()`, builds a `{data_source, plot_type, journal_template, override_params}` payload, POSTs to `{OPTICA_API_BASE}/plot/generate`, and returns graceful error dictionaries on connection failure instead of crashing.
- **Configuration** (`config/settings.py`): New `OPTICA_API_BASE` environment setting defaulting to `http://127.0.0.1:8002/api/v1`, mirrored in `config.template.json` and `example.env`.
- **TUI Entry** (`talos.py`): New "Data Visualizations (via OPTICA)" menu option in the Analysis & Insights group, prompting for plot type (`opex_dashboard` / `semantic_topology`) and journal template (`nature` / `science` / `cell`), then rendering the result in a Rich panel.

### Changed
- **DSPy PRISMA pipeline postponed** to v5.10.8 in favor of the OPTICA Bridge integration.
- Version strings synced across 5 code files and the 15 canonical documentation files to v5.10.7.

## [v5.10.6] - 2026-08-17 -- Daemon OS Autostart & Orchestrator

### Added
- **Daemon OS Autostart Generator** (`src/utils/daemon_autostart.py`): `install_windows_autostart()` generates a boot batch script (`talos_daemon_boot.bat`) and registers a Windows Startup-folder shortcut (pywin32 Shell COM) with a system icon (`shell32.dll, 43`) and minimized window style.
- **Interactive Daemon Pre-Flight** (`talos.py`): new "Configure Daemon & OS Autostart" menu option prompting for the daemon network strategy, target sources, and an optional autostart hook.
- **Daemon Source Injection** (`src/ai/drl/talos_service.py`): `_run_live_search()` reads `daemon_target_sources` from `config.json` and forwards them to `talos_live_agent.py` via `--sources`.

### Changed
- Version strings synced across 5 code files and the 15 canonical documentation files to v5.10.6.

### Fixed
- **Autostart path bug** (`src/utils/daemon_autostart.py`): the generated `talos_daemon_boot.bat` previously called `conda activate talosenv` and bare `python`/`fermion`, which could silently fall back to the system Python (dropping sources and causing a 22-vs-23 tensor mismatch). The script now uses the quoted `sys.executable` absolute path for the daemon and the CPU server, removing the conda dependency.

## [v5.10.5] - 2026-08-15 -- Universal Dynamic Model Provisioner & Self-Healing Redundancy Engine

### Added
- **Universal Dynamic Model Provisioner** (`src/utils/model_provisioner.py`): New `ModelProvisioner` class with deterministic `detect_protocol()` (cloud provider prefixes, Ollama colon, HuggingFace Hub slash), a 3-tier local path resolution cascade (`resolve_local_model_path()`: `FAST_EDGE_MODEL_PATH` then in-tree `models/<sanitized_name>` then network), and `ensure_model_available()` that performs JIT auto-pull for Ollama (`ollama pull`) and HuggingFace Hub (`huggingface_hub.snapshot_download`) with a self-healing fallback that logs `[WARNING] Auto-provisioning failed ... Reverting to baseline model.` and returns `False` without crashing.
- **Standalone CLI** (`python src/utils/model_provisioner.py [--model <name>] [--check-only]`): provisions the default fast edge and heavy models, or audits availability non-mutatingly.
- **SETUP routine integration** (`run_talos.bat` / `run_talos.sh`): step [5/5] now executes the Universal Model Provisioner to auto-provision the default fast edge and heavy models out of the box.
- **Model Manager integration** (`src/ai/llm/model_manager.py`): new `_provision_model()` helper routes uninstalled Ollama and HuggingFace model selections through the provisioner with Rich status feedback.
- **Hermetic tests** (`tests/test_model_provisioner.py`): 22 tests covering protocol detection, path resolution priority, mocked HuggingFace download, mocked Ollama pull, and self-healing fallback.

### Changed
- **Version strings synced across 6 code files and 15 documentation files** to v5.10.5.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest -v` full suite passes (272 tests).
- `python tests/test_smoke.py` passes.
- `python src/utils/verify_dependency_map.py --ci` reports 0 stale and 0 missing dependencies.

## [v5.10.4] - 2026-08-15 -- Dynamic Model Discovery Engine & SYNAPSE Protocol Interoperability

### Added
- **Dynamic Model Discovery Engine** (`src/ai/llm/model_discovery.py`): New `ModelDiscoveryEngine` class that discovers active LLM models across the local Ollama tier (GET /api/tags) and optional cloud providers (NVIDIA NIM, Groq, OpenRouter, Gemini GET /v1/models), with a fully air-gapped fallback to a local JSON benchmark registry at `data/model_benchmarks.json` (raw SWE-bench / MMLU-Pro scores, context windows, pricing tiers; auto-created when absent).
- **Dynamic relative quality scoring** -- `get_normalized_quality_scores()` computes `Q_p = raw_score(p) / max_k(raw_score(k))` over the active model set; `get_provider_quality_scores()` aggregates to provider level for the router.
- **LLM Router dynamic quality integration** (`src/ai/drl/llm_router_subagent.py`): New `refresh_quality_scores()` / `load_quality_scores()` methods let `LLMRouterSubAgent` override the static `PROVIDER_PROFILES` quality signals with discovery-engine Q_p values; `select_provider()` now emits a non-blocking `router_decision` Synapse event.
- **SYNAPSE status endpoint** (`src/api/synapse_routes.py`): New `GET /api/v1/synapse/status` returning bus reachability, queue health (emission counters), supported event types, and subscriber status.
- **New SYNAPSE event types** (`src/integration/synapse_client.py`): `model_discovered` and `router_decision` added to `EventEmitter.VALID_EVENT_TYPES`, plus thread-safe emission statistics (`get_emission_stats()`).
- **Pipeline event emission** (`daily_search.py`, `ai_manager.py`): Non-blocking `router_decision` emission wired into provider routing; `red_tester.py` already emits `agent_episode_end` per cycle.
- **Hermetic tests** (`tests/test_model_discovery.py`): 15 tests covering Ollama/cloud parsing, offline fallback, dynamic quality scoring, provider aggregation, and the status endpoint.

### Changed
- **Version strings synced across 6 code files and 15+ documentation files** to v5.10.4.
- **Endpoint count 18 to 19** with the addition of `GET /api/v1/synapse/status`.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest -v` full suite passes (253+ tests).
- `python tests/test_smoke.py` passes.
- `python src/utils/verify_dependency_map.py --ci` reports 0 stale and 0 missing dependencies.

## [v5.10.3] - 2026-08-14 -- Hierarchical DRL Orchestration (Daemon & Foraging Sub-Agent Integration)

### Added
- **Hierarchical DRL Orchestration**: The `LLMRouterSubAgent` is now invoked directly by the live DRL foraging orchestrator, the 24/7 autonomous research daemon, and the daily/historic search pipelines for optimal provider selection before every paper evaluation.
- **`foraging_evaluation` task modifier** (`src/ai/drl/llm_router_subagent.py`): New routing task type registered in `TASK_MODIFIERS` with `prompt_scale=1.0` and `quality_bias=0.02`, giving foraging evaluations a dedicated signal profile.
- **`estimate_prompt_tokens()`** (`src/ai/drl/llm_router_subagent.py`): Shared four-characters-per-token prompt-length estimator consumed by the orchestrator, daemon, and search pipelines.

### Changed
- **`src/ai/drl/live_agent_orchestrator.py` (v1.3)**: `evaluate_paper()` now consults `ai_manager.router.select_provider(prompt_length, task_type="foraging_evaluation")` before triggering evaluation, logging the routing choice to the console (`[ROUTER]`) and a module logger.
- **`src/ai/drl/talos_service.py` (v2.1)**: The 24/7 daemon now routes every background paper evaluation through `route_daemon_evaluation()`, which queries the `LLMRouterSubAgent` and logs decisions to `data/logs/talos_system.log` under the `[DAEMON/ROUTER]` tag.
- **`src/ingestion/daily_search.py` / `src/ingestion/historic_search.py`**: Added `route_evaluation_provider()`; the two-stage evaluation process (Fast Edge pre-screening via `fast_screening`, Heavy Reasoning deep analysis via `deep_research`) now queries the router for provider selection.
- **Version strings synced across 6 code files and 15 documentation files** to v5.10.3.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- `python -m pytest -v` full suite passes (245+ tests, including the new router pipeline integration tests).
- `python tests/test_smoke.py` passes.
- `python src/utils/verify_dependency_map.py --ci` reports 0 stale and 0 missing dependencies.


## [v5.10.2] - 2026-08-14 -- LLM Router Sub-Agent, Bi-Level GWO Reward Shaping & Interactive 16-Source Checkbox TUI

### Added
- **LLM Router Sub-Agent (`src/ai/drl/llm_router_subagent.py`)**: New `LLMRouterSubAgent` class that selects the optimal active provider for an inference request. Loads reward weights from `models/gwo_llm_router_reward_weights.json` (with fallback to default Pareto weights), evaluates prompt token length, provider rate-limit status, and latency against a static provider profile table, and returns the provider maximizing `R = w_quality * QualityScore - w_latency * LatencyRatio - w_cost * CostRatio - w_penalty * RateLimitPenalty`. Integrated into `AIManager` so cloud/legacy provider selection delegates to the sub-agent.
- **GWO LLM Router Reward Shaper (`src/ai/optimizers/gwo_llm_router_reward_shaper.py`)**: New `GWOLLMRouterRewardShaper` class implementing Bi-Level Multi-Objective Reward Optimization using canonical GWO (Mirjalili 2014). The outer loop runs a wolf pack (alpha/beta/delta) over the continuous 4D hypercube, projecting every candidate onto the simplex (`sum(w) == 1.0`, `w_i >= 0.0`); the inner loop evaluates the LLM Router under the reward shaping function `R = w_quality * QualityScore - w_latency * LatencyRatio - w_cost * CostRatio - w_penalty * RateLimitPenalty`. Exports optimized weights, convergence trajectory, and three Pareto profiles (Deep Research, Fast Screening, Air-Gapped Local) to `models/gwo_llm_router_reward_weights.json`. Standalone CLI: `python src/ai/optimizers/gwo_llm_router_reward_shaper.py [--wolves 10] [--iterations 30]`.
- **Interactive 16-Source Checkbox TUI (`talos.py`)**: Options 3a (Daily Search) and 3b (Historic Search) now prompt a `questionary.checkbox()` listing all 16 registered academic sources (`arxiv`, `ieee`, `semantic_scholar`, `springer`, `openalex`, `dblp`, `elsevier`, `core`, `crossref`, `openarchives`, `pubmed`, `scigov`, `osti`, `plos`, `openreview`, `openaire`), all pre-selected by default. Selected sources are passed to the search scripts via `--sources`.
- **Source filtering (`daily_search.py` / `historic_search.py`)**: Added a canonical `SOURCE_REGISTRY` + `ALL_SOURCE_NAMES` and a `build_sources(config, selected)` helper. Both scripts accept `--sources arxiv ieee ...` (space-separated) to run only the specified sources.
- **Hermetic tests (`tests/test_gwo_llm_router_reward_shaper.py`)**: Six mock-first tests covering simplex projection, deterministic seeding, and JSON export.

### Changed
- **`src/ai/optimizers/gwo_rl_optimizer.py` renamed to `src/ai/optimizers/gwo_foraging_hyperparameter_tuner.py`**: Added the `GWOForagingHyperparameterTuner` class facade while retaining module-level `run_gwo()` and `DEFAULT_RL_EPISODES` for the FastAPI background GWO task. Best-parameters export renamed from `models/gwo_best_params.json` to `models/gwo_foraging_hyperparameters.json`.
- **`src/api/main_api.py`**: GWO import updated to `gwo_foraging_hyperparameter_tuner`; `_run_scrape_background` now forwards `source_filter` into `daily_search.main(source_filter)`; stale "14 sources" references corrected to "16".
- **Version strings synced across 6 code files and 15 documentation files** to v5.10.2.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- Full test suite (including the new GWO reward shaper tests) and smoke test pass.
- Zero emojis protocol strictly enforced; pure Greek unicode maintained in all `_GR.md` files.


## [v5.10.1] - 2026-08-14 -- DRL Environment Scaling & Retraining (17 Action Space)

### Added
- **DRL environment scaling (`src/ai/drl/talos_env.py` v3.2)**: The Gymnasium `TalosEnv` state space was scaled to 23 dimensions -- 1 normalized hour (/24.0) + 16 source usage ratios + 2 streaks (low_score/10, error/10) + 4 provider ratios (gemini, deepseek, huggingface, local). The action space was scaled to 17 actions -- actions 0..15 map to the 16 sources, action 16 is sleep.
- **Canonical 16-source discovery**: `_load_source_list()` now guarantees `openreview` and `openaire` are present (appended if missing) and falls back to the full 16-source `ALL_KNOWN_SOURCES` list when no config is available.
- **DRL environment verification tests (`tests/test_multi_tier.py`)**: New `TestDRLEnvironment` class asserting `TalosEnv` produces a `(23,)` observation shape and a `Discrete(17)` action space, plus `get_default_state_space() == 23` and `get_default_action_space() == 17`.

### Changed
- **`src/ai/drl/drl_agent.py` (v2.1)**: Import-time dimension fallback updated from (6, 4) to (23, 17); `load()` auto-reconstruction documented for the new dimensions.
- **`src/ai/drl/drl_trainer.py` (v1.4)**: GWO-optimized hyperparameters documented (LR=3.361e-05, GAMMA=0.6983, EPS_DECAY=0.9202).
- **`src/ai/drl/live_agent_sources.py` (v1.1)** and **`src/ai/drl/live_agent_orchestrator.py` (v1.2)**: Source mapping and docstrings aligned to 16 sources and the 23-dim state vector.
- **Version strings synced across 6 code files and 15 documentation files** to v5.10.1.

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- Full test suite (including the new DRL environment scaling tests) and smoke test pass.
- Zero emojis protocol strictly enforced; pure Greek unicode maintained in all `_GR.md` files.


## [v5.10.0] - 2026-08-14 -- Academic Ingestion Expansion (OpenReview & OpenAIRE Integration)

### Added
- **OpenReview source (`src/ingestion/openreview.py`)**: New `OpenReviewSource` agent querying the OpenReview API V2 (https://api2.openreview.net) for forum notes. Uses an authenticated `openreview.api.OpenReviewClient` when `OPENREVIEW_USERNAME`/`OPENREVIEW_PASSWORD` are present and falls back gracefully to guest/public notes access otherwise. Maps notes to the standard `{doi, url, title, authors_str, publication_year, abstract, source="OpenReview"}` schema and appends peer-review decisions, ratings, recommendations, and venue metadata to the abstract field.
- **OpenAIRE source (`src/ingestion/openaire.py`)**: New `OpenAIRESource` agent querying the OpenAIRE Research Graph API v11.3.0 (`/search/researchProducts`). Supports the optional `Authorization: Bearer` header when `OPENAIRE_TOKEN` or `OPENAIRE_API_KEY` is present and falls back to public unauthenticated requests. Maps results to the standard schema (`source="OpenAIRE"`) and appends project grant/funding metadata to the abstract field.
- **16-source ingestion**: `daily_search.py` and `historic_search.py` now import and execute both new sources. The daily pipeline also gains `CORESource` (previously imported but never instantiated), restoring the documented 14-source baseline and bringing both pipelines to 16 active sources.
- **Unit tests for the new sources**: `tests/test_openreview_source.py` (13 tests) and `tests/test_openaire_source.py` (21 tests) -- hermetic, mock-first coverage of initialization, content-field extraction, standardized formatting, peer-review/funding enrichment, and graceful degradation.

### Changed
- **`requirements.txt`**: Added `openreview-py` under the Academic APIs section; header bumped to v5.10.0.
- **`example.env`**: Added `OPENREVIEW_USERNAME=`, `OPENREVIEW_PASSWORD=`, `OPENAIRE_TOKEN=`; header bumped to v5.10.0.
- **`config.template.json` / `config.json`**: Added `openreview_query`, `openaire_query`, and `max_results_config` entries (`openreview`, `openaire`).
- **`verify_dependency_map.py`**: Registered the two new source modules in `IMPORT_TO_DOC_MAP`.
- **Global header sweep**: every `Project: TALOS v5.9.18` module docstring synced to `v5.10.0` across 72 files in `src/`, `config/`, and `tests/` -- including the Autonomous Red Tester subsystem (`red_tester.py`, `red_tester_routes.py`, `src/ai/testing/__init__.py`) and user-facing version strings (Red Tester report footer and TUI title, baseline report generator, graphify adapter).

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- Full test suite (225 tests, including 34 new source-agent tests) and smoke test pass.
- Zero emojis protocol strictly enforced; pure Greek unicode maintained in all `_GR.md` files.


## [v5.9.18] - 2026-08-14 -- Universal Cloud Mesh & Multi-Provider Redundancy Expansion

### Added
- **Universal Cloud Mesh (`config/settings.py` + `src/core/ai_manager.py`)**: Expanded the cloud tier from three providers (Gemini, DeepSeek, Hugging Face) to a nine-provider mesh. New OpenAI-compatible providers: NVIDIA NIM (`https://integrate.api.nvidia.com/v1`, `nvidia/nemotron-3-ultra`), Groq (`https://api.groq.com/openai/v1`, `llama-3.3-70b-versatile`), Cerebras (`https://api.cerebras.ai/v1`, `llama-3.1-70b`), GitHub Models (`https://models.inference.ai.azure.com`, `gpt-4o-mini`), Mistral (`https://api.mistral.ai/v1`, `mistral-small-latest`), and OpenRouter (`https://openrouter.ai/api/v1`, `meta-llama/llama-3.3-70b-instruct:free`). Added `TALOS_CLOUD_PROVIDERS` canonical ordering list.
- **OpenAI-compatible provider registry (`OPENAI_COMPATIBLE_REGISTRY`)**: Dictionary-driven initialization in `AIManager` mapping provider name to env key, base URL, default model, and model-override key. Providers without a configured key are skipped gracefully (Constitution II -- cloud is OPTIONAL).
- **Unified request handler (`_execute_openai_compatible_request`)**: Single OpenAI-compatible execution path with independent per-provider circuit breakers (5 consecutive failures = circuit trip) and failure counting via `_handle_failure()`.
- **Model Manager Cloud Configuration TUI**: `select_cloud_models()` overhauled to render a Rich table of all nine providers with columns Provider Name, Env Key, Status (`[ACTIVE]` green / `[UNCONFIGURED]` yellow), Default Model, and Base URL. Any provider can be selected to view details, save its API key to `.env`, or modify its default model. Added `CLOUD_PROVIDER_CATALOG` and pure `get_cloud_provider_rows()` helper.

### Changed
- **`example.env`**: Added `NVIDIA_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `GITHUB_TOKEN`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY` template entries plus default-model overrides; header bumped to v5.9.18.
- **`config.template.json` / `config.json`**: `ai_provider_priority` default list now `["local", "nvidia", "groq", "cerebras", "github", "gemini", "deepseek", "mistral", "openrouter", "huggingface"]`; `failure_threshold` raised to 5.
- **`src/core/ai_manager.py`**: `_execute_cloud_chain()` and `_execute_legacy_request()` now route all non-Gemini providers through the unified handler. `_execute_openai_compatible` and `_execute_deepseek_request` retained as deprecated wrappers.
- **Version strings synced across 6 code files and 15 documentation files** to v5.9.18 (plus a full global header sweep across `src/`, `config/`, and `tests/`).

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- Full test suite (including new Cloud Mesh registry/catalog tests) and smoke test pass.
- Zero emojis protocol strictly enforced; pure Greek unicode maintained in all `_GR.md` files.


## [v5.9.17] - 2026-08-14 -- Universal Rich TUI, Enterprise Logging Upgrade & Global Header Sweep

### Added
- **Enterprise Logging (`src/utils/logger.py`)**: A single `get_logger(name)` factory wiring a `rich.logging.RichHandler` (emoji-free, colorized console output) and a `logging.handlers.RotatingFileHandler` writing to `data/logs/talos_system.log` (10 MB per file, 5 rotating backups) with the academic formatter `%(asctime)s - %(name)s - %(levelname)s - %(message)s`. The `data/logs/` directory is auto-created.

### Changed
- **Universal Rich TUI & Logger Enforcement**: Audited all interactive modules (`talos.py`, `src/ai/llm/model_manager.py`, `src/ai/llm/research_pivot.py`, `src/utils/generate_docs.py`, `src/ai/testing/red_tester.py`). Replaced naked runtime `print()` status/diagnostics with `logger.info/warning/error`; enforced `rich.console.Console` and `rich.panel.Panel` for menus, tables, and panels; kept `questionary` for all data prompts and removed the legacy raw `input()` pause (now `console.input`). Removed all emojis from `research_pivot.py` and translated inline Greek strings in `generate_docs.py` to English.
- **`src/api/main_api.py`**: Migrated the inline `logging.basicConfig` to the enterprise `get_logger("api")`; FastAPI `version="5.9.17"` and startup/description strings updated.
- **Global Header Sweep**: Updated every `Project: TALOS v5.9.15`/`v5.9.16` module docstring to `Project: TALOS v5.9.17` across `src/`, `config/`, and `tests/` (78 files).
- **Docker & Launcher Sweep**: `Dockerfile` and `docker-compose.yml` headers and the `talos:5.9.17` image tag synced; `requirements.txt` header and `docs/DOCKER.md` tags updated; `run_talos.bat` and `run_talos.sh` banners and titles synced.
- **Version strings synced across 5 code files and 15 documentation files** to v5.9.17.
- **`tests/test_multi_tier.py`**: `test_talos_version` assertion updated to "5.9.17".

### Verification
- `python -m compileall src config tests talos.py` passed with zero errors.
- Full test suite and smoke test pass.
- Zero emojis protocol strictly enforced; pure Greek unicode maintained in all `_GR.md` files.


## [v5.9.16] - 2026-08-14 -- Autonomous Red Tester Upgrade (Rename, Deep API Fuzzing & Context Truncation)

### Added
- **Deep API Fuzzing**: The Red Tester now discovers hybrid test arms -- CLI targets plus four API fuzzing arms against the local FastAPI (`POST /api/v1/synapse/webhook` malformed JSON, `GET /api/v1/papers/-999`, `POST /api/v1/search/semantic` empty body, `POST /api/v1/scrape/trigger` invalid source). Graceful rejections (400/404/422) are passes; HTTP 5xx and timeouts are crashes (reward +50).
- **LLM Context Truncation**: Crash error output sent to the Fast Edge LLM is clipped to the last 2,000 characters via `_protect_context_window()`, preventing context window overflow (OOM) on massive stack traces.

### Changed
- **Renamed `autonomous_tester.py` to `red_tester.py`** and `tester_routes.py` to `red_tester_routes.py`. The `run_autonomous_tester()` entry point is now `run_red_tester()`. The endpoint prefix `/api/v1/tester` is preserved for frontend compatibility.
- **Persistence paths renamed**: Q-table `data/red_tester_q_table.json`, reports `data/reports/red_tester/` (existing artifacts migrated).
- **Version strings synced across 5 code files and 15 documentation files** to v5.9.16.
- **`tests/test_multi_tier.py`**: `test_talos_version` assertion updated to "5.9.16".

### Verification
- `python -m compileall` passed on all Python files.
- Full test suite (180+ tests) and smoke test pass.
- Zero emojis protocol strictly enforced across all code and documentation.

## [v5.9.15] - 2026-08-14 -- RL & Daemon Hardening, Zero-Click Model Provisioning, Silent Fast Boot & Dependency Map Reconciliation

### Added
- **`docs/TECH_RADAR_GR.md`**: Complete Greek translation of the Technology Radar and Ecosystem Map, adhering to the pure Greek unicode protocol.
- **Zero-Click Local AI Model Provisioning in Launchers**: Added step [5/5] in `run_talos.bat` and `run_talos.sh` setup pipelines to automatically execute `fermion pull fermionresearch/Neutrino-8B` and `ollama pull qwen2.5:14b` during initial installation.
- **Silent Fast Boot**: Purged the legacy startup model verification (`_verify_local_models` in `talos.py`). The CLI now boots silently and instantly into the Rich dashboard; model inspection and installation are on-demand in Model Manager (Option 1).

### Changed
- **Section 7 Dependency Graph Reconciled** (`docs/PROJECT_MAP.md`, `docs/PROJECT_MAP_EN.md`): Rebuilt the architectural dependency graph using the modern `src.*` Domain-Driven Design package hierarchy, eliminating legacy drift warnings.
- **`verify_dependency_map.py` DDD Reconciliation**: Migrated `IMPORT_TO_DOC_MAP` and `COVERED_BY_PARENT` to `src.*` names and added internal-package classification so `--ci` reports zero missing drift.
- **DRL & Daemon Subsystem Hardened**: Full audit and verification across all 10 RL/Daemon modules (`talos_env.py`, `drl_agent.py`, `drl_networks.py`, `drl_trainer.py`, `live_agent_sources.py`, `live_agent_orchestrator.py`, `talos_live_agent.py`, `talos_service.py`, `gwo_rl_optimizer.py`, `autonomous_tester.py`).
- **Version strings synced across 5 code files and 15 documentation files** to v5.9.15.
- **`tests/test_multi_tier.py`**: `test_talos_version` assertion updated from "5.9.14" to "5.9.15".

### Verification
- `python -m compileall` passed on all Python files.
- Full test suite: 180 passed, 0 failed (`pytest -v`).
- `test_smoke.py`: 445 passed, 0 failed.
- Zero emojis protocol strictly enforced across all code and documentation.

## [v5.9.14] - 2026-08-02 -- Documentation Governance Restructuring

### Added
- **Three-Zone Documentation Architecture**: Created `docs/internal/` for proprietary team documents (API handovers, UX blueprints, IP strategies) and `docs/generated/` for high-volume automated documentation.
- **Gitignore Policies**: Added strict exclusion rules for `.clinerules`, `docs/internal/`, and `docs/generated/` to protect intellectual property and repository size, while keeping canonical public docs (`README`, `CHANGELOG`, `ROADMAP`) tracked.

### Changed
- **Documentation Generator**: Updated `src/utils/generate_docs.py` to output language-specific directories directly into `docs/generated/`.
- **15-File Sync Protocol**: Updated `.clinerules` path definitions to point to the new isolated directory structures.
- **Docker Infrastructure Fix & Usage Reference**: Corrected stale v5.8.2 headers in `Dockerfile`, `docker-compose.yml`, `.dockerignore`, and `example.env` to v5.9.14. Added a `config.json` bootstrap from `config.template.json`, added the `_profiles/` volume, removed the deprecated Compose `version:` key, and defaulted local-model URLs to `host.docker.internal`. Added a comprehensive `docs/DOCKER.md` usage reference and corrected the README Docker instructions.

## [v5.9.13] - 2026-08-02 -- Academic Print Theme (Light Mode) Injection

### Added
- **HTML Post-Processing**: Added `_inject_light_mode_toggle()` to `src/analysis/graphify_adapter.py`. Automatically parses the generated `graph.html` and injects a custom CSS block and UI button to toggle a high-contrast Academic Light Mode for print-ready manuscript screenshots.

## [v5.9.12] - 2026-08-02 -- Graphify Output Path Resolution & Auto-Clustering

### Fixed
- **AST Graph Path Resolution**: Fixed bug where `graphify_adapter.py` searched the project root for `graphify-out/` instead of the specified `target_dir` (e.g., `src/graphify-out/`), ensuring successful transfer to the `data/reports/` directory.

### Added
- **Auto-Clustering Execution**: The adapter now automatically spawns a secondary subprocess running `graphify cluster-only --no-label` upon successful AST extraction, ensuring the generation of `GRAPH_REPORT.md` and community labeling while maintaining offline integrity.

## [v5.9.11] - 2026-08-02 -- Vendored Dependencies Hotfix

### Added
- **AST Dependencies**: Explicitly added `tree-sitter-python` (language grammar) and `rapidfuzz` (entity resolution) to `requirements.txt` to prevent `ModuleNotFoundError` during the Graphify extraction pipeline on fresh deployments.

## [v5.9.10] - 2026-08-02 -- Vendored Graphify AST Integration & Rich Menu Reorganization

### Added
- **Vendored AST Engine**: Cloned the `graphify` repository into `vendor/graphify/` for 100% air-gapped, LLM-free codebase mapping via Abstract Syntax Trees (tree-sitter).
- **Graphify Adapter**: Created `src/analysis/graphify_adapter.py` to dynamically load the vendored package and output structural `graph.json` and `graph.html` artifacts.

### Changed
- **Rich TUI Reorganization**: Redesigned the main `talos.py` menu into 14 options strictly grouped via `rich` panels: [CORE & AI CONFIGURATION], [SEARCH & INGESTION], [ANALYSIS & TOPOLOGIES], [DAEMONS & CI/CD], and [DIAGNOSTICS & EXIT].

## [v5.9.9] - 2026-08-02 -- Report Path Consolidation & Data Directory Isolation

### Changed
- **Global Reports Migration**: Consolidated all 8 analysis scripts in `src/analysis/` to output exclusively to `data/reports/` instead of the project root. Migrated 124 historical reports.
- **Root Cleanup**: Deleted the root `reports/` directory, cementing `data/` as the sole locus for persistent runtime outputs, complying strictly with `.gitignore` policies.

## [v5.9.8] - 2026-08-02 -- Clickable Terminal Hyperlinks & Local-to-Local Fallback

### Added
- **Terminal Hyperlinks**: Introduced `_make_clickable_path()` across `talos.py` and `autonomous_tester.py` to format file outputs as `[link=file:///...]`, enabling direct CTRL+CLICK navigation in VS Code and Windows Terminal.

### Fixed
- **Local Fallback Chain**: Corrected `AIManager` logic where a failed Fast Edge tier (port 11435) would bypass the active local Heavy tier (port 11434). Connection errors now gracefully fallback to local Ollama before attempting cloud protocols.

## [v5.9.7] - 2026-08-01 -- IEEE Computer Society WEIGD Fund Badging

### Added
- **Institutional Recognition**: Embedded official IEEE Computer Society WEIGD Student Support Fund (2026) recognition across the ecosystem.
- **Visual Assets**: Deployed two-tone Rich terminal badges (`#006699` and `#002855`) in `talos.py`, Shields.io badges in Markdown files, and CSS pill badges in `SYSTEM_CAPABILITIES_MASTER.html`.
- **Citation Metadata**: Added grant metadata to `CITATION.cff`.

## [v5.9.6] - 2026-08-01 -- Dynamic Target Discovery

### Added
- **Full-Repo Fuzzing**: Upgraded `autonomous_tester.py` with `_discover_all_python_targets()`. The RL Bandit now dynamically scans the entire `src/` directory, scaling from 4 hardcoded arms to 70+ automated test targets.
- **Q-Table Reconciliation**: Persisted RL states in `data/tester_q_table.json` automatically reconcile with newly discovered files.

## [v5.9.5] - 2026-08-01 -- Silent Synapse Fallback & Non-Blocking CI/CD

### Fixed
- **Console Noise Reduction**: `synapse_client.py` now catches `ConnectionError` and uses `logger.warning()` instead of printing multi-line tracebacks when the port 8000 event bus is offline.
- **Non-Blocking Automation**: `AIManager` enforces `allow_prompt=False` when invoked by the autonomous tester, preventing interactive `(Y/n)` cloud fallback prompts from blocking background CI/CD cycles.

## [v5.9.4] - 2026-08-01 -- Advanced 2D Execution Matrix

### Added
- **2D Routing Strategy**: Implemented `TALOS_NETWORK_STRATEGY` (strict_local, local_first, cloud_first, strict_cloud) and `TALOS_HARDWARE_STRATEGY` (cpu_only, gpu_only, cpu_gpu_split).
- **Master Request Dispatcher**: Overhauled `src/core/ai_manager.py` to interpret the 2D matrix, allowing dynamic fallback chains (e.g., Cloud fails -> route to GPU -> GPU fails -> route to CPU).
- **Interactive Configuration Wizard**: TUI Model Manager now guides users through a two-step strategic selection panel.

## [v5.9.3] - 2026-08-01 -- Conda Environment Detection Hotfix

### Fixed
- **Environment Pathing**: Resolved an issue where `talos.py` displayed `Conda Environment: N/A` when launched directly via Python executables. Implemented robust `sys.prefix` and `sys.base_prefix` resolution.

## [v5.9.2] - 2026-08-01 -- Dynamic Focus Summarization & Interactive Cloud Fallback

### Added
- **LLM Context Summarization**: On startup, if no focus title exists, the Fast Edge LLM processes raw generated queries to automatically construct and display a 6-10 word active research focus title in the header.
- **Interactive Runtime Fallback**: If `AIManager` encounters a connection error to local models during an interactive terminal session, it prompts the user to switch to Cloud execution to prevent data loss.

### Removed
- **Legacy Startup Prompts**: Purged interactive initialization queries ("Local or Cloud?") to enable seamless zero-touch booting.

## [v5.9.1] - 2026-08-01 -- LLM-as-a-Judge Diagnostics

### Added
- **AI Crash Diagnostics**: Integrated `AIManager` into the autonomous tester. When a subprocess crashes, the `stderr` traceback is sent to the Fast Edge Tier (Neutrino-8B) to generate a 2-sentence human-readable debugging diagnosis.

## [v5.9.0] - 2026-08-01 -- Autonomous System Tester (RL Chaos Fuzzer)

### Added
- **RL-Driven Chaos Engineering**: Created `src/ai/testing/autonomous_tester.py`. Utilizes a Non-Stationary Epsilon-Greedy Multi-Armed Bandit algorithm to stress-test system components autonomously via background subprocesses.
- **Fragility Q-Table**: Persists learning weights to `data/tester_q_table.json`, actively prioritizing frequently crashing files.
- **REST API Routes**: Added `src/api/tester_routes.py` exposing `/api/v1/tester/status` and `/reports`.
- **System Launchers**: Option 8 integrated into `talos.py`, `run_talos.bat`, and `run_talos.sh` for automated CI/CD execution.

## [v5.8.9] - 2026-08-01 -- Full Ecosystem Deployment, Multi-Tier LLM, and TUI Dominance

### Added
- **Rich Terminal UI Dashboard**: Complete TUI rebuild in `talos.py` with the `rich` library. Dynamic status table with: Conda environment, API port (8001), Synapse bus (8000), execution mode, active LLM tiers, active research focus.
- **Active Research Focus Display**: `_build_status_table()` reads `user_research_goal` from config.json, truncates to 65 characters, displays in glowing green.
- **Interactive Research Focus View & Rotation**: Option 4 restructured into an interactive workflow with goal preview Panel, Boolean query preview, and a 3-action submenu.
- **Model Manager CLI**: `talos.py` option 1 calls `src.ai.llm.model_manager.main()` directly via import.
- **Native MCP Server**: 4 tools (system_status, semantic_search, paper_details, trigger_scrape) via stdio transport.
- **SYNAPSE Protocol**: Event-driven bus with thread-safe, non-blocking JSON event emission. 6 event types.
- **Multi-Tier LLM Routing Architecture**: Fast Edge (Neutrino-8B), Heavy Reasoning (qwen2.5:14b), Cloud. Three execution modes.
- **POSIX Launcher**: Full parity with run_talos.bat. Automatic environment detection.
- **Automated Batch Runner**: 9-option menu with Auto Conda Detection and Auto Fermion Start.
- **Expanded Test Suite**: 96 unit tests (from 29). `rich` library added.

### Changed
- **Constitution v2.0**: 8-Point Standard: Zero Emojis, 100% Air-Gapped & Local-First, Hardware-Aware VRAM, Strict Linear Execution, Verification-First, 15-File Sync, SYNAPSE Protocol, Code Documentation Standards.
- **Port Reallocation**: Port 8000 -> 8001 for TALOS API. Synapse bus occupies port 8000.
- **Docker Modernization**: python:3.10-slim -> python:3.11-slim. Exposed port 8001. Added HEALTHCHECK.

### Fixed
- **TUI Model Name Display**: Full raw strings instead of truncating via `split(":")`.
- **SQLite Column Mismatch**: 23 values for 22 columns -- fixed.
- **Fast Tier Connection Refused Fallback**: Correctly returns None on connection error.
- **Model Dimension Error**: `drl_agent.py load()` pre-checks dimensions before `load_state_dict()`.
- **Hour Normalization Inconsistency**: `/23.0` -> `/24.0`.
- **8 Broken Source Class Names**: Auto-detection via module scanning.
- **Hardcoded Local Model Verification**: Now reads `LOCAL_MODEL_NAME` from `.env`.
- **Save Path Mismatch**: Unified to `dddqn_trained.pth`.

### Removed
- **Streamlit Fully Deprecated**: `app.py`, `.streamlit/`, `tools/_gui_runner.py`.
- **Tools Folder Cleanup**: `tools/start_talos.bat`, `tools/_bump.py`, `tools/_git_status.ps1`.
- **Obsolete Files**: `talos.bat`, `venv/`, data fixup scripts, `dump.json`.

## [v5.8.8] - 2026-08-01 -- Resilient Ingestion & Elsapy Safeguard

### Added
- **API Dependencies**: Explicitly added `elsapy` and `pyzotero` to `requirements.txt`.

### Fixed
- **Graceful Import Degradation**: Wrapped `elsapy` and `pyzotero` imports in `try/except` blocks inside `elsevier_source.py` and `zotero_connector.py`. The 14-source scraping pipeline no longer crashes (`ModuleNotFoundError`) if specific vendor SDKs are missing, ensuring 100% resilient ingestion.

## [v5.8.7] - 2026-08-01 -- Sub-script Path Audit & Lazy SDK Imports

### Changed
- **Air-Gapped Resilience (Lazy Imports)**: Refactored `src/core/ai_manager.py` to import `google.generativeai` and `openai` lazily. The application boots and operates flawlessly on strictly local tiers without internet or cloud SDK installations.

### Fixed
- **Canonical Configuration Pathing**: Audited 17 standalone scripts across `src/analysis/`, `src/ingestion/`, `src/utils/`, and `src/ai/`. Replaced fragile relative paths (`../../config.json`) with a robust `_P`-based dynamic project root resolution, eliminating `FileNotFoundError` during CLI executions.

## [v5.8.6] - 2026-07-31 -- Enterprise TUI Safety Locks & Navigation Audit

### Added
- **Configuration Safety Locks**: Introduced `_confirm_setting_change()` to display a comparative `rich` panel (Previous Value vs. Proposed Value) requiring explicit user confirmation before writing to `.env`.
- **Navigation Guardrails**: Added explicit `[Cancel / Return to Main Menu]` Sentinel options to all TUI sub-menus preventing user entrapment.

## [v5.8.5] - 2026-07-31 -- Universal TUI Beautification

### Fixed
- **Model Name Parsing**: Resolved a bug in `_build_status_table()` where `split(":")[-1]` caused the Heavy Reasoning Model to display as `"14b"` instead of the full `"qwen2.5:14b"`.

### Changed
- **Sub-menu Aesthetics**: All interactive CLI options, search results, and diagnostic outputs are now wrapped in perfectly formatted `rich.panel.Panel` and `rich.table.Table` objects with zero emojis.

## [v5.8.4] - 2026-07-31 -- Rich TUI Dashboard & Model Manager Integration

### Added
- **Rich Library Integration**: Added `rich` to dependencies. Transformed the basic ASCII CLI into a high-tech, dark-mode Starship Command Dashboard.
- **Unified Menu**: The `model_manager.py` TUI was directly imported and integrated into `talos.py` as Option 1, expanding the main menu to a structured 10-option layout.

## [v5.8.3] - 2026-07-31 -- Zero-Touch Launch Chain Automation

### Added
- **Conda Auto-Detection**: `run_talos.bat` and `run_talos.sh` automatically scan common system paths to locate and activate the Conda/virtualenv silently.
- **Asynchronous Background Spawning**: Master launchers now use `start /min` (Windows) and `&` (POSIX) to spawn the FastAPI and MCP servers silently in the background, allowing seamless "Zero-Touch" UI invocation.

## [v5.8.2] - 2026-07-31 -- Docker Modernization & Workspace Sanitation

### Changed
- **Containerization Upgrade**: Upgraded `Dockerfile` to `python:3.11-slim` targeting port 8001 with native `/api/v1/health` checks.
- **Docker Compose**: Configured `docker-compose.yml` to utilize `host.docker.internal:host-gateway` for seamless access to local Ollama and Neutrino ports. Included persistent volumes for `data/`, `models/`, and `logs/`.

### Removed
- **Legacy Files**: Purged old `talos.bat` and redundant `venv/` artifacts to enforce a pristine project root.

## [v5.8.1] - 2026-07-31 -- Cross-Platform Provisioner Architecture

### Fixed
- **Hardware-Aware Provisioning**: Rewrote `frontend_provisioner.py` with strict architecture parsing (`x64` vs `arm64`) and OS detection (`Windows`, `Darwin`, `Linux`), preventing incorrect cross-platform downloads (e.g., downloading Mac binaries on Windows). Fallbacks stabilized to known v1.9.12 assets.

## [v5.8.0] - 2026-07-31 -- Multi-Tier Execution Modes & 95-Test Suite

### Added
- **Execution Modes**: TUI now supports `Local Air-Gapped`, `Hybrid`, and `Full Cloud` modes.
- **QA Expansion**: Test suite expanded to 95 automated pytest assertions covering the new multi-tier configurations.

## [v5.7.2] - 2026-07-30 -- Pragmatic "Core 5" QA Suite & Anti-Greeklish Audit

### Added
- **Core Verification**: Established the "Core 5" Pytest suite (`test_api_endpoints.py`, `test_database.py`, `test_llm_routing.py`, `test_synapse.py`, `test_smoke.py`).

### Fixed
- **Zero-Greeklish Enforcement**: All `*_GR.md` documents audited to guarantee pure formal academic Greek with proper Unicode accents.

## [v5.7.1] - 2026-07-30 -- Multi-Tier LLM Architecture & Isolated UI Provisioning

### Added
- **Multi-Tier Routing**: Introduced `tier="fast"` (targeting the ultra-compressed Neutrino-8B running on CPU) and `tier="heavy"` (targeting GPU-based local models), optimizing token throughput and VRAM conservation.
- **Interim UI Provisioner**: Created a utility to fetch the Cherry Studio portable release into an isolated, git-ignored `cherry_ui_isolated/` directory, generating its MCP configuration automatically.

## [v5.7.0] - 2026-07-30 -- SYNAPSE Event Bus & Constitution v2.0

### Added
- **Project SYNAPSE Integration**: Developed `src/integration/synapse_client.py` and `synapse_routes.py` enabling JSON-based asynchronous event publishing on port 8000.
- **Constitution v2.0**: Upgraded `.clinerules` to the 8-Point Master Standard (enforcing Linear Execution and the Timeline Tracking system).

### Changed
- **Port Reallocation**: Shifted TALOS FastAPI backend from port 8000 to `8001` to prevent collisions with the central event bus.

## [v5.6.0] - 2026-07-29 -- Streamlit Deprecation & Master Capabilities Documentation

### Added
- **Master Capabilities Record**: Introduced `SYSTEM_CAPABILITIES_MASTER.md` and dynamically served it via FastAPI at `GET /api/v1/capabilities`.
- **12-File Sync Rule**: Hardcoded the mandate to synchronize core architecture documents on every bump.

### Removed
- **Legacy GUI**: Completely eradicated `app.py` and `.streamlit/` as TALOS transitioned to a pure headless backend for React.

## [v5.5.2] - 2026-07-28 -- 100% FastAPI Coverage & DX Routes

### Added
- **Deep Integration Endpoints**: Exposed internal AI tools (`/evaluate`, `/translate-query`, `/authors`, `/recalculate-scores`) as REST endpoints.
- **Developer Experience (DX)**: Added utility endpoints serving `graph.html` and GWO historical metrics directly to the React frontend.

## [v5.5.1] - 2026-07-28 -- Frontend DX Endpoints (GWO History + Architecture Graph)

### Added
- **`GET /api/v1/optimize/gwo/history`** -- Returns GWO optimization history as `List[dict]` for direct consumption by Recharts `<LineChart>`.
- **`GET /api/v1/graph/view`** -- Serves the Alexandria Architecture Dependency Graph as HTML page via `FileResponse`.

## [v5.5.0] - 2026-07-28 -- FastAPI REST API Façade & Database Path Fix

### Added
- **`src/api/main_api.py` v1.0** -- FastAPI Façade Layer with 8 REST endpoints wrapping existing core functions without logic duplication.

### Fixed
- **`src/core/database_manager.py` v5.4.2 -- Database path resolution (CRITICAL)**: Corrected project root resolution, connecting to the populated `data/talos_research.db` instead of empty database.

## [v5.4.1] - 2026-07-28 -- Root Directory Cleanup & Technical Debt Eradication

### Changed
- **Workspace Hygiene**: Relocated miscellaneous development scripts to `tools/` and proprietary planning files to `docs/`. Refined `.gitignore` to protect environment secrets.

## [v5.4.0] - 2026-07-27 -- Domain-Driven Design (DDD) Migration

### Changed
- **Structural Overhaul**: Massive architectural migration of 55+ loose scripts from the root and `scripts/` directories into a formal, production-ready `src/` layout (`api/`, `core/`, `ai/`, `ingestion/`, `analysis/`, `utils/`).

## [v5.3.7] - 2026-07-07 -- GWO v2.0 Hyperparameter Re-Optimization

### Changed
- **`core/drl_agent.py` v2.3**: Updated GWO-optimized hyperparameters: `LR=3.361e-05`, `GAMMA=0.6983`.
- **`scripts/drl_trainer.py` v1.4**: Updated GWO-optimized epsilon decay: `EPS_DECAY=0.9202`.

## [v5.3.6 hotfix] - 2026-07-06 -- Grey Literature Miner Crash Fix (Batch 3)

### Fixed
- **`core/ai_manager.py` v3.8 -- Missing `analyze_generic_text()` (CRITICAL)**: The method was documented in PROJECT_MAP.md and called in TWO places from `grey_literature_miner.py` but had never been implemented.
- **`scripts/grey_literature_miner.py` v2.1**: Adaptive DuckDuckGo import.

## [v5.3.6] - 2026-07-06 -- TUI/CLI Hardening Update (Batch 2 Audit Fixes)

### Fixed
- **`talos.py` v5.3.6**: Fixed duplicate menu option "6.", added `safe_pause()`. `safe_select()` handles KeyboardInterrupt.
- **`scripts/drl_trainer.py` v1.3**: Graceful interrupt with partial model save on Ctrl+C.
- **`scripts/talos_live_agent.py` v3.2**: argparse replaces ad-hoc `sys.argv` scanning.

## [v5.3.5] - 2026-07-06 -- DRL/GWO Scientific Integrity Update (Batch 1)

### Fixed (5 CRITICAL bugs)
- **`scripts/gwo_rl_optimizer.py` v2.0**: `calculate_fitness()` rewritten with training + greedy evaluation phases.
- **`core/talos_env.py` v3.1**: `step()` returns `terminated=False, truncated=True` at 200-step cutoff.
- **`scripts/drl_trainer.py` v1.2**: Fixed fatal `NameError` on `args.episodes` in interactive mode.
- **`core/live_agent_orchestrator.py` v1.1**: `LOW_SCORE_MAX` 20 -> 10.
- **`core/ai_manager.py` v3.7**: `last_provider_used` tracks actual provider.

## [v5.3.4] - 2026-07-05 -- Descriptive Module Names Update

### Changed
- Replaced all mythological code names (APOLLO, CHIRON, ORPHEUS, PYTHIA, etc.) with descriptive academic titles throughout the codebase and documentation.

## [v5.3.3] - 2026-07-05 -- Light-Only Theme & Universal Documentation Update

### Changed
- **`app.py` v5.3.3**: Removed broken dark theme. Hardcoded light-only academic blue/teal palette.
- **`.clinerules` v5.3.3**: Universal progressive documentation rule covering ALL file types.

## [v5.3.2] - 2026-07-05 -- Pluggable Network Architecture Update

### Added
- **`core/drl_networks.py` v1.0**: Dedicated neural network module with `DuelingLSTM` class. Designed for future architecture swapping (Transformer, xLSTM) without touching the agent core.

## [v5.3.1] - 2026-07-05 -- DRL Live Agent & Provider-Aware Orchestration

### Added
- **`core/live_agent_sources.py` v1.0**: Dynamic source discovery with auto-detection of broken class names.
- **`core/live_agent_orchestrator.py` v1.0**: Core orchestration loop with cooldown mechanism, provider-aware state.

## [v5.3.0] - 2026-07-04 -- Multi-Language Documentation Builder

### Added
- **`scripts/generate_docs.py` v2.0**: Completely rewritten — documents the ENTIRE codebase (93+ files) in 18 languages using local Ollama instance only.

## [v5.2.1] - 2026-07-04 -- Academic Conference GUI & DRL Flagship

### Added
- **`templates/gui_theme.css`**: Professional CSS theme with glassmorphism, animations, custom scrollbar.
- **`templates/gui_strings.py`**: Translation dictionary (100+ EN/GR keys) with dynamic `t()`.

## [v5.2.0] - 2026-07-04 -- Onboarding & Dynamic Orchestration

### Added
- **`app.py` v5.2.0**: Onboarding wizard with 4-step guided setup. Research Pivot workflow.
- **`core/talos_env.py` v2.0**: Dynamic N-Source environment supporting all 14 academic APIs dynamically.
- **`core/drl_agent.py` v2.0**: Dynamic agent with metadata-aware save/load.
- **`scripts/research_pivot.py` v1.0**: Automated research direction change workflow.

## [v5.2.0] - 2026-07-04 -- The Live Agent & PDF Downloader

### Added
- **`scripts/talos_live_agent.py` v1.0**: Live DRL inference engine connecting trained agent to real APIs.
- **`scripts/pdf_downloader.py` v2.0**: Multi-threaded batch download with ThreadPoolExecutor, ~10x speedup.

## [v5.1.0] - 2026-07-04 -- DRL Dashboard & TUI/GUI Reorganization

### Added
- **`app.py` -- DRL Agent Dashboard**: Streamlit page showing GWO optimization results, agent training status, reward progression chart.
- **`talos.py` -- DRL Agent Status**: Panel with trained model status + GWO hyperparameters.

## [v5.0.1] - 2026-07-04 -- JSON Export from GWO

### Added
- **`scripts/gwo_rl_optimizer.py`**: Saves best hyperparameters to `models/gwo_best_params.json` after optimization completion.

## [v5.0.0] - 2026-07-03 -- Hybrid Embeddings & Deep RL

### Added (6 Phases, 14 new files, 22 modified)
- **Phase 0**: Multi-Provider Hybrid Embeddings v2 (Ollama + Gemini).
- **Phase 1**: DRL Environment & Agent v1.0 (Gymnasium + Double Dueling DQN with LSTM).
- **Phase 2**: Meta-Optimization & Offline Training (Grey Wolf Optimizer + offline training with real database scores).
- **Phase 4**: Autonomous Service & Notifications (Telegram, Discord, Email).
- **Baseline Report System**: Automated snapshot generator with 4 plots in 300/600 DPI.
- **GPU Acceleration**: RTX 4070 CUDA 12.1, 10x faster training.

## [v4.11.0] - 2026-07-02 -- Project Map & Diagnostics Update

### Added
- **PROJECT_MAP.md**: Complete project map documenting all 55 files, functions, dependencies, database schema.
- **`.clinerules` v5.0.0**: Mandatory PROJECT_MAP.md reading for AI agents.
- **`templates/architecture_graph.html`**: Interactive Cytoscape.js dependency graph with 102 nodes, 318 edges.
- **`scripts/verify_dependency_map.py`**: AST-based verification tool for dependency and function documentation audits.

## [v4.10.1] - 2026-06-30 -- Model Management Update

### Added
- **`scripts/model_manager.py`**: Specialized Model Management TUI with quantization-aware model selection, dynamic discovery from Ollama library, VRAM-fit indicators.
- **`core/hardware.py`**: Quantization size estimation with 30+ quantization types.

## [v4.10.0] - 2026-06-30 -- Zero-Config & Resilience Update

### Added
- **Tiered API Keys Management**: GUI + TUI with 4 sections (Free & Keyless, Premium AI, Academic APIs, Integrations).
- **API Health Check v1.1**: 25 API checks with real-time tqdm progress bar.
- **Smart Ollama Model Selector**: 3-section dropdown (Installed, Ollama Library, BitNet 1-bit).
- **PDF Downloader**: Unpaywall / OpenAlex keyless fallback.
- **System Health Check**: 78 automated checks integrated into GUI and TUI.

## [v4.9.0] - 2026-06-29 -- Streamlit GUI & Quality Update

### Added
- **Streamlit Web GUI (`app.py`)**: Complete replacement of CLI menu with 6-page professional Streamlit interface.
- **Smoke Test Suite (`test_smoke.py`)**: 78 automated checks (syntax, imports, database, AI Manager).

## [v4.8.5] - 2026-06-29 -- Bug Hunt & Quality Update

### Fixed
- 15+ bugs across all modules including elsevier_source, grey_literature_miner, recalculate_scores, metadata_enricher.
- Multi-source metadata enrichment fallback chain (OpenAlex -> Crossref -> DBLP -> Semantic Scholar).
- Recommender threshold raised from 4.0 to 7.0.

## [v4.8.4] - 2026-06-28 -- Multi-Provider & Web Search Update

### Added
- **Hugging Face Provider**: Free cloud inference via OpenAI-compatible unified API.
- **Live Web Search**: DuckDuckGo integration for grey literature mining.
- **`core/hardware.py`**: GPU VRAM detection and smart model recommendation.

## [v4.8.3] - 2026-06-27 -- Secure Local AI & Privacy Update

### Added
- **Model Pre-Verification**: Automatic check and installation of all models on startup.
- **Privacy Guard**: User consent required before any cloud fallback.
- **Bidirectional Fallback**: Local -> Cloud and Cloud -> Local with explicit user approval.

## [v4.8.2] - 2026-06-27 -- Local AI & Resilience Update

### Added
- **Local AI (Ollama) Support**: Full offline operation capability with no cloud dependencies.
- **16 Critical Bug Fixes**: Including db_stats KeyError, source agent crash without API keys, silent paper loss without DOI.

## [v4.8.1] - 2026-05-08 -- Dockerization & Portability Update

### Added
- **Docker Support**: Dockerfile based on python:3.10-slim, docker-compose.yml.
- **1-Click Launcher (Windows)**: start_talos.bat with automated venv creation and dependency installation.

## [v4.8.0] - 2025-12-20 -- Enrichment & Scientometrics Update

### Added
- **Scientometrics Suite (trend_analyzer.py)**: HTML reports with statistical analysis and visualizations (Research Timeline, Quality Landscape, Open Access Landscape, WordCloud, Top Authors).
- **Data Enricher**: Unpaywall API integration for external identifier bridging.
- **9 New Database Columns**: Including oa_pdf_url, openalex_id, pmid, pmcid, oa_status.

## [v4.7.1] - 2025-11-30 -- Performance Update

### Changed
- **pdf_retriever.py**: Rewritten with ThreadPoolExecutor (10-15x faster).

## [v4.7.0] - 2025-11-30 -- PDF Retriever (Ethical Edition)

### Added
- **pdf_retriever.py**: Scans database for DOI-bearing articles, queries Unpaywall API for legal Open Access PDFs.

## [v4.6.0] - 2025-11-30 -- Grey Literature "Horizon Scanning"

### Added
- **oracle_agent.py**: Gemini 2.0 with Google Search Grounding for grey literature discovery.

## [v4.4.0] & [v4.5.0] - 2025-11-30 -- Open Access & Onboarding Update

### Added
- **PLOS Agent**: Public Library of Science API integration.
- **Onboarding Wizard**: Automatic detection of new installations, guided setup.

## [v4.3.1] - 2025-11-30 -- Batch Execution Fix

### Fixed
- **sqlite3.ProgrammingError**: Fixed incorrect number of bindings in batch embedding updates.

## [v4.3.0] - 2025-11-28 -- Soft Shutdown Update

### Added
- **Dashboard Soft Shutdown**: Exit button in dashboard UI returning cleanly to menu.
- **/api/shutdown Endpoint**: Graceful Flask server termination.

## [v4.2.0] - 2025-11-28 -- Pythia Refinement & Architecture Hardening

### Changed
- **AIManager v3.4**: System prompt override capability.
- **AIManager v3.3**: Surgical JSON cleaning mechanism.
- **ArxivSource v3.8**: Config-driven architecture with dynamic query reading.

## [v4.1.0] - 2025-11-28 -- Quad-Layer Architecture & Profile System

### Added
- **Quad-Layer Evaluation Framework**: Extended from 3 to 4 layers (Strategic, Operational, Tactical, Playground).
- **Profile Management System**: Multiple isolated research profiles with independent config and database.

## [v4.0.0] - 2025-11-28 -- Automated Configuration ("Query Translator")

### Added
- **scripts/query_translator.py**: Natural language research goals -> optimized Boolean search queries for 10+ APIs via AI.

## [v3.2.2] - 2025-11-27 -- API Rate Limit Optimization

### Changed
- **Dynamic Rate Limiting**: Added `ai_request_delay` parameter to config.json (default 5 seconds).

## [v3.2.1] - 2025-09-27 -- The "Metrics" Update

### Added
- **scripts/db_stats.py**: Quick database statistics report tool.
- **get_database_statistics**: New method in DatabaseManager.

## [v3.2.0] - 2025-09-27 -- Operation "Genesis"

### Changed
- **Complete Upgrade of All Source Agents**: Standardized output format with guaranteed critical fields (doi, publication_year, authors_str).
- **Improved ElsevierSource Resilience**: Smart enrichment strategy with targeted second API call for missing abstracts.

## [v3.1.1] - 2025-09-27 -- Stability & UX Finalization

### Added
- **Project "APOLLO" (metadata_enricher.py)**: Smart maintenance tool scanning database for incomplete records.
- **Smart Author Identification**: ORCID iD detection, enriched disambiguation with institutional affiliation.

### Fixed
- Terminal compatibility (NoConsoleScreenBufferError), TypeError in author_profiler, FileNotFoundError.

## [v3.0.0] - 2025-09-26 -- Strategic Mentor (Knowledge Path Generator)

### Added
- **scripts/knowledge_path_generator.py**: Natural language dialogue, deep semantic search, K-Means clustering for structured knowledge paths.

## [v2.21.0] - 2025-09-26 -- Reliability Update

### Changed
- **AIManager v3.1**: Redesigned as Model-Independent with native JSON mode and provider-specific Circuit Breakers.
- **BREAKING - JSON Architecture**: All prompts restructured to require strict JSON output.

## [v2.20.1] - 2025-09-24 -- "Smart Target" Selector for Citation Analyzer

### Added
- **Interactive Target Selection**: Two ways to select target paper (manual DOI entry or smart database selection of top-10 recent core papers).

## [v2.20.0] - 2025-09-22 -- Interactive Knowledge Graph ("ORPHEUS")

### Added
- **Citation Analyzer**: DOI -> interactive HTML network graph via pyvis with full interactivity.

## [v2.19.1] - 2025-09-21 -- Trajectory Analyzer Upgrade with AIManager

### Changed
- **AIManager Integration**: Trajectory Analyzer rewritten to use centralized AIManager instead of direct Gemini API calls.

## [v2.19.0] - 2025-09-21 -- Zotero Bridge & "Smart Sync" Update

### Added
- **Zotero Connector**: pyzotero-based Web API synchronization with Pro model upgrade.

## [v2.18.1] - 2025-09-21 -- "Circuit Breaker" Smart Fallback

### Added
- **Circuit Breaker Implementation**: State-aware AIManager with consecutive failure counter, automatic fallback bypass.

## [v2.18.0] - 2025-09-21 -- AI Resilience & Agent Expansion Update

### Added
- **Centralized AI Manager**: Single point of AI execution with automatic Gemini -> DeepSeek fallback.
- **Smart Store-First Strategy**: Pre-screening with Flash model, deep analysis only for elite papers.

## [v2.17.0] - 2025-09-20 -- "Smart Store-First" Strategy & Agent Expansion

### Added
- **PubMed Agent**: Biomedical database integration via pymed.
- **OSTI.gov Agent**: US Department of Energy technical reports access.

## [v2.16.0] - 2025-09-20 -- Health & Government Intel Update

### Added
- **PubMed Agent**: Foundational biomedical research access for bio-inspired algorithms.
- **Science.gov Agent**: US government agency publications access.

## [v2.15.3] - 2025-09-20 -- Semantic Brain (Semantic Search Integration)

### Added
- **Semantic Embeddings Infrastructure**: BLOB column for vector storage, embedding_generator.py for batch creation.
- **Semantic Search Back-end**: Cosine similarity computation with natural language query support.

## [v2.15.2] - 2025-09-19 -- "Article DNA" Visualization

### Added
- **Article DNA Visualization**: Dynamic Tabulator column with color-coded sparkline bar charts for multi-axis scores.

## [v2.15.1] - 2025-09-19 -- Dashboard Refinement ("NAFSIKA")

### Added
- **Smart Filter Buttons**: Predefined filter buttons (Core Papers, Tactical Focus, etc.).
- **Modal Info Card**: Full article details in popup modal via /api/paper/<id> endpoint.

## [v2.15.0] - 2025-09-19 -- Interactive Dashboard ("NAFSIKA")

### Added
- **Interactive Dashboard (interactive_dashboard.py)**: Flask + Tabulator.js web dashboard with real-time database interaction.
- **Persistent "In Zotero" State**: Database column for permanent checkbox state storage.

## [v2.14.0] - 2025-09-17 -- Multi-Axis Evaluation & Interactive Dashboard

### Added
- **Multi-Axis Scoring**: Three independent axes (Tactical, Strategic, Simulation) with weighted overall_score.
- **Interactive Report Dashboard**: DataTables.js integration for dynamic sorting, filtering, and pagination.

## [v2.13.0] - 2025-09-16 -- Scopus Integration & Query Optimization

### Added
- **Full ElsevierSource Activation**: Two-factor authentication (APIKey + Institutional Token) with modern pagination.
- **Strategic Query Optimization**: Boolean logic combining multiple interest pillars per API syntax.

## [v2.12.0] - 2025-09-16 -- Smart Recalibrator & Agent Activation

### Added
- **Smart Recalibrator (reevaluate_database.py)**: Intelligent database re-evaluation with prioritization and batching.
- **OpenArchivesSource Activation**: Greek national aggregator integration with specialized queries.

## [v2.11.1] - 2025-08-31 -- Critical Unicode Fix

### Fixed
- **UnicodeDecodeError**: Upgraded run_script in talos.py for bulletproof encoding with forced UTF-8 environment.

## [v2.11.0] - 2025-08-31 -- Strategic Dossier Update

### Added
- **Author Trajectory Analyzer**: Holistic strategic analysis of researcher's recent work portfolio.
- **Unified "Profiler -> Analyzer" Workflow**: Chained execution with automatic ORCID iD extraction.

## [v2.10.0] - 2025-08-31 -- Unified Profiler Update

### Added
- **Unified Author Profiler**: Three-source strategy (ORCID for identity, OpenAlex for linking, Semantic Scholar for metrics).

## [v2.9.2] - 2025-08-30 -- Transparency & Filtering Optimization

### Changed
- **Full Transparency**: Detailed filtering steps printed for main_search.py.
- **VIP Pass for Titles**: Smart quality control allowing keyword-matched articles without abstracts.

## [v2.9.1] - 2025-08-30 -- Score Storage Bug Fix

### Fixed
- **Structural Restructuring**: extract_relevance_score moved exclusively to database-writing scripts.

## [v2.8.0] - 2025-08-30 -- "Two-Stage Sentinel" Update

### Added
- **Pre-Screening**: Fast initial evaluation using Flash-Lite model.
- **Store-First Strategy**: All pre-screened articles immediately stored.
- **Elite Deep Analysis**: Only high-scoring articles receive Pro model analysis.

## [v2.7.2] - 2025-08-29 -- HTML Layout Perfection

### Fixed
- **recommender.py**: Added `table-layout: fixed;` CSS property for proper column width enforcement.

## [v2.7.1] - 2025-08-29 -- HTML Layout Optimization

### Changed
- **recommender.py**: Specific column widths set for balanced, readable table display.

## [v2.7.0] - 2025-08-29 -- Elegant & Concise Reports

### Changed
- **Markdown Export Redesign**: Structured, condensed format with headings and callouts.
- **DOCX Export Redesign**: Elegant portrait document with headings and paragraphs instead of tables.

## [v2.6.1] - 2025-08-29 -- DOCX Export Fix

### Fixed
- **XML Sanitization**: Removed incompatible characters for proper Word document saving.

## [v2.6.0] - 2025-08-29 -- The Scribe Update

### Added
- **Microsoft Word (.docx) Export**: Full report export to formatted Word document.
- **Markdown (.md) Export**: Report export ready for Obsidian import.

## [v2.5.1] - 2025-08-29 -- HTML Encoding Fix

### Fixed
- **recommender.py**: Added `<meta charset="UTF-8">` for proper Greek character display.

## [v2.5.0] - 2025-08-28 -- The Keystone Update

### Added
- **Crossref API Integration**: Access to central metadata database covering all major publishers.

## [v2.4.0] - 2025-08-28 -- The Profiler Update

### Added
- **Author Profiler (author_profiler.py)**: Scopus Author Profile API integration for researcher metrics.

## [v2.3.0] - 2025-08-28 -- The Elsevier Integration

### Added
- **Elsevier Scopus Integration**: elsapy-based Scopus Search API agent.

## [v2.2.0] - 2025-08-28 -- Automatic Cluster Naming

### Added
- **TF-IDF Keyword Extraction**: Automatic extraction of top 4 representative keywords per cluster as dynamic titles.

## [v2.1.0] - 2025-08-28 -- Smart "Reading Path"

### Added
- **Strategic Recommender Upgrade**: Elite filtering for foundational papers, dedicated "State-of-the-Art" category.

## [v2.0.0] - 2025-08-27 -- The Pantheon Update

### Added
- **DBLP Integration**: High-quality Computer Science bibliography database.
- **CORE Integration**: Aggregator containing millions of open-access articles.

## [v1.11.0] - 2025-08-28 -- Perfection & Stabilization

### Added
- **Smart Launcher**: Automatic Python executable detection via sys.executable.
- **Bulletproof Score Extraction**: Multiple regex strategies for score parsing.

## [v1.10.0] - 2025-08-28 -- OpenAlex Integration

### Added
- **OpenAlex Agent**: Full pagination support, inverted index abstract reconstruction.

## [v1.9.0] - 2025-08-28 -- Semantic Scholar Upgrade

### Changed
- **Direct API Calls**: Replaced semanticscholar library with direct requests for absolute control.

## [v1.8.0] - 2025-08-28 -- Springer Upgrade

### Changed
- **Pagination Addition**: Springer agent rewritten for 100-result pagination with rate limit handling.

## [v1.7.1] - 2025-08-27 -- Flexible Parameterization

### Changed
- **Flexible days_to_search**: Separate parameters for daily and historic search.
- **Enhanced arxiv_query**: Combined category and full-text search.

## [v1.7.0] - 2025-08-27 -- Limits Optimization & Flash-Lite Adoption

### Changed
- **Per-Source Limits**: Individual result limits configurable via max_results_config.
- **gemini-2.5-flash-lite**: Adopted for historic search leveraging 1000+ requests/day free tier.

## [v1.6.0] - 2025-08-27 -- Critical Bug Fix

### Fixed
- **Score Storage**: extract_relevance_score moved from recommender to database-writing scripts.

## [v1.5.0] - 2025-08-27 -- Encyclopedic Documentation

### Added
- **CHANGELOG.md**: Project history documentation file.
- **Comprehensive README.md**: Complete rewrite as hyper-detailed encyclopedic manual.

## [v1.4.0] - 2025-08-27 -- Reports & Strategy

### Added
- **Strategic Reading Path**: Recommender upgrade with foundational-then-specialized article suggestions.
- **Report Export**: CSV and HTML report export to reports/ directory.

## [v1.3.0] - 2025-08-27 -- The Control Center

### Added
- **Project Named "TALOS"**: Official project name adopted.
- **talos.py**: Central interactive terminal menu as launcher for all functionality.
- **Gemini Model Auto-Selection**: Config-based model selection (Pro/Flash) for daily vs historic search.

## [v1.2.0] - 2025-08-27 -- The Memory

### Added
- **SQLite Database Integration**: Local database (research_bot.db) with duplicate avoidance.

## [v1.1.0] - 2025-08-27 -- The Polyphony

### Added
- **Multi-Source Support**: Object-oriented rewrite with dedicated source agents (ArXiv, Semantic Scholar, IEEE, Springer).
- **Deduplication**: Logic for removing duplicate articles across multiple sources.

## [v1.0.0] - 2025-08-27 -- The Genesis

### Added
- **Initial Creation**: Simple script querying arXiv, evaluating abstracts via Gemini AI, sending Discord notifications via Webhook.