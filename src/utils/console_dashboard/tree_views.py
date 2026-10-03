# -*- coding: utf-8 -*-
"""
Module: tree_views.py
Project: TALOS v5.22.0
Description:
    Scientific tree renderer for the TALOS console dashboard. Produces three
    Rich Tree renderables: the six-zone ISO/IEC 25010 architecture map, the
    Project ATHENA PhD research taxonomy (ST-GAT -> Dec-POMDP -> HMADRL ->
    CJCSI 3160.01A), and a live mesh-health tree of the 18 academic ingestion
    APIs plus the 16 LLM providers. All provider status is resolved from the
    local registry (air-gapped); source adapters are marked as registered.

Dependencies:
    - rich.tree.Tree: the tree primitive.
    - src.services.cognitive_mesh.registry (lazy): provider catalogue and status.
"""

from typing import List

from rich.tree import Tree

# -- Canonical 18-source academic ingestion mesh -------------------------------
ACADEMIC_SOURCES: List[str] = [
    "arxiv", "ieee", "semantic_scholar", "springer", "openalex", "dblp",
    "elsevier", "core", "crossref", "openarchives", "pubmed", "scigov",
    "osti", "plos", "openreview", "openaire", "nasa_ntrs", "hal_inria",
]

# -- The six ISO/IEC 25010 functional zones (docs/ARCHITECTURE_MAP.md) ---------
ARCHITECTURE_ZONES: List[str] = [
    "Entrypoints & Orchestration",
    "Scientific Ingestion & Harvesting",
    "PRISMA-ScR & Quality Auditing",
    "Scientific Search & Retrieval",
    "AI Core & Cognitive Routing",
    "Reinforcement Learning & ATHENA Engine",
]


class ScientificTreeViewer:
    """Render scientific knowledge as styled Rich Trees.

    Each method returns a ``rich.tree.Tree`` renderable ready for
    ``console.print``. The viewer performs no writes and no network calls
    beyond the local provider registry's socket probes.
    """

    def render_architecture_tree(self) -> Tree:
        """Render the six ISO/IEC 25010 functional zones as a Tree.

        Returns:
            Tree: The architecture map tree.
        """
        tree = Tree("[bold bright_cyan]TALOS Architecture Map[/bold bright_cyan]")
        tree.add("[bold]ISO/IEC 25010 Functional Zones (6)[/bold]")
        for idx, zone in enumerate(ARCHITECTURE_ZONES, start=1):
            branch = tree.add(f"[bold cyan]Zone {idx}[/bold cyan]: {zone}")
            branch.add("[dim]Constitution V -- verification-first workflow[/dim]")
        tree.add("[bold green]Compliance[/bold green]: ISO/IEC 25010")
        return tree

    def render_research_taxonomy_tree(self) -> Tree:
        """Render the Project ATHENA PhD research taxonomy.

        Returns:
            Tree: The research taxonomy tree.
        """
        tree = Tree("[bold bright_cyan]Project ATHENA -- Research Taxonomy[/bold bright_cyan]")
        gat = tree.add("[bold cyan]Spatio-Temporal Graph Attention Networks (ST-GAT)[/bold cyan]")
        gat.add("[dim]Graph attention over spatio-temporal UAV mission graphs[/dim]")
        dec = tree.add("[bold cyan]Dec-POMDP[/bold cyan]")
        dec.add("[dim]Decentralised partially observable Markov decision processes[/dim]")
        hmadrl = tree.add("[bold cyan]Heterogeneous Multi-Agent DRL (HMADRL)[/bold cyan]")
        hmadrl.add("[dim]Mixed agent types with shared/heterogeneous policies[/dim]")
        cjcsi = tree.add("[bold yellow]CJCSI 3160.01A Constraints[/bold yellow]")
        cjcsi.add("[dim]Command-and-control doctrine bound on autonomous routing[/dim]")
        tree.add("[bold green]Trace[/bold green]: PhD Chapter 2 -> HOU ICBE 2026 extension")
        return tree

    def render_mesh_health_tree(self) -> Tree:
        """Render the 18 ingestion APIs and 16 LLM providers with status.

        Returns:
            Tree: The live mesh-health tree.
        """
        tree = Tree("[bold bright_cyan]Active Ingestion & Provider Mesh[/bold bright_cyan]")
        ingestion = tree.add("[bold]Ingestion Mesh (18 APIs)[/bold]")
        for source in ACADEMIC_SOURCES:
            ingestion.add(f"[cyan]{source}[/cyan] [dim green]REGISTERED[/dim green]")

        provider_root = tree.add("[bold]Provider Registry (16 LLMs)[/bold]")
        descriptors = self._provider_descriptors()
        if descriptors:
            for descriptor in descriptors:
                status = descriptor.is_active
                badge = "[bold green]ONLINE[/bold green]" if status else "[dim red]OFFLINE[/dim red]"
                provider_root.add(f"[cyan]{descriptor.name}[/cyan] {badge}")
        else:
            provider_root.add("[dim]Provider registry unavailable[/dim]")
        return tree

    # ------------------------------------------------------------------
    # -- Registry access ----------------------------------------------
    # ------------------------------------------------------------------

    def _provider_descriptors(self) -> List[object]:
        """Return all provider descriptors from the local registry.

        Returns:
            list: Provider descriptors, or an empty list on failure.
        """
        try:
            from src.services.cognitive_mesh.registry import get_provider_registry

            return get_provider_registry().list_all()
        except Exception:
            return []
