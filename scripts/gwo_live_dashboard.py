# -*- coding: utf-8 -*-
"""
Module: gwo_live_dashboard.py (v1.0 — Dash Live GWO Visualizer)
Project: TALOS v5.3.3
Description:
    Dash web application for TRULY LIVE Grey Wolf Optimizer visualization.
    Uses dcc.Interval for native real-time updates (no st.rerun() issues).
    Reads gwo_progress.json and gwo_history.json from the models/ directory.

    How it works:
    1. dcc.Interval fires every 3 seconds.
    2. The callback reads gwo_progress.json for progress + gwo_history.json
       for the full per-iteration wolf positions.
    3. Updates the 3D scatter plot in-place — no page reload.
    4. When GWO completes (status="complete"), the interval stops.

    Usage:
        python scripts/gwo_live_dashboard.py
        # Then open http://localhost:8050 in your browser.

    Key design decisions:
    - Uses Dash (from Plotly) — same Plotly API as Streamlit, native live updates.
    - Runs on port 8050 (separate from Streamlit's 8501).
    - Only reads gwo_progress.json and gwo_history.json when they exist.
    - Gracefully handles missing/pending files.
"""
import os
import sys
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

# ── Paths ────────────────────────────────────────────────────────────────────
MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'models')
PROGRESS_PATH = os.path.join(MODELS_DIR, 'gwo_progress.json')
HISTORY_PATH = os.path.join(MODELS_DIR, 'gwo_history.json')

# ── Dash App ─────────────────────────────────────────────────────────────────
app = dash.Dash(__name__, title="TALOS — GWO Live Swarm Hunt")

app.layout = html.Div([
    html.H1("GWO Swarm Hunt — Live", style={
        'textAlign': 'center', 'color': '#4a9eff', 'fontFamily': 'Arial',
        'marginTop': '20px'
    }),
    html.Div(id='status-bar', style={
        'textAlign': 'center', 'fontSize': '18px', 'marginBottom': '10px', 'color': '#e0e0e0'
    }),
    dcc.Graph(id='swarm-3d', style={'height': '65vh'}),
    dcc.Interval(id='interval', interval=3000, n_intervals=0),  # 3 seconds
    html.Div(id='footer', style={
        'textAlign': 'center', 'color': '#8b949e', 'fontSize': '12px',
        'marginTop': '10px'
    }, children="Auto-refreshing every 3 seconds. Close this tab when done."),
], style={'backgroundColor': '#0a1628', 'minHeight': '100vh', 'padding': '20px'})


@app.callback(
    [Output('swarm-3d', 'figure'),
     Output('status-bar', 'children'),
     Output('interval', 'disabled')],
    [Input('interval', 'n_intervals')]
)
def update_dashboard(n_intervals):
    """
    Update the 3D scatter plot and status bar from GWO progress/history files.

    Called by dcc.Interval every 3 seconds. Reads gwo_progress.json for
    status + gwo_history.json for the full per-iteration wolf positions.

    Args:
        n_intervals (int): Number of times the interval has fired (unused).

    Returns:
        tuple: (figure, status_text, interval_disabled)
    """
    # ── Default figure for empty state ────────────────────────────────────
    empty_fig = go.Figure()
    empty_fig.update_layout(
        title="Waiting for GWO to start...",
        scene=dict(
            xaxis=dict(title="Learning Rate", type="log"),
            yaxis=dict(title="Gamma", range=[0.48, 1.0]),
            zaxis=dict(title="Epsilon Decay", range=[0.88, 1.0]),
            bgcolor='rgba(0,0,0,0)',
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0'),
        height=600,
    )

    # ── Check progress file ───────────────────────────────────────────────
    if not os.path.exists(PROGRESS_PATH):
        return empty_fig, "No GWO process detected. Run the optimizer first.", False

    try:
        with open(PROGRESS_PATH, 'r', encoding='utf-8') as f:
            progress = json.load(f)
    except Exception:
        return empty_fig, "Waiting for GWO to start...", False

    status = progress.get('status', 'unknown')
    iteration = progress.get('iteration', 0)
    max_iters = progress.get('max_iterations', '?')
    best_reward = progress.get('best_reward', 0)
    a_factor = progress.get('a_factor', 2.0)

    # ── Status bar text ───────────────────────────────────────────────────
    if status == 'complete':
        status_text = html.Span([
            html.Strong("COMPLETE! ", style={'color': '#4a9eff'}),
            f"Iteration {iteration}/{max_iters} | ",
            f"Best Reward: {best_reward:.1f} | ",
            f"Alpha: a={a_factor:.3f}",
        ])
        interval_disabled = True  # Stop polling
    elif status == 'running' or status == 'starting':
        status_text = html.Span([
            html.Strong("RUNNING", style={'color': '#ff6b6b'}),
            f" | Iteration {iteration}/{max_iters} | ",
            f"Best Reward: {best_reward:.1f} | ",
            f"a={a_factor:.3f}",
        ])
        interval_disabled = False
    else:
        status_text = f"Status: {status}"
        interval_disabled = False

    # ── Build 3D scatter from history file ────────────────────────────────
    if not os.path.exists(HISTORY_PATH):
        return empty_fig, status_text, interval_disabled

    try:
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            gwo_history = json.load(f)
    except Exception:
        return empty_fig, status_text, interval_disabled

    if not gwo_history:
        return empty_fig, status_text, interval_disabled

    # Show the LATEST iteration
    entry = gwo_history[-1]
    wolves_data = entry.get('wolves', [])
    current_iter = entry.get('iteration', iteration)

    # ── Group by role ─────────────────────────────────────────────────────
    roles = {"alpha": [], "beta": [], "delta": [], "omega": []}
    for w in wolves_data:
        roles[w["role"]].append(w)

    # ── Build Plotly figure ──────────────────────────────────────────────
    fig = go.Figure()

    # Omega wolves: colored by fitness
    if roles["omega"]:
        fig.add_trace(go.Scatter3d(
            x=[w["lr"] for w in roles["omega"]],
            y=[w["gamma"] for w in roles["omega"]],
            z=[w["eps_d"] for w in roles["omega"]],
            mode='markers',
            marker=dict(
                size=6,
                color=[w["fitness"] for w in roles["omega"]],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Fitness", x=1.02),
                opacity=0.7,
            ),
            name=f'Omega ({len(roles["omega"])})',
            hovertemplate='LR: %{x:.2e}<br>Gamma: %{y:.3f}<br>Eps Decay: %{z:.4f}<br>Fitness: %{marker.color:.1f}<extra></extra>',
        ))

    # Delta, Beta, Alpha
    for role, color, size, label in [
        ("delta", "gold", 10, "Delta"),
        ("beta", "darkorange", 12, "Beta"),
        ("alpha", "crimson", 16, "ALPHA ★"),
    ]:
        if roles[role]:
            w = roles[role][0]
            fig.add_trace(go.Scatter3d(
                x=[w["lr"]], y=[w["gamma"]], z=[w["eps_d"]],
                mode='markers+text',
                marker=dict(size=size, color=color, symbol='diamond',
                           line=dict(color='black', width=1)),
                text=[label],
                textposition='top center',
                textfont=dict(size=size-2, color=color),
                name=f'{label} (fitness={w["fitness"]:.1f})',
                hovertemplate=f'{label}<br>LR: %{{x:.2e}}<br>Gamma: %{{y:.3f}}<br>Eps Decay: %{{z:.4f}}<br>Fitness: %{{customdata:.1f}}<extra></extra>',
                customdata=[w["fitness"]],
            ))

    fig.update_layout(
        title=dict(
            text=f"GWO Swarm Hunt — Iteration {current_iter}",
            font=dict(size=18, color='#4a9eff'),
        ),
        scene=dict(
            xaxis=dict(title="Learning Rate", type="log", gridcolor='rgba(128,128,128,0.2)'),
            yaxis=dict(title="Gamma (Discount)", range=[0.48, 1.0], gridcolor='rgba(128,128,128,0.2)'),
            zaxis=dict(title="Epsilon Decay", range=[0.88, 1.0], gridcolor='rgba(128,128,128,0.2)'),
            bgcolor='rgba(0,0,0,0)',
        ),
        legend=dict(x=0.01, y=0.99, bgcolor='rgba(0,0,0,0.3)'),
        margin=dict(l=0, r=0, b=0, t=50),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#e0e0e0'),
    )

    return fig, status_text, interval_disabled


if __name__ == '__main__':
    print("=" * 55)
    print("  GWO Live Dashboard — http://localhost:8050")
    print("=" * 55)
    print("  Auto-refreshes every 3 seconds.")
    print("  Shows the LATEST iteration of the GWO swarm.")
    print("  Close this terminal to stop the dashboard.")
    print("=" * 55)
    app.run(host='127.0.0.1', port=8050, debug=False)