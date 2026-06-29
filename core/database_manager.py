# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  For commercial licensing, please contact the author.
"""
Module: database_manager.py (v4.8.5 - Enrichment & Scientometrics)
Project: TALOS v4.8.5

Description:
    Core database layer for Project TALOS. Manages the SQLite database
    (``talos_research.db``) with the complete v4.8.0 schema including 20+
    columns for paper metadata, 4-layer evaluation scores, embeddings, and
    enrichment data. Supports profile-aware initialization so maintenance
    scripts can target the active profile's database.

    Key features:
    - Full schema creation with automatic legacy migration
    - CRUD operations for papers with deduplication (DOI/URL)
    - Embedding storage and in-memory cosine similarity search
    - Batch enrichment updates via ``executemany``
    - Database statistics and health reporting
"""
import sqlite3
import os
from datetime import date, datetime, timedelta
import pickle
import numpy as np
import pandas as pd
from typing import Union, List, Dict, Any, Tuple


class DatabaseManager:
    """Manages the TALOS SQLite database with embeddings and enrichment.

    Handles schema creation, paper CRUD, embedding storage/retrieval,
    semantic search, and statistics. Supports profile-aware initialization
    via an optional ``db_path`` argument.

    Attributes:
        db_path (str): Full path to the SQLite database file.
        _embedding_ids (list of int): Paper IDs that have embeddings.
        _embedding_vectors (np.ndarray or None): Embedding vectors loaded in memory.
    """

    def __init__(self, db_path=None, db_name="talos_research.db"):
        """Initialize the database manager.

        Args:
            db_path (str, optional): Full path to the .db file (for Profiles).
            db_name (str): Filename if looking in the project root.
        """
        if db_path:
            self.db_path = db_path
        else:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            self.db_path = os.path.join(project_root, db_name)

        self.create_table()

        self._embedding_ids: List[int] = []
        self._embedding_vectors: Union[np.ndarray, None] = None
        self._load_embeddings_into_memory()

    def _table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database.

        Args:
            table_name (str): Name of the table to check.

        Returns:
            bool: True if the table exists.
        """
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        result = self.execute_query(query, (table_name,), fetch_one=True)
        return result is not None

    def _load_embeddings_into_memory(self):
        """Load all embedding vectors from the database into memory for fast search."""
        if not self._table_exists('papers'): return
        all_embeddings_data = self.get_all_embeddings()
        if not all_embeddings_data: return

        temp_vectors = []
        for item in all_embeddings_data:
            if item and 'embedding' in item and isinstance(item['embedding'], bytes):
                try:
                    self._embedding_ids.append(item['id'])
                    temp_vectors.append(pickle.loads(item['embedding']))
                except (pickle.UnpicklingError, EOFError):
                    self._embedding_ids.pop()
        if temp_vectors:
            self._embedding_vectors = np.array(temp_vectors)

    # --- Query Execution ---

    def execute_query(self, query, params=(), commit=False, fetch_one=False, fetch_all=False):
        """Execute a single SQL query.

        Args:
            query (str): SQL query string.
            params (tuple): Query parameters.
            commit (bool): If True, commit after execution and return lastrowid.
            fetch_one (bool): If True, return a single row.
            fetch_all (bool): If True, return all rows.

        Returns:
            Various: Query result depending on flags, or None on error.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                    return cursor.lastrowid
                if fetch_one:
                    return cursor.fetchone()
                if fetch_all:
                    return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            return None

    def execute_many(self, query, params_list, commit=False):
        """Execute a batch of queries using executemany.

        Args:
            query (str): SQL query string with placeholders.
            params_list (list of tuple): List of parameter tuples.
            commit (bool): If True, commit after execution.

        Returns:
            int or None: Row count, or None on error.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                if commit:
                    conn.commit()
                    return cursor.rowcount
        except sqlite3.Error as e:
            print(f"Database Error (Batch): {e}")
            return None

    # --- Schema ---

    def create_table(self):
        """Create the papers table with the complete v4.8.0 schema.

        New databases get all columns from creation. Existing databases
        are upgraded via legacy column check for operational_score.
        """
        table_query = '''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                doi TEXT UNIQUE, url TEXT, title TEXT, authors TEXT, 
                publication_year INTEGER, abstract TEXT, source TEXT,
                strategic_score INTEGER DEFAULT 0,
                operational_score INTEGER DEFAULT 0,
                tactical_score INTEGER DEFAULT 0,
                playground_score INTEGER DEFAULT 0,
                overall_score REAL DEFAULT 0.0,
                evaluation_reasoning TEXT, evaluation_contribution TEXT, evaluation_utilization TEXT,
                suggested_tags TEXT, suggested_folder TEXT, suggested_discord_channel TEXT,
                in_zotero INTEGER DEFAULT 0, 
                embedding BLOB, 
                processed_at DATE,
                last_evaluated_at DATETIME,
                oa_pdf_url TEXT,
                openalex_id TEXT,
                pmid TEXT,
                pmcid TEXT,
                oa_status TEXT,
                journal_issn TEXT,
                publisher TEXT,
                enrichment_status INTEGER DEFAULT 0
            )
        '''
        self.execute_query(table_query, commit=True)
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_papers_url ON papers(url);", commit=True)

        cols = self.execute_query("PRAGMA table_info(papers);", fetch_all=True)
        if cols and not any(col[1] == 'operational_score' for col in cols):
            self.execute_query("ALTER TABLE papers ADD COLUMN operational_score INTEGER DEFAULT 0;", commit=True)

    # --- Paper CRUD ---

    def paper_exists_by_doi(self, doi: str) -> bool:
        """Check if a paper exists by DOI.

        Args:
            doi (str): The DOI to check.

        Returns:
            bool: True if the paper exists.
        """
        if not doi: return False
        return bool(self.execute_query("SELECT 1 FROM papers WHERE doi = ?", (doi,), fetch_one=True))

    def paper_exists_by_url(self, url: str) -> bool:
        """Check if a paper exists by URL.

        Args:
            url (str): The URL to check.

        Returns:
            bool: True if the paper exists.
        """
        if not url: return False
        return bool(self.execute_query("SELECT 1 FROM papers WHERE url = ?", (url,), fetch_one=True))

    def get_paper_id_by_doi(self, doi: str) -> Union[int, None]:
        """Get a paper's ID by its DOI.

        Args:
            doi (str): The paper's DOI.

        Returns:
            int or None: Paper ID, or None if not found.
        """
        if not doi: return None
        result = self.execute_query("SELECT id FROM papers WHERE doi = ?", (doi,), fetch_one=True)
        return result[0] if result else None

    def get_paper_id_by_url(self, url: str) -> Union[int, None]:
        """Get a paper's ID by its URL.

        Args:
            url (str): The paper's URL.

        Returns:
            int or None: Paper ID, or None if not found.
        """
        if not url: return None
        result = self.execute_query("SELECT id FROM papers WHERE url = ?", (url,), fetch_one=True)
        return result[0] if result else None

    def _calculate_overall_score(self, scores: Dict[str, Any]) -> float:
        """Calculate the overall score from the 4-layer framework.

        Weights: Strategic 30%, Operational 30%, Tactical 30%, Playground 10%.

        Args:
            scores (dict): Must contain 'strategic', 'operational', 'tactical', 'playground'.

        Returns:
            float: Weighted overall score rounded to 2 decimal places.
        """
        strategic = scores.get('strategic', 0)
        operational = scores.get('operational', 0)
        tactical = scores.get('tactical', 0)
        playground = scores.get('playground', 0)
        return round((strategic * 0.3) + (operational * 0.3) + (tactical * 0.3) + (playground * 0.1), 2)

    def add_paper(self, paper_data: Dict[str, Any], evaluation_data: Dict[str, Any],
                  in_zotero: int = 0) -> Union[int, None]:
        """Insert a new paper with evaluation data.

        Args:
            paper_data (dict): Paper metadata (doi, url, title, authors, etc.).
            evaluation_data (dict): AI evaluation with scores, reasoning, tags.
            in_zotero (int): 1 if already in Zotero, 0 otherwise.

        Returns:
            int or None: New paper ID, or None on failure.
        """
        scores = evaluation_data.get('scores', {})
        tags_str = ','.join(evaluation_data.get('tags', []))
        overall_score = evaluation_data.get('overall_score') or self._calculate_overall_score(scores)

        sql = """INSERT INTO papers (
            doi, url, title, authors, publication_year, abstract, source, 
            strategic_score, operational_score, tactical_score, playground_score, overall_score, 
            evaluation_reasoning, evaluation_contribution, evaluation_utilization, 
            suggested_tags, suggested_folder, suggested_discord_channel, 
            in_zotero, processed_at, last_evaluated_at, enrichment_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)"""

        params = (
            paper_data.get('doi'), paper_data.get('url'), paper_data.get('title'),
            paper_data.get('authors_str'), paper_data.get('publication_year'),
            paper_data.get('abstract'), paper_data.get('source'),
            scores.get('strategic', 0), scores.get('operational', 0),
            scores.get('tactical', 0), scores.get('playground', 0),
            overall_score, evaluation_data.get('reasoning', ''),
            evaluation_data.get('contribution', ''), evaluation_data.get('utilization', ''),
            tags_str, evaluation_data.get('folder', ''),
            evaluation_data.get('discord_channel', ''),
            in_zotero, date.today().strftime('%Y-%m-%d'), datetime.now()
        )
        paper_id = self.execute_query(sql, params, commit=True)
        if paper_id:
            print(f"  > ID:{paper_id} - Saved '{paper_data.get('title')}' with score: {overall_score:.2f}.")
        return paper_id

    def update_paper_evaluation(self, paper_id: int, evaluation_data: Dict[str, Any]):
        """Update an existing paper's evaluation scores and reasoning.

        Args:
            paper_id (int): The paper's ID.
            evaluation_data (dict): New AI evaluation data.
        """
        scores = evaluation_data.get('scores', {})
        tags_str = ','.join(evaluation_data.get('tags', []))
        overall_score = evaluation_data.get('overall_score') or self._calculate_overall_score(scores)

        sql = """UPDATE papers SET
                    strategic_score = ?, operational_score = ?, tactical_score = ?, playground_score = ?,
                    overall_score = ?, evaluation_reasoning = ?,
                    evaluation_contribution = ?, evaluation_utilization = ?,
                    suggested_tags = ?, suggested_folder = ?, suggested_discord_channel = ?,
                    last_evaluated_at = ?
                WHERE id = ?"""
        params = (
            scores.get('strategic', 0), scores.get('operational', 0),
            scores.get('tactical', 0), scores.get('playground', 0),
            overall_score, evaluation_data.get('reasoning', ''),
            evaluation_data.get('contribution', ''), evaluation_data.get('utilization', ''),
            tags_str, evaluation_data.get('folder', ''),
            evaluation_data.get('discord_channel', ''),
            datetime.now(), paper_id
        )
        self.execute_query(sql, params, commit=True)
        print(f"  --> Updated evaluation for Paper ID: {paper_id}")

    def get_papers_not_recently_evaluated(self, days_window: int, limit: int) -> List[Tuple]:
        """Get papers that haven't been evaluated recently.

        Args:
            days_window (int): Number of days to consider "recent".
            limit (int): Maximum number of papers to return.

        Returns:
            list of tuple: Papers ordered by overall_score descending.
        """
        cutoff_date = datetime.now() - timedelta(days=days_window)
        query = "SELECT id, title, abstract, overall_score FROM papers WHERE last_evaluated_at IS NULL OR last_evaluated_at < ? ORDER BY overall_score DESC LIMIT ?"
        results = self.execute_query(query, (cutoff_date, limit), fetch_all=True)
        return results if results is not None else []

    def get_all_papers_for_dashboard(self) -> List[Dict[str, Any]]:
        """Get all papers for the interactive dashboard.

        Returns:
            list of dict: All papers ordered by overall_score descending.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT id, doi, url, title, authors, publication_year, abstract, source, strategic_score, operational_score, tactical_score, playground_score, overall_score, in_zotero, oa_pdf_url FROM papers ORDER BY overall_score DESC"
            return [dict(row) for row in conn.cursor().execute(query)]

    def get_single_paper_details(self, paper_id: int) -> Union[Dict[str, Any], None]:
        """Get all details for a single paper.

        Args:
            paper_id (int): The paper's ID.

        Returns:
            dict or None: Full paper data as a dictionary.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM papers WHERE id = ?"
            paper = conn.cursor().execute(query, (paper_id,)).fetchone()
            return dict(paper) if paper else None

    def update_zotero_status_by_id(self, paper_id: int, status: int):
        """Update the 'in_zotero' status for a paper.

        Args:
            paper_id (int): The paper's ID.
            status (int): 1 = in Zotero, 0 = not in Zotero.
        """
        self.execute_query("UPDATE papers SET in_zotero = ? WHERE id = ?", (status, paper_id), commit=True)

    # --- Embeddings ---

    def get_papers_without_embedding(self) -> List[Dict[str, Any]]:
        """Get papers that need embeddings generated.

        Returns:
            list of dict: Papers with NULL embedding, containing id, title, abstract.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.cursor().execute(
                "SELECT id, title, abstract FROM papers WHERE embedding IS NULL")]

    def update_embeddings_batch(self, updates: List[Tuple]):
        """Batch update embeddings for multiple papers.

        Args:
            updates (list of tuple): List of (embedding_blob, paper_id) tuples.
        """
        self.execute_many("UPDATE papers SET embedding = ? WHERE id = ?", updates, commit=True)

    def get_all_embeddings(self) -> List[Dict[str, Any]]:
        """Get all stored embeddings.

        Returns:
            list of dict: Papers with non-NULL embeddings (id, embedding).
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.cursor().execute(
                "SELECT id, embedding FROM papers WHERE embedding IS NOT NULL")]

    def get_papers_by_ids(self, ids: list) -> List[Dict[str, Any]]:
        """Get papers by a list of IDs.

        Args:
            ids (list of int): Paper IDs to fetch.

        Returns:
            list of dict: Paper data for the requested IDs.
        """
        if not ids: return []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            placeholders = ', '.join('?' for _ in ids)
            query = f"SELECT id, doi, url, title, authors, publication_year, abstract, source, strategic_score, operational_score, tactical_score, playground_score, overall_score, in_zotero FROM papers WHERE id IN ({placeholders})"
            return [dict(row) for row in conn.cursor().execute(query, ids)]

    def get_recent_core_papers(self, limit: int = 10, min_score: float = 7.0) -> List[Dict[str, Any]]:
        """Get recent high-scoring papers for citation analysis.

        Args:
            limit (int): Maximum number of papers.
            min_score (float): Minimum overall_score threshold.

        Returns:
            list of dict: Top papers with title, doi, overall_score.
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT title, doi, overall_score FROM papers WHERE overall_score >= ? ORDER BY processed_at DESC LIMIT ?"
            return [dict(row) for row in conn.cursor().execute(query, (min_score, limit))]

    def semantic_search(self, query_vector: np.ndarray, top_k: int = 100) -> List[int]:
        """Perform cosine similarity semantic search.

        Args:
            query_vector (np.ndarray): The query embedding vector.
            top_k (int): Number of top results to return.

        Returns:
            list of int: Paper IDs sorted by similarity (closest first).
        """
        if self._embedding_vectors is None or len(self._embedding_ids) == 0: return []
        dot_products = np.dot(self._embedding_vectors, query_vector)
        paper_norms = np.linalg.norm(self._embedding_vectors, axis=1)
        query_norm = np.linalg.norm(query_vector)
        similarities = np.zeros(len(self._embedding_ids))
        valid_indices = (paper_norms > 0) & (query_norm > 0)
        similarities[valid_indices] = dot_products[valid_indices] / (paper_norms[valid_indices] * query_norm)
        top_indices = np.argpartition(similarities, -top_k)[-top_k:]
        sorted_top_indices = top_indices[np.argsort(similarities[top_indices])][::-1]
        return [self._embedding_ids[i] for i in sorted_top_indices]

    # --- DataFrame Export ---

    def get_all_papers_as_dataframe(self) -> pd.DataFrame:
        """Export all papers as a pandas DataFrame.

        Returns:
            pd.DataFrame: All papers, or empty DataFrame on failure.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM papers", conn)
                return df
        except Exception as e:
            print(f"DataFrame load failed: {e}")
            return pd.DataFrame()

    # --- Statistics ---

    def get_database_statistics(self) -> Dict[str, Any]:
        """Get comprehensive database statistics.

        Returns:
            dict: Statistics including total_papers, elite_papers, avg_score,
            by_source breakdown, embedded_papers count, etc.
        """
        stats = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM papers")
            stats['total_papers'] = cursor.fetchone()[0]

            try:
                cursor.execute("SELECT COUNT(*) FROM papers WHERE enrichment_status = 1")
                stats['enriched_papers'] = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM papers WHERE oa_pdf_url IS NOT NULL")
                stats['pdf_links'] = cursor.fetchone()[0]
            except sqlite3.Error:
                stats['enriched_papers'] = 0
                stats['pdf_links'] = 0

            cursor.execute("SELECT source, COUNT(*) FROM papers GROUP BY source ORDER BY COUNT(*) DESC")
            stats['by_source'] = cursor.fetchall()

            cursor.execute("SELECT AVG(overall_score) FROM papers")
            avg = cursor.fetchone()[0]
            stats['avg_score'] = round(avg, 2) if avg else 0.0

            cursor.execute("SELECT COUNT(*) FROM papers WHERE overall_score > 7")
            stats['elite_papers'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM papers WHERE doi IS NULL OR doi = ''")
            stats['missing_doi'] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM papers WHERE embedding IS NOT NULL")
            stats['embedded_papers'] = cursor.fetchone()[0]

        return stats

    # --- Enrichment ---

    def get_papers_for_enrichment(self):
        """Get papers that need data enrichment (enrichment_status = 0 or NULL).

        Returns:
            list of tuple: Papers with id, doi, abstract.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = "SELECT id, doi, abstract FROM papers WHERE (enrichment_status = 0 OR enrichment_status IS NULL) AND doi IS NOT NULL"
                cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.Error:
            return []

    def update_papers_enrichment_batch(self, update_list):
        """Batch update papers with enrichment data from Unpaywall.

        Args:
            update_list (list of dict): Each dict must contain paper_id, oa_pdf_url,
                openalex_id, pmid, pmcid, oa_status, journal_issn, publisher, status.
        """
        if not update_list:
            return

        query = """
            UPDATE papers 
            SET 
                oa_pdf_url = :oa_pdf_url,
                openalex_id = :openalex_id,
                pmid = :pmid,
                pmcid = :pmcid,
                oa_status = :oa_status,
                journal_issn = :journal_issn,
                publisher = :publisher,
                enrichment_status = :status
            WHERE id = :paper_id
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(query, update_list)
                conn.commit()
        except sqlite3.Error as e:
            print(f"Error in batch enrichment update: {e}")