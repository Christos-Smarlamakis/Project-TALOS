"""
Module: generate_docs.py (v2.0)
Project: TALOS v5.3.0 — Multi-Language Codebase Documentation Builder
Description:
    Fully interactive script that documents the ENTIRE TALOS codebase (93+ files)
    in any of 18 languages using a local Ollama instance. No CLI arguments needed
    — everything is done through questionary prompts.

    Key design decisions:
    - 100% interactive (questionary) — zero CLI arguments.
    - LOCAL-only: uses Ollama exclusively. Never touches cloud APIs.
    - 18 languages: Greek, English, Chinese, Hindi, Spanish, Arabic, French,
      Bengali, Russian, Portuguese, Urdu, Indonesian, German, Japanese,
      Italian, Korean, Turkish, Persian.
    - Selective: user picks which directories/files to document.
    - Token estimator: shows line/byte counts before starting.
    - docs/{lang_code}/ output structure for multi-language runs.
"""
import os
import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests
from dotenv import load_dotenv
from tqdm import tqdm

# questionary may not be available in all environments — graceful fallback
try:
    import questionary
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False


# ── Constants ──────────────────────────────────────────────────────────────────
DEFAULT_MODEL = "gemma4"
REQUEST_TIMEOUT = 120  # seconds
OUTPUT_DIR = "docs/generated"

# Files/directories to EXCLUDE from scanning
EXCLUDE_PATTERNS = [
    "__pycache__", ".git", "data", "logs", "models", "docs",
    "reports", "_profiles", ".pth", ".db", ".png", ".jpg", ".gif",
    ".pdf", ".pyc", ".egg-info",
]

# 18 supported languages (code → display name, prompt keyword)
LANGUAGES: Dict[str, Tuple[str, str]] = {
    "el": ("Ελληνικά (Greek)", "GREEK"),
    "en": ("English", "ENGLISH"),
    "zh": ("中文 (Chinese Mandarin)", "CHINESE"),
    "hi": ("हिन्दी (Hindi)", "HINDI"),
    "es": ("Español (Spanish)", "SPANISH"),
    "ar": ("العربية (Arabic)", "ARABIC"),
    "fr": ("Français (French)", "FRENCH"),
    "bn": ("বাংলা (Bengali)", "BENGALI"),
    "ru": ("Русский (Russian)", "RUSSIAN"),
    "pt": ("Português (Portuguese)", "PORTUGUESE"),
    "ur": ("اردو (Urdu)", "URDU"),
    "id": ("Bahasa Indonesia", "INDONESIAN"),
    "de": ("Deutsch (German)", "GERMAN"),
    "ja": ("日本語 (Japanese)", "JAPANESE"),
    "it": ("Italiano (Italian)", "ITALIAN"),
    "ko": ("한국어 (Korean)", "KOREAN"),
    "tr": ("Türkçe (Turkish)", "TURKISH"),
    "fa": ("فارسی (Persian/Farsi)", "PERSIAN"),
}

# Directory groups for the checkbox menu
DIRECTORY_GROUPS = [
    ("core/", "core", "Core modules (7 .py files)"),
    ("scripts/", "scripts", "Scripts (35 .py files)"),
    ("sources/", "sources", "Search agents (14 .py files)"),
    ("templates/", "templates", "Templates (7 files — HTML, CSS, JS, JSON)"),
    ("reference_code/", "reference_code", "Reference code (17 .py files)"),
    ("Root files", "ROOT", "Root files (talos.py, app.py, Dockerfile, ...)"),
]

# ── Prompt template ───────────────────────────────────────────────────────────
PROMPT_TEMPLATE = (
    "Act as a Senior Python Architect. "
    "Read the following file. "
    "Write a highly detailed, professional Markdown documentation explaining "
    "what this file does, its architecture, design patterns used, "
    "and explain the core components. "
    "Write the documentation entirely in {language_keyword}.\n\n"
    "File: {file_path}\n\n"
    "```\n{source_code}\n```"
)


def check_ollama(url: str) -> bool:
    """
    Verify that Ollama is running and reachable.

    Args:
        url: base URL of the Ollama instance (e.g., "http://localhost:11434").

    Returns:
        True if Ollama responds, False otherwise.
    """
    try:
        r = requests.get(f"{url.rstrip('/')}/api/tags", timeout=5)
        return r.status_code == 200
    except requests.exceptions.ConnectionError:
        return False
    except Exception:
        return False


def load_configuration() -> Dict[str, str]:
    """
    Load .env settings: model name and Ollama endpoint.

    Returns:
        dict with keys: ollama_model, ollama_url
    """
    load_dotenv()

    ollama_model = (
        os.getenv("OLLAMA_MODEL")
        or os.getenv("LOCAL_MODEL_NAME")
        or DEFAULT_MODEL
    )

    base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    if base_url.endswith("/api/generate"):
        ollama_url = base_url
    else:
        ollama_url = base_url.rstrip("/") + "/api/generate"

    return {"ollama_model": ollama_model, "ollama_url": ollama_url}


def get_code_files(selected_dirs: List[str]) -> List[str]:
    """
    Recursively collect all code/text files from selected directories.

    Files that match EXCLUDE_PATTERNS are skipped.
    Binary files (.pth, .db, .pdf, .png, etc.) are also skipped.

    Args:
        selected_dirs: list of directory names or "ROOT" for root files.

    Returns:
        Sorted list of absolute file paths.
    """
    project_root = Path(__file__).resolve().parent.parent
    collected: List[str] = []

    for sel in selected_dirs:
        if sel == "ROOT":
            # Collect files directly in the project root (non-directory, non-hidden-dir)
            for item in sorted(project_root.iterdir()):
                if item.is_file():
                    name = item.name
                    # Skip excluded patterns
                    skip = False
                    for pat in EXCLUDE_PATTERNS:
                        if pat.replace("/", "").replace("\\", "") in name or name.endswith(pat):
                            skip = True
                            break
                    if skip:
                        continue
                    # Skip .md files (already documentation)
                    if name.endswith(".md"):
                        continue
                    collected.append(str(item))
        else:
            dir_path = project_root / sel
            if not dir_path.is_dir():
                print(f"[WARNING] Directory not found: {dir_path}")
                continue
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    path_str = str(file_path)
                    skip = False
                    for pat in EXCLUDE_PATTERNS:
                        if pat in path_str:
                            skip = True
                            break
                    if skip:
                        continue
                    collected.append(path_str)

    return sorted(collected)


def estimate_file_info(file_paths: List[str]) -> Dict[str, int]:
    """
    Count total lines and bytes across all selected files.

    Args:
        file_paths: list of absolute file paths.

    Returns:
        dict with keys: total_files, total_lines, total_bytes
    """
    total_lines = 0
    total_bytes = 0

    for fp in file_paths:
        try:
            text = Path(fp).read_text(encoding="utf-8", errors="replace")
            total_lines += text.count("\n") + 1
            total_bytes += len(text.encode("utf-8"))
        except Exception:
            pass

    return {
        "total_files": len(file_paths),
        "total_lines": total_lines,
        "total_bytes": total_bytes,
    }


def generate_documentation(
    source_code: str,
    file_path: str,
    model: str,
    ollama_url: str,
    language_keyword: str,
) -> Optional[str]:
    """
    Send a file's source to Ollama and get Markdown documentation back.

    Args:
        source_code: raw file contents.
        file_path: relative path of the file (used in the prompt).
        model: Ollama model name.
        ollama_url: full /api/generate endpoint URL.
        language_keyword: the language to write in (e.g., "GREEK", "JAPANESE").

    Returns:
        Generated Markdown string, or None on failure.
    """
    prompt = PROMPT_TEMPLATE.format(
        language_keyword=language_keyword,
        file_path=file_path,
        source_code=source_code,
    )

    payload = {"model": model, "prompt": prompt, "stream": False}

    try:
        response = requests.post(ollama_url, json=payload, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")
    except requests.exceptions.Timeout:
        print(f"  [ERROR] Request timed out after {REQUEST_TIMEOUT}s")
    except requests.exceptions.ConnectionError:
        print("  [ERROR] Could not connect to Ollama. Is it running?")
    except requests.exceptions.RequestException as exc:
        print(f"  [ERROR] HTTP request failed: {exc}")
    except json.JSONDecodeError:
        print("  [ERROR] Could not parse Ollama response as JSON")

    return None


def save_documentation(
    file_path: str, content: str, output_dir: str, lang_code: str
) -> None:
    """
    Write generated Markdown to docs/{lang_code}/.

    Naming: replace directory separators with underscores.
        core/ai_manager.py   → core_ai_manager_doc.md
        templates/dashboard.html → templates_dashboard_doc.md
        Dockerfile           → Dockerfile_doc.md

    Args:
        file_path: absolute path to the original file.
        content: generated Markdown.
        output_dir: base output directory (e.g., "docs").
        lang_code: 2-letter language code (e.g., "el", "en").
    """
    project_root = Path(__file__).resolve().parent.parent
    lang_dir = project_root / output_dir / lang_code
    lang_dir.mkdir(parents=True, exist_ok=True)

    # Create a safe filename from the relative path
    rel = os.path.relpath(file_path, project_root)
    safe_name = rel.replace(os.sep, "_").replace(" ", "_")
    # Replace extension with _doc.md
    if "." in safe_name:
        base = safe_name.rsplit(".", 1)[0]
    else:
        base = safe_name
    output_filename = f"{base}_doc.md"
    output_path = lang_dir / output_filename

    output_path.write_text(content, encoding="utf-8")


def main() -> None:
    """
    Fully interactive orchestrator:

    1. Check Ollama health → abort if offline.
    2. Load config (model, URL).
    3. Ask user for language (questionary select).
    4. Ask user for directories/files (questionary checkbox).
    5. Show summary with token estimate.
    6. Confirm → generate with tqdm progress bar.
    7. Print final summary.
    """
    # ── Step 0: check for questionary ──────────────────────────────────────
    if not HAS_QUESTIONARY:
        print("[ERROR] 'questionary' library is required for interactive mode.")
        print("        Install it: pip install questionary")
        sys.exit(1)

    config = load_configuration()
    model = config["ollama_model"]
    ollama_url = config["ollama_url"]

    # ── Step 1: Ollama health check ─────────────────────────────────────────
    base_url = ollama_url.replace("/api/generate", "")
    print("=" * 72)
    print("  TALOS v5.3.0 — Multi-Language Documentation Builder")
    print(f"  Model:  {model}")
    print(f"  Ollama: {base_url}")
    print("=" * 72)

    if not check_ollama(base_url):
        print("\n[ERROR] Ollama is not running or unreachable.")
        print(f"        URL: {base_url}")
        print("        Please start Ollama first (ollama serve)")
        print("        This tool is LOCAL-only — zero cloud cost, full privacy.")
        sys.exit(1)

    print("  ✓ Ollama is running")

    # ── Step 2: select language ─────────────────────────────────────────────
    lang_choices = [
        questionary.Choice(
            title=f"{display_name}",
            value=code,
        )
        for code, (display_name, _) in LANGUAGES.items()
    ]

    lang_code = questionary.select(
        "Documentation language:",
        choices=lang_choices,
    ).ask()

    if lang_code is None:
        print("\nCancelled.")
        return

    _, language_keyword = LANGUAGES[lang_code]
    print(f"\n  Language: {LANGUAGES[lang_code][0]}")

    # ── Step 3: select directories ──────────────────────────────────────────
    dir_choices = [
        questionary.Choice(
            title=f"{desc}",
            value=key,
            checked=(key != "reference_code"),  # default: all except reference_code
        )
        for desc, key, _ in DIRECTORY_GROUPS
    ]

    selected_dirs = questionary.checkbox(
        "Select directories to document (SPACE to toggle, ENTER to confirm):",
        choices=dir_choices,
    ).ask()

    if selected_dirs is None or len(selected_dirs) == 0:
        print("\nNo directories selected. Exiting.")
        return

    # ── Step 4: collect files and estimate ──────────────────────────────────
    file_paths = get_code_files(selected_dirs)
    if not file_paths:
        print("[ERROR] No files found in selected directories.")
        return

    info = estimate_file_info(file_paths)

    # ── Step 5: summary & confirmation ─────────────────────────────────────
    project_root = Path(__file__).resolve().parent.parent
    output_path = project_root / OUTPUT_DIR / lang_code

    print("\n" + "═" * 60)
    print("  Summary")
    print("═" * 60)
    print(f"  Language:      {LANGUAGES[lang_code][0]}")
    print(f"  Files:         {info['total_files']}")
    print(f"  Total lines:   ~{info['total_lines']:,}")
    print(f"  Output:        {output_path}")
    # Rough time estimate: ~3 min per file
    est_minutes = info["total_files"] * 3
    if est_minutes < 60:
        print(f"  Est. time:     ~{est_minutes} λεπτά")
    else:
        hours = est_minutes // 60
        mins = est_minutes % 60
        print(f"  Est. time:     ~{hours}ώ {mins}λ")
    print(f"  💰 Cost:       €0.00 (τοπικό Ollama — zero cloud tokens)")
    print("═" * 60)

    confirmed = questionary.confirm("Proceed with generation?", default=True).ask()
    if not confirmed:
        print("\nCancelled.")
        return

    # ── Step 6: generate ────────────────────────────────────────────────────
    success_count = 0
    fail_count = 0

    for file_path in tqdm(file_paths, desc="Generating docs", unit="file"):
        rel_path = os.path.relpath(file_path)
        tqdm.write(f"  → {rel_path}")

        try:
            source_code = Path(file_path).read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            tqdm.write(f"    [SKIP] Could not read file: {exc}")
            fail_count += 1
            continue

        doc_content = generate_documentation(
            source_code, rel_path, model, ollama_url, language_keyword
        )

        if doc_content is None:
            tqdm.write(f"    [FAIL] Ollama generation failed")
            fail_count += 1
            continue

        try:
            save_documentation(file_path, doc_content, OUTPUT_DIR, lang_code)
            tqdm.write(f"    [OK] → docs/generated/{lang_code}/")
            success_count += 1
        except Exception as exc:
            tqdm.write(f"    [FAIL] Could not write output: {exc}")
            fail_count += 1

        # Small delay to avoid overwhelming Ollama
        time.sleep(1)

    # ── Step 7: final summary ───────────────────────────────────────────────
    print("\n" + "=" * 72)
    print(f"  Done!")
    print(f"  Language:  {LANGUAGES[lang_code][0]}")
    print(f"  Success:   {success_count}")
    print(f"  Failed:    {fail_count}")
    print(f"  Output:    {output_path}")
    print(f"  💰 Cost:   €0.00 (100% local Ollama)")
    print("=" * 72)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Partial results saved in docs/.")