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
Module: trend_analyzer.py (v1.0 - Scientometrics Module)
Project: TALOS v5.9.18

Description:
    Generates interactive HTML scientometrics reports with statistical
    visualizations. Produces research timelines, score distribution plots,
    author productivity charts, Open Access pie charts, and word clouds.
    Uses matplotlib, seaborn, and wordcloud. Automatically opens the
    report in the default browser when complete.
"""
# scripts/trend_analyzer.py
# Project TALOS v4.8.0 - Scientometrics Module

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud
import os
import sys
import base64
from io import BytesIO
from datetime import datetime

# Path setup
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

# Configuration
# (Σε παραγωγή, αυτό θα έρχεται από το talos.py args)
DB_PATH = os.path.join(project_root, '_profiles', 'default', 'talos_research.db') 
# Fallback logic
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(project_root, 'talos_research.db')

REPORT_DIR = os.path.join(project_root, 'data', 'reports', 'trends')
os.makedirs(REPORT_DIR, exist_ok=True)

class TrendAnalyzer:
    def __init__(self, db_path):
        self.db_path = db_path
        print(f"--- Initializing Scientometrics Suite ---")
        print(f"--- Database: {db_path} ---")

    def load_data(self):
        """Loads data from SQLite into a Pandas DataFrame."""
        try:
            conn = sqlite3.connect(self.db_path)
            # Φορτώνουμε όλα τα πεδία που μας ενδιαφέρουν
            query = """
            SELECT 
                id, title, publication_year, authors, source, 
                strategic_score, operational_score, tactical_score, overall_score,
                oa_status, journal_issn, publisher
            FROM papers
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Data Cleaning
            df['publication_year'] = pd.to_numeric(df['publication_year'], errors='coerce')
            df = df.dropna(subset=['publication_year']) # Αφαιρούμε όσα δεν έχουν έτος
            df['publication_year'] = df['publication_year'].astype(int)
            
            print(f"Data Loaded: {len(df)} papers ready for analysis.")
            return df
        except Exception as e:
            print(f"Error loading data: {e}")
            return pd.DataFrame()

    def fig_to_base64(self, fig):
        """Converts a matplotlib figure to a base64 string for HTML embedding."""
        buf = BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img_str = base64.b64encode(buf.read()).decode('utf-8')
        plt.close(fig) # Free memory
        return img_str

    def generate_plots(self, df):
        """Generates all scientometric plots."""
        plots = {}
        
        # Set Style
        sns.set_theme(style="whitegrid")
        
        # 1. Publications per Year (Timeline)
        fig1, ax1 = plt.subplots(figsize=(10, 6))
        sns.countplot(x='publication_year', data=df, hue='publication_year', palette='viridis', legend=False, ax=ax1)
        ax1.set_title('Research Timeline: Publications per Year', fontsize=14)
        ax1.tick_params(axis='x', rotation=45)
        plots['timeline'] = self.fig_to_base64(fig1)
        
        # 2. Score Distribution (KDE Plot) — Full Quad-Layer
        fig2, ax2 = plt.subplots(figsize=(10, 6))
        sns.kdeplot(data=df, x='overall_score', fill=True, color='#e74c3c', label='Overall', ax=ax2)
        sns.kdeplot(data=df, x='strategic_score', fill=False, color='#3498db', label='Strategic', ax=ax2)
        sns.kdeplot(data=df, x='operational_score', fill=False, color='#9b59b6', label='Operational', ax=ax2)
        sns.kdeplot(data=df, x='tactical_score', fill=False, color='#2ecc71', label='Tactical', ax=ax2)
        ax2.set_title('Quality Landscape: Quad-Layer Score Distributions', fontsize=14)
        ax2.legend()
        plots['scores'] = self.fig_to_base64(fig2)

        # 3. Top Authors Analysis
        # Split authors string "Smith, J., Doe, A." -> separate rows
        authors_series = df['authors'].str.split(',').explode().str.strip()
        top_authors = authors_series.value_counts().head(15)
        
        fig3, ax3 = plt.subplots(figsize=(10, 8))
        sns.barplot(x=top_authors.values, y=top_authors.index, hue=top_authors.index, palette='rocket', legend=False, ax=ax3)
        ax3.set_title('Most Active Researchers (Top 15)', fontsize=14)
        plots['authors'] = self.fig_to_base64(fig3)

        # 4. Open Access Status (Pie Chart) - NEW v4.8 Feature
        # Check if column exists and has data
        if 'oa_status' in df.columns and df['oa_status'].notna().any():
            oa_counts = df['oa_status'].value_counts()
            fig4, ax4 = plt.subplots(figsize=(8, 8))
            ax4.pie(oa_counts, labels=oa_counts.index, autopct='%1.1f%%', startangle=140, colors=sns.color_palette('pastel'))
            ax4.set_title('Open Access Landscape', fontsize=14)
            plots['oa_pie'] = self.fig_to_base64(fig4)
        else:
            plots['oa_pie'] = None # Placeholder if data missing

        # 5. Top Venues / Publishers
        if 'publisher' in df.columns and df['publisher'].notna().any():
            top_publishers = df['publisher'].value_counts().head(10)
            fig5, ax5 = plt.subplots(figsize=(10, 6))
            sns.barplot(x=top_publishers.values, y=top_publishers.index, hue=top_publishers.index, palette='magma', legend=False, ax=ax5)
            ax5.set_title('Top Venues & Publishers', fontsize=14)
            ax5.set_xlabel('Number of Papers')
            plots['venues'] = self.fig_to_base64(fig5)
        else:
            plots['venues'] = None

        # 6. Word Cloud (Content Analysis)
        text = " ".join(title for title in df.title)
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(text)
        
        fig6, ax6 = plt.subplots(figsize=(12, 6))
        ax6.imshow(wordcloud, interpolation='bilinear')
        ax6.axis("off")
        ax6.set_title('Keyword Dominance (Title Analysis)', fontsize=14)
        plots['wordcloud'] = self.fig_to_base64(fig6)

        # 7. Quad-Layer Score Summary Table
        score_stats = {}
        for col in ['strategic_score', 'operational_score', 'tactical_score', 'playground_score', 'overall_score']:
            if col in df.columns:
                score_stats[col] = {
                    'avg': df[col].mean(),
                    'median': df[col].median(),
                    'max': df[col].max(),
                    'min': df[col].min(),
                    'elite_pct': (df[col] >= 7).sum() / len(df) * 100 if len(df) > 0 else 0
                }
        plots['score_stats'] = score_stats

        return plots

    def generate_html_report(self, plots, count):
        """Generates the final HTML file with Dark Mode & Quad-Layer stats."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Build score stats table
        stats = plots.get('score_stats', {})
        score_table = ""
        if stats:
            rows = ""
            labels = {
                'strategic_score': '🔴 Strategic', 'operational_score': '🟣 Operational',
                'tactical_score': '🔵 Tactical', 'playground_score': '🟡 Playground',
                'overall_score': '⭐ Overall'
            }
            for col, info in stats.items():
                label = labels.get(col, col)
                rows += f"""
                <tr>
                    <td>{label}</td>
                    <td>{info['avg']:.2f}</td>
                    <td>{info['median']:.1f}</td>
                    <td>{info['min']:.0f}</td>
                    <td>{info['max']:.0f}</td>
                    <td>{info['elite_pct']:.1f}%</td>
                </tr>"""
            score_table = f"""
            <h2>📊 Quad-Layer Score Summary</h2>
            <table class="score-table">
                <thead><tr><th>Layer</th><th>Avg</th><th>Median</th><th>Min</th><th>Max</th><th>Elite (≥7)</th></tr></thead>
                <tbody>{rows}</tbody>
            </table>"""
        
        # Build venues section
        venues_section = ""
        if plots.get('venues'):
            venues_section = f"""
            <h2>🏆 Top Venues & Publishers</h2>
            <div class="chart-container"><img src="data:image/png;base64,{plots['venues']}" alt="Venues"></div>"""
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>TALOS Scientometrics Report</title>
            <style>
                * {{ box-sizing: border-box; }}
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background-color: #0d1117; color: #e6edf3; }}
                h1 {{ color: #e94560; text-align: center; font-size: 2rem; margin-bottom: 5px; }}
                h2 {{ color: #c9d1d9; text-align: center; margin: 30px 0 15px; font-size: 1.3rem; }}
                .meta {{ text-align: center; color: #8b949e; margin-bottom: 40px; font-size: 0.9rem; }}
                .container {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-width: 1200px; margin: auto; }}
                .full-width {{ grid-column: span 2; }}
                .chart-container {{ background: #161b22; padding: 20px; border-radius: 10px; border: 1px solid #30363d; box-shadow: 0 2px 8px rgba(0,0,0,0.3); }}
                img {{ max-width: 100%; height: auto; }}
                .stat-box {{ text-align: center; font-size: 24px; font-weight: bold; color: #e94560; padding: 20px; background: #161b22; border-radius: 10px; border: 1px solid #30363d; }}
                .score-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background: #161b22; border-radius: 10px; overflow: hidden; border: 1px solid #30363d; }}
                .score-table th {{ background: #1a1a2e; color: #e94560; padding: 12px; text-align: left; font-size: 0.85rem; }}
                .score-table td {{ padding: 10px 12px; border-top: 1px solid #30363d; font-size: 0.9rem; }}
                .score-table tr:hover {{ background: #21262d; }}
            </style>
        </head>
        <body>
            <h1>🧠 Project TALOS: Scientometrics Analysis</h1>
            <div class="meta">Generated: {timestamp} | Papers Analyzed: {count} | Version: v4.8.6 — Dark Mode</div>

            {score_table}

            <div class="container">
                <div class="chart-container full-width stat-box">
                    📚 Knowledge Base: {count} Papers
                </div>

                <div class="chart-container full-width">
                    <h2>📈 Research Timeline: Publications per Year</h2>
                    <img src="data:image/png;base64,{plots['timeline']}" alt="Timeline">
                </div>

                <div class="chart-container">
                    <h2>📊 Quad-Layer Score Distributions</h2>
                    <img src="data:image/png;base64,{plots['scores']}" alt="Scores">
                </div>

                <div class="chart-container">
                    <h2>👥 Top Authors (Top 15)</h2>
                     <img src="data:image/png;base64,{plots['authors']}" alt="Authors">
                </div>
        """
        
        if plots.get('oa_pie'):
            html_content += f"""
                <div class="chart-container">
                    <h2>🔓 Open Access Landscape</h2>
                    <img src="data:image/png;base64,{plots['oa_pie']}" alt="Open Access">
                </div>
            """
        
        html_content += venues_section
        
        html_content += f"""
                <div class="chart-container full-width">
                    <h2>☁️ Keyword Dominance (Title Analysis)</h2>
                    <img src="data:image/png;base64,{plots['wordcloud']}" alt="Wordcloud">
                </div>
            </div>
        </body>
        </html>
        """
        
        filename = f"Scientometrics_Report_{datetime.now().strftime('%Y%m%d')}.html"
        full_path = os.path.join(REPORT_DIR, filename)
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\nReport Generated Successfully: {full_path}")
        # Try to open automatically
        if os.name == 'nt': # Windows
            os.startfile(full_path)
        elif os.name == 'posix': # Mac/Linux
            try:
                os.system(f'open "{full_path}"')
            except:
                pass

def main():
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = DB_PATH

    analyzer = TrendAnalyzer(db_path)
    df = analyzer.load_data()
    
    if not df.empty:
        print("Generating visualizations...")
        plots = analyzer.generate_plots(df)
        analyzer.generate_html_report(plots, len(df))
    else:
        print("No data found to analyze.")

if __name__ == "__main__":
    main()