# -*- coding: utf-8 -*-
"""
Module: provider_registry.py
Project: TALOS v5.21.1
Description:
    Backward-compatible shim. The sixteen-provider pluggable registry has been
    migrated into the in-tree extraction-ready microservice namespace
    (src/services/cognitive_mesh/registry.py) in v5.21.1. This module
    re-exports the canonical public API so every existing TALOS consumer
    (AIManager) and test continues to resolve
    ``from src.core.provider_registry import ...`` without modification or
    deprecation breakage.

Dependencies:
    - src.services.cognitive_mesh.registry: canonical ProviderRegistry.
"""
from src.services.cognitive_mesh.registry import (  # noqa: F401
    CATEGORY_LOCAL_GPU,
    CATEGORY_LOCAL_CPU,
    CATEGORY_CLOUD_REASONING,
    CATEGORY_CLOUD_FAST,
    CATEGORY_CLOUD_HEAVY,
    LLMProvider,
    ProviderDescriptor,
    ProviderRegistry,
    get_provider_registry,
    get_available_providers,
)
