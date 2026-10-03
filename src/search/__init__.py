# -*- coding: utf-8 -*-
"""
Module: __init__.py
Project: TALOS v5.18.1
Description:
    Package root for the Universal Scientific Search Hub. Hosts the three
    advanced graph-and-embedding discovery engines introduced in v5.15.0:
    ``CitationSnowballEngine`` (citation-graph traversal), ``NeuralVectorSearchEngine``
    (local ``nomic-embed-text`` dense retrieval), and ``CodeFirstSearchEngine``
    (reproducible, code-linked literature discovery). All three operate local-first
    and degrade gracefully to offline/deterministic behaviour.

Dependencies:
    - src.search.citation_snowballing: CitationSnowballEngine.
    - src.search.neural_vector_search: NeuralVectorSearchEngine.
    - src.search.code_first_search: CodeFirstSearchEngine.
"""
from src.search.citation_snowballing import CitationSnowballEngine
from src.search.neural_vector_search import NeuralVectorSearchEngine
from src.search.code_first_search import CodeFirstSearchEngine

__all__ = [
    "CitationSnowballEngine",
    "NeuralVectorSearchEngine",
    "CodeFirstSearchEngine",
]
