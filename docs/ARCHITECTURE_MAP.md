# TALOS Functional Architecture Map

> **Project:** TALOS v5.21.0 -- Cognitive Mesh Extraction-Ready In-Tree Microservice & Autonomous LLM Scavenger Agent (ISO/IEC 25010 Compliant)
> **Classification:** Public Technical Reference
> **Last Updated:** 2026-10-03
> **Standard:** ISO/IEC 25010 (Functional Suitability, Performance Efficiency, Maintainability)

---

## 1. Overview

This document decomposes the TALOS codebase into six functional zones according to
ISO/IEC 25010 quality characteristics. Each zone is described in terms of its
constituting scripts, the input contracts it accepts, the output artifacts it
produces, and the communication edges that bind it to neighbouring zones.

The six zones are:

1. **Entrypoints & Orchestration** -- the human and machine-facing surfaces.
2. **Scientific Ingestion & Harvesting** -- the academic source mesh and PDF pipeline.
3. **PRISMA-ScR & Quality Auditing** -- scientific rigor and synthesis.
4. **Scientific Search & Retrieval** -- full-text, vector, code, and citation search.
5. **AI Core & Cognitive Routing** -- the unified `src/services/cognitive_mesh/` microservice (provider registry, cognitive meta-router, benchmark client, autonomous scavenger, dual reporter) (extraction-ready).
6. **Reinforcement Learning & ATHENA Engine** -- the autonomous decision layer.

Zone 5 is explicitly flagged as **extraction-ready**: its unified package
(`src/services/cognitive_mesh/`) imports only `config.settings`, the standard library,
Pydantic v2 DTOs, and (in `server.py`) FastAPI, carrying zero SQLite WAL, PRISMA, or CLI
dependencies. In v6.0.0, Zone 5 is slated for extraction into a standalone SYNAPSE
(:8000) microservice shared between TALOS and MEMEX.

---

## 2. Zone 1 -- Entrypoints & Orchestration

**Role.** The outer shell of the system: command-line, desktop, and HTTP surfaces
through which operators and downstream services invoke every lower zone.

| Script | Purpose | Input Contract | Output Artifact |
|--------|---------|----------------|-----------------|
| `talos.py` | Interactive Rich TUI (6-group menu) and CLI fast-dispatch flags | `sys.argv` flags; active profile `config.json` | Terminal dashboard, subprocess dispatch to `src/` entrypoints |
| `src/api/main_api.py` | Headless FastAPI facade (25 endpoints) on port 8001 | REST/JSON requests; Pydantic v2 bodies | JSON responses, background task statuses, HTML viewers |
| `run_talos.bat` / `run_talos.sh` | Platform launchers for the TUI and FastAPI server | None (operator-invoked) | Console session on port 8001 (FastAPI) |
| `src/utils/desktop_shortcut.py` | One-click Windows desktop launcher provisioner | None | `.lnk` shortcut targeting `talos.py` |

**Inter-zone communication.** Zone 1 delegates to Zones 2, 3, 4, 5, and 6 by importing
their modules or spawning their `main()` entrypoints in-process. It never reimplements
domain logic; it only routes.

---

## 3. Zone 2 -- Scientific Ingestion & Harvesting

**Role.** Acquire candidate literature from 18 academic sources, deduplicate it, and
resolve legal full-text PDFs for the quality and search layers.

| Script / Package | Purpose | Input Contract | Output Artifact |
|------------------|---------|----------------|-----------------|
| `src/ingestion/resilient_gateway.py` | Self-healing wrapper over all 18 source adapters with fast-fail circuit breaking (401/403/quota) and OpenAlex mirroring | Per-source queries from `config.json` | Unified paper records `{doi, url, title, authors_str, publication_year, abstract, source}` |
| `src/ingestion/daily_search.py` | Concurrent daily harvest + Tier-1/Tier-2 evaluation | Source list, LLM provider routing | SQLite `papers` rows with scores and evidence quadrant |
| `src/ingestion/historic_search.py` | Deep archive window crawl | `--days` window, source list | Back-filled `papers` rows |
| `src/ingestion/pdf_harvester/` | 13-source legal Open Access resolver cascade (arXiv, TechRxiv, HAL, NTRS, PMC, Unpaywall, OpenAlex, Semantic Scholar, CORE, Crossref OA, SSRN) | `doi` / `title` / `url` | `data/fulltext_cache/*.pdf` with SHA-256 and magic-bytes validation |
| `src/ingestion/section_extractor.py` | Smart section slicing of cached PDFs | Local PDF path | Methodology / Experiments / Code / Limitations text windows |

**Inter-zone communication.** Zone 2 writes paper records into SQLite (consumed by
Zones 3 and 4) and cached PDF bodies into `data/fulltext_cache/` (indexed by Zone 4).
It requests LLM evaluation through Zone 5 via `AIManager`.

---

## 4. Zone 3 -- PRISMA-ScR & Quality Auditing

**Role.** Apply Kitchenham (2007) scientific quality appraisal, PRISMA-ScR systematic
review synthesis, and forensic multi-auditor consensus to the candidate corpus.

| Script | Purpose | Input Contract | Output Artifact |
|--------|---------|----------------|-----------------|
| `src/prisma/signatures.py` | DSPy signature definitions for relevance and rigor | Typed input/output fields | DSPy signature objects |
| `src/prisma/pipeline.py` | Declarative PRISMA-ScR synthesis pipeline | Candidate paper set, profile prompts | Structured synthesis document |
| `src/prisma/swarm_evaluators.py` | Specialized evaluator skills for the consensus swarm | Paper record + skill context | Per-auditor verdicts |
| `src/prisma/quality_swarm.py` | Tier-2 forensic quality swarm (4 auditors + Fleiss kappa) | Candidate papers, compiled skills | Consensus `S_qual` with inter-auditor agreement |
| `src/prisma/quality_appraisal.py` | Kitchenham 2007 six-question rubric + 2D evidence quadrant | Candidate papers | `quality_score`, `quality_rubric_json`, `evidence_quadrant` |
| `src/prisma/scoping_review_synthesizer.py` | LaTeX synthesis of the scoping review | Filtered, appraised corpus | LaTeX-ready synthesis report |

**Inter-zone communication.** Zone 3 reads the SQLite corpus from Zone 2, requests LLM
reasoning from Zone 5 (REASONING_RIGOR routing to DeepSeek / Anthropic / SambaNova), and
writes quality fields back into `papers` for export by Zone 1 and search by Zone 4.

---

## 5. Zone 4 -- Scientific Search & Retrieval

**Role.** Provide four complementary retrieval paradigms over the corpus and its
full-text cache.

| Script | Purpose | Input Contract | Output Artifact |
|--------|---------|----------------|-----------------|
| `src/search/fulltext_search.py` | SQLite FTS5 + BM25 search over cached PDF bodies | Query string | Ranked, snippet-highlighted matches |
| `src/search/neural_vector_search.py` | Cosine-similarity semantic search over `nomic-embed-text` embeddings | Query string | Semantic ranking report |
| `src/search/citation_snowballing.py` | Backward/forward citation genealogy | Seed DOI / title / DB id | Snowballing graph report |
| `src/search/code_first_search.py` | Reproducible code-first discovery (GitHub / PapersWithCode) | Query string | Code-first ranking report |

**Inter-zone communication.** Zone 4 reads SQLite + embeddings from the storage layer,
full-text from Zone 2's PDF cache, and embedding vectors produced via Zone 5's vector
embedding model (`nomic-embed-text`).

---

## 6. Zone 5 -- AI Core & Cognitive Routing (Extraction-Ready)

**Role.** The decoupled cognitive layer, now unified under the in-tree
extraction-ready microservice `src/services/cognitive_mesh/`, plus hardware-aware model
budgeting and profile management.

| Script | Purpose | Input Contract | Output Artifact |
|--------|---------|----------------|-----------------|
| `src/services/cognitive_mesh/dto.py` | Standalone Pydantic v2 schemas (`RoutingStrategy`, `RouterTaskRequest`, `ScavengedModel`, `MarketIntelligenceReport`) | Typed task/market payloads | Validated DTOs |
| `src/services/cognitive_mesh/registry.py` | 16-provider adapter registry (Open-Closed) with `LLMProvider` enum and `get_available_providers()` | Environment API keys | `ProviderDescriptor` catalogue |
| `src/services/cognitive_mesh/router.py` | Decoupled `CognitiveMetaRouter` with 4 strategies, circuit breaker, quota latching, `Semaphore(2)` | `RouterTaskRequest` DTO | `RouterTaskResponse` DTO |
| `src/services/cognitive_mesh/benchmarks.py` | `ModelBenchmarkClient` with cached benchmark store and `get_top_models_by_role()` | `data/cache/llm_benchmarks.json` | Four-role top-model pairing |
| `src/services/cognitive_mesh/scavenger.py` | `ModelScavengerAgent` foraging Hugging Face / OpenRouter / Ollama with hardware-aware VRAM classifier | Live catalogues + cached benchmarks | `MarketIntelligenceReport` |
| `src/services/cognitive_mesh/reporter.py` | `IntelligenceReporter` rendering dual Markdown/HTML deliverables | `MarketIntelligenceReport` | `llm_market_intelligence_*.md` / `.html` |
| `src/services/cognitive_mesh/server.py` | FastAPI mini-application (port 8003) mounting `/dispatch`, `/providers`, `/benchmarks`, `/scavenge`, `/health` | HTTP requests | JSON responses |
| `src/services/cognitive_mesh/client.py` | `CognitiveMeshClient` high-level facade (in-process and HTTP) | `RouterTaskRequest` | `RouterTaskResponse` |
| `src/core/hardware_advisor.py` | VRAM parameter budget + 4-role SOTA matcher | GPU/CPU telemetry | Recommended model stack |
| `src/core/profile_manager.py` | Isolated profile workspaces under `_profiles/<name>/` | Profile name | Per-profile `config.json` + SQLite |
| `src/core/ai_manager.py` | Multi-provider LLM executor (Gemini/DeepSeek/Ollama + cloud mesh) | Prompt, tier, provider priority | Text/JSON/embedding completions |

**Extraction-ready guarantee.** The `src/services/cognitive_mesh/` package imports only
`config.settings`, the standard library, Pydantic v2 DTOs, and (in `server.py`) FastAPI --
never SQLite WAL storage, PRISMA pipelines, or CLI scripts. Backward-compatible shims in
`src/core/` (`provider_registry.py`, `cognitive_router.py`, `model_benchmark_client.py`)
re-export the canonical API. The package can therefore be lifted into a standalone
SYNAPSE (:8000) microservice serving both TALOS and MEMEX in v6.0.0.

**Inter-zone communication.** Zone 5 serves every other zone: Zone 2 (screening),
Zone 3 (rigor audits), Zone 4 (embeddings), and Zone 6 (RL reward inference). The
Cognitive Mesh FastAPI router is additionally mounted in `main_api.py` under
`/api/v1/cognitive`.

---

## 7. Zone 6 -- Reinforcement Learning & ATHENA Engine

**Role.** The autonomous decision layer: a Dueling DDDQN agent that orchestrates source
selection, provider routing, and evaluation cadence under CJCSI 3160.01A constraints.

| Script / Asset | Purpose | Input Contract | Output Artifact |
|----------------|---------|----------------|-----------------|
| `src/ai/drl/agent.py` | Dueling DDDQN agent (LSTM state encoder) | 25-dimensional state vector | Action distribution (19 actions) |
| `src/ai/drl/environment.py` | Mission-planning environment and reward shaping | Agent action | Scalar reward, next state |
| `models/dddqn_trained.pth` | Trained DDDQN checkpoint (Net2Net-expanded) | PyTorch runtime | Loaded policy weights |

**Inter-zone communication.** Zone 6 drives Zone 2 (source selection), requests
inference from Zone 5 (via the LLM Router Sub-Agent), and is supervised by Zone 1
(daemon/service lifecycle) and Zone 3 (quality feedback shaping the reward signal).

---

## 8. Inter-Zone Communication Matrix

| From \ To | Zone 1 | Zone 2 | Zone 3 | Zone 4 | Zone 5 | Zone 6 |
|-----------|:------:|:------:|:------:|:------:|:------:|:------:|
| Zone 1    |  --    | invoke | invoke | invoke | import | daemon |
| Zone 2    | report |  --    | write DB | write cache | request LLM |  --   |
| Zone 3    | export | read DB |  --     |  --    | request LLM | reward |
| Zone 4    | render | read cache |  --  |  --    | embed |  --   |
| Zone 5    |  --    |  --    |  --    |  --    |  --   |  --   |
| Zone 6    |  --    | select |  --    |  --    | request LLM |  --  |

---

## 9. Data Flow Summary

1. **Operator -> Zone 1** issues a command (`--daily`, `--prisma`, `--search`, or a TUI selection).
2. **Zone 1 -> Zone 2** triggers ingestion; Zone 2 harvests 18 sources and resolves full-text PDFs.
3. **Zone 2 -> Zone 5** requests screening; Zone 5 routes via the Cognitive Meta-Router.
4. **Zone 2 -> Zone 3** escalates candidates; Zone 3 appraises quality and synthesizes the review.
5. **Zone 3/4 -> Zone 5** request rigor audits and embeddings; results persist to SQLite and the vector store.
6. **Zone 6** orchestrates the above autonomously under mission constraints, with Zone 5 serving reward inference.



