"""Cross-layer contracts for AgentScope-backed skills.

The runner talks to a skill through :class:`SkillRequest` and receives a
validated :class:`SkillResult`.  Payloads stay canonical JSON text: the same
bytes the legacy provider receives, so shadow comparisons are byte-exact.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SkillFailureKind(str, Enum):
    """How the runner should treat a failed skill call."""

    RETRYABLE = "retryable"
    PERMANENT = "permanent"


class SkillError(Exception):
    """A skill call failed with an explicit retry classification."""

    def __init__(self, message: str, *, kind: SkillFailureKind = SkillFailureKind.RETRYABLE) -> None:
        super().__init__(message)
        self.kind = kind


@dataclass(frozen=True)
class SkillRequest:
    """One stage call: stable prompt identity plus the canonical payload."""

    stage: str
    model_id: str
    window_id: str
    prompt: str
    payload: str


@dataclass(frozen=True)
class SkillResult:
    """Validated stage reply plus the cost telemetry of one skill call."""

    stage: str
    # The reply is external model JSON that the stage contract validates before
    # this point; a typed model per stage arrives when another stage moves to
    # AgentScope.
    data: dict[str, Any]
    provider_calls: int = 1
    latency_ms: float = 0.0


__all__ = [
    "SkillError",
    "SkillFailureKind",
    "SkillRequest",
    "SkillResult",
]
