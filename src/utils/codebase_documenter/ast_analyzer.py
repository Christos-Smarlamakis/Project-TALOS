# -*- coding: utf-8 -*-
"""
Module: ast_analyzer.py
Project: TALOS v5.25.0
Description:
    AST-based static analyzer for the TALOS codebase documentation subsystem.
    Uses the Python ``ast`` module to extract classes, functions, signatures,
    docstrings, imports, and inter-module dependency edges across all project
    modules (112+ files). The extracted blueprint is consumed by the
    MultiLlmRelayOrchestrator to produce ``docs/CODEBASE_DOCUMENTATION_MASTER.md``
    and its standalone HTML companion.

    Key design decisions:
    - Pure standard library (``ast``, ``os``, ``pathlib``, ``dataclasses``) so
      the documenter runs fully air-gapped with zero third-party dependencies.
    - Dependency resolution maps intra-project imports (``src.*``, ``config.*``)
      to their filesystem paths, enabling a deterministic dependency graph.
    - The analyzer is side-effect free: it only reads source files and returns
      plain dictionaries, leaving all persistence to ArchitectureLedger.

Dependencies:
    - ast, os, pathlib, dataclasses: source parsing and filesystem traversal.
    - typing: type annotations.
"""

import ast
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class FunctionSymbol:
    """A single function or method symbol extracted from a module.

    Attributes:
        name (str): Function or method name.
        args (str): Human-readable argument signature.
        line_number (int): One-based line of the definition.
        docstring (str): First sentence of the docstring (if any).
    """

    name: str
    args: str
    line_number: int
    docstring: str = ""


@dataclass
class ClassSymbol:
    """A single class symbol extracted from a module.

    Attributes:
        name (str): Class name.
        line_number (int): One-based line of the definition.
        docstring (str): First sentence of the class docstring (if any).
        methods (list[FunctionSymbol]): Methods defined inside the class.
    """

    name: str
    line_number: int
    docstring: str = ""
    methods: List[FunctionSymbol] = field(default_factory=list)


@dataclass
class ModuleBlueprint:
    """Static analysis result for one source module.

    Attributes:
        path (str): Project-relative filesystem path.
        docstring (str): Module-level docstring summary.
        line_count (int): Total physical line count.
        classes (list[ClassSymbol]): Extracted classes.
        functions (list[FunctionSymbol]): Module-level functions.
        imports (list[str]): Imported module dotted names.
        dependencies (list[str]): Intra-project dependency file paths.
    """

    path: str = ""
    docstring: str = ""
    line_count: int = 0
    classes: List[ClassSymbol] = field(default_factory=list)
    functions: List[FunctionSymbol] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)


class CodebaseAstAnalyzer:
    """AST parser that extracts a documentation blueprint for every module.

    Attributes:
        root_dir (str): Absolute project root directory.
        include_roots (list[str]): Relative directories to scan.
        exclude_dirs (set[str]): Directory names to skip during traversal.
    """

    def __init__(
        self,
        root_dir: Optional[str] = None,
        include_roots: Optional[List[str]] = None,
        exclude_dirs: Optional[Set[str]] = None,
    ) -> None:
        self.root_dir = root_dir or self._resolve_root()
        self.include_roots = include_roots or ["src", "config"]
        self.exclude_dirs = exclude_dirs or {
            "__pycache__",
            ".git",
            ".vscode",
            "vendor",
            "cherry_ui_isolated",
            "graft",
            "tools",
            "models",
            "static",
            "templates",
            "data",
            "logs",
        }

    @staticmethod
    def _resolve_root() -> str:
        """Resolve the project root by walking up to the ``talos.py`` marker."""
        p = os.path.abspath(os.path.dirname(__file__))
        while p and not os.path.exists(os.path.join(p, "talos.py")):
            p = os.path.dirname(p)
        return p or os.path.abspath(os.path.dirname(__file__))

    # ------------------------------------------------------------------
    # -- Discovery -------------------------------------------------------
    # ------------------------------------------------------------------

    def discover_modules(self) -> List[str]:
        """Return project-relative paths of every analyzable Python module.

        Returns:
            list[str]: Sorted relative paths (POSIX separators) to scan.
        """
        modules: List[str] = []
        for root in self.include_roots:
            base = os.path.join(self.root_dir, root)
            if not os.path.isdir(base):
                continue
            for dirpath, dirnames, filenames in os.walk(base):
                dirnames[:] = [
                    d for d in dirnames if d not in self.exclude_dirs
                ]
                for filename in filenames:
                    if not filename.endswith(".py"):
                        continue
                    full = os.path.join(dirpath, filename)
                    modules.append(self._relative(full))
        # -- Include the top-level entry point. --
        entry = os.path.join(self.root_dir, "talos.py")
        if os.path.isfile(entry):
            modules.append("talos.py")
        return sorted(set(modules))

    def _relative(self, path: str) -> str:
        return os.path.relpath(path, self.root_dir).replace(os.sep, "/")

    # ------------------------------------------------------------------
    # -- AST extraction --------------------------------------------------
    # ------------------------------------------------------------------

    def analyze_file(self, rel_path: str) -> Optional[ModuleBlueprint]:
        """Parse one module and return its documentation blueprint.

        Args:
            rel_path (str): Project-relative path to the Python source file.

        Returns:
            Optional[ModuleBlueprint]: The extracted blueprint, or None when
                the file cannot be read or parsed.
        """
        full = os.path.join(self.root_dir, rel_path)
        try:
            with open(full, "r", encoding="utf-8") as fh:
                source = fh.read()
        except OSError:
            return None
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return None

        blueprint = ModuleBlueprint(path=rel_path)
        blueprint.line_count = source.count("\n") + 1
        blueprint.docstring = ast.get_docstring(tree) or ""

        imports: List[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)

        blueprint.imports = sorted(set(imports))
        blueprint.classes = self._extract_classes(tree)
        blueprint.functions = self._extract_functions(tree)
        return blueprint

    @staticmethod
    def _extract_classes(tree: ast.AST) -> List[ClassSymbol]:
        classes: List[ClassSymbol] = []
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            symbol = ClassSymbol(
                name=node.name,
                line_number=node.lineno,
                docstring=_first_sentence(ast.get_docstring(node)),
            )
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    symbol.methods.append(
                        FunctionSymbol(
                            name=item.name,
                            args=_format_args(item),
                            line_number=item.lineno,
                            docstring=_first_sentence(ast.get_docstring(item)),
                        )
                    )
            classes.append(symbol)
        return classes

    @staticmethod
    def _extract_functions(tree: ast.AST) -> List[FunctionSymbol]:
        functions: List[FunctionSymbol] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(
                    FunctionSymbol(
                        name=node.name,
                        args=_format_args(node),
                        line_number=node.lineno,
                        docstring=_first_sentence(ast.get_docstring(node)),
                    )
                )
        return functions

    # ------------------------------------------------------------------
    # -- Aggregate analysis & dependency graph ---------------------------
    # ------------------------------------------------------------------

    def analyze_all(self) -> Dict[str, ModuleBlueprint]:
        """Analyze every discovered module.

        Returns:
            dict[str, ModuleBlueprint]: Mapping of relative path to blueprint.
        """
        result: Dict[str, ModuleBlueprint] = {}
        for rel_path in self.discover_modules():
            blueprint = self.analyze_file(rel_path)
            if blueprint is not None:
                result[rel_path] = blueprint
        return result

    def build_dependency_graph(
        self, analyses: Optional[Dict[str, ModuleBlueprint]] = None
    ) -> Dict[str, List[str]]:
        """Resolve intra-project imports into a dependency adjacency list.

        Args:
            analyses (Optional[dict]): Precomputed analyses (default: analyze
                all modules now).

        Returns:
            dict[str, list[str]]: Module path to sorted dependency paths.
        """
        analyses = analyses if analyses is not None else self.analyze_all()
        file_index = self._file_index(list(analyses.keys()))

        graph: Dict[str, List[str]] = {}
        for path, blueprint in analyses.items():
            deps: Set[str] = set()
            for dotted in blueprint.imports:
                target = file_index.get(dotted)
                if target and target != path:
                    deps.add(target)
            blueprint.dependencies = sorted(deps)
            graph[path] = blueprint.dependencies
        return graph

    def _file_index(self, paths: List[str]) -> Dict[str, str]:
        """Map dotted module names to relative file paths.

        Args:
            paths (list[str]): Project-relative file paths.

        Returns:
            dict[str, str]: Dotted module name to relative path.
        """
        index: Dict[str, str] = {}
        for path in paths:
            stem = path[:-3].replace("/", ".")
            index[stem] = path
            parts = stem.split(".")
            for i in range(1, len(parts)):
                index[".".join(parts[i:])] = path
        return index

    def to_serializable(
        self, analyses: Dict[str, ModuleBlueprint]
    ) -> List[Dict[str, Any]]:
        """Convert blueprints into JSON-serializable dictionaries.

        Args:
            analyses (dict[str, ModuleBlueprint]): The analysis results.

        Returns:
            list[dict]: Serializable per-module blueprint records.
        """
        return [self._blueprint_to_dict(b) for _, b in sorted(analyses.items())]

    @staticmethod
    def _blueprint_to_dict(blueprint: ModuleBlueprint) -> Dict[str, Any]:
        return {
            "path": blueprint.path,
            "docstring": blueprint.docstring,
            "line_count": blueprint.line_count,
            "classes": [
                {
                    "name": c.name,
                    "line_number": c.line_number,
                    "docstring": c.docstring,
                    "methods": [
                        {
                            "name": m.name,
                            "args": m.args,
                            "line_number": m.line_number,
                            "docstring": m.docstring,
                        }
                        for m in c.methods
                    ],
                }
                for c in blueprint.classes
            ],
            "functions": [
                {
                    "name": f.name,
                    "args": f.args,
                    "line_number": f.line_number,
                    "docstring": f.docstring,
                }
                for f in blueprint.functions
            ],
            "imports": blueprint.imports,
            "dependencies": blueprint.dependencies,
        }


def _format_args(node: ast.AST) -> str:
    """Render a function or method argument signature.

    Args:
        node (ast.AST): A FunctionDef or AsyncFunctionDef node.

    Returns:
        str: Comma-separated argument names.
    """
    args = getattr(node, "args", None)
    if args is None:
        return ""
    names = [a.arg for a in getattr(args, "args", [])]
    if getattr(args, "vararg", None):
        names.append("*" + args.vararg.arg)
    for a in getattr(args, "kwonlyargs", []):
        names.append(a.arg)
    if getattr(args, "kwarg", None):
        names.append("**" + args.kwarg.arg)
    return ", ".join(names)


def _first_sentence(docstring: Optional[str]) -> str:
    """Return the first sentence of a docstring for compact summaries.

    Args:
        docstring (Optional[str]): The full docstring.

    Returns:
        str: The first sentence (period-delimited), or an empty string.
    """
    if not docstring:
        return ""
    text = docstring.strip().splitlines()[0].strip()
    for sep in (". ", ".\n"):
        if sep in text:
            text = text.split(sep)[0] + "."
            break
    return text
