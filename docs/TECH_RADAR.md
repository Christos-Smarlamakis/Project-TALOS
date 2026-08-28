# TALOS Tech Radar & Ecosystem Map

> **Last Updated:** 2026-08-28 (v5.10.13 -- Desktop Control Hub, Self-Healing Infrastructure, Active Profile Persistence & Environment Canon Overhaul)

This document is the technology radar of Project TALOS. It catalogues the development stack, the agentic architecture, the document-comprehension tooling, and the simulation capabilities that surround the core TALOS research intelligence system. It tracks State-of-the-Art (SOTA) technologies and maps the surrounding research-intelligence ecosystem.

---

## 1. Development Stack (The Tools That Build TALOS)

The development tooling that lets developers iterate on TALOS quickly and safely.

*   **Free Claude Code (via NVIDIA NIM / Ollama)**
    *   **What it is:** A local proxy for running an AI coding assistant (Claude Code) with no per-token cost.
    *   **Role in TALOS:** Acts as a junior developer. Writes and edits Python scripts (for example, the PDF Downloader in v4.9.0) under human review.

*   **Spec Kit (Spec-Driven Development)**
    *   **What it is:** A spec-driven workflow that turns natural-language specifications into AI coding tasks.
    *   **Role in TALOS:** Complements Claude Code. Produces a specification (Constitution/Plan) that the AI follows so changes stay deterministic and auditable.

*   **LeanKG**
    *   **What it is:** A lightweight knowledge-graph engine for project memory.
    *   **Role in TALOS:** Stores what TALOS already knows so Claude Code can retrieve relevant context without re-reading files, saving tokens.

*   **Mini-Wiki (Plugin: paper-drafter)**
    *   **What it is:** A wiki-style plugin for generating documentation and LaTeX papers.
    *   **Role in TALOS:** Drafts papers from TALOS results, producing an IMRaD draft with Mermaid diagrams for visualization.

---

*   **Daemon OS Autostart (pywin32 Shell COM)**
    *   **What it is:** A Windows OS autostart orchestrator that generates a boot batch script and registers a Startup-folder shortcut for the 24/7 daemon.
    *   **Role in TALOS:** Keeps the autonomous research daemon running across reboots (minimized console, system icon) with configurable network strategy and target sources.

*   **System Tray Automation & Native OS Desktop Bridge (v5.10.13)**
    *   **What it is:** A pystray-based Desktop Control Hub plus a native OS desktop bridge (`os.startfile` / `open` / `xdg-open`) with self-healing API auto-bootstrap (`uvicorn` spawn on demand via `_ensure_api_server()`).
    *   **Role in TALOS:** Gives the 24/7 daemon a seven-item tray menu (visualizer, reports folder, system log, Swagger docs, instant scrape, console toggle, terminate) that boots the FastAPI backend on demand.

## 2. Agentic & Core Architecture (TALOS v5.0)

The architecture that turns TALOS from a script into an agent swarm.

*   **AgentScope**
    *   **What it is:** A production-ready Multi-Agent framework with Agentic Reinforcement Learning.
    *   **Role in TALOS:** Serves as the backbone of v5.0. Orchestrates the scripts into an agent swarm where each agent decides which API to query next.

---

## 3. Document Comprehension & RAG (Reading What TALOS Finds)

Tools for reading and understanding the papers TALOS ingests, including PDFs.

*   **RAG-Anything / LightRAG (GraphRAG)**
    *   **What it is:** Retrieval-Augmented Generation that builds a knowledge graph over retrieved documents.
    *   **Role in TALOS:** When TALOS ingests a PDF, these tools extract structured, graph-based knowledge from it.

*   **OpenRAG**
    *   **What it is:** An open-source, pluggable RAG pipeline with a UI.
    *   **Role in TALOS:** Provides an alternative (with a web UI) for reading TALOS-ingested papers, keeping retrieval costs low.

---

## 4. Simulation & Playground (The World of the Drones)

Simulation and rendering tooling for the Drone Swarms research domain.

*   **Urbanity**
    *   **What it is:** A Python library for generating OpenStreetMap-derived street networks for AI.
    *   **Role in TALOS:** Provides realistic urban environments (buildings, streets, parks) for drone-swarm path-planning simulations.

*   **forge3d**
    *   **What it is:** A Python library for 3D GPU-accelerated rendering.
    *   **Role in TALOS:** Produces publication-quality (4K) 3D visualizations of drone swarms for reports and papers.

---

## 5. Related Works & Competitors (The Papers and Projects Nearby)

Related systems and competitors that TALOS is evaluated against, tracked to keep the roadmap honest.

*   **AutoResearchClaw:** An autonomous end-to-end pipeline for reading papers. Compared to TALOS to highlight the value of the human-in-the-loop approach.
*   **Hermes Agent Ecosystem:** An agent with a built-in learning loop and a skills marketplace.
*   **OnionClaw:** An autonomous agent for Dark Web/Tor research. Tracked under "Future Work / Security in Swarms" for threat intelligence.

---

> **Project Version:** v5.10.13 | **Last Updated:** 2026-08-28 (v5.10.13 -- Desktop Control Hub, Self-Healing Infrastructure, Active Profile Persistence & Environment Canon Overhaul)
