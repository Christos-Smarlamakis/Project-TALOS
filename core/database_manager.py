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
Module: database_manager.py (v4.8.0 - Enrichment & Scientometrics)
Project: TALOS v4.8.0

Description:
Διαχειρίζεται τη βάση δεδομένων SQLite.
- v4.8.0: Updated Schema for Enrichment (IDs, OA Status).
- v4.8.0: Support for Profiles (db_path).
- v4.8.0: Batch Enrichment methods.
"""
import sqlite3
import os
from datetime import date, datetime, timedelta
import pickle
import numpy as np
import pandas as pd
from typing import Union, List, Dict, Any, Tuple

class DatabaseManager:
    def __init__(self, db_path=None, db_name="talos_research.db"):
        """
        Αρχικοποίηση.
        :param db_path: (Προαιρετικό) Πλήρες path για το αρχείο .db (για Profiles).
        :param db_name: (Προαιρετικό) Όνομα αρχείου αν ψάχνουμε στο root.
        """
        if db_path:
            self.db_path = db_path
        else:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
            self.db_path = os.path.join(project_root, db_name)
        
        # 1. Δημιουργία Πινάκων (με το πλήρες v4.8.0 schema)
        self.create_table()

        # 2. Φόρτωση Embeddings
        self._embedding_ids: List[int] = []
        self._embedding_vectors: Union[np.ndarray, None] = None
        self._load_embeddings_into_memory()
        
    def _table_exists(self, table_name: str) -> bool:
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        result = self.execute_query(query, (table_name,), fetch_one=True)
        return result is not None

    def _load_embeddings_into_memory(self):
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

    def execute_query(self, query, params=(), commit=False, fetch_one=False, fetch_all=False):
        """Εκτελεί ΕΝΑ query."""
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
        """Εκτελεί ΠΟΛΛΑ queries μαζικά (Batch execution)."""
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

    # --- INITIALIZATION ---

    def create_table(self):
        """
        Δημιουργεί τον πίνακα με το πλήρες schema της v4.8.0.
        Αυτό εξασφαλίζει ότι οι ΝΕΕΣ βάσεις θα είναι εξαρχής σωστές.
        Οι υπάρχουσες βάσεις αναβαθμίζονται μέσω του 'scripts/upgrade_to_v4_8.py'.
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
                -- v4.8.0 New Columns (Data Enrichment) --
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
        
        # Legacy check για πολύ παλιές βάσεις που μπορεί να μην έχουν το operational_score
        try:
            self.execute_query("ALTER TABLE papers ADD COLUMN operational_score INTEGER DEFAULT 0;", commit=True)
        except sqlite3.OperationalError:
            pass

    # --- CORE METHODS ---

    def paper_exists_by_doi(self, doi: str) -> bool:
        if not doi: return False
        return bool(self.execute_query("SELECT 1 FROM papers WHERE doi = ?", (doi,), fetch_one=True))

    def paper_exists_by_url(self, url: str) -> bool:
        if not url: return False
        return bool(self.execute_query("SELECT 1 FROM papers WHERE url = ?", (url,), fetch_one=True))

    def get_paper_id_by_doi(self, doi: str) -> Union[int, None]:
        if not doi: return None
        result = self.execute_query("SELECT id FROM papers WHERE doi = ?", (doi,), fetch_one=True)
        return result[0] if result else None

    def get_paper_id_by_url(self, url: str) -> Union[int, None]:
        if not url: return None
        result = self.execute_query("SELECT id FROM papers WHERE url = ?", (url,), fetch_one=True)
        return result[0] if result else None
        
    def _calculate_overall_score(self, scores: Dict[str, Any]) -> float:
        strategic = scores.get('strategic', 0)
        operational = scores.get('operational', 0)
        tactical = scores.get('tactical', 0)
        playground = scores.get('playground', 0)
        return round((strategic * 0.3) + (operational * 0.3) + (tactical * 0.3) + (playground * 0.1), 2)

    def add_paper(self, paper_data: Dict[str, Any], evaluation_data: Dict[str, Any], in_zotero: int = 0) -> Union[int, None]:
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
            scores.get('strategic', 0), scores.get('operational', 0), scores.get('tactical', 0), scores.get('playground', 0),
            overall_score, evaluation_data.get('reasoning', ''), 
            evaluation_data.get('contribution', ''), evaluation_data.get('utilization', ''), 
            tags_str, evaluation_data.get('folder', ''), evaluation_data.get('discord_channel', ''),
            in_zotero, date.today().strftime('%Y-%m-%d'), datetime.now()
        )
        paper_id = self.execute_query(sql, params, commit=True)
        if paper_id:
            print(f"  > ID:{paper_id} - Saved '{paper_data.get('title')}' with score: {overall_score:.2f}.")
        return paper_id

    def update_paper_evaluation(self, paper_id: int, evaluation_data: Dict[str, Any]):
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
            scores.get('strategic', 0), scores.get('operational', 0), scores.get('tactical', 0), scores.get('playground', 0),
            overall_score, evaluation_data.get('reasoning', ''), 
            evaluation_data.get('contribution', ''), evaluation_data.get('utilization', ''), 
            tags_str, evaluation_data.get('folder', ''), evaluation_data.get('discord_channel', ''),
            datetime.now(), paper_id
        )
        self.execute_query(sql, params, commit=True)
        print(f"  --> Updated evaluation for Paper ID: {paper_id}")

    def get_papers_not_recently_evaluated(self, days_window: int, limit: int) -> List[Tuple]:
        cutoff_date = datetime.now() - timedelta(days=days_window)
        query = "SELECT id, title, abstract, overall_score FROM papers WHERE last_evaluated_at IS NULL OR last_evaluated_at < ? ORDER BY overall_score DESC LIMIT ?"
        results = self.execute_query(query, (cutoff_date, limit), fetch_all=True)
        return results if results is not None else []

    def get_all_papers_for_dashboard(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT id, doi, url, title, authors, publication_year, abstract, source, strategic_score, operational_score, tactical_score, playground_score, overall_score, in_zotero, oa_pdf_url FROM papers ORDER BY overall_score DESC"
            return [dict(row) for row in conn.cursor().execute(query)]
    
    def get_single_paper_details(self, paper_id: int) -> Union[Dict[str, Any], None]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM papers WHERE id = ?" 
            paper = conn.cursor().execute(query, (paper_id,)).fetchone()
            return dict(paper) if paper else None

    def update_zotero_status_by_id(self, paper_id: int, status: int):
         self.execute_query("UPDATE papers SET in_zotero = ? WHERE id = ?", (status, paper_id), commit=True)

    def get_papers_without_embedding(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.cursor().execute("SELECT id, title, abstract FROM papers WHERE embedding IS NULL")]

    def update_embeddings_batch(self, updates: List[Tuple]):
        self.execute_many("UPDATE papers SET embedding = ? WHERE id = ?", updates, commit=True)

    def get_all_embeddings(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.cursor().execute("SELECT id, embedding FROM papers WHERE embedding IS NOT NULL")]

    def get_papers_by_ids(self, ids: list) -> List[Dict[str, Any]]:
        if not ids: return []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            placeholders = ', '.join('?' for _ in ids)
            query = f"SELECT id, doi, url, title, authors, publication_year, abstract, source, strategic_score, operational_score, tactical_score, playground_score, overall_score, in_zotero FROM papers WHERE id IN ({placeholders})"
            return [dict(row) for row in conn.cursor().execute(query, ids)]

    def get_recent_core_papers(self, limit: int = 10, min_score: float = 7.0) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = "SELECT title, doi, overall_score FROM papers WHERE overall_score >= ? ORDER BY processed_at DESC LIMIT ?"
            return [dict(row) for row in conn.cursor().execute(query, (min_score, limit))]
    
    def semantic_search(self, query_vector: np.ndarray, top_k: int = 100) -> List[int]:
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
    
    def get_all_papers_as_dataframe(self) -> pd.DataFrame:
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM papers", conn)
                return df
        except Exception as e:
            print(f"DataFrame load failed: {e}")
            return pd.DataFrame()

    def get_database_statistics(self) -> Dict[str, Any]:
        stats = {}
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM papers")
            stats['total_papers'] = cursor.fetchone()[0]
            
            # v4.8.0 Stats with safety check
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
            
        return stats
    
    # --- TALOS v4.8.0 ENRICHMENT METHODS ---

    def get_papers_for_enrichment(self):
        """
        Retrieves papers that have not yet been enriched (enrichment_status = 0).
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                query = "SELECT id, doi, abstract FROM papers WHERE (enrichment_status = 0 OR enrichment_status IS NULL) AND doi IS NOT NULL"
                cursor.execute(query)
                return cursor.fetchall()
        except sqlite3.Error as e:
            # print(f"Error fetching papers for enrichment: {e}")
            return []

    def update_papers_enrichment_batch(self, update_list):
        """
        Batch updates papers with enrichment data.
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