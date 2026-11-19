"""Tests for the Phase 3 source-fact-chain adapter."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.agents.contracts import (
    ParseOutput,
    PhaseStatus,
    PhaseStatusDetail,
    PipelineGraphState,
    PipelineMode,
    SkipPhase4Reason,
    SourceType,
)
from src.pipeline.graph.phases.phase_3 import Phase3Adapter
from src.core.agents.extraction.contracts import (
    DualEvidenceExtractionResult,
    ExtractionTarget,
)
from src.pipeline.skills.fact_chain.service import SourceFactChainService
from src.pipeline.skills.runtime.llm import ProviderError

GENE_QUOTE = "先证者携带BRCA1变异。"
PHENOTYPE_QUOTE = "患者表现为严重肌张力低下。"


class StubProvider:
    def __init__(self, facts: list[dict[str, object]]) -> None:
        self.facts = facts
        self.calls: list[str] = []

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        self.calls.append(stage)
        data = json.loads(payload)
        if stage == "extract":
            window_text = str(data["window_text"])
            return json.dumps(
                {"facts": [fact for fact in self.facts if str(fact["quote"]) in window_text]},
                ensure_ascii=False,
            )
        if stage == "verify":
            return json.dumps(
                {
                    "verdicts": [
                        {"fact_id": item["fact_id"], "label": "supported", "reason": "in window"}
                        for item in data["items"]
                    ]
                }
            )
        if stage == "translate":
            return json.dumps(
                {
                    "translations": [
                        {"fact_id": item["fact_id"], "english_text": f"EN:{item['raw_value']}"}
                        for item in data["items"]
                    ]
                }
            )
        raise ProviderError(f"unexpected stage {stage}")


def sample_text() -> str:
    filler = "背景介绍，无临床事实。" * 8
    return f"{filler}{GENE_QUOTE} {filler}{PHENOTYPE_QUOTE} {filler}"


def sample_facts() -> list[dict[str, object]]:
    return [
        {
            "field_id": "A.gene_symbol",
            "raw_value": "BRCA1",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": GENE_QUOTE,
        },
        {
            "field_id": "B.clinical_phenotypes",
            "raw_value": "严重肌张力低下",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": PHENOTYPE_QUOTE,
        },
    ]


@pytest.fixture
def parsed_state(tmp_path: Path) -> PipelineGraphState:
    text = sample_text()
    metadata = {
        "pages": [{"page_number": 1, "markdown": text}],
        "content_blocks": [{"type": "text", "page_idx": 0, "text": text}],
    }
    metadata_path = tmp_path / "metadata.json"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
    md_path = tmp_path / "doc.md"
    md_path.write_text(text, encoding="utf-8")
    return PipelineGraphState(
        processing_run_id="run-1",
        source_document_id="doc-1",
        mode=PipelineMode.FULL,
        source_type=SourceType.LOCAL,
        phase_2_output=ParseOutput(
            md_path=str(md_path),
            metadata_path=str(metadata_path),
            output_dir=str(tmp_path),
            images_dir=None,
        ),
        extraction_target=ExtractionTarget(gene_symbol="BRCA1", disease_name="breast cancer"),
    )


def build_adapter(
    tmp_path: Path,
    facts: list[dict[str, object]],
    *,
    window_chars: int = 300,
    window_overlap: int = 60,
) -> tuple[Phase3Adapter, StubProvider]:
    provider = StubProvider(facts)
    cfg = SimpleNamespace(
        llm=SimpleNamespace(model="fast-model"),
        reasoning=SimpleNamespace(model="reasoning-model"),
    )
    service = SourceFactChainService(
        cfg,
        provider=provider,
        window_chars=window_chars,
        window_overlap=window_overlap,
    )
    return Phase3Adapter(service, output_root=tmp_path / "runs"), provider


@pytest.mark.asyncio
async def test_adapter_runs_chain_and_persists_bilingual_artifacts(
    parsed_state: PipelineGraphState,
    tmp_path: Path,
) -> None:
    adapter, provider = build_adapter(tmp_path, sample_facts())

    state = await adapter.run(parsed_state)

    assert state.phase_3_status.status == PhaseStatus.COMPLETED
    output = state.phase_3_output
    assert output is not None
    assert output.source_language == "zh"
    assert output.translated_text is None
    assert output.original_text == sample_text()
    assert output.original_blocks
    assert output.bilingual_rows_path and Path(output.bilingual_rows_path).exists()
    assert output.source_facts_path and Path(output.source_facts_path).exists()
    assert output.chain_run_path and Path(output.chain_run_path).exists()

    extraction = DualEvidenceExtractionResult.model_validate_json(
        Path(output.extraction_result_path).read_text(encoding="utf-8")
    )
    assert {item.field_id for item in extraction.original_result.evidence_items} == {
        "A.gene_symbol",
        "B.clinical_phenotypes",
    }
    translated = {item.field_id: item.value for item in extraction.translated_result.evidence_items}
    assert translated["B.clinical_phenotypes"] == "EN:严重肌张力低下"

    assert state.phase_3_status.summary is not None
    assert state.phase_3_status.summary["route"] == "source_fact_chain"
    assert state.phase_3_status.summary["facts"] == 2
    assert state.phase_3_status.summary["supported_facts"] == 2
    assert state.skip_phase_4_reason is None
    assert provider.calls.count("translate") >= 1  # non-English source translates presented facts


@pytest.mark.asyncio
async def test_adapter_retry_reuses_persisted_chain_run(
    parsed_state: PipelineGraphState,
    tmp_path: Path,
) -> None:
    adapter, provider = build_adapter(tmp_path, sample_facts())
    state = await adapter.run(parsed_state)
    first_calls = len(provider.calls)

    state.phase_3_status = PhaseStatusDetail()
    state = await adapter.run(state)

    assert len(provider.calls) == first_calls
    assert state.phase_3_output is not None
    assert state.phase_3_status.summary is not None
    assert state.phase_3_status.summary["facts"] == 2


@pytest.mark.asyncio
async def test_adapter_marks_document_not_relevant_when_no_supported_fact(
    parsed_state: PipelineGraphState,
    tmp_path: Path,
) -> None:
    adapter, _ = build_adapter(tmp_path, [])

    state = await adapter.run(parsed_state)

    assert state.phase_3_status.status == PhaseStatus.COMPLETED
    assert state.skip_phase_4_reason == SkipPhase4Reason.NOT_RELEVANT
    assert state.phase_3_output is not None
    extraction = DualEvidenceExtractionResult.model_validate_json(
        Path(state.phase_3_output.extraction_result_path).read_text(encoding="utf-8")
    )
    assert extraction.original_result.evidence_items == []


@pytest.mark.asyncio
async def test_adapter_rebuilds_empty_persisted_run_and_clears_skip_reason(
    parsed_state: PipelineGraphState,
    tmp_path: Path,
) -> None:
    empty_adapter, _ = build_adapter(tmp_path, [])
    state = await empty_adapter.run(parsed_state)
    assert state.skip_phase_4_reason == SkipPhase4Reason.NOT_RELEVANT

    adapter, provider = build_adapter(tmp_path, sample_facts())
    state.phase_3_status = PhaseStatusDetail()
    state = await adapter.run(state)

    assert provider.calls  # an empty run is never reused
    assert state.phase_3_status.summary is not None
    assert state.phase_3_status.summary["supported_facts"] == 2
    assert state.skip_phase_4_reason is None


@pytest.mark.asyncio
async def test_adapter_rebuilds_when_chain_config_changes(
    parsed_state: PipelineGraphState,
    tmp_path: Path,
) -> None:
    first_adapter, _ = build_adapter(tmp_path, sample_facts(), window_chars=300)
    state = await first_adapter.run(parsed_state)

    adapter, provider = build_adapter(tmp_path, sample_facts(), window_chars=400)
    state.phase_3_status = PhaseStatusDetail()
    state = await adapter.run(state)

    assert provider.calls
    assert state.phase_3_status.summary is not None
    assert state.phase_3_status.summary["supported_facts"] == 2


@pytest.mark.asyncio
async def test_adapter_rebuilds_when_source_changes(
    parsed_state: PipelineGraphState,
    tmp_path: Path,
) -> None:
    adapter, _ = build_adapter(tmp_path, sample_facts())
    state = await adapter.run(parsed_state)

    new_text = "背景介绍。先证者携带TP53变异。"
    new_fact = {
        "field_id": "A.gene_symbol",
        "raw_value": "TP53",
        "polarity": "positive",
        "subject_status": "unknown",
        "subject_id": None,
        "quote": "先证者携带TP53变异。",
    }
    assert state.phase_2_output is not None
    Path(state.phase_2_output.metadata_path).write_text(
        json.dumps({"pages": [{"page_number": 1, "markdown": new_text}], "content_blocks": []}),
        encoding="utf-8",
    )
    Path(state.phase_2_output.md_path).write_text(new_text, encoding="utf-8")

    adapter, provider = build_adapter(tmp_path, [new_fact])
    state.phase_3_status = PhaseStatusDetail()
    state = await adapter.run(state)

    assert provider.calls
    extraction = DualEvidenceExtractionResult.model_validate_json(
        Path(state.phase_3_output.extraction_result_path).read_text(encoding="utf-8")
    )
    assert [item.value for item in extraction.original_result.evidence_items] == ["TP53"]


@pytest.mark.asyncio
async def test_adapter_regenerates_jsonl_artifacts_on_reuse(
    parsed_state: PipelineGraphState,
    tmp_path: Path,
) -> None:
    adapter, provider = build_adapter(tmp_path, sample_facts())
    state = await adapter.run(parsed_state)
    assert state.phase_3_output is not None
    artifacts = [
        Path(state.phase_3_output.source_facts_path),
        Path(state.phase_3_output.bilingual_rows_path),
    ]
    for artifact in artifacts:
        artifact.unlink()
    first_calls = len(provider.calls)

    state.phase_3_status = PhaseStatusDetail()
    state = await adapter.run(state)

    assert len(provider.calls) == first_calls  # persisted run reused
    assert all(artifact.exists() and artifact.read_text(encoding="utf-8").strip() for artifact in artifacts)


@pytest.mark.asyncio
async def test_adapter_force_rebuild_reruns_provider(
    parsed_state: PipelineGraphState,
    tmp_path: Path,
) -> None:
    adapter, provider = build_adapter(tmp_path, sample_facts())
    state = await adapter.run(parsed_state)
    first_calls = len(provider.calls)

    state.phase_3_status = PhaseStatusDetail()
    state = await adapter.run(state, force_rebuild=True)

    assert len(provider.calls) > first_calls
    assert state.skip_phase_4_reason is None
