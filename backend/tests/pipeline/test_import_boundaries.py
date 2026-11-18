"""Import-boundary checks for the pipeline domain layer.

These tests are deliberately AST-based: they inspect imports without importing
the modules under test, so they stay cheap and independent of optional runtime
dependencies (AgentScope, database drivers, external services).
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = BACKEND_ROOT / "src"
PIPELINE_ROOT = SRC_ROOT / "pipeline"

# Modules replaced by the pipeline directory migration.  Their transitional
# re-export shims were removed, so importing an old path is a hard failure; the
# AST check also guards against re-introducing a legacy module.
REMOVED_LEGACY_MODULES = (
    "src.agents.orchestrator",
    "src.agents.phase_1_adapter",
    "src.agents.phase_2_adapter",
    "src.agents.phase_3_adapter",
    "src.agents.phase_4_adapter",
    "src.core.source_fact_chain",
)


def _iter_python_files(root: Path) -> list[Path]:
    """Return Python files below ``root``, skipping caches and virtualenvs."""
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts and ".venv" not in path.parts)


def _module_name(path: Path, package_root: Path) -> str:
    """Return the dotted module name for a file under ``package_root``."""
    relative = path.relative_to(package_root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _resolve_import(node: ast.AST, importer: Path, package_root: Path) -> list[str]:
    """Resolve absolute and relative imports of one AST node to module names."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []

    if node.level == 0:
        return [node.module] if node.module else []

    importer_parts = _module_name(importer, package_root).split(".")
    if importer.is_file() and importer.name != "__init__.py":
        importer_parts = importer_parts[:-1]
    # ``level == 1`` means the current package, ``level == 2`` its parent, ...
    keep = len(importer_parts) - (node.level - 1)
    base = importer_parts[:keep]
    if node.module:
        base.append(node.module)
    return [".".join(base)] if base else []


def _imported_modules(path: Path, package_root: Path = SRC_ROOT) -> set[str]:
    """Return every module name imported by ``path`` (including submodules)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules.update(_resolve_import(node, path, package_root))
    return modules


def _matches(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def _imports_any(imports: set[str], prefixes: tuple[str, ...]) -> list[str]:
    return sorted(module for module in imports if any(_matches(module, prefix) for prefix in prefixes))


def _assert_no_imports(
    root: Path,
    forbidden: tuple[str, ...],
    boundary: str,
    package_root: Path = SRC_ROOT,
) -> None:
    violations: list[str] = []
    for path in _iter_python_files(root):
        hits = _imports_any(_imported_modules(path, package_root), forbidden)
        if hits:
            relative = path.relative_to(BACKEND_ROOT)
            violations.append(f"{relative} -> {', '.join(hits)}")
    assert not violations, f"{boundary} violated:\n" + "\n".join(violations)


def test_pipeline_skeleton_packages_exist() -> None:
    for layer in ("graph", "skills", "tools", "mcp", "contracts"):
        package = PIPELINE_ROOT / layer
        assert (package / "__init__.py").is_file(), f"missing skeleton package: {package}"


def test_graph_does_not_import_agentscope() -> None:
    _assert_no_imports(
        PIPELINE_ROOT / "graph",
        ("agentscope",),
        "graph/ must not import agentscope (prompts and model calls belong to skills/)",
    )


def test_skills_do_not_import_database_clients() -> None:
    _assert_no_imports(
        PIPELINE_ROOT / "skills",
        (
            "sqlalchemy",
            "neo4j",
            "asyncpg",
            "psycopg",
            "psycopg2",
            "sqlite3",
            "src.dao",
        ),
        "skills/ must not import database clients or src.dao (use tools/)",
    )


def test_skills_do_not_import_graph() -> None:
    _assert_no_imports(
        PIPELINE_ROOT / "skills",
        ("src.pipeline.graph",),
        "skills/ must not import graph/ (graph depends on skills, not the reverse)",
    )


def test_tools_do_not_import_agentscope() -> None:
    _assert_no_imports(
        PIPELINE_ROOT / "tools",
        ("agentscope",),
        "tools/ must not import agentscope (tools carry no agent decisions)",
    )


def test_tools_do_not_import_skills_or_graph() -> None:
    _assert_no_imports(
        PIPELINE_ROOT / "tools",
        ("src.pipeline.skills", "src.pipeline.graph"),
        "tools/ must not import skills/ or graph/ (tools stay deterministic leaves)",
    )


def test_mcp_does_not_import_skills_or_tools() -> None:
    _assert_no_imports(
        PIPELINE_ROOT / "mcp",
        ("src.pipeline.skills", "src.pipeline.tools"),
        "mcp/ must not import skills/ or tools/ (external adapters stay isolated)",
    )


def test_phase_modules_resolve_default_output_root_to_app_root() -> None:
    """Phase modules must keep ``<app root>/data/pipeline`` as the default.

    ``phase_2.py`` and ``phase_3.py`` derive the data directory from their own
    location.  Moving them one level deeper must come with an explicit depth
    change, otherwise artifacts silently land in ``src/data``.
    """
    for name in ("phase_2.py", "phase_3.py"):
        module_path = PIPELINE_ROOT / "graph" / "phases" / name
        assert module_path.resolve().parents[5] == BACKEND_ROOT.parent, (
            f"{name} no longer sits four levels below the app root; update its parents[] depth"
        )


def test_pipeline_tree_does_not_import_removed_legacy_modules() -> None:
    _assert_no_imports(
        PIPELINE_ROOT,
        REMOVED_LEGACY_MODULES,
        "src/pipeline must import the new module paths, not the removed legacy shims",
    )


def test_source_and_tests_do_not_import_removed_legacy_modules() -> None:
    for root, package_root, boundary in (
        (SRC_ROOT, SRC_ROOT, "src/"),
        (BACKEND_ROOT / "tests", BACKEND_ROOT / "tests", "tests/"),
    ):
        _assert_no_imports(
            root,
            REMOVED_LEGACY_MODULES,
            f"{boundary} must not import the removed legacy shim modules",
            package_root,
        )
