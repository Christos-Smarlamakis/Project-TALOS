# -*- coding: utf-8 -*-
"""
Module: neural_vector_search.py
Project: TALOS v5.15.0
Description:
    Neural vector semantic search engine. Encodes a research query and candidate
    paper abstracts into dense embedding vectors using the local Ollama model
    ``nomic-embed-text`` (port 11434), then ranks candidates by cosine similarity
    to overcome the vocabulary-mismatch problem of pure keyword retrieval. The
    engine is fully local-first: it never contacts an external vector database and
    degrades gracefully to a deterministic lexical fallback when Ollama is
    unreachable.

    Key design decisions:
    - Embeddings are obtained via the native Ollama HTTP API (``/api/embeddings``
      with a ``/api/embed`` fallback for older Ollama builds).
    - Cosine similarity is computed with NumPy for memory-efficient, vectorized
      ranking over the candidate corpus.
    - The embedding model is configurable via the ``TALOS_EMBEDDING_MODEL``
      environment variable (default ``nomic-embed-text``).

Dependencies:
    - os: Environment variable access.
    - json: Payload serialization.
    - requests: HTTP client for the local Ollama embedding endpoint.
    - numpy: Vectorized cosine-similarity computation.
"""
import os
import json

import requests
import numpy as np

try:
    from config.settings import OLLAMA_BASE_URL
except ImportError:  # pragma: no cover - settings package fallback
    OLLAMA_BASE_URL = "http://127.0.0.1:11434"


class NeuralVectorSearchEngine:
    """Rank papers semantically using local dense embeddings and cosine similarity.

    Encodes the query and every candidate abstract with ``nomic-embed-text``
    running on the local Ollama instance, then returns the top-k candidates ranked
    by the cosine similarity metric
    ``S_C(u, v) = (u . v) / (||u|| * ||v||)``.

    Attributes:
        model (str): Embedding model label.
        base_url (str): Ollama base URL.
        endpoint (str or None): Resolved embedding endpoint (detected lazily).
    """

    DEFAULT_MODEL = "nomic-embed-text"
    ENDPOINT_CANDIDATES = ("/api/embeddings", "/api/embed")

    def __init__(self, model: str = None, base_url: str = None, timeout: int = 30):
        """Initialize the engine.

        Args:
            model (str, optional): Embedding model label. Defaults to
                ``nomic-embed-text`` or the ``TALOS_EMBEDDING_MODEL`` env var.
            base_url (str, optional): Ollama base URL. Defaults to the configured
                ``OLLAMA_BASE_URL``.
            timeout (int): HTTP request timeout in seconds.
        """
        self.model = model or os.getenv("TALOS_EMBEDDING_MODEL", self.DEFAULT_MODEL)
        self.base_url = (base_url or OLLAMA_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.endpoint = None

    def embed(self, text: str):
        """Encode a single text string into a dense embedding vector.

        Args:
            text (str): Input text (query or abstract).

        Returns:
            numpy.ndarray: The embedding vector, or None when Ollama is unreachable.
        """
        if not text or not text.strip():
            return None
        for endpoint in self.ENDPOINT_CANDIDATES:
            try:
                url = f"{self.base_url}{endpoint}"
                payload = {"model": self.model, "prompt": text}
                response = requests.post(url, json=payload, timeout=self.timeout)
                if response.status_code == 404:
                    continue  # try the legacy endpoint
                response.raise_for_status()
                data = response.json()
                vector = self._extract_vector(data)
                if vector is not None:
                    self.endpoint = endpoint
                    return np.asarray(vector, dtype=np.float32)
            except (requests.RequestException, ValueError, KeyError):
                continue
        return None

    @staticmethod
    def _extract_vector(data):
        """Recover a flat embedding vector from either Ollama response schema.

        Args:
            data (dict): Parsed JSON response.

        Returns:
            list or None: The embedding vector, or None when absent.
        """
        if isinstance(data.get("embeddings"), list) and data["embeddings"]:
            return data["embeddings"][0]
        if isinstance(data.get("embedding"), list):
            return data["embedding"]
        return None

    @staticmethod
    def cosine_similarity(u, v):
        """Compute the cosine similarity between two vectors.

        Args:
            u (numpy.ndarray): First vector.
            v (numpy.ndarray): Second vector.

        Returns:
            float: Cosine similarity in [-1, 1], or 0.0 on a zero-norm input.
        """
        u = np.asarray(u, dtype=np.float32)
        v = np.asarray(v, dtype=np.float32)
        norm_u = float(np.linalg.norm(u))
        norm_v = float(np.linalg.norm(v))
        if norm_u == 0.0 or norm_v == 0.0:
            return 0.0
        return float(np.dot(u, v) / (norm_u * norm_v))

    def rank(self, query: str, candidates):
        """Rank candidate papers by semantic similarity to the query.

        Args:
            query (str): Natural-language research query.
            candidates (list): Candidate records, each a dict with at least
                ``title`` and ``abstract`` keys.

        Returns:
            list: Candidates annotated with a ``similarity`` score, sorted
                descending. Falls back to lexical scoring when embeddings fail.
        """
        if not candidates:
            return []
        query_vector = self.embed(query)
        if query_vector is None:
            return self._lexical_rank(query, candidates)

        scored = []
        for candidate in candidates:
            abstract = str(candidate.get("abstract") or candidate.get("title") or "")
            vector = self.embed(abstract)
            score = self.cosine_similarity(query_vector, vector) if vector is not None else 0.0
            enriched = dict(candidate)
            enriched["similarity"] = round(score, 4)
            scored.append(enriched)

        scored.sort(key=lambda item: item["similarity"], reverse=True)
        return scored

    @staticmethod
    def _lexical_rank(query: str, candidates):
        """Fallback lexical scorer used when the embedding endpoint is offline.

        Args:
            query (str): Research query.
            candidates (list): Candidate records.

        Returns:
            list: Candidates annotated with a lexical overlap similarity score.
        """
        terms = {t.lower() for t in query.split() if len(t) > 2}
        scored = []
        for candidate in candidates:
            blob = " ".join(
                str(candidate.get(k) or "")
                for k in ("title", "abstract")
            ).lower()
            hits = sum(1 for term in terms if term in blob)
            similarity = (hits / len(terms)) if terms else 0.0
            enriched = dict(candidate)
            enriched["similarity"] = round(similarity, 4)
            enriched["lexical_fallback"] = True
            scored.append(enriched)
        scored.sort(key=lambda item: item["similarity"], reverse=True)
        return scored

    def search(self, query: str, candidates, top_k: int = 10):
        """Rank candidates and return the top-k most relevant.

        Args:
            query (str): Natural-language research query.
            candidates (list): Candidate paper records.
            top_k (int): Number of results to return.

        Returns:
            list: Top-k ranked candidates.
        """
        ranked = self.rank(query, candidates)
        return ranked[:max(0, top_k)]

    def run(self, query: str, top_k: int = 10):
        """Search the active profile database semantically.

        Loads candidate papers (with abstracts) from the active-profile database
        and ranks them against the query.

        Args:
            query (str): Natural-language research query.
            top_k (int): Number of results to return.

        Returns:
            list: Top-k ranked paper records.
        """
        candidates = self._load_candidates()
        if not candidates:
            print("[WARN] NeuralVectorSearchEngine: no candidates with abstracts in the active profile DB.")
            return []
        return self.search(query, candidates, top_k=top_k)

    def _load_candidates(self):
        """Load candidate papers from the active profile database.

        Returns:
            list: Paper records with id/title/abstract/doi/url.
        """
        try:
            from src.core.database_manager import DatabaseManager
            db = DatabaseManager()
            rows = db.execute_query(
                "SELECT id, title, abstract, doi, url FROM papers "
                "WHERE abstract IS NOT NULL AND abstract != ''",
                fetch_all=True,
            )
            return [
                {
                    "id": row[0],
                    "title": row[1],
                    "abstract": row[2],
                    "doi": row[3],
                    "url": row[4],
                }
                for row in (rows or [])
            ]
        except Exception as exc:  # pragma: no cover - DB unavailable
            print(f"[WARN] NeuralVectorSearchEngine: could not load candidates ({exc}).")
            return []


def dump_result(results):
    """Serialize ranked results to JSON for CLI output.

    Args:
        results (list): Ranked candidate records.

    Returns:
        str: Pretty-printed JSON string.
    """
    return json.dumps(results, ensure_ascii=False, indent=2, default=str)
