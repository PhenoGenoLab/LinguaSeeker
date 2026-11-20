"""Runtime mode routing shared by pipeline skills.

``pipeline.agent_runtime`` selects how a phase executes:

- ``legacy``    — call the deterministic core implementation (default).
- ``shadow``    — run both; return the legacy result and append a diff row.
- ``agentscope``— return the agent result.

The shadow report is the gate for ever flipping a phase to ``agentscope``: it
records a hash of both payloads plus equality, so an agent whose output drifts
shows up as ``equal=false`` instead of silently replacing the deterministic path.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Awaitable, Callable

DEFAULT_REPORT_PATH = "data/pipeline/shadow_report.json"


@dataclass(frozen=True)
class ShadowRow:
    """One legacy-vs-agent comparison."""

    phase: str
    legacy_hash: str
    agent_hash: str | None
    equal: bool
    agent_error: str | None = None


def agent_mode() -> str:
    """Return the configured runtime mode (``legacy`` when unset)."""
    from src.core.config import get_config

    return get_config().pipeline.agent_runtime


def report_path() -> Path:
    """Where shadow rows are appended. Overridable for tests."""
    return Path(os.environ.get("PIPELINE_SHADOW_REPORT", DEFAULT_REPORT_PATH))


def payload_hash(value: Any) -> str:
    """Stable short hash of a result payload, used for the diff row."""
    try:
        payload = json.dumps(value, sort_keys=True, default=str)
    except TypeError:
        payload = repr(value)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def record(row: ShadowRow) -> None:
    """Append one comparison row to the shadow report (creates the file)."""
    path = report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, Any] = {"rows": []}
    if path.is_file():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {"rows": []}
    existing.setdefault("rows", []).append(asdict(row))
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def _decide(phase: str, legacy_value: Any, agent_value: Any, agent_error: str | None, mode: str) -> Any:
    legacy_hash = payload_hash(legacy_value)
    if mode == "shadow":
        record(
            ShadowRow(
                phase=phase,
                legacy_hash=legacy_hash,
                agent_hash=None if agent_error else payload_hash(agent_value),
                equal=agent_error is None and payload_hash(agent_value) == legacy_hash,
                agent_error=agent_error,
            )
        )
        return legacy_value
    if mode == "agentscope":
        if agent_error is not None:
            raise RuntimeError(f"{phase}: agent path failed: {agent_error}")
        return agent_value
    return legacy_value


def run_phase_sync(
    phase: str,
    *,
    legacy: Callable[[], Any],
    agent: Callable[[], Any] | None = None,
) -> Any:
    """Run one phase in the configured mode (synchronous surfaces)."""
    mode = agent_mode()
    legacy_value = legacy()
    if mode == "legacy" or agent is None:
        return legacy_value
    try:
        agent_value, agent_error = agent(), None
    except Exception as exc:  # agent failures must not hide the legacy result
        agent_value, agent_error = None, f"{type(exc).__name__}: {exc}"
    return _decide(phase, legacy_value, agent_value, agent_error, mode)


async def run_phase_async(
    phase: str,
    *,
    legacy: Callable[[], Awaitable[Any]],
    agent: Callable[[], Awaitable[Any]] | None = None,
) -> Any:
    """Run one phase in the configured mode (async surfaces)."""
    mode = agent_mode()
    legacy_value = await legacy()
    if mode == "legacy" or agent is None:
        return legacy_value
    try:
        agent_value, agent_error = await agent(), None
    except Exception as exc:  # agent failures must not hide the legacy result
        agent_value, agent_error = None, f"{type(exc).__name__}: {exc}"
    return _decide(phase, legacy_value, agent_value, agent_error, mode)


__all__ = ["ShadowRow", "agent_mode", "payload_hash", "record", "report_path", "run_phase_async", "run_phase_sync"]
