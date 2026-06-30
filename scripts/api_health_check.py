# -*- coding: utf-8 -*-
"""
Module: api_health_check.py (v1.1)
Project: TALOS v4.10.0
Description:
    Lightweight API diagnostics tool. Pings each configured API to verify
    key validity and returns structured status results. Supports all TALOS
    data sources and AI providers. Keyless sources are always marked as
    available. Premium sources are tested with dummy queries.
    Uses tqdm progress bar for real-time feedback.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def ping_api(url, headers=None, timeout=8):
    """Send a GET request and return HTTP status code."""
    try:
        r = requests.get(url, headers=headers or {}, timeout=timeout)
        return r.status_code
    except requests.RequestException:
        return -1


def _format_result(name, status, detail):
    """Format a single check result for tqdm.write(). No emoji for compatibility."""
    if status == "available":
        return f"  [OK]    {name}: {detail}"
    elif status == "keyless":
        return f"  [FREE]  {name}: {detail}"
    elif status == "missing_key":
        return f"  [NONE]  {name}: {detail}"
    elif status == "invalid_key":
        return f"  [FAIL]  {name}: {detail}"
    else:
        return f"  [WARN]  {name}: {detail}"


def check_source(source_name, key_env_var, ping_url, headers_fn=None, pbar=None):
    """
    Check a single API source. Writes result immediately via tqdm.write().
    Returns: (source_name, status, detail)
    """
    key = os.getenv(key_env_var, "").strip()

    if key_env_var == "KEYLESS":
        result = (source_name, "keyless", "Free -- no API key required")
    elif not key:
        result = (source_name, "missing_key", "Not configured (Free Mode)")
    else:
        headers = {"User-Agent": "TALOS-HealthCheck/1.0"}
        if headers_fn:
            headers = headers_fn(key, headers)
        status = ping_api(ping_url, headers)
        if status == 200:
            result = (source_name, "available", "Valid key -- API operational")
        elif status in (401, 403):
            result = (source_name, "invalid_key", f"Invalid/expired key (HTTP {status})")
        elif status == 429:
            result = (source_name, "available", "Rate limited (key may be valid)")
        elif status == -1:
            result = (source_name, "error", "Connection failed -- check network")
        else:
            result = (source_name, "available", f"Responded (HTTP {status})")

    if pbar:
        pbar.set_postfix_str(source_name)
        tqdm.write(_format_result(*result))
        pbar.update(1)
    return result


def check_ai_provider(provider_name, env_var, pbar=None):
    """Check an AI provider by attempting a minimal generation."""
    key = os.getenv(env_var, "").strip()
    if not key:
        result = (provider_name, "missing_key", "Not configured")
        if pbar:
            tqdm.write(_format_result(*result))
            pbar.update(1)
        return result

    try:
        if provider_name == "Gemini":
            import google.generativeai as genai
            genai.configure(api_key=key)
            models = genai.list_models()
            result = (provider_name, "available", f"Valid key -- {len(list(models))} models found")
        elif provider_name == "DeepSeek":
            import openai
            client = openai.OpenAI(api_key=key, base_url="https://api.deepseek.com")
            client.models.list()
            result = (provider_name, "available", "Valid key -- API operational")
        elif provider_name == "HuggingFace":
            import openai
            client = openai.OpenAI(api_key=key, base_url="https://router.huggingface.co/v1")
            client.models.list()
            result = (provider_name, "available", "Valid token -- API operational")
    except Exception as e:
        msg = str(e)
        if any(s in msg for s in ("401", "403", "Unauthorized")):
            result = (provider_name, "invalid_key", "Invalid/expired key")
        else:
            result = (provider_name, "error", f"Error: {msg[:80]}")

    if pbar:
        pbar.set_postfix_str(provider_name)
        tqdm.write(_format_result(*result))
        pbar.update(1)
    return result


def run_diagnostics():
    """Run all API diagnostics with tqdm progress bar. Results printed in real-time."""
    # Count all checks
    keyless_count = 10
    premium_count = 8
    integration_count = 4
    total_checks = 3 + keyless_count + premium_count + integration_count

    print("\n" + "=" * 50)
    print("  TALOS API Health Check -- v4.10.0")
    print(f"  Testing {total_checks} APIs...")
    print("=" * 50 + "\n")

    # Collect results for return (sorted by category)
    all_results = []
    with tqdm(total=total_checks, desc="Checking APIs", unit="api",
              bar_format="{l_bar}{bar:30}{r_bar}", ncols=80) as pbar:

        # ─── AI Providers (3) ───
        tqdm.write("\n  [AI Providers]")
        all_results.append({"category": "AI Providers"})
        all_results.append(check_ai_provider("Gemini", "GEMINI_API_KEY", pbar))
        all_results.append(check_ai_provider("DeepSeek", "DEEPSEEK_API_KEY", pbar))
        all_results.append(check_ai_provider("HuggingFace", "HF_TOKEN", pbar))

        # ─── Keyless (10) ───
        tqdm.write("\n  [Keyless Sources -- Always Available]")
        all_results.append({"category": "Keyless Sources (Always Available)"})
        for name in ["arXiv", "OpenAlex", "Crossref", "DBLP", "CORE",
                      "PubMed", "OSTI.gov", "Science.gov", "PLOS", "OpenArchives"]:
            all_results.append(check_source(name, "KEYLESS", "", pbar=pbar))

        # ─── Premium Academic (8) ───
        tqdm.write("\n  [Premium Academic Sources (Optional)]")
        all_results.append({"category": "Premium Academic Sources (Optional)"})
        all_results.append(check_source(
            "Semantic Scholar", "SEMANTIC_SCHOLAR_API_KEY",
            "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1",
            lambda k, h: {**h, "x-api-key": k}, pbar))
        all_results.append(check_source(
            "Semantic Scholar Basic", "SEMANTIC_SCHOLAR_API_KEY_basic",
            "https://api.semanticscholar.org/graph/v1/paper/search?query=test&limit=1",
            lambda k, h: {**h, "x-api-key": k}, pbar))
        all_results.append(check_source(
            "IEEE Xplore", "IEEE_API_KEY",
            "https://ieeexploreapi.ieee.org/api/v1/search/articles?apikey=" +
            os.getenv("IEEE_API_KEY", "test") + "&format=json&max_records=1",
            pbar=pbar))
        all_results.append(check_source(
            "Elsevier/Scopus", "ELSEVIER_API_KEY",
            "https://api.elsevier.com/content/search/scopus?query=test&count=1",
            lambda k, h: {**h, "X-ELS-APIKey": k, "Accept": "application/json"}, pbar))
        all_results.append(check_source(
            "Elsevier InstToken", "ELSEVIER_INST_TOKEN",
            "https://api.elsevier.com/content/search/scopus?query=test&count=1",
            lambda k, h: {**h, "X-ELS-Insttoken": k, "Accept": "application/json"}, pbar))
        all_results.append(check_source(
            "Springer Nature", "SPRINGER_API_KEY",
            "https://api.springernature.com/meta/v2/json?q=test&api_key=" +
            os.getenv("SPRINGER_API_KEY", "test") + "&p=1", pbar=pbar))
        all_results.append(check_source(
            "CORE", "CORE_API_KEY",
            "https://api.core.ac.uk/v3/search/works?q=test&limit=1",
            lambda k, h: {**h, "Authorization": f"Bearer {k}"}, pbar))
        all_results.append(check_source(
            "OpenArchives.gr", "OPENARCHIVES_API_KEY",
            "https://www.openarchives.gr/api/v1/search?q=test&size=1",
            lambda k, h: {**h, "Authorization": k}, pbar))

        # ─── Integrations (4) ───
        tqdm.write("\n  [Integrations (Optional)]")
        all_results.append({"category": "Integrations (Optional)"})
        all_results.append(check_source(
            "Zotero", "ZOTERO_API_KEY",
            f"https://api.zotero.org/users/{os.getenv('ZOTERO_USER_ID', '0')}/items?limit=1",
            lambda k, h: {**h, "Zotero-API-Key": k}, pbar))
        all_results.append(check_source(
            "ORCID API", "ORCID_CLIENT_ID",
            "https://pub.orcid.org/v3.0/0000-0002-1825-0097",
            lambda k, h: {**h, "Accept": "application/json"}, pbar))
        all_results.append(check_source(
            "Unpaywall", "UNPAYWALL_EMAIL",
            "https://api.unpaywall.org/v2/10.1038/nature12373?email=" +
            os.getenv("UNPAYWALL_EMAIL", os.getenv("MAILTO", "test@example.com")), pbar=pbar))
        all_results.append(check_source(
            "Discord Webhook", "DISCORD_WEBHOOK_URL",
            os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/test"),
            lambda k, h: h, pbar))

    print("\n" + "=" * 50)
    print("  Diagnostics complete.")
    print("=" * 50 + "\n")
    return all_results


if __name__ == "__main__":
    run_diagnostics()