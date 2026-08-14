# -*- coding: utf-8 -*-
"""
Module: pdf_downloader.py (v1.0)
Project: TALOS v5.9.17
Description:
    Zero-Config PDF Downloader for Open Access papers.
    Queries Unpaywall (requires email) and OpenAlex (keyless) for OA PDF URLs.
    Downloads PDFs to data/pdfs/ with timeout handling and graceful degradation.
    Requires NO API keys — only the user's email for Unpaywall polite pool.
"""

import os
import sys
import time
import requests
from pathlib import Path
from tqdm import tqdm
import questionary

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)

from src.core.database_manager import DatabaseManager
from dotenv import load_dotenv

load_dotenv()

PDF_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'pdfs'))
os.makedirs(PDF_DIR, exist_ok=True)

# Timeout and retry config
DOWNLOAD_TIMEOUT = 30
MAX_RETRIES = 2
MAX_WORKERS = 10  # Thread pool size for multi-threaded batch downloads
REQUEST_DELAY = 1.0  # Be polite to APIs


def get_mailto():
    """Get user email from env or config."""
    email = os.getenv("UNPAYWALL_EMAIL", "") or os.getenv("MAILTO", "")
    if not email:
        import json
        config_path = os.path.join(_P if _P else os.getcwd(), 'config.json')
        if not os.path.exists(config_path):
            config_path = os.path.join(_P if _P else os.getcwd(), 'config.template.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            email = config.get("mailto", "")
        except Exception:
            pass
    if not email:
        print("WARNING: No email configured. Unpaywall may rate-limit you.")
        email = "anonymous@example.com"
    return email


def find_oa_pdf(doi, mailto):
    """
    Try to find an Open Access PDF URL for a given DOI.
    Strategy: Unpaywall first → OpenAlex fallback.
    
    Returns: (pdf_url, source) or (None, None)
    """
    headers = {"User-Agent": f"TALOS-PDFDownloader/1.0 (mailto:{mailto})"}
    
    # ── Strategy 1: Unpaywall ──
    try:
        url = f"https://api.unpaywall.org/v2/{doi}?email={mailto}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            best = data.get("best_oa_location", {})
            if best:
                pdf_url = best.get("url_for_pdf") or best.get("url")
                if pdf_url:
                    return (pdf_url, "Unpaywall")
    except requests.RequestException:
        pass
    
    # ── Strategy 2: OpenAlex (keyless fallback) ──
    try:
        clean_doi = doi.replace("https://doi.org/", "")
        url = f"https://api.openalex.org/works/doi:{clean_doi}"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            oa = data.get("open_access", {})
            if oa.get("is_oa") and oa.get("oa_url"):
                return (oa["oa_url"], "OpenAlex")
    except requests.RequestException:
        pass
    
    # ── Strategy 3: CORE API (keyless — free open access repository) ──
    try:
        clean_doi = doi.replace("https://doi.org/", "")
        url = f"https://api.core.ac.uk/v3/search/works?doi={clean_doi}&limit=1"
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = data.get("results", [])
            if results:
                first = results[0]
                download_url = first.get("downloadUrl") or first.get("fullTextIdentifier")
                if download_url:
                    return (download_url, "CORE API")
    except requests.RequestException:
        pass
    
    return (None, None)


def download_pdf(pdf_url, filename, max_retries=MAX_RETRIES):
    """
    Download a PDF file safely with retries and timeout.
    
    Returns: local_path or None on failure.
    """
    safe_name = "".join(c for c in filename if c.isalnum() or c in " _-.")[:100]
    filepath = os.path.join(PDF_DIR, f"{safe_name}.pdf")
    
    if os.path.exists(filepath):
        return filepath
    
    # Browser-like User-Agent to avoid publisher blocks
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                       "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 "
                       "TALOS-PDFDownloader/1.0 (mailto:TALOS-bot)",
        "Accept": "application/pdf,text/html,application/octet-stream,*/*",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    for attempt in range(max_retries):
        try:
            r = requests.get(
                pdf_url, headers=headers, stream=True,
                timeout=DOWNLOAD_TIMEOUT, allow_redirects=True
            )
            if r.status_code == 200:
                content_type = r.headers.get("Content-Type", "").lower()
                # Check if response is a PDF
                is_pdf = "pdf" in content_type or "octet-stream" in content_type
                # If not PDF by content-type, check first bytes for PDF magic number
                if not is_pdf and len(r.content) > 10:
                    first_bytes = r.raw.read(8)
                    r.raw.seek(0)
                    is_pdf = first_bytes.startswith(b"%PDF")
                if not is_pdf:
                    print(f"  ⚠️  Response is not a PDF (Content-Type: {content_type})")
                    return None
                
                with open(filepath, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                # Verify file size
                if os.path.getsize(filepath) < 1000:
                    os.remove(filepath)
                    print(f"  ⚠️  Downloaded file too small — likely invalid")
                    return None
                
                return filepath
            elif r.status_code in (403, 404):
                return None
            elif r.status_code == 429:
                # Rate limited — exponential backoff
                wait = 5 * (2 ** attempt)
                time.sleep(wait)
            else:
                time.sleep(2 * (attempt + 1))
        except requests.RequestException:
            time.sleep(2 * (attempt + 1))
    
    return None


def get_papers_to_process(db_manager, limit=None):
    """Get papers with DOIs that need PDF links."""
    try:
        import sqlite3
        with sqlite3.connect(db_manager.db_path) as conn:
            conn.row_factory = sqlite3.Row
            query = """
                SELECT id, doi, title FROM papers 
                WHERE doi IS NOT NULL AND doi != '' 
                AND (oa_pdf_url IS NULL OR oa_pdf_url = '')
                ORDER BY overall_score DESC
            """
            if limit:
                query += f" LIMIT {limit}"
            return [dict(row) for row in conn.cursor().execute(query)]
    except Exception as e:
        print(f"ERROR fetching papers: {e}")
        return []


def update_paper_pdf(db_manager, paper_id, pdf_url, local_path):
    """Update paper record with PDF information."""
    try:
        import sqlite3
        with sqlite3.connect(db_manager.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE papers SET oa_pdf_url = ? WHERE id = ?",
                (pdf_url if pdf_url else local_path, paper_id)
            )
            conn.commit()
    except Exception as e:
        print(f"  ⚠️  Failed to update DB for paper ID {paper_id}: {e}")


def main():
    print("\n📥 TALOS PDF Downloader — v4.10.0 (Zero-Config)")
    print(f"   Output directory: {PDF_DIR}")
    print("   Sources: Unpaywall → OpenAlex (keyless fallback)")
    
    mailto = get_mailto()
    print(f"   Email: {mailto}\n")
    
    db = DatabaseManager()
    papers = get_papers_to_process(db)
    
    if not papers:
        print("✅ No papers need PDF retrieval. Database is up to date.")
        return
    
    print(f"Found {len(papers)} papers to process.\n")
    
    if not questionary.confirm(f"Attempt to download PDFs for {len(papers)} papers? This may take time.", default=True).ask():
        return
    
    use_batch = questionary.confirm(
        "Use multi-threaded batch download? (Faster — ~10x speedup with ThreadPoolExecutor)", 
        default=True
    ).ask()

    success = 0
    failed = 0
    sources_found = {"Unpaywall": 0, "OpenAlex": 0}

    if use_batch:
        import concurrent.futures
        
        def _process_single_paper(paper, mailto_val):
            """Process one paper: find OA PDF + download."""
            doi = paper.get("doi", "")
            title = paper.get("title", "Untitled")[:60]
            pdf_url, source = find_oa_pdf(doi, mailto_val)
            if not pdf_url:
                return None
            local_path = download_pdf(pdf_url, f"{paper['id']}_{title[:50]}")
            if local_path:
                return (paper, pdf_url, local_path, source)
            return None

        print(f"\n  ⚡ Multi-threaded mode: {MAX_WORKERS} workers")
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(_process_single_paper, p, mailto): p for p in papers}
            with tqdm(total=len(papers), desc="Downloading PDFs (batch)", unit="paper") as pbar:
                for future in concurrent.futures.as_completed(futures):
                    try:
                        result = future.result()
                        if result:
                            results.append(result)
                            paper, pdf_url, local_path, source = result
                            sources_found[source] = sources_found.get(source, 0) + 1
                            update_paper_pdf(db, paper["id"], pdf_url, local_path)
                            tqdm.write(f"    ✅ [{source}] {paper['title'][:60]}")
                            success += 1
                        else:
                            failed += 1
                    except Exception as e:
                        failed += 1
                        tqdm.write(f"    ❌ Error: {e}")
                    pbar.update(1)
                    time.sleep(0.1)  # Minimal delay between thread completions
    else:
        # Sequential mode (original behavior)
        for paper in tqdm(papers, desc="Downloading PDFs"):
            doi = paper.get("doi", "")
            title = paper.get("title", "Untitled")[:60]
            
            pdf_url, source = find_oa_pdf(doi, mailto)
            
            if not pdf_url:
                failed += 1
                continue
            
            sources_found[source] = sources_found.get(source, 0) + 1
            tqdm.write(f"  [{source}] Found OA PDF for: {title}")
            
            local_path = download_pdf(pdf_url, f"{paper['id']}_{title[:50]}")
            
            if local_path:
                update_paper_pdf(db, paper["id"], pdf_url, local_path)
                tqdm.write(f"    ✅ Downloaded: {local_path}")
                success += 1
            else:
                tqdm.write(f"    ❌ Download failed")
                failed += 1
            
            time.sleep(REQUEST_DELAY)

    print(f"\n{'='*50}")
    print(f"  PDF DOWNLOAD COMPLETE")
    print(f"  ✅ Successfully downloaded: {success}")
    print(f"  ❌ Failed/No OA: {failed}")
    print(f"  📊 Sources: Unpaywall={sources_found.get('Unpaywall',0)}, OpenAlex={sources_found.get('OpenAlex',0)}")
    print(f"  📁 Files saved to: {PDF_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()