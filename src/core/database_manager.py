# -*- coding: utf-8 -*-
#  Project TALOS
#  Copyright (C) 2026 Christos Smarlamakis
#
#  This program is free software...
"""
Module: database_manager.py (v5.0 - Multi-Provider Hybrid Embeddings)
Project: TALOS v5.9.18
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
        if db_path:
            self.db_path = db_path
        else:
            # Resolve actual project root by walking up from this file until talos.py is found
            # (same pattern used by every src/*.py script in the project)
            project_root = os.path.abspath(os.path.dirname(__file__))
            while project_root and not os.path.exists(os.path.join(project_root, 'talos.py')):
                parent = os.path.dirname(project_root)
                if parent == project_root:  # reached filesystem root
                    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
                    break
                project_root = parent
            # Canonical location: data/talos_research.db (takes priority over profiles)
            data_dir = os.path.join(project_root, "data")
            canonical_path = os.path.join(data_dir, db_name)
            if os.path.exists(canonical_path):
                self.db_path = canonical_path
            else:
                # Fallback to active profile DB; if neither exists, create in data/
                profile_db = self._resolve_profile_db(project_root)
                if profile_db:
                    self.db_path = profile_db
                else:
                    os.makedirs(data_dir, exist_ok=True)
                    self.db_path = canonical_path

        self.create_table()
        self._embedding_ids: List[int] = []
        self._embedding_vectors: Union[np.ndarray, None] = None
        self._loaded_model = None
        self._load_embeddings_into_memory()

    @staticmethod
    def _resolve_profile_db(project_root):
        profile_dir = os.path.join(project_root, "_profiles")
        active_file = os.path.join(profile_dir, "active_profile.txt")
        if os.path.exists(active_file):
            try:
                with open(active_file, "r", encoding="utf-8") as f:
                    active_profile = f.read().strip()
                profile_db = os.path.join(profile_dir, active_profile, "talos_research.db")
                if os.path.exists(profile_db):
                    return profile_db
            except Exception:
                pass
        return None

    def _table_exists(self, table_name: str) -> bool:
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"
        result = self.execute_query(query, (table_name,), fetch_one=True)
        return result is not None

    # --- Query Execution ---
    def execute_query(self, query, params=(), commit=False, fetch_one=False, fetch_all=False):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                if commit: conn.commit(); return cursor.lastrowid
                if fetch_one: return cursor.fetchone()
                if fetch_all: return cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            return None

    def execute_many(self, query, params_list, commit=False):
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                if commit: conn.commit(); return cursor.rowcount
        except sqlite3.Error as e:
            print(f"Database Error (Batch): {e}")
            return None

    # --- Schema ---
    def create_table(self):
        table_query = '''
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT, doi TEXT UNIQUE, url TEXT,
                title TEXT, authors TEXT, publication_year INTEGER, abstract TEXT, source TEXT,
                strategic_score INTEGER DEFAULT 0, operational_score INTEGER DEFAULT 0,
                tactical_score INTEGER DEFAULT 0, playground_score INTEGER DEFAULT 0,
                overall_score REAL DEFAULT 0.0,
                evaluation_reasoning TEXT, evaluation_contribution TEXT, evaluation_utilization TEXT,
                suggested_tags TEXT, suggested_folder TEXT, suggested_discord_channel TEXT,
                in_zotero INTEGER DEFAULT 0, embedding BLOB, embedding_model TEXT DEFAULT 'gemini',
                processed_at DATE, last_evaluated_at DATETIME,
                oa_pdf_url TEXT, openalex_id TEXT, pmid TEXT, pmcid TEXT,
                oa_status TEXT, journal_issn TEXT, publisher TEXT,
                enrichment_status INTEGER DEFAULT 0
            )
        '''
        self.execute_query(table_query, commit=True)
        self.execute_query("CREATE INDEX IF NOT EXISTS idx_papers_url ON papers(url);", commit=True)
        cols = self.execute_query("PRAGMA table_info(papers);", fetch_all=True)
        if cols and not any(col[1] == 'operational_score' for col in cols):
            self.execute_query("ALTER TABLE papers ADD COLUMN operational_score INTEGER DEFAULT 0;", commit=True)

    # --- Paper CRUD ---
    def paper_exists_by_doi(self, doi):
        if not doi: return False
        return bool(self.execute_query("SELECT 1 FROM papers WHERE doi = ?", (doi,), fetch_one=True))
    def paper_exists_by_url(self, url):
        if not url: return False
        return bool(self.execute_query("SELECT 1 FROM papers WHERE url = ?", (url,), fetch_one=True))
    def get_paper_id_by_doi(self, doi):
        if not doi: return None
        r = self.execute_query("SELECT id FROM papers WHERE doi = ?", (doi,), fetch_one=True)
        return r[0] if r else None
    def get_paper_id_by_url(self, url):
        if not url: return None
        r = self.execute_query("SELECT id FROM papers WHERE url = ?", (url,), fetch_one=True)
        return r[0] if r else None

    def _calculate_overall_score(self, scores):
        return round((scores.get('strategic',0)*0.3)+(scores.get('operational',0)*0.3)+
                     (scores.get('tactical',0)*0.3)+(scores.get('playground',0)*0.1), 2)

    def add_paper(self, paper_data, evaluation_data, in_zotero=0):
        scores = evaluation_data.get('scores', {})
        tags_str = ','.join(evaluation_data.get('tags', []))
        overall_score = evaluation_data.get('overall_score') or self._calculate_overall_score(scores)
        sql = """INSERT INTO papers (doi,url,title,authors,publication_year,abstract,source,
            strategic_score,operational_score,tactical_score,playground_score,overall_score,
            evaluation_reasoning,evaluation_contribution,evaluation_utilization,
            suggested_tags,suggested_folder,suggested_discord_channel,
            in_zotero,processed_at,last_evaluated_at,enrichment_status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        params = (paper_data.get('doi'), paper_data.get('url'), paper_data.get('title'),
            paper_data.get('authors_str'), paper_data.get('publication_year'),
            paper_data.get('abstract'), paper_data.get('source'),
            scores.get('strategic',0), scores.get('operational',0),
            scores.get('tactical',0), scores.get('playground',0), overall_score,
            evaluation_data.get('reasoning',''), evaluation_data.get('contribution',''),
            evaluation_data.get('utilization',''), tags_str,
            evaluation_data.get('folder',''), evaluation_data.get('discord_channel',''),
            in_zotero, date.today().strftime('%Y-%m-%d'), datetime.now(), 0)
        paper_id = self.execute_query(sql, params, commit=True)
        if paper_id:
            print(f"  > ID:{paper_id} - Saved '{paper_data.get('title')}' with score: {overall_score:.2f}.")
        return paper_id

    def update_paper_evaluation(self, paper_id, evaluation_data):
        scores = evaluation_data.get('scores', {})
        tags_str = ','.join(evaluation_data.get('tags', []))
        overall_score = evaluation_data.get('overall_score') or self._calculate_overall_score(scores)
        sql = """UPDATE papers SET strategic_score=?,operational_score=?,tactical_score=?,
            playground_score=?,overall_score=?,evaluation_reasoning=?,
            evaluation_contribution=?,evaluation_utilization=?,
            suggested_tags=?,suggested_folder=?,suggested_discord_channel=?,
            last_evaluated_at=? WHERE id=?"""
        params = (scores.get('strategic',0), scores.get('operational',0),
            scores.get('tactical',0), scores.get('playground',0), overall_score,
            evaluation_data.get('reasoning',''), evaluation_data.get('contribution',''),
            evaluation_data.get('utilization',''), tags_str,
            evaluation_data.get('folder',''), evaluation_data.get('discord_channel',''),
            datetime.now(), paper_id)
        self.execute_query(sql, params, commit=True)
        print(f"  --> Updated evaluation for Paper ID: {paper_id}")

    def get_papers_not_recently_evaluated(self, days_window, limit):
        cutoff = datetime.now() - timedelta(days=days_window)
        q = "SELECT id,title,abstract,overall_score FROM papers WHERE last_evaluated_at IS NULL OR last_evaluated_at < ? ORDER BY overall_score DESC LIMIT ?"
        return self.execute_query(q, (cutoff, limit), fetch_all=True) or []

    def get_all_papers_for_dashboard(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            q = "SELECT id,doi,url,title,authors,publication_year,abstract,source,strategic_score,operational_score,tactical_score,playground_score,overall_score,in_zotero,oa_pdf_url FROM papers ORDER BY overall_score DESC"
            return [dict(row) for row in conn.cursor().execute(q)]

    def get_single_paper_details(self, paper_id):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            paper = conn.cursor().execute("SELECT * FROM papers WHERE id=?", (paper_id,)).fetchone()
            return dict(paper) if paper else None

    def update_zotero_status_by_id(self, paper_id, status):
        self.execute_query("UPDATE papers SET in_zotero=? WHERE id=?", (status, paper_id), commit=True)

    # --- Embeddings ---
    def get_papers_needing_embedding(self, model=None):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if self._table_exists('embeddings'):
                if model:
                    return [dict(r) for r in conn.cursor().execute(
                        "SELECT p.id,p.title,p.abstract FROM papers p WHERE p.abstract IS NOT NULL AND p.abstract!='' AND p.id NOT IN (SELECT paper_id FROM embeddings WHERE embedding_model=?)", (model,))]
                else:
                    return [dict(r) for r in conn.cursor().execute(
                        "SELECT p.id,p.title,p.abstract FROM papers p WHERE p.abstract IS NOT NULL AND p.abstract!='' AND p.id NOT IN (SELECT DISTINCT paper_id FROM embeddings)")]
            else:
                return [dict(r) for r in conn.cursor().execute(
                    "SELECT id,title,abstract FROM papers WHERE embedding IS NULL AND abstract IS NOT NULL AND abstract!=''")]

    def store_embeddings_batch(self, updates):
        self.execute_many("INSERT INTO embeddings (paper_id,embedding,embedding_model) VALUES (?,?,?)", updates, commit=True)

    def get_all_embeddings(self, model_filter=None):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if self._table_exists('embeddings'):
                if model_filter:
                    return [dict(r) for r in conn.cursor().execute("SELECT paper_id as id,embedding FROM embeddings WHERE embedding_model=?", (model_filter,))]
                else:
                    return [dict(r) for r in conn.cursor().execute("SELECT paper_id as id,embedding FROM embeddings")]
            else:
                if model_filter:
                    return [dict(r) for r in conn.cursor().execute("SELECT id,embedding FROM papers WHERE embedding IS NOT NULL AND embedding_model=?", (model_filter,))]
                else:
                    return [dict(r) for r in conn.cursor().execute("SELECT id,embedding FROM papers WHERE embedding IS NOT NULL")]

    def get_papers_by_ids(self, ids):
        if not ids: return []
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            ph = ','.join('?' for _ in ids)
            q = f"SELECT id,doi,url,title,authors,publication_year,abstract,source,strategic_score,operational_score,tactical_score,playground_score,overall_score,in_zotero FROM papers WHERE id IN ({ph})"
            return [dict(r) for r in conn.cursor().execute(q, ids)]

    def get_recent_core_papers(self, limit=10, min_score=7.0):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [dict(r) for r in conn.cursor().execute("SELECT title,doi,overall_score FROM papers WHERE overall_score>=? ORDER BY processed_at DESC LIMIT ?", (min_score, limit))]

    def get_embedding_model_stats(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                if self._table_exists('embeddings'):
                    return [dict(r) for r in conn.cursor().execute("SELECT embedding_model as model, COUNT(DISTINCT paper_id) as count FROM embeddings GROUP BY embedding_model ORDER BY count DESC")]
                return [dict(r) for r in conn.cursor().execute("SELECT embedding_model as model, COUNT(*) as count FROM papers WHERE embedding IS NOT NULL AND embedding_model IS NOT NULL GROUP BY embedding_model ORDER BY count DESC")]
        except sqlite3.Error:
            return []

    def _load_embeddings_into_memory(self, model_filter=None):
        if not self._table_exists('papers'): return
        data = self.get_all_embeddings(model_filter)
        if not data: return
        self._embedding_ids = []
        temp = []
        for item in data:
            if item and 'embedding' in item and isinstance(item['embedding'], bytes):
                try:
                    self._embedding_ids.append(item['id'])
                    temp.append(pickle.loads(item['embedding']))
                except (pickle.UnpicklingError, EOFError):
                    self._embedding_ids.pop()
        self._embedding_vectors = np.array(temp) if temp else None

    def reload_embeddings_for_model(self, model_filter=None):
        self._embedding_ids = []
        self._embedding_vectors = None
        self._load_embeddings_into_memory(model_filter)

    def semantic_search(self, query_vector, top_k=100, model_filter=None):
        if model_filter != self._loaded_model:
            self.reload_embeddings_for_model(model_filter)
            self._loaded_model = model_filter
        if self._embedding_vectors is None or len(self._embedding_ids) == 0:
            return []
        dot = np.dot(self._embedding_vectors, query_vector)
        pn = np.linalg.norm(self._embedding_vectors, axis=1)
        qn = np.linalg.norm(query_vector)
        sim = np.zeros(len(self._embedding_ids))
        v = (pn > 0) & (qn > 0)
        sim[v] = dot[v] / (pn[v] * qn)
        ti = np.argpartition(sim, -top_k)[-top_k:]
        sti = ti[np.argsort(sim[ti])][::-1]
        return [self._embedding_ids[i] for i in sti]

    # --- DataFrame Export ---
    def get_all_papers_as_dataframe(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                return pd.read_sql_query("SELECT * FROM papers", conn)
        except Exception as e:
            print(f"DataFrame load failed: {e}")
            return pd.DataFrame()

    # --- Statistics ---
    def get_database_statistics(self):
        stats = {}
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM papers"); stats['total_papers'] = c.fetchone()[0]
            try:
                c.execute("SELECT COUNT(*) FROM papers WHERE enrichment_status=1"); stats['enriched_papers'] = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM papers WHERE oa_pdf_url IS NOT NULL"); stats['pdf_links'] = c.fetchone()[0]
            except sqlite3.Error:
                stats['enriched_papers'] = 0; stats['pdf_links'] = 0
            c.execute("SELECT source,COUNT(*) FROM papers GROUP BY source ORDER BY COUNT(*) DESC"); stats['by_source'] = c.fetchall()
            c.execute("SELECT AVG(overall_score) FROM papers")
            avg = c.fetchone()[0]; stats['avg_score'] = round(avg,2) if avg else 0.0
            c.execute("SELECT COUNT(*) FROM papers WHERE overall_score>7"); stats['elite_papers'] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM papers WHERE doi IS NULL OR doi=''"); stats['missing_doi'] = c.fetchone()[0]
            c.execute("SELECT COUNT(*) FROM papers WHERE embedding IS NOT NULL"); stats['embedded_papers'] = c.fetchone()[0]
        return stats

    # --- Enrichment ---
    def get_papers_for_enrichment(self):
        try:
            with sqlite3.connect(self.db_path) as conn:
                c = conn.cursor()
                c.execute("SELECT id,doi,abstract FROM papers WHERE (enrichment_status=0 OR enrichment_status IS NULL) AND doi IS NOT NULL")
                return c.fetchall()
        except sqlite3.Error:
            return []

    def update_papers_enrichment_batch(self, update_list):
        if not update_list: return
        q = """UPDATE papers SET oa_pdf_url=:oa_pdf_url,openalex_id=:openalex_id,pmid=:pmid,
            pmcid=:pmcid,oa_status=:oa_status,journal_issn=:journal_issn,
            publisher=:publisher,enrichment_status=:status WHERE id=:paper_id"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.cursor().executemany(q, update_list); conn.commit()
        except sqlite3.Error as e:
            print(f"Error in batch enrichment update: {e}")