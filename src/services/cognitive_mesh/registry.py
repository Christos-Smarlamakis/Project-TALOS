# -*- coding: utf-8 -*-
"""
Module: registry.py
Project: TALOS v5.21.0
Description:
    Pluggable, adapter-based LLM provider registry implementing the
    Open-Closed Principle (software entities should be open for extension
    but closed for modification). The registry is a single catalogue of
    :class:`ProviderDescriptor` records describing every inference provider
    TALOS can route through -- local Ollama plus fifteen cloud providers
    (NVIDIA NIM, DeepSeek, Gemini, Groq, Cerebras, Mistral, Hugging Face,
    OpenRouter, Anthropic, SambaNova, Together, Fireworks, DeepInfra,
    Cohere, and Perplexity). The registry exposes a stable, small API
    surface (register / get / list_all / list_active / get_available_providers)
    so that adding any future provider requires only constructing a
    ``ProviderDescriptor`` and calling ``register`` -- the core evaluation
    loops in ``AIManager`` and the cognitive routing layers never need to be
    edited to support a new adapter.

    Key design decisions:
    - ``is_active`` is evaluated dynamically at query time: cloud providers
      are active when their ``api_key_env`` is present in the environment,
      while the local Ollama runtime is active when its port answers a
      lightweight socket probe. This keeps the registry truthful across the
      life of a process (keys injected on demand, runtimes brought online).
    - The registry is air-gapped by construction (Constitution II): every
      provider defaults to inactive when unconfigured, and local operation
      never depends on a cloud key.
    - Descriptors carry an ``is_openai_compatible`` flag and a ``category``
      label so routing layers can reason about transport shape and latency
      class without hard-coded per-provider branches.
    - The registry is extraction-ready (Constitution, v5.21.0): it imports
      only ``config.settings`` and the standard library, never SQLite WAL
      storage, PRISMA pipelines, or CLI scripts, so it can be lifted into a
      standalone SYNAPSE (:8000) / MEMEX microservice without dependency
      surgery.

Dependencies:
    - dataclasses: Definition of the ProviderDescriptor value object.
    - enum: Definition of the LLMProvider canonical name enumeration.
    - os: Environment-variable lookup for API-key presence checks.
    - socket: Lightweight local port probe for the Ollama runtime.
    - config.settings: Canonical base URLs and default model names.
"""

import os
import socket
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

# -- Resolve project root (same pattern as all src/*.py modules) --------------
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, "talos.py")):
    _P = os.path.dirname(_P)
if _P:
    import sys
    sys.path.insert(0, _P)

# -- Canonical configuration constants (single source of truth) ---------------
from config.settings import (
    NVIDIA_BASE_URL, NVIDIA_DEFAULT_MODEL,
    GROQ_BASE_URL, GROQ_DEFAULT_MODEL,
    CEREBRAS_BASE_URL, CEREBRAS_DEFAULT_MODEL,
    MISTRAL_BASE_URL, MISTRAL_DEFAULT_MODEL,
    OPENROUTER_BASE_URL, OPENROUTER_DEFAULT_MODEL,
    DEEPSEEK_BASE_URL, DEEPSEEK_MODEL_CHAT,
    HF_BASE_URL, HF_MODEL_NAME,
    GEMINI_FLASH_MODEL, OLLAMA_BASE_URL,
    SAMBANOVA_BASE_URL, SAMBANOVA_DEFAULT_MODEL,
    TOGETHER_BASE_URL, TOGETHER_DEFAULT_MODEL,
    FIREWORKS_BASE_URL, FIREWORKS_DEFAULT_MODEL,
    DEEPINFRA_BASE_URL, DEEPINFRA_DEFAULT_MODEL,
    COHERE_BASE_URL, COHERE_DEFAULT_MODEL,
    PERPLEXITY_BASE_URL, PERPLEXITY_DEFAULT_MODEL,
)

# -- Provider category labels (used by routing/UI layers) ----------------------
CATEGORY_LOCAL_GPU = "local_gpu"
CATEGORY_LOCAL_CPU = "local_cpu"
CATEGORY_CLOUD_REASONING = "cloud_reasoning"
CATEGORY_CLOUD_FAST = "cloud_fast"
CATEGORY_CLOUD_HEAVY = "cloud_heavy"


class LLMProvider(str, Enum):
    """Canonical enumeration of the sixteen registered inference providers.

    This enumeration is a stable, decoupled name space consumed by routing
    layers (such as ``CognitiveMetaRouter``) to reference providers without
    string literals. Members subclass ``str`` so they interoperate directly
    with ``ProviderDescriptor.name`` values and JSON serialization.
    """

    OLLAMA = "ollama"
    NVIDIA = "nvidia"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"
    GROQ = "groq"
    CEREBRAS = "cerebras"
    MISTRAL = "mistral"
    HUGGINGFACE = "huggingface"
    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"
    SAMBANOVA = "sambanova"
    TOGETHER = "together"
    FIREWORKS = "fireworks"
    DEEPINFRA = "deepinfra"
    COHERE = "cohere"
    PERPLEXITY = "perplexity"


@dataclass
class ProviderDescriptor:
    """Value object describing a single inference provider adapter.

    Attributes:
        name (str): Canonical identifier (e.g. ``"ollama"``, ``"nvidia"``,
            ``"deepseek"``, ``"gemini"``, ``"groq"``, ``"cerebras"``,
            ``"mistral"``, ``"huggingface"``, ``"openrouter"``,
            ``"anthropic"``).
        base_url (str): Root HTTP endpoint for the provider's API.
        api_key_env (Optional[str]): Environment variable holding the API key.
            ``None`` for keyless runtimes such as local Ollama.
        default_model (str): Default model identifier for this provider.
        category (str): Latency/compute class label (see CATEGORY_* constants).
        is_openai_compatible (bool): True when the provider speaks the
            OpenAI-compatible ``/v1/chat/completions`` protocol.
        is_active (bool): Runtime availability flag. For cloud providers this
            mirrors key presence; for Ollama it mirrors port responsiveness.
    """

    name: str
    base_url: str
    api_key_env: Optional[str] = None
    default_model: str = ""
    category: str = CATEGORY_CLOUD_HEAVY
    is_openai_compatible: bool = True
    is_active: bool = False


class ProviderRegistry:
    """Extensible registry of LLM provider descriptors.

    Pre-registers the local Ollama runtime and the fifteen supported cloud
    providers. The registry follows the Open-Closed Principle: extending the
    provider set is a data operation (``register(descriptor)``) that never
    requires modifying the routing/evaluation loops in ``AIManager``.

    Methods:
        register(descriptor): Insert or replace a provider descriptor.
        get(name): Return a refreshed descriptor or ``None``.
        list_all(): Return every descriptor with ``is_active`` refreshed.
        list_active(): Return only currently-active descriptors.
    """

    def __init__(self) -> None:
        self._providers: Dict[str, ProviderDescriptor] = {}
        self._register_defaults()

    # ------------------------------------------------------------------
    # -- Default catalogue ---------------------------------------------
    # ------------------------------------------------------------------

    def _register_defaults(self) -> None:
        """Pre-register the canonical provider set (Ollama + fifteen clouds)."""
        defaults: List[ProviderDescriptor] = [
            # -- Local runtime (keyless; active when port 11434 responds) --
            ProviderDescriptor(
                name="ollama",
                base_url=OLLAMA_BASE_URL,
                api_key_env=None,
                default_model="llama3.1:8b",
                category=CATEGORY_LOCAL_GPU,
                is_openai_compatible=True,
            ),
            # -- Cloud: OpenAI-compatible mesh --
            ProviderDescriptor(
                name="nvidia",
                base_url=NVIDIA_BASE_URL,
                api_key_env="NVIDIA_API_KEY",
                default_model=NVIDIA_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_HEAVY,
                is_openai_compatible=True,
            ),
            ProviderDescriptor(
                name="deepseek",
                base_url=DEEPSEEK_BASE_URL,
                api_key_env="DEEPSEEK_API_KEY",
                default_model=DEEPSEEK_MODEL_CHAT,
                category=CATEGORY_CLOUD_REASONING,
                is_openai_compatible=True,
            ),
            ProviderDescriptor(
                name="groq",
                base_url=GROQ_BASE_URL,
                api_key_env="GROQ_API_KEY",
                default_model=GROQ_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_FAST,
                is_openai_compatible=True,
            ),
            ProviderDescriptor(
                name="cerebras",
                base_url=CEREBRAS_BASE_URL,
                api_key_env="CEREBRAS_API_KEY",
                default_model=CEREBRAS_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_FAST,
                is_openai_compatible=True,
            ),
            ProviderDescriptor(
                name="mistral",
                base_url=MISTRAL_BASE_URL,
                api_key_env="MISTRAL_API_KEY",
                default_model=MISTRAL_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_FAST,
                is_openai_compatible=True,
            ),
            ProviderDescriptor(
                name="huggingface",
                base_url=HF_BASE_URL,
                api_key_env="HF_TOKEN",
                default_model=HF_MODEL_NAME,
                category=CATEGORY_CLOUD_HEAVY,
                is_openai_compatible=True,
            ),
            ProviderDescriptor(
                name="openrouter",
                base_url=OPENROUTER_BASE_URL,
                api_key_env="OPENROUTER_API_KEY",
                default_model=OPENROUTER_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_HEAVY,
                is_openai_compatible=True,
            ),
            # -- Cloud: non-OpenAI-compatible SDK paths --
            ProviderDescriptor(
                name="gemini",
                base_url="https://generativelanguage.googleapis.com",
                api_key_env="GEMINI_API_KEY",
                default_model=GEMINI_FLASH_MODEL,
                category=CATEGORY_CLOUD_REASONING,
                is_openai_compatible=False,
            ),
            ProviderDescriptor(
                name="anthropic",
                base_url="https://api.anthropic.com/v1",
                api_key_env="ANTHROPIC_API_KEY",
                default_model="claude-sonnet-4-5",
                category=CATEGORY_CLOUD_REASONING,
                is_openai_compatible=False,
            ),
            # -- Cloud: v5.20.0 high-throughput inference mesh (OpenAI-compatible) --
            ProviderDescriptor(
                name="sambanova",
                base_url=SAMBANOVA_BASE_URL,
                api_key_env="SAMBANOVA_API_KEY",
                default_model=SAMBANOVA_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_FAST,
                is_openai_compatible=True,
            ),
            ProviderDescriptor(
                name="together",
                base_url=TOGETHER_BASE_URL,
                api_key_env="TOGETHER_API_KEY",
                default_model=TOGETHER_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_FAST,
                is_openai_compatible=True,
            ),
            ProviderDescriptor(
                name="fireworks",
                base_url=FIREWORKS_BASE_URL,
                api_key_env="FIREWORKS_API_KEY",
                default_model=FIREWORKS_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_FAST,
                is_openai_compatible=True,
            ),
            ProviderDescriptor(
                name="deepinfra",
                base_url=DEEPINFRA_BASE_URL,
                api_key_env="DEEPINFRA_API_KEY",
                default_model=DEEPINFRA_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_FAST,
                is_openai_compatible=True,
            ),
            # -- Cloud: v5.20.0 non-OpenAI-compatible SDK paths --
            ProviderDescriptor(
                name="cohere",
                base_url=COHERE_BASE_URL,
                api_key_env="COHERE_API_KEY",
                default_model=COHERE_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_REASONING,
                is_openai_compatible=False,
            ),
            ProviderDescriptor(
                name="perplexity",
                base_url=PERPLEXITY_BASE_URL,
                api_key_env="PERPLEXITY_API_KEY",
                default_model=PERPLEXITY_DEFAULT_MODEL,
                category=CATEGORY_CLOUD_REASONING,
                is_openai_compatible=True,
            ),
        ]
        for descriptor in defaults:
            self.register(descriptor)

    # ------------------------------------------------------------------
    # -- Public API -----------------------------------------------------
    # ------------------------------------------------------------------

    def register(self, descriptor: ProviderDescriptor) -> None:
        """Insert or replace a provider descriptor in the registry.

        Args:
            descriptor (ProviderDescriptor): The descriptor to store.

        Returns:
            None
        """
        self._providers[descriptor.name] = descriptor

    def _refresh(self, descriptor: ProviderDescriptor) -> ProviderDescriptor:
        """Return a descriptor copy with ``is_active`` re-evaluated.

        Args:
            descriptor (ProviderDescriptor): The stored descriptor.

        Returns:
            ProviderDescriptor: A refreshed copy reflecting current state.
        """
        return ProviderDescriptor(
            name=descriptor.name,
            base_url=descriptor.base_url,
            api_key_env=descriptor.api_key_env,
            default_model=descriptor.default_model,
            category=descriptor.category,
            is_openai_compatible=descriptor.is_openai_compatible,
            is_active=self._evaluate_active(descriptor),
        )

    def _evaluate_active(self, descriptor: ProviderDescriptor) -> bool:
        """Determine whether a provider is currently usable.

        Keyless providers (``api_key_env`` is ``None``) are treated as local
        runtimes and probed for port responsiveness. Keyed providers are
        active when their key is present and non-empty.

        Args:
            descriptor (ProviderDescriptor): The descriptor to evaluate.

        Returns:
            bool: True when the provider is currently active.
        """
        if descriptor.api_key_env is None:
            return self._is_port_open(descriptor.base_url)
        key = os.getenv(descriptor.api_key_env, "")
        return bool(key and key.strip())

    @staticmethod
    def _is_port_open(base_url: str, timeout: float = 0.8) -> bool:
        """Probe whether a host/port extracted from a URL answers a TCP connect.

        Args:
            base_url (str): A URL of the form ``http://host:port[/path]``.
            timeout (float): Socket connect timeout in seconds.

        Returns:
            bool: True when the TCP handshake succeeds.
        """
        try:
            host = "127.0.0.1"
            port = 11434
            stripped = base_url.split("://", 1)[-1]
            netloc = stripped.split("/", 1)[0]
            if ":" in netloc:
                host, port_s = netloc.rsplit(":", 1)
                if port_s.isdigit():
                    port = int(port_s)
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except Exception:
            return False
        return False

    def get(self, name: str) -> Optional[ProviderDescriptor]:
        """Return a refreshed descriptor for the named provider.

        Args:
            name (str): Canonical provider identifier.

        Returns:
            Optional[ProviderDescriptor]: The descriptor, or ``None`` when the
                name is not registered.
        """
        descriptor = self._providers.get(name)
        if descriptor is None:
            return None
        return self._refresh(descriptor)

    def list_all(self) -> List[ProviderDescriptor]:
        """Return every registered descriptor with ``is_active`` refreshed.

        Returns:
            list[ProviderDescriptor]: All descriptors in registration order.
        """
        return [self._refresh(d) for d in self._providers.values()]

    def list_active(self) -> List[ProviderDescriptor]:
        """Return only the currently-active descriptors.

        Returns:
            list[ProviderDescriptor]: Active descriptors in registration order.
        """
        return [d for d in self.list_all() if d.is_active]


# -- Module-level convenience singleton ----------------------------------------
_registry_singleton: Optional[ProviderRegistry] = None


def get_provider_registry() -> ProviderRegistry:
    """Return a shared ProviderRegistry singleton.

    Returns:
        ProviderRegistry: The shared registry instance.
    """
    global _registry_singleton
    if _registry_singleton is None:
        _registry_singleton = ProviderRegistry()
    return _registry_singleton


def get_available_providers() -> List[ProviderDescriptor]:
    """Return every currently-active provider descriptor without raising.

    This convenience wrapper reports the active provider set for routing and
    CLI surfaces. It degrades gracefully to an empty list if registry
    construction ever fails (for example, a transient socket probe error),
    honouring the air-gapped, never-crash guarantee of Constitution II. A
    provider with an absent or empty API key is simply reported as inactive
    rather than raising an unhandled exception.

    Returns:
        list[ProviderDescriptor]: The currently-active provider descriptors,
            or an empty list when no provider is usable.
    """
    try:
        return get_provider_registry().list_active()
    except Exception:
        return []
