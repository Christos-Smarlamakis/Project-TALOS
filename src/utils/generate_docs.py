"""
Module: generate_docs.py (v2.0)
Project: TALOS v5.9.17 — Multi-Language Codebase Documentation Builder
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

# questionary may not be available in all environments -- graceful fallback
try:
    import questionary
    HAS_QUESTIONARY = True
except ImportError:
    HAS_QUESTIONARY = False


# -- v5.9.17: Enterprise logging & Universal Rich TUI --
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))
from src.utils.logger import get_logger
from rich.console import Console
from rich.panel import Panel

logger = get_logger(__name__)
console = Console()


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

# Directory groups for the checkbox menu (Domain-Driven Design layout)
DIRECTORY_GROUPS = [
    ("src/core/", "src/core", "Core modules (database, AI manager, hardware)"),
    ("src/ingestion/", "src/ingestion", "Search agents and ingestion pipelines"),
    ("src/ai/", "src/ai", "AI modules (DRL, embeddings, LLM, optimizers, testing)"),
    ("src/analysis/", "src/analysis", "Analysis modules (recommender, citation, trends)"),
    ("src/utils/", "src/utils", "Utility modules (docs, stats, health checks)"),
    ("src/api/", "src/api", "API modules (FastAPI facade, service API)"),
    ("Root files", "ROOT", "Root files (talos.py, Dockerfile, ...)"),
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


def _is_excluded(path_str: str) -> bool:
    """Return True if a path should be excluded from documentation.

    Matches directory names by whole path component and file extensions
    by suffix, avoiding false positives such as "data" inside a filename.

    Args:
        path_str: absolute or relative path to a file.

    Returns:
        True if the path matches an exclusion pattern, False otherwise.
    """
    norm = path_str.replace("\\", "/")
    parts = norm.split("/")
    for pat in EXCLUDE_PATTERNS:
        if pat.startswith("."):
            if norm.endswith(pat):
                return True
        else:
            if pat in parts:
                return True
    return False


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
    project_root = Path(__file__).resolve().parent.parent.parent
    collected: List[str] = []

    for sel in selected_dirs:
        if sel == "ROOT":
            # Collect files directly in the project root
            for item in sorted(project_root.iterdir()):
                if item.is_file():
                    if item.name.endswith(".md"):
                        continue
                    if _is_excluded(str(item)):
                        continue
                    collected.append(str(item))
        else:
            dir_path = project_root / sel
            if not dir_path.is_dir():
                logger.warning("Directory not found: %s", dir_path)
                continue
            for file_path in dir_path.rglob("*"):
                if file_path.is_file():
                    path_str = str(file_path)
                    if _is_excluded(path_str):
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
        logger.error("Request timed out after %ss", REQUEST_TIMEOUT)
    except requests.exceptions.ConnectionError:
        logger.error("Could not connect to Ollama. Is it running?")
    except requests.exceptions.RequestException as exc:
        logger.error("HTTP request failed: %s", exc)
    except json.JSONDecodeError:
        logger.error("Could not parse Ollama response as JSON")

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
    project_root = Path(__file__).resolve().parent.parent.parent
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
        logger.error("'questionary' library is required for interactive mode.")
        logger.error("        Install it: pip install questionary")
        sys.exit(1)

    config = load_configuration()
    model = config["ollama_model"]
    ollama_url = config["ollama_url"]

    # ── Step 1: Ollama health check ─────────────────────────────────────────
    base_url = ollama_url.replace("/api/generate", "")
    console.print(Panel(
        "[bold bright_cyan]Multi-Language Documentation Builder[/bold bright_cyan]\n"
        f"[dim]Model:[/dim]  {model}\n"
        f"[dim]Ollama:[/dim] {base_url}",
        title="[bold]TALOS[/bold]",
        border_style="bright_magenta",
    ))

    if not check_ollama(base_url):
        logger.error("Ollama is not running or unreachable. URL: %s", base_url)
        logger.error("        Please start Ollama first (ollama serve)")
        logger.error("        This tool is LOCAL-only -- zero cloud cost, full privacy.")
        sys.exit(1)

    logger.info("Ollama is running.")

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
        logger.info("Cancelled.")
        return

    _, language_keyword = LANGUAGES[lang_code]
    logger.info("Language: %s", LANGUAGES[lang_code][0])

    # ── Step 3: select directories ──────────────────────────────────────────
    dir_choices = [
        questionary.Choice(
            title=f"{desc}",
            value=key,
            checked=True,  # default: all directories selected
        )
        for desc, key, _ in DIRECTORY_GROUPS
    ]

    selected_dirs = questionary.checkbox(
        "Select directories to document (SPACE to toggle, ENTER to confirm):",
        choices=dir_choices,
    ).ask()

    if selected_dirs is None or len(selected_dirs) == 0:
        logger.info("No directories selected. Exiting.")
        return

    # -- Step 4: collect files and estimate --
    file_paths = get_code_files(selected_dirs)
    if not file_paths:
        logger.error("No files found in selected directories.")
        return

    info = estimate_file_info(file_paths)

    # ── Step 5: summary & confirmation ─────────────────────────────────────
    project_root = Path(__file__).resolve().parent.parent.parent
    output_path = project_root / OUTPUT_DIR / lang_code

    # Rough time estimate: ~3 min per file
    est_minutes = info["total_files"] * 3
    if est_minutes < 60:
        est_time = f"~{est_minutes} minutes"
    else:
        hours = est_minutes // 60
        mins = est_minutes % 60
        est_time = f"~{hours}h {mins}m"

    console.print(Panel(
        "[bold bright_cyan]Summary[/bold bright_cyan]\n"
        f"[dim]Language:[/dim]      {LANGUAGES[lang_code][0]}\n"
        f"[dim]Files:[/dim]         {info['total_files']}\n"
        f"[dim]Total lines:[/dim]   ~{info['total_lines']:,}\n"
        f"[dim]Output:[/dim]        {output_path}\n"
        f"[dim]Est. time:[/dim]     {est_time}\n"
        f"[dim]Cost:[/dim]          EUR 0.00 (local Ollama -- zero cloud tokens)",
        title="[bold]GENERATION PLAN[/bold]",
        border_style="cyan",
    ))

    confirmed = questionary.confirm("Proceed with generation?", default=True).ask()
    if not confirmed:
        logger.info("Cancelled.")
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

    # -- Step 7: final summary --
    logger.info("Done! Language: %s | Success: %s | Failed: %s | Output: %s",
                LANGUAGES[lang_code][0], success_count, fail_count, output_path)
    console.print(Panel(
        "[bold bright_cyan]Generation Complete[/bold bright_cyan]\n"
        f"[dim]Language:[/dim]  {LANGUAGES[lang_code][0]}\n"
        f"[dim]Success:[/dim]   {success_count}\n"
        f"[dim]Failed:[/dim]    {fail_count}\n"
        f"[dim]Output:[/dim]    {output_path}\n"
        f"[dim]Cost:[/dim]      EUR 0.00 (100% local Ollama)",
        title="[bold]DONE[/bold]",
        border_style="green",
    ))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("Interrupted. Partial results saved in docs/.")