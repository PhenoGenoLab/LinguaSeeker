"""Inventory the pipeline migration scope and its inbound imports.

Status: historical (2026-11-19).  The migration this script measures was
superseded: ``tools`` / ``mcp`` / ``contracts`` now live under ``src/core``
(``shared/tools``, ``adapters/mcp``, ``shared/contracts``) and the core
packages are named after agents rather than phases.  The ``LAYER_SPECS`` table
below still describes the 2026-11-17 plan on purpose, so the numbers it prints
are a record of that plan, not of the current tree.  Current layout:
``src/core/README.md``, enforced by ``tests/core/test_layer_boundaries.py``.

The original purpose: the migration plan
(``docs/planned/2026-11-17-pipeline-agentscope-reme-migration.md``) required a
fresh inventory at the start and end of every stage.  This script walks the
backend tree with the standard library only and reports, per target layer:

* legacy-path files/lines and how many of them are transitional shims;
* target-path files/lines (empty until that layer is migrated);
* inbound import statements from ``src``, ``tests``, ``scripts`` and ``app``.

Usage (from ``backend/``)::

    .venv/bin/python scripts/pipeline_migration_inventory.py
    .venv/bin/python scripts/pipeline_migration_inventory.py --format json
"""

from __future__ import annotations

import argparse
import ast
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SCAN_ROOTS = ("src", "tests", "scripts", "app")
SHIM_MARKER = "Transitional re-export shim"


@dataclass(frozen=True)
class LayerSpec:
    """One migration target from section 3.2.3 of the migration plan."""

    key: str
    label: str
    target: str
    legacy_paths: tuple[str, ...]
    target_paths: tuple[str, ...]
    module_prefixes: tuple[str, ...]


@dataclass
class PathStats:
    """File and line counts for a set of paths."""

    files: int = 0
    lines: int = 0
    shim_files: int = 0


@dataclass
class LayerInventory:
    """Inventory of one migration target."""

    key: str
    label: str
    target: str
    legacy: PathStats
    migrated: PathStats
    inbound_src: int = 0
    inbound_tests: int = 0
    inbound_scripts: int = 0
    inbound_app: int = 0
    inbound_files: int = 0

    @property
    def inbound_total(self) -> int:
        return self.inbound_src + self.inbound_tests + self.inbound_scripts + self.inbound_app


@dataclass
class Inventory:
    """Full migration inventory."""

    commit: str
    generated_at: str
    layers: list[LayerInventory]
    pipeline_files: int
    pipeline_lines: int
    shim_files: int


LAYER_SPECS: tuple[LayerSpec, ...] = (
    LayerSpec(
        key="graph",
        label="orchestrator + phase adapters",
        target="src/pipeline/graph",
        legacy_paths=(
            "src/agents/orchestrator.py",
            "src/agents/phase_1_adapter.py",
            "src/agents/phase_2_adapter.py",
            "src/agents/phase_3_adapter.py",
            "src/agents/phase_4_adapter.py",
        ),
        target_paths=("src/pipeline/graph",),
        module_prefixes=(
            "src.agents.orchestrator",
            "src.agents.phase_1_adapter",
            "src.agents.phase_2_adapter",
            "src.agents.phase_3_adapter",
            "src.agents.phase_4_adapter",
            "src.pipeline.graph",
        ),
    ),
    LayerSpec(
        key="fact_chain",
        label="source fact chain",
        target="src/pipeline/tools/fact_chain + skills/fact_chain",
        legacy_paths=("src/core/source_fact_chain",),
        target_paths=("src/pipeline/tools/fact_chain", "src/pipeline/skills/fact_chain"),
        module_prefixes=(
            "src.core.source_fact_chain",
            "src.pipeline.tools.fact_chain",
            "src.pipeline.skills.fact_chain",
        ),
    ),
    LayerSpec(
        key="acquisition",
        label="document acquisition",
        target="src/pipeline/tools/acquisition",
        legacy_paths=("src/core/ingest_and_digitize_data/document_acquisition",),
        target_paths=("src/pipeline/tools/acquisition",),
        module_prefixes=(
            "src.core.agents.acquisition",
            "src.pipeline.tools.acquisition",
        ),
    ),
    LayerSpec(
        key="parsing",
        label="document parsing",
        target="src/pipeline/tools/parsing",
        legacy_paths=("src/core/ingest_and_digitize_data/parse_document",),
        target_paths=("src/pipeline/tools/parsing",),
        module_prefixes=(
            "src.core.agents.parsing",
            "src.pipeline.tools.parsing",
        ),
    ),
    LayerSpec(
        key="terminology",
        label="entity standardization",
        target="src/pipeline/tools/terminology + src/core/terminology_shared",
        legacy_paths=("src/core/standardize_entities_and_align_knowledge",),
        target_paths=("src/pipeline/tools/terminology", "src/core/terminology_shared"),
        module_prefixes=(
            "src.core.standardize_entities_and_align_knowledge",
            "src.pipeline.tools.terminology",
            "src.core.terminology_shared",
        ),
    ),
)


def _python_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts and ".venv" not in path.parts)


def _relative(path: Path) -> str:
    return path.relative_to(BACKEND_ROOT).as_posix()


def _module_name(path: Path) -> str:
    relative = path.relative_to(BACKEND_ROOT).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _resolve_import(node: ast.AST, importer: Path) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []

    if node.level == 0:
        return [node.module] if node.module else []

    importer_parts = _module_name(importer).split(".")
    if importer.name != "__init__.py":
        importer_parts = importer_parts[:-1]
    keep = len(importer_parts) - (node.level - 1)
    base = importer_parts[:keep]
    if node.module:
        base.append(node.module)
    return [".".join(base)] if base else []


def _matches(module: str, prefix: str) -> bool:
    return module == prefix or module.startswith(prefix + ".")


def _path_stats(relative_paths: tuple[str, ...], marker: str) -> PathStats:
    stats = PathStats()
    seen: set[Path] = set()
    for relative in relative_paths:
        root = BACKEND_ROOT / relative
        files = [root] if root.is_file() else _python_files(root)
        for path in files:
            if path in seen:
                continue
            seen.add(path)
            stats.files += 1
            text = path.read_text(encoding="utf-8")
            stats.lines += len(text.splitlines())
            if marker in text:
                stats.shim_files += 1
    return stats


def _is_inside(path: Path, relative_roots: tuple[str, ...]) -> bool:
    relative = _relative(path)
    for root in relative_roots:
        if relative == root or relative.startswith(root + "/"):
            return True
    return False


def _collect_inbound(spec: LayerSpec, store: dict[str, int], files: set[str]) -> None:
    for scan_root in SCAN_ROOTS:
        for path in _python_files(BACKEND_ROOT / scan_root):
            relative = _relative(path)
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                if _is_inside(path, spec.legacy_paths + spec.target_paths):
                    continue
                modules = _resolve_import(node, path)
                if not any(_matches(module, prefix) for prefix in spec.module_prefixes for module in modules):
                    continue
                store[scan_root] = store.get(scan_root, 0) + 1
                files.add(relative)


def build_inventory() -> Inventory:
    """Build the migration inventory for the current working tree."""
    layers: list[LayerInventory] = []
    for spec in LAYER_SPECS:
        inbound_files: set[str] = set()
        inbound: dict[str, int] = {}
        _collect_inbound(spec, inbound, inbound_files)
        layers.append(
            LayerInventory(
                key=spec.key,
                label=spec.label,
                target=spec.target,
                legacy=_path_stats(spec.legacy_paths, SHIM_MARKER),
                migrated=_path_stats(spec.target_paths, SHIM_MARKER),
                inbound_src=inbound.get("src", 0),
                inbound_tests=inbound.get("tests", 0),
                inbound_scripts=inbound.get("scripts", 0),
                inbound_app=inbound.get("app", 0),
                inbound_files=len(inbound_files),
            )
        )

    pipeline = _path_stats(("src/pipeline",), SHIM_MARKER)
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(BACKEND_ROOT), "rev-parse", "--short", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "unknown"

    return Inventory(
        commit=commit,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        layers=layers,
        pipeline_files=pipeline.files,
        pipeline_lines=pipeline.lines,
        shim_files=sum(layer.legacy.shim_files for layer in layers),
    )


def _format_markdown(inventory: Inventory) -> str:
    lines = [
        "# Pipeline migration inventory",
        "",
        f"- commit: `{inventory.commit}`",
        f"- generated: `{inventory.generated_at}`",
        f"- `src/pipeline`: {inventory.pipeline_files} files / {inventory.pipeline_lines} lines",
        f"- transitional shims: {inventory.shim_files}",
        "",
        "| Layer | Target | Legacy files | Shims | Target files | Target lines | Inbound imports (src/tests/scripts/app) |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for layer in inventory.layers:
        lines.append(
            f"| `{layer.key}` | {layer.target} | {layer.legacy.files} | "
            f"{layer.legacy.shim_files} | {layer.migrated.files} | {layer.migrated.lines} | "
            f"{layer.inbound_src}/{layer.inbound_tests}/{layer.inbound_scripts}/{layer.inbound_app} |"
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    args = parser.parse_args()

    inventory = build_inventory()
    if args.format == "json":
        print(json.dumps(asdict(inventory), indent=2))
    else:
        print(_format_markdown(inventory), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
