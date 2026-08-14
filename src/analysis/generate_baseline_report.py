# -*- coding: utf-8 -*-
"""
Module: generate_baseline_report.py (v1.1 — Academic Style)
Project: TALOS v5.10.0
Description:
    Automated reporting module that generates a comprehensive baseline
    snapshot of the TALOS knowledge base BEFORE the DRL agent alters the
    paper distribution. Produces publication-quality figures and reports
    suitable for academic papers (IEEE/Springer format).

    How it works:
    - Connects to the profile-aware SQLite database.
    - Loads all paper metadata (scores, sources, embeddings) into a DataFrame.
    - Computes metrics: total papers, elite count, score distribution, etc.
    - Generates 4 plots at 300 DPI (600 DPI with --academic):
        1. Score distribution histogram + KDE
        2. Layer average bar chart (Strategic/Operational/Tactical/Playground)
        3. Source distribution pie chart
        4. Embedding model distribution bar chart
    - Saves everything to a date-organized directory:
        reports/general_status_report/YYYY-MM-DD/
    - Generates both report.md and report.html with embedded images.

    Key design decisions:
    - Profile-aware: auto-detects the active profile's database.
    - 300 DPI default, 600 DPI with --academic flag.
    - All exceptions are caught; the script never crashes.
    - Date subfolders allow archival by day.
    - Clean terminal output showing exactly where files were saved.

    Usage:
        python scripts/generate_baseline_report.py              # default style
        python scripts/generate_baseline_report.py --academic   # publication quality
"""
import os
import sys
import os, sys
_P = os.path.abspath(os.path.dirname(__file__))
while _P and not os.path.exists(os.path.join(_P, 'talos.py')):
    _P = os.path.dirname(_P)
if _P: sys.path.insert(0, _P)
import sqlite3
import argparse
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

# ── Add project root to Python's import path ────────────────────────────────
# ── Matplotlib backend setup (no GUI required) ──────────────────────────────
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server/script use
import matplotlib.pyplot as plt

# Try to import seaborn for prettier plots; fall back to pure matplotlib
try:
    import seaborn as sns
    _HAS_SEABORN = True
except ImportError:
    _HAS_SEABORN = False

# ── Styling constants ───────────────────────────────────────────────────────
# TALOS color palette (consistent across all plots)
COLORS_TALOS = ['#e94560', '#0f3460', '#16213e', '#533483', '#1a1a2e',
                '#e94560', '#f39c12', '#2ecc71', '#3498db', '#9b59b6']
# Layer colors matching the Quad-Layer Framework
LAYER_COLORS = ['#e74c3c', '#9b59b6', '#3498db', '#f1c40f']
LAYER_LABELS = ['Strategic', 'Operational', 'Tactical', 'Playground']
# Academic muted palette (grayscale + muted tones — suitable for journals)
ACADEMIC_PALETTE = ['#2c3e50', '#5d6d7e', '#839192', '#aab7b8', '#34495e',
                    '#7f8c8d', '#95a5a6', '#bdc3c7', '#4a235a', '#1a5276']
ACADEMIC_LAYER_COLORS = ['#2c3e50', '#5d6d7e', '#839192', '#aab7b8']


def apply_academic_style():
    """Apply publication-quality matplotlib style (serif fonts, clean layout).

    Sets Times New Roman / DejaVu Serif as the default font family,
    removes chartjunk (top/right spines), and increases figure DPI.
    This matches the formatting guidelines of IEEE and Springer journals.
    """
    style = {
        'font.family': 'serif',
        'font.serif': ['Times New Roman', 'DejaVu Serif', 'Georgia', 'serif'],
        'font.size': 10,
        'axes.titlesize': 12,
        'axes.labelsize': 10,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'legend.fontsize': 8,
        'figure.titlesize': 13,
        'lines.linewidth': 1.2,
        'axes.grid': True,
        'grid.alpha': 0.25,
        'axes.spines.top': False,
        'axes.spines.right': False,
        'figure.dpi': 150,
        'savefig.dpi': 600,
        'savefig.bbox': 'tight',
        'savefig.pad_inches': 0.1,
    }
    for key, val in style.items():
        matplotlib.rcParams[key] = val


def resolve_db_path():
    """
    Find the active profile's database, falling back to root.

    Returns:
        str: Absolute path to the SQLite database.
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    profile_dir = project_root / "_profiles"
    active_file = profile_dir / "active_profile.txt"

    if active_file.exists():
        try:
            active_profile = active_file.read_text(encoding="utf-8").strip()
            profile_db = profile_dir / active_profile / "talos_research.db"
            if profile_db.exists():
                return str(profile_db)
        except Exception:
            pass
    root_db = project_root / "data" / "talos_research.db"
    return str(root_db)


def load_dataframe(db_path):
    """Load all scored papers from the database into a DataFrame.

    Args:
        db_path (str): Path to the SQLite database.

    Returns:
        pd.DataFrame: DataFrame with id, scores, abstract, source.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            return pd.read_sql_query(
                "SELECT id, overall_score, strategic_score, operational_score, "
                "tactical_score, playground_score, abstract, source "
                "FROM papers WHERE overall_score IS NOT NULL AND overall_score > 0",
                conn
            )
    except sqlite3.Error as e:
        print(f"  ERROR loading database: {e}")
        return pd.DataFrame()


def load_embedding_stats(db_path):
    """Load embedding model distribution from the database.

    Args:
        db_path (str): Path to the SQLite database.

    Returns:
        list of tuple: [(model_name, count), ...] or empty list.
    """
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='embeddings'"
            )
            if cursor.fetchone():
                cursor.execute(
                    "SELECT embedding_model, COUNT(DISTINCT paper_id) "
                    "FROM embeddings GROUP BY embedding_model ORDER BY COUNT(*) DESC"
                )
                return cursor.fetchall()
            else:
                cursor.execute("SELECT COUNT(*) FROM papers WHERE embedding IS NOT NULL")
                embedded = cursor.fetchone()[0]
                if embedded > 0:
                    return [("Legacy (gemini)", embedded)]
                return []
    except sqlite3.Error as e:
        print(f"  WARNING: Could not load embedding stats: {e}")
        return []


def compute_metrics(df):
    """Calculate summary metrics from the paper DataFrame.

    Args:
        df (pd.DataFrame): Paper DataFrame with score columns.

    Returns:
        dict: Dictionary of computed metrics.
    """
    if df.empty:
        return {"total_papers": 0}
    scores = df["overall_score"]
    elites = df[df["overall_score"] >= 8]
    return {
        "total_papers": len(df),
        "avg_score": float(scores.mean()),
        "median_score": float(scores.median()),
        "std_dev_score": float(scores.std()),
        "min_score": float(scores.min()),
        "max_score": float(scores.max()),
        "elite_count": len(elites),
        "elite_pct": round(100 * len(elites) / len(df), 1),
        "with_abstract": int(df["abstract"].notna().sum()),
        "without_abstract": int(df["abstract"].isna().sum()),
        "avg_strategic": float(df["strategic_score"].mean()),
        "avg_operational": float(df["operational_score"].mean()),
        "avg_tactical": float(df["tactical_score"].mean()),
        "avg_playground": float(df["playground_score"].mean()),
        "num_sources": int(df["source"].nunique()),
        "top_sources": df["source"].value_counts().head(5).to_dict(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# PLOT GENERATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def plot_score_distribution(df, outdir, academic=False):
    """Generate a histogram + KDE of overall paper scores.

    Args:
        df (pd.DataFrame): Paper DataFrame.
        outdir (str): Output directory path.
        academic (bool): Use publication-quality styling.

    Returns:
        str: Path to the saved PNG.
    """
    dpi = 600 if academic else 300
    colors = ACADEMIC_PALETTE if academic else COLORS_TALOS
    fig, ax = plt.subplots(figsize=(10, 6))

    if _HAS_SEABORN:
        sns.histplot(df["overall_score"], bins=25, kde=True, color=colors[0],
                     edgecolor='white' if not academic else 'none',
                     linewidth=0.5, ax=ax)
    else:
        ax.hist(df["overall_score"], bins=25, color=colors[0],
                edgecolor='white', alpha=0.85)
        counts, bin_edges = np.histogram(df["overall_score"], bins=25, density=True)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        ax.plot(bin_centers, counts, color=colors[1], linewidth=2, alpha=0.7)

    # ── Labels and thresholds ───────────────────────────────────────────────
    ax.set_xlabel("Overall Score (0–10)", fontweight='bold')
    ax.set_ylabel("Number of Papers", fontweight='bold')
    ax.set_title("Paper Score Distribution (Baseline)", fontweight='bold', pad=12)

    avg_score = df["overall_score"].mean()
    ax.axvline(avg_score, color='#e74c3c' if academic else '#f39c12',
               linestyle='--', linewidth=1.5, label=f'Mean = {avg_score:.2f}')
    ax.axvline(8.0, color='#2ecc71', linestyle=':', linewidth=1.5,
               label='Elite Threshold (≥8)')
    ax.legend(loc='upper left')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    path = os.path.join(outdir, "score_distribution.png")
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return path


def plot_layer_averages(df, outdir, academic=False):
    """Generate a bar chart of average scores across the 4 layers.

    Args:
        df (pd.DataFrame): Paper DataFrame.
        outdir (str): Output directory path.
        academic (bool): Use publication-quality styling.

    Returns:
        str: Path to the saved PNG.
    """
    dpi = 600 if academic else 300
    lcolors = ACADEMIC_LAYER_COLORS if academic else LAYER_COLORS
    layer_cols = ["strategic_score", "operational_score",
                  "tactical_score", "playground_score"]
    averages = [df[col].mean() for col in layer_cols]

    fig, ax = plt.subplots(figsize=(9, 6))
    bars = ax.bar(LAYER_LABELS, averages, color=lcolors,
                  edgecolor='white' if not academic else 'black',
                  linewidth=1.2 if not academic else 0.5, width=0.6)

    for bar, val in zip(bars, averages):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.15,
                f"{val:.2f}", ha='center', va='bottom', fontsize=11,
                fontweight='bold')

    ax.set_ylabel("Average Score (0–10)", fontweight='bold')
    ax.set_title("Quad-Layer Framework — Baseline Averages",
                 fontweight='bold', pad=12)
    ax.set_ylim(0, max(averages) * 1.2 if max(averages) > 0 else 10)
    ax.grid(axis='y', alpha=0.3)
    plt.tight_layout()
    path = os.path.join(outdir, "layer_averages.png")
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return path


def plot_source_distribution(df, outdir, academic=False):
    """Generate a pie chart of paper distribution across sources.

    Args:
        df (pd.DataFrame): Paper DataFrame with 'source' column.
        outdir (str): Output directory path.
        academic (bool): Use publication-quality styling.

    Returns:
        str: Path to the saved PNG.
    """
    dpi = 600 if academic else 300
    colors_base = ACADEMIC_PALETTE if academic else COLORS_TALOS
    source_counts = df["source"].value_counts()
    top_n = 8
    top_sources = source_counts.head(top_n)
    other_count = source_counts[top_n:].sum()

    labels = list(top_sources.index)
    sizes = list(top_sources.values)
    if other_count > 0:
        labels.append("Other")
        sizes.append(other_count)

    fig, ax = plt.subplots(figsize=(10, 8))
    colors = colors_base[:len(labels)]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, autopct='%1.1f%%', startangle=140,
        colors=colors, pctdistance=0.75, explode=[0.02] * len(labels)
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_fontweight('bold')
        at.set_color('white')

    ax.set_title("Paper Distribution by Source (Baseline)",
                 fontweight='bold', pad=16)
    ax.legend(wedges, labels, title="Sources", loc="center left",
              bbox_to_anchor=(1.0, 0.5), fontsize=8)
    plt.tight_layout()
    path = os.path.join(outdir, "source_distribution.png")
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return path


def plot_embedding_distribution(embedding_stats, outdir, academic=False):
    """Generate a horizontal bar chart of embedding model coverage.

    Args:
        embedding_stats (list of tuple): [(model_name, count), ...].
        outdir (str): Output directory path.
        academic (bool): Use publication-quality styling.

    Returns:
        str or None: Path to the saved PNG, or None if no embeddings.
    """
    if not embedding_stats:
        return None
    dpi = 600 if academic else 300
    colors_base = ACADEMIC_PALETTE if academic else COLORS_TALOS
    labels = [s[0] for s in embedding_stats]
    values = [s[1] for s in embedding_stats]

    fig, ax = plt.subplots(figsize=(8, 5))
    colors = colors_base[:len(labels)]
    bars = ax.barh(labels, values, color=colors,
                   edgecolor='white' if not academic else 'black',
                   linewidth=1.0 if not academic else 0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + bar.get_width() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{val:,}", va='center', fontsize=11, fontweight='bold')

    ax.set_xlabel("Number of Papers Embedded", fontweight='bold')
    ax.set_title("Embedding Model Coverage (Baseline)", fontweight='bold', pad=12)
    ax.grid(axis='x', alpha=0.3)
    plt.tight_layout()
    path = os.path.join(outdir, "embedding_distribution.png")
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# REPORT GENERATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def generate_markdown(metrics, embedding_stats, plot_paths, outdir, timestamp):
    """Generate a Markdown report.

    Args:
        metrics (dict): Computed metrics.
        embedding_stats (list): Embedding model distribution.
        plot_paths (dict): Plot name → file path.
        outdir (str): Output directory.
        timestamp (str): Formatted timestamp.

    Returns:
        str: Path to the saved .md file.
    """
    lines = [
        f"# TALOS Baseline Report — Pre-DRL Agent",
        f"**Generated:** {timestamp}",
        f"**Database:** {metrics['total_papers']:,} papers | Profile: default_drones",
        "",
        "## 📊 Database Summary",
        "",
        "| Metric | Value |", "|--------|-------|",
        f"| Total Papers | {metrics['total_papers']:,} |",
        f"| Elite Papers (≥8) | {metrics['elite_count']:,} ({metrics['elite_pct']}%) |",
        f"| Average Score | {metrics['avg_score']:.2f} |",
        f"| Median Score | {metrics['median_score']:.2f} |",
        f"| Std Deviation | {metrics['std_dev_score']:.2f} |",
        f"| Score Range | {metrics['min_score']:.1f} – {metrics['max_score']:.1f} |",
        f"| Papers with Abstracts | {metrics['with_abstract']:,} |",
        f"| Papers without Abstracts | {metrics['without_abstract']:,} |",
        f"| Unique Sources | {metrics['num_sources']} |",
        "",
        "## 🎯 Quad-Layer Framework Averages",
        "",
        "| Layer | Average Score |", "|-------|---------------|",
        f"| 🔴 Strategic | {metrics['avg_strategic']:.2f} |",
        f"| 🟣 Operational | {metrics['avg_operational']:.2f} |",
        f"| 🔵 Tactical | {metrics['avg_tactical']:.2f} |",
        f"| 🟡 Playground | {metrics['avg_playground']:.2f} |",
        "",
        "## 📚 Top 5 Sources", "", "| Source | Papers |", "|--------|--------|",
    ]
    for source, count in metrics.get("top_sources", {}).items():
        lines.append(f"| {source} | {count:,} |")
    lines.append("")

    if embedding_stats:
        lines += [
            "## 🧠 Embedding Model Distribution", "",
            "| Model | Papers |", "|-------|--------|",
        ]
        for model, count in embedding_stats:
            lines.append(f"| {model} | {count:,} |")
        lines.append("")

    lines += [
        "## 📈 Visualizations", "",
    ]
    caption_map = {
        "score_distribution": "Score Distribution (Histogram + KDE)",
        "layer_averages": "Quad-Layer Average Scores",
        "source_distribution": "Paper Distribution by Source",
        "embedding_distribution": "Embedding Model Coverage",
    }
    for key, path in plot_paths.items():
        if path and os.path.exists(path):
            filename = os.path.basename(path)
            caption = caption_map.get(key, key.replace("_", " ").title())
            lines.append(f"![{caption}]({filename})")
            lines.append(f"*Figure: {caption}*")
            lines.append("")

    lines += [
        "---",
        f"*Report generated by Project TALOS v5.0.0 — Baseline Report Module*",
        f"*Timestamp: {timestamp}*",
    ]

    content = "\n".join(lines)
    path = os.path.join(outdir, "report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def generate_html(metrics, embedding_stats, plot_paths, outdir, timestamp):
    """Generate a styled HTML report.

    Args:
        metrics (dict): Computed metrics.
        embedding_stats (list): Embedding model distribution.
        plot_paths (dict): Plot name → file path.
        outdir (str): Output directory.
        timestamp (str): Formatted timestamp.

    Returns:
        str: Path to the saved .html file.
    """
    source_rows = ""
    for source, count in metrics.get("top_sources", {}).items():
        source_rows += f"<tr><td>{source}</td><td>{count:,}</td></tr>"

    embed_rows = ""
    for model, count in embedding_stats:
        embed_rows += f"<tr><td>{model}</td><td>{count:,}</td></tr>"

    caption_map = {
        "score_distribution": "Score Distribution — Histogram + KDE",
        "layer_averages": "Quad-Layer Averages — Strategic, Operational, Tactical, Playground",
        "source_distribution": "Paper Distribution by Academic Source",
        "embedding_distribution": "Embedding Model Coverage (Semantic Brain)",
    }
    img_cards = ""
    for key, path in plot_paths.items():
        if path and os.path.exists(path):
            filename = os.path.basename(path)
            caption = caption_map.get(key, key)
            img_cards += f"""<div class="card"><img src="{filename}" alt="{caption}">
            <div class="caption">{caption}</div></div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TALOS Baseline Report — {timestamp}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,sans-serif;background:#0d1117;color:#c9d1d9;padding:2rem;line-height:1.6}}
.container{{max-width:1100px;margin:0 auto}}
.header{{background:linear-gradient(135deg,#1a1a2e,#0f3460);padding:2rem;border-radius:12px;margin-bottom:2rem;
border:1px solid rgba(233,69,96,0.3);text-align:center}}
.header h1{{color:#e94560;font-size:2rem;margin-bottom:.5rem}}
.header p{{color:#8b949e;font-size:.9rem}}
h2{{color:#e94560;margin:2rem 0 1rem;border-bottom:2px solid #0f3460;padding-bottom:.5rem}}
.metrics-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1rem;margin-bottom:2rem}}
.metric-card{{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:1.2rem;text-align:center}}
.metric-card .value{{font-size:1.8rem;font-weight:700;color:#e94560}}
.metric-card .label{{font-size:.8rem;color:#8b949e;margin-top:.3rem}}
table{{width:100%;border-collapse:collapse;margin:1rem 0 2rem}}
th,td{{padding:.7rem 1rem;text-align:left;border-bottom:1px solid #30363d}}
th{{background:#161b22;color:#e94560;font-weight:600}}
tr:hover{{background:rgba(233,69,96,0.05)}}
.card{{background:#161b22;border:1px solid #30363d;border-radius:10px;margin-bottom:1.5rem;overflow:hidden}}
.card img{{width:100%;display:block}}
.card .caption{{padding:.8rem 1.2rem;color:#8b949e;font-size:.85rem}}
.footer{{text-align:center;color:#484f58;margin-top:3rem;padding-top:1.5rem;border-top:1px solid #30363d;font-size:.8rem}}
</style></head>
<body><div class="container">
<div class="header"><h1>🧠 TALOS Baseline Report — Pre-DRL Agent</h1>
<p>Generated: {timestamp} | Database: {metrics['total_papers']:,} papers | Profile: default_drones</p></div>
<h2>📊 Key Metrics</h2>
<div class="metrics-grid">
<div class="metric-card"><div class="value">{metrics['total_papers']:,}</div><div class="label">Total Papers</div></div>
<div class="metric-card"><div class="value">{metrics['elite_count']:,}</div><div class="label">Elite Papers (≥8)</div></div>
<div class="metric-card"><div class="value">{metrics['avg_score']:.2f}</div><div class="label">Average Score</div></div>
<div class="metric-card"><div class="value">{metrics['std_dev_score']:.2f}</div><div class="label">Std Deviation</div></div>
<div class="metric-card"><div class="value">{metrics['num_sources']}</div><div class="label">Unique Sources</div></div>
<div class="metric-card"><div class="value">{metrics['elite_pct']}%</div><div class="label">Elite Rate</div></div>
</div>
<h2>🎯 Quad-Layer Framework</h2>
<table><tr><th>Layer</th><th>Average Score</th></tr>
<tr><td>🔴 Strategic</td><td>{metrics['avg_strategic']:.2f}</td></tr>
<tr><td>🟣 Operational</td><td>{metrics['avg_operational']:.2f}</td></tr>
<tr><td>🔵 Tactical</td><td>{metrics['avg_tactical']:.2f}</td></tr>
<tr><td>🟡 Playground</td><td>{metrics['avg_playground']:.2f}</td></tr>
</table>
<h2>📚 Top 5 Sources</h2>
<table><tr><th>Source</th><th>Papers</th></tr>{source_rows}</table>
<h2>🧠 Embedding Model Distribution</h2>
<table><tr><th>Model</th><th>Papers</th></tr>
{embed_rows if embed_rows else '<tr><td colspan="2">No embeddings recorded yet.</td></tr>'}</table>
<h2>📈 Visualizations</h2>{img_cards}
<div class="footer">Project TALOS v5.0.0 — Automated Baseline Report Module<br>
© 2026 Christos Smarlamakis | {timestamp}</div>
</div></body></html>"""

    path = os.path.join(outdir, "report.html")
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Generate a complete baseline report with plots, metrics, and HTML/MD output."""
    parser = argparse.ArgumentParser(description='TALOS Baseline Report Generator')
    parser.add_argument('--academic', action='store_true',
                        help='Use publication-quality styling (serif fonts, 600 DPI)')
    args = parser.parse_args()

    if args.academic:
        apply_academic_style()

    print("=" * 65)
    print("  TALOS Baseline Report Generator — v5.10.0" +
          (" (Academic Style)" if args.academic else ""))
    print("=" * 65)

    db_path = resolve_db_path()
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d_%H%M")
    date_folder = now.strftime("%Y-%m-%d")
    report_base = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data", "reports", "general_status_report"
    )
    outdir = os.path.join(report_base, date_folder)
    os.makedirs(outdir, exist_ok=True)

    print(f"\n  Database: {os.path.basename(db_path)}")
    print(f"  Output:   data/reports/general_status_report/{date_folder}/")
    if args.academic:
        print(f"  Style:    Academic (serif fonts, 600 DPI)")
    print()

    # ── Step 1: Load data ──────────────────────────────────────────────────
    print("  [1/4] Loading data from database...")
    df = load_dataframe(db_path)
    embedding_stats = load_embedding_stats(db_path)
    if df.empty:
        print("  ERROR: No scored papers found in database.")
        return
    print(f"    Loaded {len(df):,} papers with scores.")

    # ── Step 2: Compute metrics ────────────────────────────────────────────
    print("  [2/4] Computing metrics...")
    metrics = compute_metrics(df)

    # ── Step 3: Generate plots ─────────────────────────────────────────────
    dpi_label = "600" if args.academic else "300"
    print(f"  [3/4] Generating plots ({dpi_label} DPI)...")
    plot_paths = {}
    for name, func in [
        ("score_distribution", plot_score_distribution),
        ("layer_averages", plot_layer_averages),
        ("source_distribution", plot_source_distribution),
    ]:
        try:
            plot_paths[name] = func(df, outdir, args.academic)
            print(f"    ✓ {name} saved")
        except Exception as e:
            print(f"    ✗ {name} failed: {e}")
    try:
        emb_path = plot_embedding_distribution(embedding_stats, outdir, args.academic)
        if emb_path:
            plot_paths["embedding_distribution"] = emb_path
            print(f"    ✓ embedding_distribution saved")
        else:
            print(f"    - No embedding data available")
    except Exception as e:
        print(f"    ✗ embedding_distribution failed: {e}")

    # ── Step 4: Generate reports ───────────────────────────────────────────
    print("  [4/4] Generating reports...")
    fmt_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        md_path = generate_markdown(metrics, embedding_stats, plot_paths, outdir, fmt_ts)
        print(f"    ✓ report.md saved")
    except Exception as e:
        print(f"    ✗ report.md failed: {e}")
    try:
        html_path = generate_html(metrics, embedding_stats, plot_paths, outdir, fmt_ts)
        print(f"    ✓ report.html saved")
    except Exception as e:
        print(f"    ✗ report.html failed: {e}")

    # ── Final summary ──────────────────────────────────────────────────────
    print("\n" + "=" * 65)
    print("  ✅ Baseline Report Complete")
    print("=" * 65)
    print(f"\n  📁 Report directory: data/reports/general_status_report/{date_folder}/")
    print(f"  📊 Total papers:      {metrics['total_papers']:,}")
    print(f"  ⭐ Elite (≥8):       {metrics['elite_count']:,} ({metrics['elite_pct']}%)")
    print(f"  📈 Average score:     {metrics['avg_score']:.2f} ± {metrics['std_dev_score']:.2f}")
    print(f"\n  Files generated:")
    for key, path in sorted(plot_paths.items()):
        print(f"    📊 {os.path.basename(path)}")
    if os.path.exists(os.path.join(outdir, "report.md")):
        print(f"    📄 report.md")
    if os.path.exists(os.path.join(outdir, "report.html")):
        print(f"    🌐 report.html")
    print(f"\n  Open in browser:")
    print(f"    file:///{outdir.replace(os.sep, '/')}/report.html")
    print("=" * 65)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n  ❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()