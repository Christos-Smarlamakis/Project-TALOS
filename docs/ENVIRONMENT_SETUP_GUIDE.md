# Environment & Credentials Setup Guide

**Project TALOS v5.13.1 -- Canonical English Reference**

> **Scope:** This document is the authoritative, single reference for configuring
> the TALOS environment surface. It covers the strict decoupling between
> `config/settings.py`, `.env`, and `config.json`; the local Ollama runtime; the
> Universal Cloud AI Mesh; the academic literature ingestion APIs; and the
> network/port strategy matrix.
>
> **Audience:** Principal Systems Architect, Lead DevOps, and Academic Principal
> Investigator.
>
> **Last Updated:** 2026-09-28

---

## Section 1: Security & Architecture (The .env vs settings.py Decoupling)

TALOS enforces a strict three-way separation of configuration concerns so that
secrets never enter the source tree and local (air-gapped) operation never
depends on a credential.

| Surface | Role | Secrets allowed? | Committed to Git? |
|---------|------|------------------|-------------------|
| `config/settings.py` | Canonical schema and defaults. Reads `os.getenv(KEY, DEFAULT)`. | **No** | Yes |
| `.env` | Runtime secrets and operator overrides (API keys, tokens, webhooks). | **Yes** | **No** (gitignored) |
| `config.json` | Non-secret behavioral config (queries, prompts, rate limits, `mailto`, `auto_start_local_llm`). | **No** | Yes |
| `example.env` | Annotated, zero-secret template for onboarding. | **No** | Yes |

**Zero-git-leak principles:**

1. Every secret is read at runtime through `os.getenv(...)` with an empty-string
   default. A missing key degrades gracefully (the provider parks itself in
   `STANDBY_NO_KEY`), never crashes.
2. `.env` is excluded from version control. `example.env` contains **no real
   credentials** -- only keys, blank values, and registration URLs.
3. API keys MUST **never** be committed to Git and MUST **never** be hardcoded in
   `settings.py` or `config.json`. If a key is ever exposed, rotate it immediately
   at the provider console.
4. In CI/CD and container contexts, inject secrets via the environment or a
   secrets manager. The Docker image is self-contained and contains no keys.
5. **Unquoted string convention:** `load_dotenv` does not strip quotes. Write
   `TALOS_NETWORK_STRATEGY=local_first`, **not** `"local_first"`. A stray pair of
   quotes becomes part of the value and breaks equality checks.

---

## Section 2: Local AI Runtime Setup (Zero-Key, Zero-Internet)

The local tier is the **primary and default** inference surface. It requires
**zero API keys** and **zero internet access** when `TALOS_USE_LOCAL=1`.

| Endpoint | Port | Role | Env key | Default model |
|----------|------|------|---------|---------------|
| Ollama (GPU) | `11434` | Heavy reasoning tier | `OLLAMA_BASE_URL` | `qwen2.5:14b` (`HEAVY_REASONING_MODEL`) |
| CPU Edge | `11435` | Fast pre-screening tier | `FAST_EDGE_BASE_URL` | `fermionresearch/Neutrino-8B` (`FAST_EDGE_MODEL`) |

**Verified local models:**

- `llama3.1:8b` -- preferred GPU chat model (`LOCAL_GPU_MODEL`, `LOCAL_MODEL_NAME`). Zero thinking overhead, fast and deterministic.
- `qwen2.5:14b` -- heavy reasoning model for deep analysis and synthesis.
- `gemma3:12b` -- legacy alternate local model name (the historical default).
- `nomic-embed-text` -- embedding model for semantic search vectors (`LOCAL_EMBEDDING_MODEL`).

**Provisioning (one-time):**

```bash
ollama pull llama3.1:8b
ollama pull qwen2.5:14b
ollama pull nomic-embed-text
```

**Relevant environment variables:**

| Env key | Default | Purpose |
|---------|---------|---------|
| `LOCAL_GPU_MODEL` | `llama3.1:8b` | Local GPU chat model |
| `LOCAL_MODEL_NAME` | `gemma3:12b` | Legacy alias consumed by `ai_manager` init |
| `LOCAL_MODEL_BASE_URL` | `http://127.0.0.1:11434/v1` | OpenAI-compatible local endpoint (derived from `OLLAMA_BASE_URL` + `/v1`) |
| `HEAVY_REASONING_MODEL` | `qwen2.5:14b` | Heavy tier model |
| `FAST_EDGE_MODEL` | `fermionresearch/Neutrino-8B` | Fast CPU edge model |
| `FAST_EDGE_BASE_URL` | `http://127.0.0.1:11435/v1` | CPU edge endpoint |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Standard Ollama endpoint (no trailing `/v1`) |
| `LOCAL_EMBEDDING_MODEL` | `nomic-embed-text` | Semantic search embedding model |
| `TALOS_USE_LOCAL` | `1` | Air-gapped switch (`1` disables cloud) |
| `TALOS_DEFAULT_TIER` | `fast` | Default request tier (`fast` / `heavy`) |

**Auto-start of the local runtime:** the `auto_start_local_llm` boolean lives in
`config.json` (not `.env`). When the runtime is offline, `AIManager` probes
`http://127.0.0.1:11434/api/tags`, and (when `auto_start_local_llm` is `true`)
spawns `ollama serve` detached before degrading gracefully.

## Section 3: Universal Cloud AI Mesh

The cloud tier provides optional redundancy and failover. It is **never required**
for local operation. TALOS enumerates the providers declared in
`OPENAI_COMPATIBLE_REGISTRY` (`src/core/ai_manager.py`) and parks any provider
whose key is absent. The canonical ordering list is `TALOS_CLOUD_PROVIDERS`.

Nine providers are wired in this release: **Gemini, DeepSeek, HuggingFace,
NVIDIA NIM, Groq, Cerebras, GitHub Models, Mistral, and OpenRouter**.

| Provider | Env key (secret) | Model env key | Base URL | Key source |
|----------|------------------|---------------|----------|------------|
| Google Gemini | `GEMINI_API_KEY` | `GEMINI_FLASH_MODEL` / `GEMINI_PRO_MODEL` | (Google GenAI SDK) | https://aistudio.google.com/apikey -- Free tier |
| DeepSeek | `DEEPSEEK_API_KEY` | `DEEPSEEK_MODEL_CHAT` | `https://api.deepseek.com/v1` | https://platform.deepseek.com -- high-reasoning economy |
| HuggingFace | `HF_TOKEN` | `HF_MODEL_NAME` | `https://router.huggingface.co/hf-inference/v1` | https://huggingface.co/settings/tokens |
| NVIDIA NIM | `NVIDIA_API_KEY` | `NVIDIA_DEFAULT_MODEL` | `https://integrate.api.nvidia.com/v1` | https://build.nvidia.com |
| Groq | `GROQ_API_KEY` | `GROQ_DEFAULT_MODEL` | `https://api.groq.com/openai/v1` | https://console.groq.com/keys |
| Cerebras | `CEREBRAS_API_KEY` | `CEREBRAS_DEFAULT_MODEL` | `https://api.cerebras.ai/v1` | https://cloud.cerebras.ai |
| GitHub Models | `GITHUB_TOKEN` | `GITHUB_MODELS_DEFAULT_MODEL` | `https://models.inference.ai.azure.com` | https://github.com/settings/tokens (PAT) |
| Mistral | `MISTRAL_API_KEY` | `MISTRAL_DEFAULT_MODEL` | `https://api.mistral.ai/v1` | https://console.mistral.ai |
| OpenRouter | `OPENROUTER_API_KEY` | `OPENROUTER_DEFAULT_MODEL` | `https://openrouter.ai/api/v1` | https://openrouter.ai/keys |

**Provider selection:** `TALOS_CLOUD_PROVIDER` (default `gemini`) selects the
primary cloud provider; the remaining providers act as a failover cascade.
Gemini uses the Google Generative AI SDK; all other providers use the unified
OpenAI-compatible request path.

**Forward-compatibility note:** OpenAI and Anthropic are listed in the canonical
cloud mesh roadmap but are **not yet wired** as first-class providers in this
release. No `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable is
consumed by the current codebase.

## Section 4: Academic Literature Ingestion APIs

TALOS ingests from sixteen source agents (`src/ingestion/*_source.py`). Sources
are categorized by credential requirement.

### Category A -- Zero-Key Open APIs

These sources require **no API key**. Some use the `mailto` field from
`config.json` to join the polite pool (recommended, not mandatory).

| Source | Module | Notes |
|--------|--------|-------|
| arXiv | `arxiv_source.py` | Open arXiv API, no key |
| OpenAlex | `openalex_source.py` | Uses `config.json` `mailto` (polite pool) |
| DBLP | `dblp_source.py` | Open bibliographic API |
| PubMed | `pubmed_source.py` | NCBI E-utilities; uses `mailto` |
| Science.gov | `scigov_source.py` | Federated search, no key |
| OSTI | `osti_source.py` | DOE Office of Scientific and Technical Information |
| PLOS | `plos_source.py` | PLOS Search API, no key |
| OpenReview V2 | `openreview_source.py` | Optional `OPENREVIEW_USERNAME` / `OPENREVIEW_PASSWORD` |
| OpenArchives (EADD) | `openarchives_source.py` | Hellenic academic repositories |
| Crossref | `crossref_source.py` | Uses `config.json` `mailto` (polite pool) |
| OpenAIRE | `openaire_source.py` | Optional `OPENAIRE_TOKEN` |

### Category B -- Free Developer Registration

| Provider | Env key | Registration | Rate-limit notes |
|----------|---------|--------------|------------------|
| Semantic Scholar | `SEMANTIC_SCHOLAR_API_KEY` | https://www.semanticscholar.org/product/api#api-key-form | Higher throughput than anonymous (100 req / 5 min unauth) |
| CORE | `CORE_API_KEY` | https://core.ac.uk/services/api | Authenticated access to full-text metadata |
| Crossref | `mailto` in `config.json` | https://www.crossref.org | The `mailto` email joins the polite pool |
| Springer Nature | `SPRINGER_API_KEY` | https://dev.springernature.com | Free developer tier |

### Category C -- Institutional / Subscription

| Provider | Env key | Guidance |
|----------|---------|----------|
| IEEE Xplore | `IEEE_API_KEY` | https://developer.ieee.org -- institutional or developer key |
| Elsevier Scopus | `ELSEVIER_API_KEY` **and** `ELSEVIER_INST_TOKEN` | https://dev.elsevier.com -- obtain via institutional proxy (e.g. HEAL-Link for Greek universities); the insttoken is required alongside the API key |

**Naming note:** Scopus credentials are exposed as `ELSEVIER_API_KEY` /
`ELSEVIER_INST_TOKEN` (there is no `SCOPUS_API_KEY`/`SCOPUS_INST_TOKEN` in this
release). Crossref uses the `mailto` field of `config.json` (there is no
`CROSSREF_MAILTO` environment variable).

**Auxiliary integration keys:**

| Key | Purpose |
|-----|---------|
| `ORCID_CLIENT_ID` / `ORCID_CLIENT_SECRET` | Author identity resolution |
| `ZOTERO_API_KEY` / `ZOTERO_USER_ID` | Zotero reference manager bridge |
| `OPENAIRE_TOKEN` | Authenticated OpenAIRE calls |
| `UNPAYWALL_EMAIL` / `MAILTO` | Unpaywall open-access PDF lookup (falls back to `config.json` `mailto`) |

## Section 5: Network Strategies & Port Mappings

### The 2D Execution Matrix

TALOS v5.9.4 replaced the legacy `TALOS_EXECUTION_MODE` with a two-axis matrix:
`TALOS_NETWORK_STRATEGY` (where inference is routed) and
`TALOS_HARDWARE_STRATEGY` (which local device is used).

**`TALOS_NETWORK_STRATEGY` values:**

| Value | Behavior |
|-------|----------|
| `strict_local` | Air-gapped. All inference via local tiers only; cloud is never called. |
| `local_first` | Local tiers primary; automatic cloud fallback on connection error. |
| `cloud_first` | Cloud primary; automatic local fallback on auth/rate/timeout error. |
| `strict_cloud` | Pure cloud; local tiers are never called. Requires valid cloud keys. |
| `auto_dynamic` | Autonomous Execution Matrix (v5.10.14): resolves at runtime to `strict_local` / `local_first` / `cloud_first` from connectivity, VRAM, task type, and Privacy Guardrail consent. `strict_local` is never overridden. |

**`TALOS_HARDWARE_STRATEGY` values:** `cpu_only` (all local requests to port
`11435`), `gpu_only` (all local requests to port `11434`), `cpu_gpu_split`
(default: fast on CPU, heavy on GPU).

### Why `strict_cloud` preserves GPU VRAM

In `strict_cloud`, the local Ollama tiers are never initialized for inference.
This leaves **100% of GPU VRAM** free for external deep-learning workloads that
are run alongside TALOS -- for example Spatio-Temporal Graph Neural Networks
(ST-GNNs) and Heterogeneous Multi-Agent Deep Reinforcement Learning (HMADRL)
training. The CPU Edge tier also remains idle, so the host's accelerator is fully
reserved for the researcher's own PyTorch/CUDA jobs.

### Port map

| Port | Service |
|------|---------|
| `8001` | TALOS FastAPI backend and TUI API surface |
| `8000` | SYNAPSE event bus (sister microservice) |
| `11434` | Ollama GPU (heavy reasoning tier) |
| `11435` | Ollama CPU Edge (fast tier) |
| `8002` | OPTICA bridge (visualization microservice) |
| `5002` | Legacy `talos_service_api` status endpoint |

### System & ecosystem variables

| Env key | Default | Purpose |
|---------|---------|---------|
| `SYNAPSE_BUS_URL` | `http://localhost:8000/api/v1/events` | Outbound SYNAPSE events |
| `OPTICA_API_BASE` | `http://127.0.0.1:8002/api/v1` | OPTICA visualization bridge |
| `TALOS_API_PORT` | `8001` | TALOS FastAPI port |
| `TALOS_ALLOW_CLOUD_FALLBACK` | `0` | Explicit cloud-fallback gate |

---

## Appendix: Consolidated Variable Reference

See `example.env` for the fully annotated, unquoted production template. The
canonical defaults are defined in `config/settings.py`; behavioral (non-secret)
settings such as `mailto`, `provider_limits`, and `auto_start_local_llm` live in
`config.json`.



