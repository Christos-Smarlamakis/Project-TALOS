import os
# ── Dynamic project root: tools/_bump.py → up one level ─────────────────
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(_PROJECT_ROOT)
for f in ["CHANGELOG_GR.md", "CHANGELOG_EN.md", "README.md", "talos.py", "src/core/ai_manager.py"]:
    with open(f, "r", encoding="utf-8") as fh:
        data = fh.read()
    data = data.replace("v4.8.2", "v4.8.3")
    data = data.replace("June 2026", "June 2026")
    with open(f, "w", encoding="utf-8") as fh:
        fh.write(data)
    print(f"Updated {f}")
print("Done - now commit & push")
