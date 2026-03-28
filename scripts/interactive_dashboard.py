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
Project: TALOS v4.2

Description:
Η αναβαθμισμένη έκδοση του back-end.
- Προσθέτει το endpoint `/api/shutdown` για ομαλό τερματισμό από τον browser.
- Αξιοποιεί τον AIManager και DatabaseManager.
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
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    config_path = os.path.join(project_root, 'config.json')
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)

config = load_configuration()
template_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_folder)

db_manager = DatabaseManager()
ai_manager = AIManager(config)

# --- ROUTES ---

@app.route('/')
def index():
    return render_template('dashboard.html', title='TALOS Dashboard')

@app.route('/api/data')
def get_data():
    return jsonify(db_manager.get_all_papers_for_dashboard())

@app.route('/api/paper/<int:paper_id>')
def get_paper_details(paper_id):
    details = db_manager.get_single_paper_details(paper_id)
    return jsonify(details) if details else (jsonify({'error': 'Paper not found'}), 404)

@app.route('/api/update_zotero', methods=['POST'])
def update_zotero_status():
    data = request.get_json()
    try:
        db_manager.update_zotero_status_by_id(data.get('id'), 1 if data.get('status') else 0)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/semantic_search', methods=['POST'])
def semantic_search():
    data = request.get_json()
    query_text = data.get('query')
    if not query_text: return jsonify({'error': 'Query text is missing.'}), 400

    try:
        query_vector_list = ai_manager.generate_embeddings([query_text], task_type="RETRIEVAL_QUERY")
        if not query_vector_list: raise Exception("AIManager failed.")
        query_vector = np.array(query_vector_list[0])
        
        sorted_paper_ids = db_manager.semantic_search(query_vector, top_k=100)
        results_data = db_manager.get_papers_by_ids(sorted_paper_ids)
        
        if results_data:
            results_data.sort(key=lambda x: sorted_paper_ids.index(x['id']))
        return jsonify(results_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# --- NEW: SHUTDOWN ENDPOINT ---
@app.route('/api/shutdown', methods=['POST'])
def shutdown():
    """Τερματίζει τον server ομαλά."""
    print("\n--- Λήψη εντολής τερματισμού από το Dashboard ---")
    # Χρησιμοποιούμε thread για να δώσουμε χρόνο στο request να επιστρέψει απάντηση πριν "πεθάνει" ο server
    def kill_server():
        os.kill(os.getpid(), signal.SIGINT)
    
    timer = threading.Timer(1.0, kill_server)
    timer.start()
    return jsonify({'success': True, 'message': 'Server shutting down...'})

if __name__ == '__main__':
    print("--- ΕΚΚΙΝΗΣΗ TALOS INTERACTIVE DASHBOARD (v2.2) ---")
    print("INFO: Ανοίξτε τον browser σας στη διεύθυνση: http://127.0.0.1:5000")
    # Χρησιμοποιούμε threaded=True για να μην μπλοκάρει το shutdown request
    app.run(debug=False, port=5000, threaded=True)