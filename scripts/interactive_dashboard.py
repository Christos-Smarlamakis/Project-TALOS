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
Module: interactive_dashboard.py (v2.2 - Soft Shutdown)
Project: TALOS v4.8.5

Description:
    Flask web server powering the TALOS Interactive Dashboard. Serves a
    Tabulator.js-based HTML interface for browsing, sorting, filtering, and
    semantically searching papers in the database. Includes a graceful shutdown
    endpoint and real-time Zotero status updates. Integrates with AIManager
    for semantic search embeddings.
"""
import os
import sys
import json
import signal
import threading
from flask import Flask, jsonify, render_template, request
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.database_manager import DatabaseManager
from core.ai_manager import AIManager


def load_configuration():
    """Load the project configuration from config.json.

    Returns:
        dict: Configuration dictionary.
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


config = load_configuration()
template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_folder)

db_manager = DatabaseManager()
ai_manager = AIManager(config)


@app.route('/')
def index():
    """Serve the dashboard HTML page."""
    return render_template('dashboard.html', title='TALOS Dashboard')


@app.route('/api/data')
def get_data():
    """Return all papers as JSON for the dashboard table."""
    return jsonify(db_manager.get_all_papers_for_dashboard())


@app.route('/api/paper/<int:paper_id>')
def get_paper_details(paper_id):
    """Return full details for a single paper.

    Args:
        paper_id (int): The paper's database ID.

    Returns:
        JSON response with paper data or 404.
    """
    details = db_manager.get_single_paper_details(paper_id)
    return jsonify(details) if details else (jsonify({'error': 'Paper not found'}), 404)


@app.route('/api/update_zotero', methods=['POST'])
def update_zotero_status():
    """Update the 'in_zotero' status for a paper via AJAX."""
    data = request.get_json()
    try:
        db_manager.update_zotero_status_by_id(
            data.get('id'), 1 if data.get('status') else 0)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/semantic_search', methods=['POST'])
def semantic_search():
    """Perform semantic search via embedding cosine similarity."""
    data = request.get_json()
    query_text = data.get('query')
    if not query_text: return jsonify({'error': 'Query text is missing.'}), 400

    try:
        result = ai_manager.generate_embeddings([query_text])
        query_vector_list, _ = result if isinstance(result, tuple) else (result, None)
        if not query_vector_list: raise Exception("AIManager failed.")
        query_vector = np.array(query_vector_list[0])

        sorted_paper_ids = db_manager.semantic_search(query_vector, top_k=100)
        results_data = db_manager.get_papers_by_ids(sorted_paper_ids)

        if results_data:
            id_order = {pid: i for i, pid in enumerate(sorted_paper_ids)}
            results_data.sort(key=lambda x: id_order.get(x['id'], len(sorted_paper_ids)))
        return jsonify(results_data or [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """Gracefully terminate the Flask server."""
    print("\n--- Shutdown command received from Dashboard ---")
    def kill_server():
        os.kill(os.getpid(), signal.SIGINT)
    timer = threading.Timer(1.0, kill_server)
    timer.start()
    return jsonify({'success': True, 'message': 'Server shutting down...'})


if __name__ == '__main__':
    print("--- TALOS INTERACTIVE DASHBOARD STARTING (v2.2) ---")
    print("INFO: Open your browser at: http://127.0.0.1:5000")
    app.run(debug=False, port=5000, threaded=True)