# -*- coding: utf-8 -*-
"""
Module: relay_orchestrator.py
Project: TALOS v5.25.0
Description:
    Stateful multi-LLM relay orchestrator for the TALOS codebase documentation
    subsystem. It walks every discovered module, builds an AST blueprint,
    passes that blueprint plus prior decisions and a rolling handoff memo to
    the Cognitive Meta-Router under the ``AUTO_SWARM_CASCADE`` strategy, and
    logs every step to the Explainable AI decision ledger. The compiled output
    is handed to ``CodebaseDocGenerator`` to produce the master Markdown and
    standalone HTML documents.

    Key design decisions:
    - Deterministic dry-run: when no router transport is available, the
      orchestrator still builds the AST dependency graph, records architectural
      decisions, registers symbols, and emits a full documentation set from the
      blueprints alone (exit 0, fully offline).
    - Mode-aware dispatch: ``cascade`` uses AUTO_SWARM_CASCADE, ``local`` uses
      LOCAL_AIRGAPPED, and ``dry_run`` performs no model dispatch.
    - Every module step logs exactly one XAI audit record via the injected
      XAiDecisionLedger.

Dependencies:
    - typing: type annotations.
    - src.utils.codebase_documenter.ast_analyzer: CodebaseAstAnalyzer.
    - src.utils.codebase_documenter.architecture_ledger: ArchitectureLedger.
    - src.utils.codebase_documenter.markdown_html_generator: CodebaseDocGenerator.
    - src.services.cognitive_mesh: router, dto, and xai_ledger.
"""

from typing import Any, Dict, List, Optional

from src.services.cognitive_mesh.dto import (
    RouterTaskRequest,
    RoutingStrategy,
)
from src.services.cognitive_mesh.router import (
    CognitiveMetaRouter,
    DynamicSwarmSizer,
)
from src.services.cognitive_mesh.xai_ledger import XAiDecisionLedger
from src.utils.codebase_documenter.architecture_ledger import ArchitectureLedger
from src.utils.codebase_documenter.ast_analyzer import (
    CodebaseAstAnalyzer,
    ModuleBlueprint,
)
from src.utils.codebase_documenter.markdown_html_generator import (
    CodebaseDocGenerator,
)


class MultiLlmRelayOrchestrator:
    """Stateful multi-LLM relay orchestrator with XAI tracking.

    Attributes:
        analyzer (CodebaseAstAnalyzer): AST blueprint extractor.
        architecture_ledger (ArchitectureLedger): Decision log and symbol table.
        xai_ledger (XAiDecisionLedger): Append-only XAI audit ledger.
        router (Optional[CognitiveMetaRouter]): Router used for dispatch.
        generator (CodebaseDocGenerator): Markdown/HTML compiler.
    """

    def __init__(
        self,
        analyzer: Optional[CodebaseAstAnalyzer] = None,
        architecture_ledger: Optional[ArchitectureLedger] = None,
        xai_ledger: Optional[XAiDecisionLedger] = None,
        router: Optional[CognitiveMetaRouter] = None,
        generator: Optional[CodebaseDocGenerator] = None,
    ) -> None:
        self.analyzer = analyzer or CodebaseAstAnalyzer()
        self.architecture_ledger = architecture_ledger or ArchitectureLedger()
        self.xai_ledger = xai_ledger or XAiDecisionLedger()
        self.router = router
        self.generator = generator or CodebaseDocGenerator()

    # ------------------------------------------------------------------
    # -- Public API -----------------------------------------------------
    # ------------------------------------------------------------------

    def run(
        self,
        mode: str = "cascade",
        dry_run: bool = False,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Execute the codebase documentation relay.

        Args:
            mode (str): ``"cascade"``, ``"local"``, or ``"dry_run"``.
            dry_run (bool): Force decision-only execution without dispatch.
            limit (Optional[int]): Restrict to the first N modules (testing).

        Returns:
            dict: Summary with generated artefact paths and module count.
        """
        blueprints = self.analyzer.analyze_all()
        graph = self.analyzer.build_dependency_graph(blueprints)
        modules = sorted(blueprints.keys())
        if limit:
            modules = modules[: max(0, int(limit))]

        sizer = DynamicSwarmSizer(ledger=self.xai_ledger)
        llm_contents: Dict[str, str] = {}
        handoff_memo = ""
        prior_paths: List[str] = []

        for path in modules:
            blueprint = blueprints[path]
            prompt = self._build_prompt(blueprint, prior_paths, handoff_memo)
            payload = {
                "text": prompt,
                "module": path,
                "task": "codebase_documentation",
            }

            # -- Log one XAI audit record per module step (swarm sizing). --
            sizer.recommend_swarm("documentation", payload)

            # -- Optional LLM dispatch through the cognitive meta-router. --
            content = None
            if not dry_run and self.router is not None:
                strategy = (
                    RoutingStrategy.AUTO_SWARM_CASCADE
                    if mode == "cascade"
                    else RoutingStrategy.LOCAL_AIRGAPPED
                )
                response = self.router.dispatch(
                    RouterTaskRequest(
                        task_type="documentation",
                        strategy=strategy,
                        payload=payload,
                        messages=[{"role": "user", "content": prompt}],
                        response_format="text",
                    )
                )
                content = self._extract_content(response)
            if content:
                llm_contents[path] = content

            self.architecture_ledger.record_decision(
                path, "documented", blueprint.docstring[:160]
            )
            self.architecture_ledger.register_symbols(
                path,
                [c.name for c in blueprint.classes],
                [f.name for f in blueprint.functions],
            )
            self.architecture_ledger.mark_documented(path)

            handoff_memo = self._handoff(path, blueprint)
            prior_paths.append(path)

        records = self.analyzer.to_serializable(
            {p: blueprints[p] for p in modules}
        )
        result = self.generator.generate(records, llm_contents, graph)
        result["mode"] = mode
        result["dry_run"] = dry_run
        result["xai_records"] = len(self.xai_ledger.latest(10000))
        return result

    # ------------------------------------------------------------------
    # -- Prompt & handoff helpers -----------------------------------------
    # ------------------------------------------------------------------

    def _build_prompt(
        self,
        blueprint: ModuleBlueprint,
        prior_paths: List[str],
        handoff_memo: str,
    ) -> str:
        parts = [
            "Document one module of the TALOS codebase in academic prose.",
            "Module path: {}".format(blueprint.path),
            "Module docstring: {}".format(blueprint.docstring or "(none)"),
            "Classes: {}".format(
                ", ".join(c.name for c in blueprint.classes) or "(none)"
            ),
            "Functions: {}".format(
                ", ".join(f.name for f in blueprint.functions) or "(none)"
            ),
            "Dependencies: {}".format(
                ", ".join(blueprint.dependencies) or "(none)"
            ),
        ]
        if prior_paths:
            parts.append(
                "Previously documented: {}".format(", ".join(prior_paths[-5:]))
            )
        if handoff_memo:
            parts.append("Handoff memo: {}".format(handoff_memo))
        return "\n".join(parts)

    @staticmethod
    def _handoff(path: str, blueprint: ModuleBlueprint) -> str:
        return "Documented {} ({} classes, {} functions).".format(
            path, len(blueprint.classes), len(blueprint.functions)
        )

    @staticmethod
    def _extract_content(response: Any) -> Optional[str]:
        content = getattr(response, "content", None)
        return content if isinstance(content, str) else None

