"""Guards for the ``src.runs`` public surface and its persistence boundary."""

from __future__ import annotations

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[2] / "src"
RUNS_ROOT = SRC_ROOT / "runs"
PUBLIC_SUBMODULES = {"src.runs", "src.runs.contracts", "src.runs.ports"}


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            modules.append(node.module)
    return modules


def test_runs_internals_are_only_imported_from_inside_the_package() -> None:
    """Outside packages must use ``src.runs`` / ``contracts`` / ``ports`` only."""
    violations: list[str] = []
    for path in SRC_ROOT.rglob("*.py"):
        if RUNS_ROOT in path.parents:
            continue
        for module in _imported_modules(path):
            if not module.startswith("src.runs."):
                continue
            if module in PUBLIC_SUBMODULES:
                continue
            violations.append(f"{path.relative_to(SRC_ROOT.parent)} imports {module}")
    assert not violations, "Import run lifecycle entry points from `src.runs`:\n" + "\n".join(violations)


def test_runs_package_does_not_know_about_storage_backends() -> None:
    """``src.runs`` must not import SQLAlchemy, a driver, or the DAO layer."""
    forbidden = ("sqlalchemy", "asyncpg", "psycopg", "redis", "src.dao")
    violations: list[str] = []
    for path in RUNS_ROOT.rglob("*.py"):
        for module in _imported_modules(path):
            if module.startswith(forbidden):
                violations.append(f"{path.relative_to(SRC_ROOT.parent)} imports {module}")
    assert not violations, "src.runs must stay persistence-agnostic:\n" + "\n".join(violations)
