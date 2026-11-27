"""Compare two source-fact-chain runs for shadow acceptance.

The comparison is the acceptance gate for the AgentScope runtime: facts must be
identical (id, fields, polarity, subject, span, window), verification labels and
reasons must match, and English views must carry the same status/text.  Cost is
reported separately and never fails the comparison by itself.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.core.shared.tools.fact_chain.contracts import ChainRun


class FactDifference(BaseModel):
    """One commonly-known fact whose stored fields differ."""

    fact_id: str
    fields: list[str]


class RuntimeDifference(BaseModel):
    """A configuration or prompt identity that differs between the runs."""

    field: str
    legacy: str
    agent: str


class ShadowReport(BaseModel):
    """Deterministic diff between a legacy run and an agent run."""

    identical: bool
    legacy_facts: int
    agent_facts: int
    facts_only_legacy: list[str] = Field(default_factory=list)
    facts_only_agent: list[str] = Field(default_factory=list)
    fact_field_diffs: list[FactDifference] = Field(default_factory=list)
    verification_diffs: list[str] = Field(default_factory=list)
    english_diffs: list[str] = Field(default_factory=list)
    config_diffs: list[RuntimeDifference] = Field(default_factory=list)
    prompt_version_diffs: list[RuntimeDifference] = Field(default_factory=list)
    legacy_provider_calls: int = 0
    agent_provider_calls: int = 0


def _verification_map(run: ChainRun) -> dict[str, str]:
    """Fact id -> ``label: reason`` for the first verification of each fact."""
    mapping: dict[str, str] = {}
    for verification in run.verifications:
        mapping.setdefault(verification.fact_id, f"{verification.label.value}: {verification.reason}")
    return mapping


def _english_map(run: ChainRun) -> dict[str, str]:
    """``fact_id/field_id/mode`` -> ``status: text`` for every English view."""
    mapping: dict[str, str] = {}
    for view in run.english:
        key = f"{view.fact_id}/{view.field_id}/{view.mode.value}"
        mapping.setdefault(key, f"{view.status.value}: {view.english_text or ''}")
    return mapping


def compare_chain_runs(legacy: ChainRun, agent: ChainRun) -> ShadowReport:
    """Build the acceptance diff; ``identical`` ignores only cost counters."""
    legacy_facts = {fact.fact_id: fact for fact in legacy.facts}
    agent_facts = {fact.fact_id: fact for fact in agent.facts}
    only_legacy = sorted(set(legacy_facts) - set(agent_facts))
    only_agent = sorted(set(agent_facts) - set(legacy_facts))

    field_diffs: list[FactDifference] = []
    for fact_id in sorted(set(legacy_facts) & set(agent_facts)):
        left = legacy_facts[fact_id].model_dump(mode="json", exclude={"fact_id"})
        right = agent_facts[fact_id].model_dump(mode="json", exclude={"fact_id"})
        changed = sorted(key for key in left if left[key] != right.get(key))
        if changed:
            field_diffs.append(FactDifference(fact_id=fact_id, fields=changed))

    legacy_verifications = _verification_map(legacy)
    agent_verifications = _verification_map(agent)
    verification_diffs: list[str] = []
    for fact_id in sorted(set(legacy_verifications) | set(agent_verifications)):
        left = legacy_verifications.get(fact_id, "missing")
        right = agent_verifications.get(fact_id, "missing")
        if left != right:
            verification_diffs.append(f"{fact_id}: legacy={left} agent={right}")

    legacy_english = _english_map(legacy)
    agent_english = _english_map(agent)
    english_diffs: list[str] = []
    for key in sorted(set(legacy_english) | set(agent_english)):
        left = legacy_english.get(key, "missing")
        right = agent_english.get(key, "missing")
        if left != right:
            english_diffs.append(f"{key}: legacy={left} agent={right}")

    legacy_config = legacy.config.model_dump(mode="json")
    agent_config = agent.config.model_dump(mode="json")
    config_diffs = [
        RuntimeDifference(field=key, legacy=str(legacy_config.get(key)), agent=str(agent_config.get(key)))
        for key in sorted(set(legacy_config) | set(agent_config))
        if legacy_config.get(key) != agent_config.get(key)
    ]

    legacy_prompts = legacy.prompt_versions.model_dump() if legacy.prompt_versions else {}
    agent_prompts = agent.prompt_versions.model_dump() if agent.prompt_versions else {}
    prompt_version_diffs = [
        RuntimeDifference(field=key, legacy=str(legacy_prompts.get(key)), agent=str(agent_prompts.get(key)))
        for key in sorted(set(legacy_prompts) | set(agent_prompts))
        if legacy_prompts.get(key) != agent_prompts.get(key)
    ]

    identical = not (
        only_legacy
        or only_agent
        or field_diffs
        or verification_diffs
        or english_diffs
        or config_diffs
        or prompt_version_diffs
    )
    return ShadowReport(
        identical=identical,
        legacy_facts=len(legacy_facts),
        agent_facts=len(agent_facts),
        facts_only_legacy=only_legacy,
        facts_only_agent=only_agent,
        fact_field_diffs=field_diffs,
        verification_diffs=verification_diffs,
        english_diffs=english_diffs,
        config_diffs=config_diffs,
        prompt_version_diffs=prompt_version_diffs,
        legacy_provider_calls=legacy.provider_calls,
        agent_provider_calls=agent.provider_calls,
    )


__all__ = ["FactDifference", "RuntimeDifference", "ShadowReport", "compare_chain_runs"]
