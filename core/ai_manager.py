# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software...
#
"""
Module: ai_manager.py (v3.6 - Hybrid Multi-Provider Embeddings)
Project: TALOS v5.0.0

Description:
    Centralized AI provider manager implementing a multi-provider architecture
    with automatic fallback and circuit breaker pattern. Orchestrates all LLM
    interactions across four independent providers and embedding across three
    independent providers:

    - Gemini (Google Generative AI) — primary cloud provider
    - DeepSeek — fallback cloud provider via OpenAI-compatible API
    - Hugging Face — free cloud inference via router.huggingface.co (text)
                   and api-inference.huggingface.co (embeddings)
    - Local (Ollama) — offline operation via OpenAI-compatible API

    Supports JSON mode, text generation, and HYBRID embedding generation with
    automatic failover across Ollama → HuggingFace → Gemini.
"""

import os, json, re, requests
from dotenv import load_dotenv
import google.generativeai as genai
import openai
from typing import Union, List, Dict, Any, Tuple
import numpy as np

# New GA Gemini SDK for embeddings (replaces deprecated embed_content on v1beta)
try:
    from google import genai as genai_client
    from google.genai import types as genai_types
    _GENAI_V2 = True
except ImportError:
    _GENAI_V2 = False


class AIManager:
    """Manages all LLM and embedding interactions with multi-provider fallback
    and circuit breaker pattern.

    Embedding providers tried in order:
        local (Ollama) → huggingface (free) → gemini

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
        # v3.7 (Batch 1 audit fix): name of the provider that served the LAST
        # successful text/JSON request. Consumers (e.g. the live DRL agent's
        # provider-usage counters) read this to attribute calls correctly
        # instead of blindly assuming "gemini".
        self.last_provider_used = None

        # --- Gemini Provider ---
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if gemini_api_key:
            genai.configure(api_key=gemini_api_key)
            self.providers['gemini'] = {
                'flash_model': genai.GenerativeModel(config.get("pre_screening_model", "gemini-2.5-flash-lite")),
                'pro_model': genai.GenerativeModel(config.get("model_for_daily_search", "gemini-2.5-pro")),
                'embedding_model': "models/embedding-001",
                'consecutive_failures': 0, 'circuit_open': False
            }
            print("INFO: Gemini provider initialized.")

        # --- DeepSeek Provider ---
        deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_api_key:
            self.providers['deepseek'] = {
                'client': openai.OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1"),
                'model_name': config.get("deepseek_model_chat", "deepseek-chat"),
                'consecutive_failures': 0, 'circuit_open': False
            }
            print("INFO: DeepSeek provider initialized.")

        # --- Hugging Face Provider (Free cloud inference) ---
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            self.providers['huggingface'] = {
                'client': openai.OpenAI(api_key=hf_token, base_url="https://router.huggingface.co/v1"),
                'model_name': os.getenv("HF_MODEL_NAME", "Qwen/Qwen2.5-7B-Instruct"),
                'consecutive_failures': 0, 'circuit_open': False
            }
            print("INFO: Hugging Face provider initialized.")
            if 'huggingface' not in self.provider_priority:
                self.provider_priority.insert(0, 'huggingface')  # Free first

        # --- Local Model Provider (Ollama) ---
        local_url = os.getenv("LOCAL_MODEL_BASE_URL", "http://localhost:11434/v1")
        self.local_enabled = os.getenv("TALOS_USE_LOCAL", "").lower() in ("1", "true", "yes")
        if self.local_enabled:
            self.providers['local'] = {
                'client': openai.OpenAI(api_key=os.getenv("LOCAL_MODEL_API_KEY", "ollama"), base_url=local_url),
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
        print(f"INFO: AIManager v3.6 (Hybrid Multi-Provider Embeddings) initialized.")

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

        v3.8 (Batch 3 hotfix): This method was documented in PROJECT_MAP.md
        and called by grey_literature_miner.py, but was never implemented —
        causing AttributeError crashes. It is a thin wrapper around
        _execute_request() so it inherits the circuit breaker, provider
        fallback chain, and last_provider_used tracking.

        Args:
            full_prompt (str): Complete prompt text to send to the LLM.

        Returns:
            str or None: Model response text, or None if all providers fail.
        """
        return self._execute_request(full_prompt, model_type='pro', response_format='text')

    # ── Embeddings ─────────────────────────────────────────────────────────

    def generate_embeddings(self, texts: List[str]) -> Tuple[Union[List[List[float]], None], Union[str, None]]:
        """Generate embeddings with automatic fallback across providers.

        Provider order:
            local (Ollama) → huggingface (free) → gemini (paid)

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

        # HuggingFace embedding removed — DNS issues with api-inference endpoints

        # Fallback to Gemini — with retry for rate limits (free tier: 100 RPM)
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
                            # Parse retry delay
                            wait = 60
                            try:
                                m = re.search(r'retryDelay["\']:\s*["\'](\d+)s', err_str)
                                if m:
                                    wait = int(m.group(1)) + 5
                            except Exception:
                                pass
                            print(f"  >!> Gemini rate limited (attempt {attempt+1}/{MAX_RETRIES}), waiting {wait}s...")
                            _time.sleep(wait)
                            # Rate limits should NOT trip the circuit breaker
                            # Only trip if we've tried many times
                            if attempt >= MAX_RETRIES - 2:
                                self._handle_failure('gemini')
                                return None, None
                        else:
                            # Real error (not rate limit)
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

        Uses the sentence-transformers/all-MiniLM-L6-v2 model by default,
        which produces 384-dimensional vectors.

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
                    api_url,
                    headers=headers,
                    json={"inputs": text, "options": {"wait_for_model": True}},
                    timeout=60
                )
                if response.status_code == 200:
                    data = response.json()
                    # Handle both [[float]] and [float] response formats
                    if isinstance(data, list):
                        if len(data) > 0 and isinstance(data[0], list):
                            embeddings.append(data[0])
                        else:
                            embeddings.append(data)
                    else:
                        print(f"  >!> Unexpected HF response format: {type(data)}")
                        return None
                elif response.status_code == 503:
                    print(f"  >!> HF model loading (503), retrying once after 10s...")
                    time_out = 15
                    import time as _time
                    _time.sleep(time_out)
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
                        print(f"  >!> HF embedding retry failed: {response2.status_code}")
                        return None
                else:
                    print(f"  >!> HF embedding status: {response.status_code}")
                    return None
            except Exception as e:
                print(f"  >!> HF embedding exception: {e}")
                return None

        return embeddings if len(embeddings) == len(texts) else None

    # --- Internal: Request Execution ---

    def _execute_request(self, prompt: str, model_type: str,
                         response_format: str = 'text') -> Union[Dict[str, Any], str, None]:
        """Execute a request across all enabled providers with fallback.

        Iterates through ``provider_priority``, attempting each non-open-circuit
        provider. On success, resets the failure counter for that provider.
        On failure, increments the counter and continues to the next provider.

        Args:
            prompt (str): Full prompt text to send.
            model_type (str): ``'pro'`` or ``'flash'`` (Gemini only).
            response_format (str): ``'json'`` or ``'text'``.

        Returns:
            dict, str, or None: Parsed response, or None if all providers fail.
        """
        for provider_name in self.provider_priority:
            if provider_name in self.providers and not self.providers[provider_name]['circuit_open']:
                print(f"  > Attempting request with provider: {provider_name.upper()}")
                result = None
                if provider_name == 'gemini':
                    result = self._execute_gemini_request(prompt, model_type, response_format)
                elif provider_name == 'deepseek':
                    result = self._execute_deepseek_request(prompt, response_format)
                elif provider_name == 'huggingface':
                    result = self._execute_openai_compatible(prompt, response_format, 'huggingface')
                elif provider_name == 'local':
                    result = self._execute_openai_compatible(prompt, response_format, 'local')
                if result is not None:
                    self.providers[provider_name]['consecutive_failures'] = 0
                    # v3.7: record which provider actually served this request
                    self.last_provider_used = provider_name
                    return result
                else:
                    print(f"  >!> Provider {provider_name.upper()} failed. Trying next provider...")
                    continue
        print("FATAL: All AI providers failed.")
        return None

    def _execute_gemini_request(self, prompt: str, model_type: str,
                                response_format: str) -> Union[Dict[str, Any], str, None]:
        provider = self.providers['gemini']
        model = provider['pro_model'] if model_type == 'pro' else provider['flash_model']
        try:
            if response_format == 'json':
                gen_config = genai.types.GenerationConfig(response_mime_type="application/json")
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
        provider = self.providers['deepseek']
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
                    return json.loads(self._clean_json_string(response_text))
                except json.JSONDecodeError:
                    print(f"  >!> DeepSeek JSON decode failed.")
                    return None
            return response_text
        except Exception as e:
            print(f"  >!> DeepSeek execution error: {e}")
            return None

    def _execute_openai_compatible(self, prompt: str, response_format: str,
                                   provider_name: str) -> Union[Dict[str, Any], str, None]:
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
                    return json.loads(self._clean_json_string(response_text))
                except json.JSONDecodeError:
                    print(f"  >!> {provider_name} JSON decode failed.")
                    return None
            return response_text
        except Exception as e:
            print(f"  >!> {provider_name} execution error: {e}")
            return None

    # --- Circuit Breaker ---

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

    # ── Local Model Management ──────────────────────────────────────────

    def _ensure_local_model(self):
        """Verify and auto-install required local models for Ollama."""
        print("\n[Verifying local models...]")
        base = "http://localhost:11434"
        try:
            resp = requests.get(f"{base}/api/tags", timeout=5)
            if resp.status_code != 200:
                print("WARNING: Ollama not reachable.")
                return
            models = [m['name'] for m in resp.json().get('models', [])]

            # Read user-configured model from .env, fallback to gemma3:12b
            local_model = os.getenv("LOCAL_MODEL_NAME", "gemma3:12b")
            local_embedding = os.getenv("LOCAL_EMBEDDING_MODEL", "nomic-embed-text")

            for model in [local_model, local_embedding]:
                # Strip tag for detection (e.g. "gemma4:12b" may be listed as "gemma4:12b")
                found = any(m == model or m.startswith(model) for m in models)
                if not found:
                    print(f"  >> Pulling {model}...")
                    import subprocess
                    subprocess.run(["ollama", "pull", model], check=True)
                else:
                    print(f"  >> {model} already installed.")
            os.environ["TALOS_MODELS_VERIFIED"] = "1"
            print("[All local models ready.]")
        except Exception as e:
            print(f"WARNING: Model verification failed: {e}")