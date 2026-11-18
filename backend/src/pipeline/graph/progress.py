"""Node-level progress for the pipeline state graph.

Progress is additive: each phase keeps its existing status fields and gains a
``summary["nodes"]`` list that the status API already returns.  Consumers that
ignore the key keep working unchanged.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime

from src.agents.contracts import PhaseStatusDetail


@dataclass(frozen=True)
class NodeProgress:
    """Terminal record of one graph node execution."""

    node: str
    status: str
    started_at: str | None = None
    completed_at: str | None = None
    duration_seconds: float | None = None
    detail: str = ""

    def as_dict(self) -> dict[str, object]:
        return asdict(self)

    @classmethod
    def from_status(cls, node: str, status: PhaseStatusDetail, *, detail: str = "") -> NodeProgress:
        """Build a record from the phase status the adapter produced."""
        return cls(
            node=node,
            status=status.status.value,
            started_at=status.started_at,
            completed_at=status.completed_at,
            duration_seconds=status.duration_seconds,
            detail=detail,
        )

    @classmethod
    def failed(cls, node: str, *, started_at: str | None, detail: str) -> NodeProgress:
        completed_at = datetime.now().isoformat()
        duration = None
        if started_at:
            try:
                duration = (datetime.fromisoformat(completed_at) - datetime.fromisoformat(started_at)).total_seconds()
            except (TypeError, ValueError):
                # A malformed persisted timestamp must not mask the phase error.
                duration = None
        return cls(
            node=node,
            status="failed",
            started_at=started_at,
            completed_at=completed_at,
            duration_seconds=duration,
            detail=detail,
        )


def record_node(status: PhaseStatusDetail, entry: NodeProgress) -> None:
    """Append ``entry`` to ``status.summary["nodes"]`` without dropping other keys."""
    summary = dict(status.summary or {})
    nodes = list(summary.get("nodes") or [])
    nodes.append(entry.as_dict())
    summary["nodes"] = nodes
    status.summary = summary


__all__ = ["NodeProgress", "record_node"]
