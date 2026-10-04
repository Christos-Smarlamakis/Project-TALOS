# -*- coding: utf-8 -*-
"""
Module: __init__.py
Project: TALOS v5.25.0
Description:
    Public API surface for the TALOS codebase documentation subsystem. Re-exports
    the AST analyzer, the living architecture ledger, the stateful multi-LLM
    relay orchestrator, and the Markdown/HTML compiler. The package depends only
    on the Python standard library and the extraction-ready Cognitive Mesh
    microservice, so it can be lifted into the documentation relay for any
    sibling project.

Dependencies:
    - src.utils.codebase_documenter.ast_analyzer: CodebaseAstAnalyzer.
    - src.utils.codebase_documenter.architecture_ledger: ArchitectureLedger.
    - src.utils.codebase_documenter.relay_orchestrator: MultiLlmRelayOrchestrator.
    - src.utils.codebase_documenter.markdown_html_generator: CodebaseDocGenerator.
"""

from src.utils.codebase_documenter.architecture_ledger import (  # noqa: F401
    ArchitectureLedger,
)
from src.utils.codebase_documenter.ast_analyzer import (  # noqa: F401
    CodebaseAstAnalyzer,
    ModuleBlueprint,
)
from src.utils.codebase_documenter.markdown_html_generator import (  # noqa: F401
    CodebaseDocGenerator,
)
from src.utils.codebase_documenter.relay_orchestrator import (  # noqa: F401
    MultiLlmRelayOrchestrator,
)

__all__ = [
    "CodebaseAstAnalyzer",
    "ModuleBlueprint",
    "ArchitectureLedger",
    "MultiLlmRelayOrchestrator",
    "CodebaseDocGenerator",
]
