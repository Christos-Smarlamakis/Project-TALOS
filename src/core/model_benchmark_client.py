# -*- coding: utf-8 -*-
"""
Module: model_benchmark_client.py
Project: TALOS v5.21.0
Description:
    Backward-compatible shim. The scientific model benchmark client has been
    migrated into the in-tree extraction-ready microservice namespace
    (src/services/cognitive_mesh/benchmarks.py) in v5.21.0. This module
    re-exports the canonical public API so every existing TALOS consumer and
    test continues to resolve
    ``from src.core.model_benchmark_client import ...`` without modification.

Dependencies:
    - src.services.cognitive_mesh.benchmarks: canonical benchmark client.
"""
from src.services.cognitive_mesh.benchmarks import (  # noqa: F401
    DEFAULT_CACHE_PATH,
    DEFAULT_BENCHMARKS,
    ROLE_TITLES,
    ModelBenchmarkClient,
    run_discover_llms,
)
