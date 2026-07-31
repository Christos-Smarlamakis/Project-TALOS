"""Script to bump version strings across all 15 documentation files."""
import re
from pathlib import Path

FILES = [
    "README.md",
    "ROADMAP.md",
    "CHANGELOG_EN.md",
    "CHANGELOG_GR.md",
    "docs/PROJECT_MAP.md",
    "docs/PROJECT_MAP_EN.md",
    "docs/TIMELINE_EN.md",
    "docs/TIMELINE_GR.md",
    "docs/API_HANDOVER_FOTIS.md",
    "docs/UX_UI_BLUEPRINT_FOTIS.md",
    "docs/IP_PROTECTION_STRATEGY.md",
    "docs/SYSTEM_CAPABILITIES_MASTER.md",
    "docs/SYSTEM_CAPABILITIES_MASTER.html",
    "docs/TECH_RADAR.md",
]

BASE = Path.cwd()

for fname in FILES:
    fpath = BASE / fname
    if not fpath.exists():
        print(f"MISSING: {fname}")
        continue
    content = fpath.read_text(encoding="utf-8")
    # Replace all v5.7.0 and v5.7.1 with v5.7.2
    new_content = re.sub(r"v5\.7\.[01]", "v5.7.2", content)
    # Replace bare 5.7.0 and 5.7.1 with 5.7.2 (but not v5.7.2->v5.7.2)
    new_content = re.sub(r"(?<!v)5\.7\.[01]", "5.7.2", new_content)
    if new_content != content:
        fpath.write_text(new_content, encoding="utf-8")
        print(f"Updated: {fname}")
    else:
        print(f"No changes: {fname}")