"""Stage routing between the legacy provider and AgentScope skills.

``legacy`` keeps the old path untouched.  ``agentscope`` replaces the stages
that have a registered skill and leaves the rest on the legacy provider.
``shadow`` calls both paths, returns the legacy reply and records differences,
so the production output stays byte-identical while the agent is evaluated.
"""

from __future__ import annotations

from collections.abc import Mapping
import json

from loguru import logger
from pydantic import BaseModel

from src.pipeline.contracts.skill_io import SkillError
from src.pipeline.skills.fact_chain.agent_skill import StageInvoker
from src.pipeline.skills.runtime.llm import Provider, ProviderError
from src.pipeline.tools.fact_chain.contracts import canonical_json

_STAGE_FIELDS = {"extract": "facts", "verify": "verdicts", "translate": "translations"}


class ShadowStats(BaseModel):
    """Counters for one shadow-mode router."""

    calls: int = 0
    mismatches: int = 0
    agent_failures: int = 0


def compare_stage_replies(stage: str, legacy_text: str, agent_text: str) -> list[str]:
    """Return human-readable differences between two stage replies."""
    field = _STAGE_FIELDS.get(stage)
    if field is None:
        return [f"unknown stage: {stage}"]
    try:
        legacy = json.loads(legacy_text).get(field)
        agent = json.loads(agent_text).get(field)
    except (json.JSONDecodeError, AttributeError) as exc:
        return [f"unparsable reply: {exc}"]
    if not isinstance(legacy, list) or not isinstance(agent, list):
        return [f"{field} must be a list"]
    left = sorted(canonical_json(item) for item in legacy)
    right = sorted(canonical_json(item) for item in agent)
    if left == right:
        return []
    differences = [f"{field} count legacy={len(left)} agent={len(right)}"]
    only_legacy = [item for item in left if item not in right]
    only_agent = [item for item in right if item not in left]
    differences.extend(f"legacy_only: {item}" for item in only_legacy)
    differences.extend(f"agent_only: {item}" for item in only_agent)
    return differences


class StageRouterProvider:
    """Route registered stages to AgentScope; keep the rest on the legacy provider."""

    def __init__(self, *, legacy: Provider, skills: Mapping[str, StageInvoker], mode: str) -> None:
        if mode not in {"shadow", "agentscope"}:
            raise ValueError(f"unsupported agent runtime mode: {mode}")
        self._legacy = legacy
        self._skills = dict(skills)
        self._mode = mode
        self._stats = ShadowStats()

    @property
    def stats(self) -> ShadowStats:
        return self._stats

    @property
    def stages(self) -> tuple[str, ...]:
        """Stage names handled by AgentScope skills."""
        return tuple(self._skills)

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        skill = self._skills.get(stage)
        if skill is None:
            return self._legacy.invoke(stage=stage, model_id=model_id, prompt=prompt, payload=payload)
        if self._mode == "agentscope":
            try:
                return skill.invoke(stage=stage, model_id=model_id, prompt=prompt, payload=payload)
            except SkillError as exc:
                # The runner retries ProviderError and records stage events; an
                # uncaught SkillError would abort the whole phase instead.
                raise ProviderError(f"{stage}: {exc}") from exc
        legacy_text = self._legacy.invoke(stage=stage, model_id=model_id, prompt=prompt, payload=payload)
        self._stats.calls += 1
        try:
            agent_text = skill.invoke(stage=stage, model_id=model_id, prompt=prompt, payload=payload)
        except (ProviderError, SkillError) as exc:
            self._stats.agent_failures += 1
            logger.warning("{} shadow agent failed, legacy reply kept: {}", stage, exc)
            return legacy_text
        differences = compare_stage_replies(stage, legacy_text, agent_text)
        if differences:
            self._stats.mismatches += 1
            logger.warning("{} shadow diff ({}): {}", stage, model_id, "; ".join(differences))
        else:
            logger.info("{} shadow match: model={}", stage, model_id)
        return legacy_text


__all__ = ["ShadowStats", "StageRouterProvider", "compare_stage_replies"]
