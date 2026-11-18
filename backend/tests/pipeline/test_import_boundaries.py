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

# The five modules moved to ``src/pipeline/graph`` in stage 1.  Their old paths
# remain as re-export shims; production code may only reach them through the
# allowlist below (in practice, ``src/api/wiring.py``).
LEGACY_GRAPH_MODULES = (
    "src.agents.orchestrator",
    "src.agents.phase_1_adapter",
    "src.agents.phase_2_adapter",
    "src.agents.phase_3_adapter",
    "src.agents.phase_4_adapter",
)

# The source-fact-chain modules moved to ``src/pipeline/{tools,skills}`` in
# stage 2.  Their old paths stay importable as shims for one release cycle.
LEGACY_FACT_CHAIN_MODULES = ("src.core.source_fact_chain",)

# The ingest slices moved to ``src/pipeline/tools/{acquisition,parsing}`` in
# stage 3; the old paths remain as re-export shims.
LEGACY_INGEST_MODULES = (
    "src.core.ingest_and_digitize_data.document_acquisition",
    "src.core.ingest_and_digitize_data.parse_document",
)

# The terminology slices moved to ``src/pipeline/tools/terminology`` and
# ``src/core/terminology_shared`` in stage 4b.
LEGACY_TERMINOLOGY_MODULES = ("src.core.standardize_entities_and_align_knowledge",)

# Files outside ``src/pipeline`` that are allowed to import a legacy module
# path.  Wiring intentionally keeps the old imports so the outer service layer
# does not change in the migration.
LEGACY_IMPORT_ALLOWLIST = frozenset({"api/wiring.py"})


def _iter_python_files(root: Path) -> list[Path]:
    """Return Python files below ``root``, skipping caches and virtualenvs."""
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts and ".venv" not in path.parts)


def _module_name(path: Path) -> str:
    """Return the dotted module name for a file under ``src``."""
    relative = path.relative_to(SRC_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _resolve_import(node: ast.AST, importer: Path) -> list[str]:
    """Resolve absolute and relative imports of one AST node to module names."""
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []

    if node.level == 0:
        return [node.module] if node.module else []

    importer_parts = _module_name(importer).split(".")
    if importer.is_file() and importer.name != "__init__.py":
        importer_parts = importer_parts[:-1]
    # ``level == 1`` means the current package, ``level == 2`` its parent, ...
    keep = len(importer_parts) - (node.level - 1)
    base = importer_parts[:keep]
    if node.module:
        base.append(node.module)
    return [".".join(base)] if base else []


def _imported_modules(path: Path) -> set[str]:
    """Return every module name imported by ``path`` (including submodules)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules.update(_resolve_import(node, path))
    return modules


def _matches(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def _imports_any(imports: set[str], prefixes: tuple[str, ...]) -> list[str]:
    return sorted(module for module in imports if any(_matches(module, prefix) for prefix in prefixes))


def _assert_no_imports(
    root: Path,
    forbidden: tuple[str, ...],
    boundary: str,
) -> None:
    violations: list[str] = []
    for path in _iter_python_files(root):
        hits = _imports_any(_imported_modules(path), forbidden)
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


def test_terminology_shared_does_not_import_pipeline() -> None:
    shared_root = SRC_ROOT / "core" / "terminology_shared"
    assert _iter_python_files(shared_root), f"no files to scan under {shared_root}"
    _assert_no_imports(
        shared_root,
        ("src.pipeline",),
        "src/core/terminology_shared must stay neutral (graph_rag and evidence_extraction import it)",
    )


def test_dormant_and_shared_core_do_not_import_pipeline() -> None:
    """graph_rag/evidence_extraction/translation must never depend on the pipeline layer."""
    for name in ("graph_rag", "evidence_extraction", "cross_lingual_translation"):
        root = SRC_ROOT / "core" / name
        assert _iter_python_files(root), f"no files to scan under {root}"
        _assert_no_imports(
            root,
            ("src.pipeline",),
            f"src/core/{name} must not import src.pipeline (reverse dependency)",
        )


def test_pipeline_tree_does_not_import_legacy_modules() -> None:
    _assert_no_imports(
        PIPELINE_ROOT,
        LEGACY_GRAPH_MODULES + LEGACY_FACT_CHAIN_MODULES + LEGACY_INGEST_MODULES + LEGACY_TERMINOLOGY_MODULES,
        "src/pipeline must import the new module paths, not the legacy shims",
    )


def test_legacy_imports_are_confined_to_allowlist() -> None:
    legacy = LEGACY_GRAPH_MODULES + LEGACY_FACT_CHAIN_MODULES + LEGACY_INGEST_MODULES + LEGACY_TERMINOLOGY_MODULES
    violations: list[str] = []
    for path in _iter_python_files(SRC_ROOT):
        relative = path.relative_to(SRC_ROOT)
        if not relative.parts or relative.parts[0] == "pipeline":
            continue
        if str(relative) in LEGACY_IMPORT_ALLOWLIST:
            continue
        hits = _imports_any(_imported_modules(path), legacy)
        if hits:
            violations.append(f"src/{relative} -> {', '.join(hits)}")
    assert not violations, (
        "legacy module imports are only allowed in the shim allowlist "
        f"{sorted(LEGACY_IMPORT_ALLOWLIST)}:\n" + "\n".join(violations)
    )
