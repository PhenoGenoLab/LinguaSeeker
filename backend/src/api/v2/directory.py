"""Directory scanning for v2 directory runs.

A run covers a whole directory: files are resolved relative to the configured
pipeline input root, matched against the request patterns, and capped before
anything is enqueued.
"""

from __future__ import annotations

import fnmatch
import os
from dataclasses import dataclass
from pathlib import Path

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_INPUT_ROOT = _BACKEND_ROOT / "data" / "pipeline" / "inputs"


@dataclass(frozen=True)
class ScannedFile:
    """One file selected by a directory run."""

    relative_path: str
    absolute_path: Path


def input_root() -> Path:
    """Return the allowed directory root (``PIPELINE_INPUT_ROOT`` or default)."""
    configured = os.environ.get("PIPELINE_INPUT_ROOT", "").strip()
    root = Path(configured).expanduser().resolve() if configured else _DEFAULT_INPUT_ROOT.resolve()
    return root


def resolve_directory(
    directory: str,
    *,
    recursive: bool,
    patterns: list[str],
    max_documents: int,
    root: Path | None = None,
) -> list[ScannedFile]:
    """Resolve *directory* under the input root and return matched files.

    Raises:
        ValueError: path escapes the root, is missing, is not a directory, or
            has no matching files.
        OverflowError: more matches than ``max_documents``.
    """
    base = (root or input_root()).resolve()
    target = (base / directory).resolve()
    if base != target and base not in target.parents:
        raise ValueError("directory escapes the pipeline input root")
    if not target.exists():
        raise ValueError(f"directory does not exist: {directory}")
    if not target.is_dir():
        raise ValueError(f"not a directory: {directory}")

    iterator = target.rglob("*") if recursive else target.glob("*")
    matches: list[ScannedFile] = []
    for path in sorted(iterator):
        if not path.is_file():
            continue
        if not any(fnmatch.fnmatch(path.name, pattern) for pattern in patterns):
            continue
        matches.append(
            ScannedFile(
                relative_path=path.relative_to(base).as_posix(),
                absolute_path=path,
            )
        )
        if len(matches) > max_documents:
            raise OverflowError(f"directory contains more than {max_documents} matching files")

    if not matches:
        raise ValueError(f"no files matching {patterns} in {directory}")
    return matches
