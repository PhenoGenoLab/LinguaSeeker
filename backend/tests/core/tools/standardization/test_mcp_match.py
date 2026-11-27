"""Tests for FastHPOCR MCP phenotype matching."""

from __future__ import annotations

import pytest

from src.core.adapters.mcp.hpocr import HpoAnnotation
from src.core.tools.standardization.contracts import (
    BindingRole,
    EntityMatch,
    EntityType,
    MatchMethod,
    MatchStatus,
    StandardizationCandidate,
)
from src.core.tools.standardization.mcp_match.core import HpoMcpTerminologyMatcher


def _candidate(entity_type=EntityType.PHENOTYPE, raw_text="seizures") -> StandardizationCandidate:
    return StandardizationCandidate(
        candidate_id="c1",
        entity_type=entity_type,
        role=BindingRole.CONTEXT,
        raw_text=raw_text,
        chain_id="chain-1",
        track="original",
    )


def _annotation(uri="HP:0001250", label="Seizures", span="seizures") -> HpoAnnotation:
    return HpoAnnotation(hpo_uri=uri, hpo_label=label, start=0, end=len(span), text_span=span)


class FakeClient:
    def __init__(self, annotations=(), error=None):
        self.annotations = tuple(annotations)
        self.error = error

    async def annotate(self, text, *, longest_match=True):
        if self.error is not None:
            raise self.error
        return self.annotations


class FakeFallback:
    def __init__(self, match):
        self._match = match

    async def match(self, candidate):
        return self._match


@pytest.mark.asyncio
async def test_phenotype_maps_single_annotation() -> None:
    matcher = HpoMcpTerminologyMatcher(FakeClient([_annotation()]), FakeFallback(None))
    match = await matcher.match(_candidate())

    assert match.status == MatchStatus.STANDARDIZED
    assert match.external_id == "HP:0001250"
    assert match.display_name == "Seizures"
    assert match.match_method == MatchMethod.MCP


@pytest.mark.asyncio
async def test_phenotype_duplicate_uri_is_not_ambiguous() -> None:
    annotations = [_annotation(), _annotation(span="seizure")]
    matcher = HpoMcpTerminologyMatcher(FakeClient(annotations), FakeFallback(None))

    match = await matcher.match(_candidate(raw_text="seizures and seizure"))

    assert match.status == MatchStatus.STANDARDIZED
    assert match.external_id == "HP:0001250"


@pytest.mark.asyncio
async def test_phenotype_distinct_uris_are_ambiguous() -> None:
    annotations = [
        _annotation(),
        _annotation(uri="HP:0001252", label="Hypotonia", span="hypotonia"),
    ]
    matcher = HpoMcpTerminologyMatcher(FakeClient(annotations), FakeFallback(None))

    match = await matcher.match(_candidate(raw_text="seizures with hypotonia"))

    assert match.status == MatchStatus.AMBIGUOUS
    assert match.external_id is None


@pytest.mark.asyncio
async def test_phenotype_exact_span_wins_among_distinct_uris() -> None:
    annotations = [
        _annotation(uri="HP:9999999", label="Other", span="seizures with"),
        _annotation(uri="HP:0001250", label="Seizures", span="seizures"),
    ]
    matcher = HpoMcpTerminologyMatcher(FakeClient(annotations), FakeFallback(None))

    match = await matcher.match(_candidate(raw_text="seizures"))

    assert match.status == MatchStatus.STANDARDIZED
    assert match.external_id == "HP:0001250"


@pytest.mark.asyncio
async def test_phenotype_without_annotation_is_unmapped() -> None:
    matcher = HpoMcpTerminologyMatcher(FakeClient([]), FakeFallback(None))

    match = await matcher.match(_candidate())

    assert match.status == MatchStatus.UNMAPPED
    assert match.match_method == MatchMethod.MCP


@pytest.mark.asyncio
async def test_phenotype_service_failure_is_unmapped_without_local_fallback() -> None:
    fallback_match = EntityMatch(
        candidate=_candidate(),
        status=MatchStatus.STANDARDIZED,
        external_id="HP:local",
        display_name="Local",
    )
    matcher = HpoMcpTerminologyMatcher(FakeClient(error=RuntimeError("down")), FakeFallback(fallback_match))

    match = await matcher.match(_candidate())

    assert match.status == MatchStatus.UNMAPPED
    assert match.external_id is None


@pytest.mark.asyncio
async def test_non_phenotype_delegates_to_fallback() -> None:
    candidate = _candidate(entity_type=EntityType.GENE, raw_text="GLA")
    fallback_match = EntityMatch(
        candidate=candidate,
        status=MatchStatus.STANDARDIZED,
        external_id="HGNC:4296",
        display_name="GLA",
        match_method=MatchMethod.PRECISE,
    )
    client = FakeClient(error=RuntimeError("must not be called"))
    matcher = HpoMcpTerminologyMatcher(client, FakeFallback(fallback_match))

    match = await matcher.match(candidate)

    assert match.external_id == "HGNC:4296"
