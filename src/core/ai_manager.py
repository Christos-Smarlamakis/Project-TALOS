# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software...
#
"""
Module: ai_manager.py (v3.9 - Universal Cloud Mesh & 2D Execution Matrix)
Project: TALOS v5.10.4

Description:
    Centralized AI provider manager implementing a multi-provider architecture
    with automatic fallback and independent circuit breakers. Orchestrates all
    LLM interactions across a Universal Cloud Mesh of nine providers (v5.9.18)
    and embeddings across three providers:

    - Gemini (Google Generative AI SDK) -- non-OpenAI-compatible path
    - NVIDIA NIM, Groq, Cerebras, GitHub Models, Mistral, OpenRouter,
      DeepSeek, Hugging Face -- OpenAI-compatible cloud providers, driven by a
      unified dictionary registry (OPENAI_COMPATIBLE_REGISTRY)
    - Local (Ollama) -- offline operation via OpenAI-compatible API

    Supports JSON mode, text generation, and HYBRID embedding generation with
    automatic failover across Ollama -> HuggingFace -> Gemini.

    v5.9.18: Universal Cloud Mesh -- cloud providers are initialized from a
    single registry and routed through _execute_openai_compatible_request().
    The failover chain iterates provider_priority, skipping open circuits and
    unconfigured providers, with 5 consecutive failures tripping a circuit.

    v5.9.4: Introduces the 2D Execution Matrix for routing:
      - Network Strategy (strict_local | local_first | cloud_first | strict_cloud)
        controls local-to-cloud fallback behavior.
      - Hardware Strategy (cpu_only | gpu_only | cpu_gpu_split) controls how
        local requests are distributed across CPU and GPU endpoints.
      - Automatic cross-environment fallback: transparently reroutes failed
        requests to the alternative environment with [WARNING] logging.
    Falls back to legacy TALOS_EXECUTION_MODE / per-tier routing if the new
    strategy variables are not set.
"""

import os, json, re, requests, sys
from dotenv import load_dotenv
from typing import Union, List, Dict, Any, Tuple, Optional
import numpy as np

# -- v5.9.18: Universal Cloud Mesh provider metadata (single source of truth) --
from config.settings import (
    NVIDIA_BASE_URL, NVIDIA_DEFAULT_MODEL,
    GROQ_BASE_URL, GROQ_DEFAULT_MODEL,
    CEREBRAS_BASE_URL, CEREBRAS_DEFAULT_MODEL,
    GITHUB_MODELS_BASE_URL, GITHUB_MODELS_DEFAULT_MODEL,
    MISTRAL_BASE_URL, MISTRAL_DEFAULT_MODEL,
    OPENROUTER_BASE_URL, OPENROUTER_DEFAULT_MODEL,
    DEEPSEEK_BASE_URL, DEEPSEEK_MODEL_CHAT,
    HF_BASE_URL, HF_MODEL_NAME,
)

# -- Lazy SDK imports (Constitution II: cloud providers are OPTIONAL) --
# All SDKs are loaded only when their provider is configured and needed.
# The module itself must be importable without any cloud SDK installed.

# OpenAI SDK (v1.x) -- used by DeepSeek, HuggingFace, and local Ollama providers
_openai: Optional[Any] = None
_openai_available: bool = False
_openai_import_error: Optional[str] = None

def _try_import_openai() -> bool:
    """Lazy-import openai (v1.x SDK). Returns True on success."""
    global _openai, _openai_available, _openai_import_error
    if _openai_available:
        return True
    try:
        import openai
        _openai = openai
        _openai_available = True
        return True
    except ImportError as e:
        _openai_import_error = str(e)
        return False

# Google Generative AI SDK (v1) -- used by Gemini text generation
_genai: Optional[Any] = None
_genai_available: bool = False
_genai_import_error: Optional[str] = None

def _try_import_genai() -> bool:
    """Lazy-import google.generativeai (v1 SDK). Returns True on success."""
    global _genai, _genai_available, _genai_import_error
    if _genai_available:
        return True
    try:
        import google.generativeai as genai
        _genai = genai
        _genai_available = True
        return True
    except ImportError as e:
        _genai_import_error = str(e)
        return False

# New GA Gemini SDK for embeddings (replaces deprecated embed_content on v1beta)
try:
    from google import genai as genai_client
    from google.genai import types as genai_types
    _GENAI_V2 = True
except ImportError:
    _GENAI_V2 = False


# -- v5.9.18: Universal Cloud Mesh -- OpenAI-compatible provider registry --
# Maps provider name to metadata: environment key name, base URL, default model,
# and the environment key used to override the default model. Gemini is absent
# because it uses the Google Generative AI SDK (non-OpenAI-compatible path).
OPENAI_COMPATIBLE_REGISTRY = {
    "nvidia": {
        "env_key": "NVIDIA_API_KEY",
        "base_url": NVIDIA_BASE_URL,
        "default_model": NVIDIA_DEFAULT_MODEL,
        "model_env_key": "NVIDIA_DEFAULT_MODEL",
    },
    "groq": {
        "env_key": "GROQ_API_KEY",
        "base_url": GROQ_BASE_URL,
        "default_model": GROQ_DEFAULT_MODEL,
        "model_env_key": "GROQ_DEFAULT_MODEL",
    },
    "cerebras": {
        "env_key": "CEREBRAS_API_KEY",
        "base_url": CEREBRAS_BASE_URL,
        "default_model": CEREBRAS_DEFAULT_MODEL,
        "model_env_key": "CEREBRAS_DEFAULT_MODEL",
    },
    "github": {
        "env_key": "GITHUB_TOKEN",
        "base_url": GITHUB_MODELS_BASE_URL,
        "default_model": GITHUB_MODELS_DEFAULT_MODEL,
        "model_env_key": "GITHUB_MODELS_DEFAULT_MODEL",
    },
    "mistral": {
        "env_key": "MISTRAL_API_KEY",
        "base_url": MISTRAL_BASE_URL,
        "default_model": MISTRAL_DEFAULT_MODEL,
        "model_env_key": "MISTRAL_DEFAULT_MODEL",
    },
    "openrouter": {
        "env_key": "OPENROUTER_API_KEY",
        "base_url": OPENROUTER_BASE_URL,
        "default_model": OPENROUTER_DEFAULT_MODEL,
        "model_env_key": "OPENROUTER_DEFAULT_MODEL",
    },
    "deepseek": {
        "env_key": "DEEPSEEK_API_KEY",
        "base_url": DEEPSEEK_BASE_URL,
        "default_model": DEEPSEEK_MODEL_CHAT,
        "model_env_key": "DEEPSEEK_MODEL_CHAT",
    },
    "huggingface": {
        "env_key": "HF_TOKEN",
        "base_url": HF_BASE_URL,
        "default_model": HF_MODEL_NAME,
        "model_env_key": "HF_MODEL_NAME",
    },
}


class AIManager:
    """Manages all LLM and embedding interactions with multi-provider fallback
    and circuit breaker pattern.

    Embedding providers tried in order:
        local (Ollama) -> huggingface (free) -> gemini

    The active embedding model name is stored in ``self.active_embedding_model``
    and returned alongside vectors so the database can tag each record.

    Attributes:
        providers (dict): Initialized provider configurations keyed by name.
        provider_priority (list): Ordered list of provider names to try.
        FAILURE_THRESHOLD (int): Consecutive failures before circuit opens.
        active_embedding_model (str): Name of the embedding model that
            successfully generated vectors, or ``None``.
    """

    def __init__(self, config: Dict[str, Any]):
        load_dotenv()
        self.config = config
        self.providers = {}
        self.provider_priority = config.get("ai_provider_priority", ["gemini", "deepseek"])
        self.active_embedding_model = None  # set after first successful embedding generation
        self.last_provider_used = None
        # -- v5.10.2: LLM Router Sub-Agent (provider selection delegate) --
        self.router = self._init_router()

        # --- Gemini Provider ---
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key and _try_import_genai():
            _genai.configure(api_key=gemini_api_key)
            self.providers['gemini'] = {
                'flash_model': _genai.GenerativeModel(config.get("pre_screening_model", "gemini-2.5-flash-lite")),
                'pro_model': _genai.GenerativeModel(config.get("model_for_daily_search", "gemini-2.5-pro")),
                'embedding_model': "models/embedding-001",
                'consecutive_failures': 0, 'circuit_open': False
            }
            print("INFO: Gemini provider initialized.")
        elif gemini_api_key:
            print(f"WARNING: Gemini API key found but google-generativeai not installed ({_genai_import_error}). Skipping Gemini.")

        # --- Universal Cloud Mesh (v5.9.18): OpenAI-compatible provider registry ---
        # Dictionary-driven initialization. Each entry supplies the environment
        # variable key name, base URL, default model, and model-override key.
        # Providers without a configured key are skipped gracefully (Constitution
        # II: cloud providers are OPTIONAL, never required for local operation).
        for provider_name, meta in OPENAI_COMPATIBLE_REGISTRY.items():
            api_key = os.getenv(meta["env_key"], "")
            if api_key and _try_import_openai():
                model_name = os.getenv(meta["model_env_key"], meta["default_model"])
                self.providers[provider_name] = {
                    'client': _openai.OpenAI(api_key=api_key, base_url=meta["base_url"]),
                    'model_name': model_name,
                    'consecutive_failures': 0, 'circuit_open': False
                }
                print(f"INFO: {provider_name.capitalize()} provider initialized ({model_name}).")
            elif api_key:
                print(f"WARNING: {meta['env_key']} found but openai not installed "
                      f"({_openai_import_error}). Skipping {provider_name}.")

        # --- Local Model Provider (Ollama) ---
        local_url = os.getenv("LOCAL_MODEL_BASE_URL", "http://localhost:11434/v1")
        self.local_enabled = os.getenv("TALOS_USE_LOCAL", "").lower() in ("1", "true", "yes")
        if self.local_enabled and _try_import_openai():
            self.providers['local'] = {
                'client': _openai.OpenAI(api_key=os.getenv("LOCAL_MODEL_API_KEY", "ollama"), base_url=local_url),
                'model_name': os.getenv("LOCAL_MODEL_NAME", "gemma3:12b"),
                'embedding_model': os.getenv("LOCAL_EMBEDDING_MODEL", "nomic-embed-text"),
                'ollama_url': local_url.replace("/v1", ""),
                'consecutive_failures': 0, 'circuit_open': False
            }
            if not os.getenv("TALOS_MODELS_VERIFIED"):
                self._ensure_local_model()
            print(f"INFO: Local provider initialized ({self.providers['local']['model_name']}).")
            self.provider_priority.insert(0, 'local')  # local first when enabled

        self.FAILURE_THRESHOLD = config.get("failure_threshold", 5)
        print(f"INFO: AIManager v3.8 (2D Execution Matrix) initialized.")

    # ==================================================================
    # -- v5.10.2: LLM Router Sub-Agent integration --
    # ==================================================================

    def _init_router(self):
        """Instantiate the LLM Router Sub-Agent, or None if unavailable.

        Returns:
            LLMRouterSubAgent | None: The router instance, or None on import or
                weights-loading failure.
        """
        try:
            from src.ai.drl.llm_router_subagent import LLMRouterSubAgent
            return LLMRouterSubAgent()
        except Exception:
            return None

    @staticmethod
    def _task_type(model_type):
        """Map a model_type string to a router task type.

        Args:
            model_type (str): 'pro'/'heavy' or 'flash'/'fast'.

        Returns:
            str: Router task type key.
        """
        if model_type in ("pro", "heavy"):
            return "deep_research"
        if model_type in ("flash", "fast"):
            return "fast_screening"
        return "default"

    def _emit_router_decision_synapse(self, provider, task_type, prompt_length):
        """Emit a non-blocking router_decision Synapse event (best-effort).

        Args:
            provider (str | None): The selected provider name.
            task_type (str): The routing task type.
            prompt_length (int): The estimated prompt length in tokens.
        """
        if provider is None:
            return
        try:
            from src.integration.synapse_client import synapse_emitter
            synapse_emitter.emit("router_decision", {
                "provider": provider,
                "task_type": task_type,
                "prompt_length": int(prompt_length or 0),
            })
        except Exception:
            pass


    def _get_router_ordered_providers(self, prompt, task_type):
        """Return provider names with the router's preferred provider first.

        The router is consulted only over the active (configured, circuit-closed)
        providers, so this method never introduces a provider the caller would
        not otherwise have tried.

        Args:
            prompt (str): Prompt text (used to estimate token length).
            task_type (str): Routing task type.

        Returns:
            list: Provider names from provider_priority, with the preferred
                active provider moved to the front.
        """
        if self.router is None:
            return list(self.provider_priority)
        active = [p for p in self.provider_priority
                  if p in self.providers and not self.providers[p]['circuit_open']]
        if not active:
            return list(self.provider_priority)
        prompt_length = max(1, len(prompt) // 4)
        preferred = self.router.select_provider(prompt_length, task_type, active)
        self._emit_router_decision_synapse(preferred, task_type, prompt_length)
        ordered = list(self.provider_priority)
        if preferred and preferred in ordered:
            ordered.remove(preferred)
            ordered.insert(0, preferred)
        return ordered

    # --- JSON Cleaning ---

    def _clean_json_string(self, text: str) -> str:
        """Extract a valid JSON object from a potentially messy LLM response.

        Handles Markdown code fences and leading/trailing text.

        Args:
            text (str): Raw LLM response.

        Returns:
            str: Cleaned JSON string.
        """
        if "```json" in text:
            text = text.split("```json", 1)[-1]
            text = text.split("```", 1)[0]
        elif "```" in text:
            text = text.split("```", 1)[-1]
            text = text.split("```", 1)[0]
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            return text[start:end + 1]
        return text

    # --- Text Generation ---

    def evaluate_paper_json(self, abstract: str, model_type: str = "pro",
                             system_prompt_override: str = None) -> Union[Dict[str, Any], None]:
        """Evaluate a paper abstract and return structured JSON results.

        Args:
            abstract (str): Paper abstract text.
            model_type (str): ``'pro'`` or ``'flash'``.
            system_prompt_override (str, optional): Custom system prompt.

        Returns:
            dict or None: Parsed JSON evaluation or None if all providers fail.
        """
        prompt = self.config.get("pre_screening_prompt", "Evaluate this paper.")
        if system_prompt_override:
            prompt = system_prompt_override + "\n\n" + abstract
        else:
            prompt = prompt + "\n\n" + abstract

        return self._execute_request(prompt, model_type, response_format='json')

    def analyze_generic_text(self, full_prompt: str) -> Union[str, None]:
        """Run an arbitrary text prompt through the multi-provider chain.

        Args:
            full_prompt (str): Complete prompt text to send to the LLM.

        Returns:
            str or None: Model response text, or None if all providers fail.
        """
        return self._execute_request(full_prompt, model_type='pro', response_format='text')

    # -- Embeddings --

    def generate_embeddings(self, texts: List[str]) -> Tuple[Union[List[List[float]], None], Union[str, None]]:
        """Generate embeddings with automatic fallback across providers.

        Provider order:
            local (Ollama) -> huggingface (free) -> gemini (paid)

        Args:
            texts (List[str]): List of text strings to embed.

        Returns:
            Tuple[List[List[float]], str]: (embeddings list, model_name) or
            (None, None) if all providers fail.
        """
        # Try local embeddings first
        if 'local' in self.providers and not self.providers['local']['circuit_open']:
            try:
                p = self.providers['local']
                resp = requests.post(
                    f"{p['ollama_url']}/api/embed",
                    json={"model": p['embedding_model'], "input": texts},
                    timeout=60
                )
                if resp.status_code == 200:
                    self.active_embedding_model = f"ollama:{p['embedding_model']}"
                    return resp.json().get('embeddings'), self.active_embedding_model
                print(f"  >!> Local embedding status: {resp.status_code}")
            except Exception as e:
                print(f"  >!> Local embedding error: {e}")

        # Fallback to Gemini -- with retry for rate limits (free tier: 100 RPM)
        if 'gemini' in self.providers and not self.providers['gemini']['circuit_open']:
            import time as _time
            if _GENAI_V2:
                client = genai_client.Client(
                    api_key=os.getenv("GEMINI_API_KEY"),
                    http_options={'api_version': 'v1'}
                )
                MAX_RETRIES = 10
                for attempt in range(MAX_RETRIES):
                    try:
                        response = client.models.embed_content(
                            model="gemini-embedding-001",
                            contents=texts,
                            config=genai_types.EmbedContentConfig(
                                task_type="RETRIEVAL_DOCUMENT",
                                output_dimensionality=768,
                            )
                        )
                        if response and response.embeddings:
                            vectors = [e.values for e in response.embeddings]
                            self.active_embedding_model = "gemini:gemini-embedding-001"
                            if self.providers['gemini']['consecutive_failures'] > 0:
                                self.providers['gemini']['consecutive_failures'] = 0
                                print("  >!> Gemini recovered from rate limit.")
                            return vectors, self.active_embedding_model
                        else:
                            print(f"  >!> Gemini empty response (attempt {attempt+1}/{MAX_RETRIES})")
                            _time.sleep(3)
                    except Exception as e:
                        err_str = str(e)
                        is_rate_limit = "429" in err_str or "RESOURCE_EXHAUSTED" in err_str
                        if is_rate_limit:
                            wait = 60
                            try:
                                m = re.search(r'retryDelay["\']:\s*["\'](\d+)s', err_str)
                                if m:
                                    wait = int(m.group(1)) + 5
                            except Exception:
                                pass
                            print(f"  >!> Gemini rate limited (attempt {attempt+1}/{MAX_RETRIES}), waiting {wait}s...")
                            _time.sleep(wait)
                            if attempt >= MAX_RETRIES - 2:
                                self._handle_failure('gemini')
                                return None, None
                        else:
                            print(f"  >!> Gemini embedding error: {err_str[:200]}")
                            self._handle_failure('gemini')
                            return None, None
            else:
                print("  >!> Gemini v1beta embedContent is deprecated. Install google-genai for embedding support.")

        print("ERROR: No embedding provider available.")
        return None, None

    def _execute_huggingface_embedding(self, texts: List[str],
                                        hf_token: str) -> Union[List[List[float]], None]:
        """Generate embeddings using HuggingFace free Inference API.

        Args:
            texts (List[str]): List of texts to embed.
            hf_token (str): HuggingFace API token.

        Returns:
            List[List[float]] or None: List of embedding vectors, or None.
        """
        api_url = ("https://api-inference.huggingface.org/pipeline/"
                   "feature-extraction/sentence-transformers/all-MiniLM-L6-v2")
        headers = {
            "Authorization": f"Bearer {hf_token}",
            "Content-Type": "application/json"
        }
        embeddings = []
        for text in texts:
            try:
                response = requests.post(
                    api_url, headers=headers,
                    json={"inputs": text, "options": {"wait_for_model": True}},
                    timeout=60
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        if len(data) > 0 and isinstance(data[0], list):
                            embeddings.append(data[0])
                        else:
                            embeddings.append(data)
                    else:
                        return None
                elif response.status_code == 503:
                    import time as _time
                    _time.sleep(15)
                    response2 = requests.post(
                        api_url, headers=headers,
                        json={"inputs": text, "options": {"wait_for_model": True}},
                        timeout=90
                    )
                    if response2.status_code == 200:
                        data = response2.json()
                        if isinstance(data, list):
                            if len(data) > 0 and isinstance(data[0], list):
                                embeddings.append(data[0])
                            else:
                                embeddings.append(data)
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            except Exception:
                return None
        return embeddings if len(embeddings) == len(texts) else None

    # ==================================================================
    # -- v5.9.4: 2D Execution Matrix Strategy Resolution --
    # ==================================================================

    def _resolve_strategies(self):
        """Resolve the effective Network and Hardware strategies for routing.

        Reads TALOS_NETWORK_STRATEGY and TALOS_HARDWARE_STRATEGY from the
        environment. If either is not set, falls back to the legacy
        TALOS_EXECUTION_MODE mapping.

        Returns:
            tuple[str, str]: (network_strategy, hardware_strategy)
        """
        network = os.getenv("TALOS_NETWORK_STRATEGY", "")
        hardware = os.getenv("TALOS_HARDWARE_STRATEGY", "")

        # -- If either is not set, resolve from legacy TALOS_EXECUTION_MODE --
        if not network or not hardware:
            legacy_mode = os.getenv("TALOS_EXECUTION_MODE", "local")
            if not network:
                if legacy_mode == "local":
                    network = "strict_local"
                elif legacy_mode == "hybrid":
                    network = "local_first"
                elif legacy_mode == "cloud":
                    network = "cloud_first"
                else:
                    network = "strict_local"
            if not hardware:
                hardware = "cpu_gpu_split"

        return network, hardware

    # ==================================================================
    # -- Master Request Dispatcher --
    # ==================================================================

    def _execute_request(self, prompt: str, model_type: str,
                         response_format: str = 'text',
                         tier: str = 'fast',
                         allow_prompt: bool = True) -> Union[Dict[str, Any], str, None]:
        """Execute a request with 2D Execution Matrix routing and auto-fallback.

        v5.9.4: Replaces legacy per-tier routing. The routing logic is:

        Network Strategy controls WHERE (local vs. cloud) and fallback:
          - strict_local:  Only local endpoints. Never call cloud.
          - local_first:   Try local first. On ConnectionError, auto-fallback
                           to cloud providers.
          - cloud_first:   Try cloud providers first. On failure, auto-fallback
                           to local.
          - strict_cloud:  Only cloud providers. Never call local.

        Hardware Strategy controls HOW local compute is used:
          - cpu_only:       All local requests -> FAST_EDGE_BASE_URL (11435).
          - gpu_only:       All local requests -> OLLAMA_BASE_URL (11434).
          - cpu_gpu_split:  Fast tier -> CPU (11435), Heavy tier -> GPU (11434).

        Args:
            prompt: Full prompt text to send.
            model_type: 'pro' or 'flash' (Gemini only).
            response_format: 'json' or 'text'.
            tier: 'fast' or 'heavy'.
            allow_prompt: If False, auto-accepts cloud fallback without user input.

        Returns:
            Parsed response, or None if all providers fail.
        """
        network_strategy, hardware_strategy = self._resolve_strategies()

        # -- strict_local --
        if network_strategy == "strict_local":
            result = self._execute_local_strategy(
                prompt, response_format, tier, hardware_strategy, allow_prompt=allow_prompt
            )
            if result is not None:
                self.last_provider_used = 'local'
                return result
            print("  >!> Strict Local: local request failed. No cloud fallback configured.")
            return None

        # -- local_first --
        if network_strategy == "local_first":
            result = self._execute_local_strategy(
                prompt, response_format, tier, hardware_strategy, allow_prompt=allow_prompt
            )
            if result is not None:
                self.last_provider_used = 'local'
                return result
            # Auto-fallback to cloud
            print("  [WARNING] Local-First: local request failed. "
                  "Auto-fallback to cloud providers...")
            cloud_result = self._execute_cloud_chain(prompt, model_type, response_format)
            if cloud_result is not None:
                return cloud_result
            print("FATAL: All local and cloud providers failed (local_first).")
            return None

        # -- cloud_first --
        if network_strategy == "cloud_first":
            cloud_result = self._execute_cloud_chain(prompt, model_type, response_format)
            if cloud_result is not None:
                return cloud_result
            # Auto-fallback to local
            print("  [WARNING] Cloud-First: cloud request failed. "
                  "Auto-fallback to local endpoints...")
            result = self._execute_local_strategy(
                prompt, response_format, tier, hardware_strategy, allow_prompt=allow_prompt
            )
            if result is not None:
                self.last_provider_used = 'local'
                return result
            print("FATAL: All cloud and local providers failed (cloud_first).")
            return None

        # -- strict_cloud --
        if network_strategy == "strict_cloud":
            cloud_result = self._execute_cloud_chain(prompt, model_type, response_format)
            if cloud_result is not None:
                return cloud_result
            print("  >!> Strict Cloud: cloud request failed. No local fallback configured.")
            return None

        # -- Fallback: legacy routing path --
        print(f"  > Unknown network strategy '{network_strategy}'. Falling back to legacy routing.")
        return self._execute_legacy_request(prompt, model_type, response_format, tier, allow_prompt=allow_prompt)

    # ==================================================================
    # -- v5.9.4: Local Strategy Execution (Hardware-Aware) --
    # ==================================================================

    def _execute_local_strategy(self, prompt: str, response_format: str,
                                tier: str, hardware_strategy: str,
                                allow_prompt: bool = True
                                ) -> Union[Dict[str, Any], str, None]:
        """Execute a local request respecting the Hardware Strategy.

        Args:
            prompt: Full prompt text.
            response_format: 'json' or 'text'.
            tier: 'fast' or 'heavy'.
            hardware_strategy: 'cpu_only', 'gpu_only', or 'cpu_gpu_split'.
            allow_prompt: If False, auto-accepts cloud fallback without user input.

        Returns:
            Parsed response, or None on failure.
        """
        if hardware_strategy == "cpu_only":
            return self._execute_ollama_http(prompt, response_format, use_edge=True, allow_prompt=allow_prompt)
        elif hardware_strategy == "gpu_only":
            return self._execute_ollama_http(prompt, response_format, use_edge=False, allow_prompt=allow_prompt)
        else:  # cpu_gpu_split
            if tier == 'fast':
                result = self._execute_ollama_http(prompt, response_format, use_edge=True, allow_prompt=allow_prompt)
                if result is not None:
                    return result
                print("  >!> Fast (CPU) tier failed. Trying heavy (GPU) tier...")
                return self._execute_ollama_http(prompt, response_format, use_edge=False, allow_prompt=allow_prompt)
            else:  # heavy
                return self._execute_ollama_http(prompt, response_format, use_edge=False, allow_prompt=allow_prompt)

    def _execute_ollama_http(self, prompt: str, response_format: str,
                             use_edge: bool = True,
                             allow_prompt: bool = True
                             ) -> Union[Dict[str, Any], str, None]:
        """Execute a request against an Ollama HTTP endpoint.

        Args:
            prompt: Full prompt text.
            response_format: 'json' or 'text'.
            use_edge: If True, use FAST_EDGE_BASE_URL/FAST_EDGE_MODEL (CPU).
                      If False, use OLLAMA_BASE_URL/LOCAL_MODEL_BASE_URL (GPU).
            allow_prompt: If False, auto-accepts cloud fallback without user input.

        Returns:
            Parsed response, or None on failure.
        """
        if use_edge:
            try:
                from config.settings import FAST_EDGE_BASE_URL, FAST_EDGE_MODEL
            except ImportError:
                FAST_EDGE_BASE_URL = os.getenv("FAST_EDGE_BASE_URL", "http://127.0.0.1:11435/v1")
                FAST_EDGE_MODEL = os.getenv("FAST_EDGE_MODEL", "fermionresearch/Neutrino-8B")
            base_url = FAST_EDGE_BASE_URL
            model = FAST_EDGE_MODEL
            label = "CPU Edge"
        else:
            base_url = os.getenv("LOCAL_MODEL_BASE_URL", "http://localhost:11434/v1")
            model = os.getenv("LOCAL_MODEL_NAME", "gemma3:12b")
            label = "GPU Ollama"

        final_prompt = prompt
        if response_format == 'json':
            final_prompt += (
                "\n\nIMPORTANT: Your response MUST be a single, valid JSON object. "
                "Do not include any text explanation before or after the JSON."
            )

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": final_prompt}],
            "temperature": 0.5,
        }

        try:
            print(f"  > Attempting {label} request: {model} @ {base_url}")
            response = requests.post(
                f"{base_url}/chat/completions",
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                data = response.json()
                response_text = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not response_text:
                    print(f"  >!> {label} returned empty response.")
                    return None
                if response_format == 'json':
                    try:
                        return json.loads(self._clean_json_string(response_text))
                    except json.JSONDecodeError:
                        print(f"  >!> {label} JSON decode failed.")
                        return None
                return response_text
            else:
                print(f"  >!> {label} HTTP {response.status_code}: {response.text[:200]}")
                return None
        except requests.exceptions.ConnectionError as e:
            print(f"  [WARNING] {label} ({model}) connection refused: {e}")
            # -- v5.9.8: Local-to-Local Fast-Tier Fallback --
            # When the fast edge tier (CPU, port 11435) fails, automatically
            # fall back to local Ollama GPU (port 11434) FIRST before attempting
            # cloud fallback. This preserves air-gapped operation and avoids
            # unnecessary cloud API calls when only the edge endpoint is down.
            if use_edge:
                print("  [WARNING] Fast tier (11435) offline. Falling back to local Ollama (11434)...")
                # -- Try the GPU Ollama endpoint --
                gpu_result = self._execute_ollama_http(
                    prompt, response_format, use_edge=False, allow_prompt=allow_prompt
                )
                if gpu_result is not None:
                    print("  [RECOVERY] Fast-tier fallback to local Ollama (GPU) succeeded.")
                    return gpu_result
                print("  [WARNING] Local Ollama (GPU) also unavailable.")
                # -- Both local endpoints failed -- fall through to cloud fallback --
            tier_label = "fast" if use_edge else "heavy"
            return self._interactive_cloud_fallback(e, tier=tier_label, allow_prompt=allow_prompt)
        except Exception as e:
            print(f"  >!> {label} unexpected error: {e}")
            return None

    # ==================================================================
    # -- v5.9.4: Cloud Provider Chain Execution --
    # ==================================================================

    def _execute_cloud_chain(self, prompt: str, model_type: str,
                             response_format: str
                             ) -> Union[Dict[str, Any], str, None]:
        """Execute a request through the Universal Cloud Mesh provider chain.

        Iterates through provider_priority, skipping 'local', unconfigured
        providers, and open-circuit providers. Gemini uses the Google SDK; all
        other cloud providers use the unified OpenAI-compatible handler.

        Args:
            prompt: Full prompt text.
            model_type: 'pro' or 'flash' (Gemini only).
            response_format: 'json' or 'text'.

        Returns:
            Parsed response, or None if all cloud providers fail.
        """
        ordered = self._get_router_ordered_providers(prompt, self._task_type(model_type))
        for provider_name in ordered:
            if provider_name == 'local':
                continue  # Skip local in cloud chain
            if provider_name not in self.providers:
                continue  # Skip unconfigured providers
            if self.providers[provider_name]['circuit_open']:
                continue  # Skip open-circuit providers
            print(f"  > Attempting cloud request with provider: {provider_name.upper()}")
            if provider_name == 'gemini':
                result = self._execute_gemini_request(prompt, model_type, response_format)
            else:
                result = self._execute_openai_compatible_request(provider_name, prompt, model_type, response_format)
            if result is not None:
                self.providers[provider_name]['consecutive_failures'] = 0
                self.last_provider_used = provider_name
                return result
            print(f"  >!> Provider {provider_name.upper()} failed. Trying next provider...")
            continue
        print("  >!> All cloud providers failed.")
        return None

    # ==================================================================
    # -- Legacy Request Execution (backward compatibility) --
    # ==================================================================

    def _execute_legacy_request(self, prompt: str, model_type: str,
                                response_format: str,
                                tier: str,
                                allow_prompt: bool = True) -> Union[Dict[str, Any], str, None]:
        """Fallback to legacy per-tier routing when strategies are unknown.

        Args:
            prompt: Full prompt text.
            model_type: 'pro' or 'flash'.
            response_format: 'json' or 'text'.
            tier: 'fast' or 'heavy'.
            allow_prompt: If False, auto-accepts cloud fallback without user input.

        Returns:
            Parsed response, or None on failure.
        """
        fast_routing = os.getenv("TALOS_FAST_ROUTING", "local")
        heavy_routing = os.getenv("TALOS_HEAVY_ROUTING", "local")

        if tier == 'fast':
            if fast_routing == "local":
                result = self._execute_ollama_http(prompt, response_format, use_edge=True, allow_prompt=allow_prompt)
                if result is not None:
                    self.last_provider_used = 'fast_edge'
                    return result
                print("  >!> Fast tier (local) failed. Falling back to cloud providers...")
            else:
                print("  > FAST_ROUTING=cloud: routing directly to cloud providers...")

        elif tier == 'heavy':
            if heavy_routing == "cloud":
                print("  > HEAVY_ROUTING=cloud: routing directly to cloud providers...")

        ordered = self._get_router_ordered_providers(prompt, self._task_type(model_type))
        for provider_name in ordered:
            if provider_name in self.providers and not self.providers[provider_name]['circuit_open']:
                print(f"  > Attempting request with provider: {provider_name.upper()}")
                if provider_name == 'gemini':
                    result = self._execute_gemini_request(prompt, model_type, response_format)
                else:
                    result = self._execute_openai_compatible_request(provider_name, prompt, model_type, response_format)
                if result is not None:
                    self.providers[provider_name]['consecutive_failures'] = 0
                    self.last_provider_used = provider_name
                    return result
                else:
                    print(f"  >!> Provider {provider_name.upper()} failed. Trying next provider...")
                    continue
        print("FATAL: All AI providers failed.")
        return None

    # ==================================================================
    # -- v5.7.1: Fast Tier (Edge) Request (DEPRECATED wrapper) --
    # ==================================================================

    def _execute_fast_tier_request(self, prompt: str,
                                   response_format: str = 'text') -> Union[Dict[str, Any], str, None]:
        """Execute a request against the fast edge tier (Neutrino-8B).

        DEPRECATED in v5.9.4: Use _execute_local_strategy() instead.
        Retained for backward compatibility with tests and legacy callers.

        Args:
            prompt: Full prompt text.
            response_format: 'json' or 'text'.

        Returns:
            Parsed response, or None on failure.
        """
        return self._execute_ollama_http(prompt, response_format, use_edge=True)

    # ==================================================================
    # -- Provider-Specific Execution Methods --
    # ==================================================================

    def _execute_gemini_request(self, prompt: str, model_type: str,
                                response_format: str) -> Union[Dict[str, Any], str, None]:
        provider = self.providers['gemini']
        model = provider['pro_model'] if model_type == 'pro' else provider['flash_model']
        try:
            if response_format == 'json':
                gen_config = _genai.types.GenerationConfig(response_mime_type="application/json")
                response = model.generate_content(prompt, generation_config=gen_config)
                return json.loads(response.text)
            else:
                response = model.generate_content(prompt)
                return response.text
        except Exception as e:
            print(f"  >!> Gemini execution error: {e}")
            if "429" in str(e) or "resource exhausted" in str(e).lower():
                self._handle_failure('gemini')
            return None

    def _execute_deepseek_request(self, prompt: str,
                                   response_format: str) -> Union[Dict[str, Any], str, None]:
        """DEPRECATED (v5.9.18): DeepSeek is now routed through the unified
        OpenAI-compatible handler. Retained for backward compatibility.

        Args:
            prompt: Full prompt text to send.
            response_format: 'json' or 'text'.

        Returns:
            Parsed response, or None on failure.
        """
        return self._execute_openai_compatible_request('deepseek', prompt, 'pro', response_format)

    def _execute_openai_compatible_request(self, provider_name: str, prompt: str,
                                           model_type: str,
                                           response_format: str) -> Union[Dict[str, Any], str, None]:
        """Execute a request through any OpenAI-compatible cloud provider.

        Unified handler for the Universal Cloud Mesh (v5.9.18). On failure the
        provider's consecutive-failure counter is incremented via
        _handle_failure() so its circuit breaker trips after the configured
        threshold; on success the counter is reset.

        Args:
            provider_name: Registry key of the provider (e.g. 'groq', 'deepseek').
            prompt: Full prompt text to send.
            model_type: 'pro' or 'flash'. Unused by OpenAI-compatible providers;
                retained for a uniform signature across the cloud mesh.
            response_format: 'json' or 'text'.

        Returns:
            Parsed response, or None if the provider fails.
        """
        provider = self.providers[provider_name]
        final_prompt = prompt
        if response_format == 'json':
            final_prompt += "\n\nIMPORTANT: Your response MUST be a single, valid JSON object. Do not include any text explanation before or after the JSON."
        try:
            chat_completion = provider['client'].chat.completions.create(
                model=provider['model_name'],
                messages=[{"role": "user", "content": final_prompt}],
                temperature=0.5)
            response_text = chat_completion.choices[0].message.content
            if response_format == 'json':
                try:
                    parsed = json.loads(self._clean_json_string(response_text))
                except json.JSONDecodeError:
                    print(f"  >!> {provider_name} JSON decode failed.")
                    self._handle_failure(provider_name)
                    return None
                self.providers[provider_name]['consecutive_failures'] = 0
                return parsed
            self.providers[provider_name]['consecutive_failures'] = 0
            return response_text
        except Exception as e:
            print(f"  >!> {provider_name} execution error: {e}")
            self._handle_failure(provider_name)
            return None

    def _execute_openai_compatible(self, prompt: str, response_format: str,
                                   provider_name: str) -> Union[Dict[str, Any], str, None]:
        """DEPRECATED (v5.9.18): use _execute_openai_compatible_request() instead.

        Retained for backward compatibility with legacy callers and tests.

        Args:
            prompt: Full prompt text to send.
            response_format: 'json' or 'text'.
            provider_name: Registry key of the provider.

        Returns:
            Parsed response, or None on failure.
        """
        return self._execute_openai_compatible_request(provider_name, prompt, 'pro', response_format)

    # ==================================================================
    # -- v5.9.2: Interactive Runtime Cloud Fallback --
    # ==================================================================

    def _interactive_cloud_fallback(self, error, tier="fast",
                                     allow_prompt: bool = True):
        """Handle cloud fallback on local model connection failure.

        If `allow_prompt=True` and the session is interactive, prompts the user
        via questionary. If `allow_prompt=False` or the session is non-interactive,
        automatically switches the tier to cloud routing with a warning log.

        Args:
            error: The exception that triggered the fallback.
            tier: Which tier failed ('fast' or 'heavy').
            allow_prompt: If False, auto-accepts cloud fallback without user input.

        Returns:
            None always. The caller should check env vars and retry.
        """
        # -- Headless override: never block on an interactive prompt --
        is_headless = os.environ.get("TALOS_HEADLESS") == "1"
        if is_headless:
            print(f"  [HEADLESS] Local {tier} connection failed. "
                  f"Interactive fallback suppressed.")
            return None

        # -- Non-interactive session: log and skip (no interactive prompt possible) --
        if not sys.stdin.isatty():
            print(f"  >!> Non-interactive session -- cloud fallback not available for {tier} tier.")
            return None

        # -- Auto-accept fallback (non-blocking mode) --
        if not allow_prompt:
            print(f"  [WARNING] Fast tier connection failed. Auto-switching to "
                  f"cloud/standard fallback for automated task ({tier} tier).")
            if tier == "fast":
                os.environ["TALOS_FAST_ROUTING"] = "cloud"
            elif tier == "heavy":
                os.environ["TALOS_HEAVY_ROUTING"] = "cloud"
            return None

        # -- Interactive mode: prompt the user --
        try:
            import questionary
            answer = questionary.confirm(
                f"Local {tier} model connection failed ({error}).\n"
                "Switch to Cloud fallback (Gemini/DeepSeek) for this session?",
                default=True,
            ).ask()
            if answer:
                if tier == "fast":
                    os.environ["TALOS_FAST_ROUTING"] = "cloud"
                elif tier == "heavy":
                    os.environ["TALOS_HEAVY_ROUTING"] = "cloud"
                print(f"  > [FALLBACK] {tier} tier rerouted to cloud for this session.")
                return None
            else:
                print(f"  > [SKIP] Cloud fallback declined for {tier} tier.")
                return None
        except KeyboardInterrupt:
            return None

    # ==================================================================
    # -- Circuit Breaker --
    # ==================================================================

    def _handle_failure(self, provider_name: str):
        """Increment failure counter and open circuit if threshold exceeded.

        Args:
            provider_name (str): Name of the provider that failed.
        """
        if provider_name in self.providers:
            self.providers[provider_name]['consecutive_failures'] += 1
            fails = self.providers[provider_name]['consecutive_failures']
            print(f"  >!> Provider {provider_name}: {fails} consecutive failures (threshold: {self.FAILURE_THRESHOLD})")
            if fails >= self.FAILURE_THRESHOLD:
                self.providers[provider_name]['circuit_open'] = True
                print(f"  >!> Circuit OPENED for {provider_name}. Skipping for rest of session.")

    # ==================================================================
    # -- Local Model Management --
    # ==================================================================

    def _ensure_local_model(self):
        """Verify required local Ollama models are present (non-blocking).

        v5.9.15: this method no longer auto-pulls models. It only reports
        missing models; installation is handled on-demand by
        src/ai/llm/model_manager.py (Option 1). Skips silently when Ollama
        is unreachable or when verification already happened.
        """
        base = "http://localhost:11434"
        try:
            resp = requests.get(f"{base}/api/tags", timeout=5)
            if resp.status_code != 200:
                return
            models = [m['name'] for m in resp.json().get('models', [])]

            local_model = os.getenv("LOCAL_MODEL_NAME", "gemma3:12b")
            local_embedding = os.getenv("LOCAL_EMBEDDING_MODEL", "nomic-embed-text")

            missing = [m for m in (local_model, local_embedding)
                       if not any(x == m or x.startswith(m) for x in models)]
            if missing:
                print(f"WARNING: Missing local models: {', '.join(missing)}. "
                      f"Install them via Model Manager (Option 1).")
            os.environ["TALOS_MODELS_VERIFIED"] = "1"
        except Exception:
            pass