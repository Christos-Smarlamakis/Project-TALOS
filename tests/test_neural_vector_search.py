# -*- coding: utf-8 -*-
"""
Module: test_neural_vector_search.py
Project: TALOS v5.15.1
Description:
    Unit tests for the NeuralVectorSearchEngine covering cosine similarity,
    embedding response extraction (both Ollama schemas), ranking order, and the
    lexical fallback path when the embedding endpoint is unavailable. Embeddings
    are mocked to keep the suite hermetic and offline, exercising the local
    ``nomic-embed-text`` pipeline without a running Ollama instance.

Dependencies:
    - pytest: Test runner.
    - numpy: Vector construction for assertions.
    - unittest.mock: patch for hermetic embedding stubs.
"""
import numpy as np
import pytest
from unittest.mock import patch

from src.search.neural_vector_search import NeuralVectorSearchEngine


def test_cosine_similarity_identical():
    vector = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    assert NeuralVectorSearchEngine.cosine_similarity(vector, vector) == pytest.approx(1.0)


def test_cosine_similarity_orthogonal():
    u = np.array([1.0, 0.0], dtype=np.float32)
    v = np.array([0.0, 1.0], dtype=np.float32)
    assert NeuralVectorSearchEngine.cosine_similarity(u, v) == pytest.approx(0.0)


def test_cosine_similarity_zero_norm_returns_zero():
    u = np.array([0.0, 0.0], dtype=np.float32)
    v = np.array([1.0, 1.0], dtype=np.float32)
    assert NeuralVectorSearchEngine.cosine_similarity(u, v) == 0.0


def test_extract_vector_new_schema():
    assert NeuralVectorSearchEngine._extract_vector(
        {"embeddings": [[0.1, 0.2, 0.3]]}
    ) == [0.1, 0.2, 0.3]


def test_extract_vector_legacy_schema():
    assert NeuralVectorSearchEngine._extract_vector({"embedding": [0.4, 0.5]}) == [0.4, 0.5]


def test_rank_orders_by_similarity():
    engine = NeuralVectorSearchEngine()
    query_vector = np.array([1.0, 0.0], dtype=np.float32)
    vectors = {
        "": query_vector,
        "matching": query_vector,
        "orthogonal": np.array([0.0, 1.0], dtype=np.float32),
    }
    with patch.object(engine, "embed", side_effect=lambda text: vectors.get(text)):
        candidates = [
            {"id": 1, "title": "orthogonal", "abstract": "orthogonal"},
            {"id": 2, "title": "matching", "abstract": "matching"},
        ]
        ranked = engine.rank("", candidates)
    assert ranked[0]["id"] == 2
    assert ranked[1]["id"] == 1


def test_rank_lexical_fallback_when_embedding_unavailable():
    engine = NeuralVectorSearchEngine()
    with patch.object(engine, "embed", return_value=None):
        candidates = [
            {"id": 1, "title": "swarm robot planning", "abstract": "swarm robot planning"},
            {"id": 2, "title": "unrelated topic", "abstract": "unrelated topic"},
        ]
        ranked = engine.rank("swarm robot planning", candidates)
    assert ranked[0]["id"] == 1
    assert ranked[0].get("lexical_fallback") is True
