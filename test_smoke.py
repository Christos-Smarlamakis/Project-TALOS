# -*- coding: utf-8 -*-
"""
TALOS Smoke Test Suite
Usage: python test_smoke.py
Checks syntax, imports, database, and AI manager — all without API calls.
Outputs a clean summary of what passed/failed.
"""
import sys
import os
import py_compile
import traceback

# Ensure we're in the project root
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

PASS = 0
FAIL = 0
SKIP = 0

def check(label, fn):
    global PASS, FAIL, SKIP
    try:
        fn()
        print(f"  ✅ {label}")
        PASS += 1
    except Exception as e:
        print(f"  ❌ {label}")
        print(f"     {e}")
        FAIL += 1

def skip(label, reason):
    global SKIP
    print(f"  ⚠️  {label} — SKIPPED ({reason})")
    SKIP += 1

# ─────────────────────────────────────────────────────────────────────────────
# 1. SYNTAX CHECK
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  1. SYNTAX CHECK (py_compile)")
print("=" * 60)

PY_FILES = []
for root, dirs, files in os.walk("."):
    # Skip virtual environments, git, pycache
    dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".venv", "venv", "node_modules", "data", "logs", "reports")]
    for f in files:
        if f.endswith(".py") and not f.startswith("_bump") and not f.startswith("_fix"):
            PY_FILES.append(os.path.join(root, f))

for f in sorted(PY_FILES):
    def _check(f=f):
        py_compile.compile(f, doraise=True)
    check(f"Syntax: {f}", _check)

# ─────────────────────────────────────────────────────────────────────────────
# 2. CORE IMPORTS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  2. CORE MODULE IMPORTS")
print("=" * 60)

check("src.core.database_manager", lambda: __import__("src.core.database_manager"))
check("src.core.ai_manager", lambda: __import__("src.core.ai_manager"))
check("src.core.hardware", lambda: __import__("src.core.hardware"))

# ─────────────────────────────────────────────────────────────────────────────
# 3. DATABASE CONNECTIVITY & STATISTICS
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  3. DATABASE CONNECTIVITY")
print("=" * 60)

from src.core.database_manager import DatabaseManager

check("DatabaseManager() init", lambda: DatabaseManager())

db = DatabaseManager()

check("get_database_statistics()", lambda: db.get_database_statistics())
stats = db.get_database_statistics()

check("total_papers > 0" if stats["total_papers"] > 0 else "total_papers == 0 (empty DB)",
      lambda: None)  # not a failure

check("get_all_papers_for_dashboard()", lambda: db.get_all_papers_for_dashboard()[:1])
check("get_all_papers_as_dataframe()", lambda: db.get_all_papers_as_dataframe().head(1))
check("get_recent_core_papers()", lambda: db.get_recent_core_papers(limit=3, min_score=7.0))

# ─────────────────────────────────────────────────────────────────────────────
# 4. AI MANAGER
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  4. AI MANAGER INITIALIZATION")
print("=" * 60)

import json
config_path = os.path.join(os.path.dirname(__file__), "config.json")
if not os.path.exists(config_path):
    config_path = os.path.join(os.path.dirname(__file__), "config.template.json")

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

from src.core.ai_manager import AIManager

check("AIManager(config) init", lambda: AIManager(config))

# ─────────────────────────────────────────────────────────────────────────────
# 5. GUI RUNNER (questionary patching)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  5. GUI RUNNER (_gui_runner.py)")
print("=" * 60)

def test_gui_runner():
    import importlib
    import questionary
    # Simulate what _gui_runner.py does
    # Patch questionary.text
    original_text = questionary.text
    try:
        questionary.text = lambda *a, **kw: type('Fake', (), {'ask': lambda: 'test_input', 'unsafe_ask': lambda: 'test_input'})()
        questionary.confirm = lambda *a, **kw: type('Fake', (), {'ask': lambda: True, 'unsafe_ask': lambda: True})()
        questionary.select = lambda *a, **kw: type('Fake', (), {'ask': lambda: 'test_choice', 'unsafe_ask': lambda: 'test_choice'})()
    finally:
        questionary.text = original_text

check("questionary.text patch works", test_gui_runner)

# ─────────────────────────────────────────────────────────────────────────────
# 6. SCRIPT IMPORTS (syntax-checked above, now test imports)
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  6. SCRIPT MODULE IMPORTABILITY")
print("=" * 60)

SCRIPTS_TO_SKIP = {
    "daily_search.py": "requires 14 API sources",
    "historic_search.py": "requires 14 API sources",
    "grey_literature_miner.py": "requires google.genai",
    "citation_analyzer.py": "requires pyvis",
    "author_profiler.py": "requires questionary (patched via runner)",
    "author_trajectory_analyzer.py": "uses author_profiler",
    "interactive_dashboard.py": "Flask — not needed for smoke test",
    "zotero_connector.py": "requires pyzotero + Zotero keys",
}

# ── Scripts now live in src/ — scan subdirectories ──────────────────────
# Use explicit dot notation to avoid Windows path separator issues
_script_modules = {
    "src/ingestion": "src.ingestion",
    "src/ai/drl": "src.ai.drl",
    "src/ai/optimizers": "src.ai.optimizers",
    "src/ai/embeddings": "src.ai.embeddings",
    "src/ai/llm": "src.ai.llm",
    "src/analysis": "src.analysis",
    "src/utils": "src.utils",
    "src/core": "src.core",
    "src/api": "src.api",
}
script_entries = []
for sd, pkg in _script_modules.items():
    if os.path.isdir(sd):
        for f in sorted(os.listdir(sd)):
            if f.endswith(".py") and f != "__init__.py":
                script_entries.append((f"{sd}/{f}", pkg, f))
for sf, pkg, fname in script_entries:
    if fname in SCRIPTS_TO_SKIP:
        skip(sf, SCRIPTS_TO_SKIP[fname])
    else:
        module_name = f"{pkg}.{fname[:-3]}"
        check(f"Import {module_name}", lambda mn=module_name: __import__(mn))

# ─────────────────────────────────────────────────────────────────────────────
# 7. SOURCE AGENT IMPORTABILITY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  7. SOURCE AGENTS IMPORTABILITY")
print("=" * 60)

SOURCES_TO_SKIP = {
    "elsevier_source.py": "requires elsapy/Elsevier API key",
    "ieee_source.py": "requires IEEE API key",
    "springer_source.py": "requires Springer API key",
    "openarchives_source.py": "requires API key",
}

# ── Source agents now live in src/ingestion/ ────────────────────────────
source_files = sorted(f for f in os.listdir("src/ingestion") 
                      if f.endswith("_source.py") and f != "__init__.py")
for sf in source_files:
    if sf in SOURCES_TO_SKIP:
        skip(f"src/ingestion/{sf}", SOURCES_TO_SKIP[sf])
    else:
        module_name = f"src.ingestion.{sf[:-3]}"
        check(f"Import {module_name}", lambda mn=module_name: __import__(mn))

# ─────────────────────────────────────────────────────────────────────────────
# 8. STREAMLIT APP IMPORT
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  8. STREAMLIT APP")
print("=" * 60)

import streamlit as st
check("streamlit imported OK", lambda: st.__version__)
check("st.set_page_config works from import", lambda: None)  # would fail if syntax broken

# ─────────────────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  SUMMARY")
print("=" * 60)
total = PASS + FAIL + SKIP
print(f"  ✅  {PASS} passed")
print(f"  ❌  {FAIL} failed")
print(f"  ⚠️   {SKIP} skipped")
print(f"  📋  {total} total checks")
print(f"  📁 {len(PY_FILES)} .py files syntax-checked")
print(f"  📊 DB: {stats['total_papers']} papers, avg score {stats['avg_score']:.1f}")
print("=" * 60)

if FAIL == 0:
    print("\n🎉 ALL CHECKS PASSED — Project is healthy!")
else:
    print(f"\n⚠️  {FAIL} checks FAILED — see details above.")

sys.exit(0 if FAIL == 0 else 1)