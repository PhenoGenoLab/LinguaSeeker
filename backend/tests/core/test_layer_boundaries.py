"""Layer-boundary checks for ``src.core``.

``src.core`` is split into four strata.  Phase numbering is *not* a core concept —
the phases live in ``src.pipeline.graph``; core holds the agents each phase calls.

    foundation  ← shared ← agents
                    ↑
                 adapters

``core.root`` (``config.py``) is importable by everyone and
imports nothing from the strata.  The tests are AST-based so they stay cheap and
independent of optional runtime dependencies.
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = BACKEND_ROOT / "src"
CORE_ROOT = SRC_ROOT / "core"

FOUNDATION = CORE_ROOT / "foundation"
SHARED = CORE_ROOT / "shared"
ADAPTERS = CORE_ROOT / "adapters"


def _iter_python_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _imported_modules(path: Path) -> set[str]:
    """Return absolute ``src.*`` modules imported by ``path``, relative ones resolved."""
    parts = path.relative_to(SRC_ROOT).with_suffix("").parts
    package = list(parts[:-1])
    modules: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = package[: len(package) - node.level + 1]
                modules.add(".".join(base + ([node.module] if node.module else [])))
            elif node.module:
                modules.add(node.module)
    return modules


def _violations(root: Path, prefixes: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for path in _iter_python_files(root):
        for module in sorted(_imported_modules(path)):
            if any(module == p or module.startswith(p + ".") for p in prefixes):
                found.append(f"{path.relative_to(BACKEND_ROOT)} imports {module}")
    return found


def test_foundation_depends_on_nothing_but_config() -> None:
    violations = _violations(FOUNDATION, ("src.core.shared", "src.core.adapters", "src.pipeline"))
    assert not violations, "foundation/ must stay at the bottom of the core layering:\n" + "\n".join(violations)


def test_shared_does_not_reach_downstream_layers() -> None:
    violations = _violations(SHARED, ("src.core.adapters", "src.pipeline"))
    assert not violations, "shared/ may use foundation and read-only agent contracts:\n" + "\n".join(violations)


def test_adapters_stay_isolated() -> None:
    violations = _violations(ADAPTERS, ("src.core.shared.tools", "src.pipeline"))
    assert not violations, "adapters/ must not depend on tools or the pipeline:\n" + "\n".join(violations)


def test_core_has_no_agents_package() -> None:
    """Agent implementations live in src/pipeline/graph/agents, not in core."""
    assert not (CORE_ROOT / "agents").exists(), "core/ must not contain an agents package"


def test_core_root_modules_stay_dependency_free() -> None:
    """``config.py`` must not depend on a stratum."""
    root_modules = {path for path in _iter_python_files(CORE_ROOT) if path.parent == CORE_ROOT}
    found = [
        f"{path.name} imports {module}"
        for path in root_modules
        for module in sorted(_imported_modules(path))
        if module.startswith(("src.core.shared", "src.core.adapters", "src.pipeline"))
    ]
    assert not found, "core root modules must not depend on a stratum:\n" + "\n".join(found)
