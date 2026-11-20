"""Unit tests for the source fact chain (window -> extract -> verify -> English)."""

from __future__ import annotations

import json

import pytest

from src.core.shared.tools.fact_chain.contracts import (
    ChainConfig,
    ChainRun,
    SourceDocument,
    SourceHashMismatch,
    sha256_text,
)
from src.core.shared.tools.fact_chain.projection import project_dual_result
from src.core.shared.tools.fact_chain.windowing import chunk_document
from src.pipeline.skills.extraction.runner import BudgetExhausted, ChainRunner
from src.pipeline.skills.runtime.llm import ProviderError


def make_config(**overrides: object) -> ChainConfig:
    values: dict[str, object] = {
        "extract_model": "fast-model",
        "verify_model": "reasoning-model",
        "translate_model": "fast-model",
        "window_chars": 4000,
        "window_overlap": 200,
        "max_attempts": 2,
    }
    values.update(overrides)
    return ChainConfig(**values)  # type: ignore[arg-type]


def make_document(text: str, language: str = "zh") -> SourceDocument:
    return SourceDocument(
        document_id="doc-1",
        text=text,
        language=language,
        source_hash=sha256_text(text),
    )


class StubProvider:
    """Deterministic provider: extraction returns fixtures whose quote is in the window."""

    def __init__(
        self,
        facts: list[dict[str, object]],
        *,
        labels: dict[str, str] | None = None,
        fail_stage: str | None = None,
        english_prefix: str = "EN:",
        filter_quotes: bool = True,
    ) -> None:
        self.facts = facts
        self.labels = labels or {}
        self.fail_stage = fail_stage
        self.english_prefix = english_prefix
        self.filter_quotes = filter_quotes
        self.calls: list[str] = []

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        self.calls.append(stage)
        if self.fail_stage == stage:
            raise ProviderError(f"{stage} exploded")
        data = json.loads(payload)
        if stage == "extract":
            window_text = str(data["window_text"])
            found = (
                [fact for fact in self.facts if str(fact["quote"]) in window_text]
                if self.filter_quotes
                else list(self.facts)
            )
            return json.dumps({"facts": found}, ensure_ascii=False)
        if stage == "verify":
            verdicts = [
                {
                    "fact_id": item["fact_id"],
                    "label": self.labels.get(str(item["field_id"]), "supported"),
                    "reason": "checked against window",
                }
                for item in data["items"]
            ]
            return json.dumps({"verdicts": verdicts}, ensure_ascii=False)
        if stage == "translate":
            translations = [
                {"fact_id": item["fact_id"], "english_text": f"{self.english_prefix}{item['raw_value']}"}
                for item in data["items"]
            ]
            return json.dumps({"translations": translations}, ensure_ascii=False)
        raise AssertionError(f"unexpected stage {stage}")


GENE_QUOTE = "The proband carried a BRCA1 variant."
PHENOTYPE_QUOTE = "The patient had severe hypotonia."


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
            "raw_value": "severe hypotonia",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": PHENOTYPE_QUOTE,
        },
    ]


def sample_text() -> str:
    filler = "Background prose without clinical facts. " * 5
    return f"{filler}{GENE_QUOTE} {filler}{PHENOTYPE_QUOTE} {filler}"


def run_chain(
    *,
    text: str | None = None,
    language: str = "zh",
    config: ChainConfig | None = None,
    provider: StubProvider | None = None,
) -> ChainRun:
    source = text if text is not None else sample_text()
    return ChainRunner(provider or StubProvider(sample_facts()), config or make_config()).run(
        make_document(source, language)
    )


def test_windowing_covers_every_character_with_boundary_overlap() -> None:
    text = "".join(f"line-{index}\n" for index in range(400))
    windows = list(chunk_document(text, max_window_length=120, overlap=20))

    assert windows[0].start_offset == 0
    assert windows[-1].end_offset == len(text)
    assert all(window.length > 0 for window in windows)
    covered: set[int] = set()
    for window in windows:
        covered.update(range(window.start_offset, window.end_offset))
    assert covered == set(range(len(text)))
    assert any(right.start_offset < left.end_offset for left, right in zip(windows, windows[1:]))


def test_windowing_rejects_invalid_parameters() -> None:
    with pytest.raises(ValueError):
        list(chunk_document("abc", max_window_length=0))
    with pytest.raises(ValueError):
        list(chunk_document("abc", max_window_length=10, overlap=10))
    assert list(chunk_document("", max_window_length=10, overlap=1)) == []


def test_chain_runs_stages_in_order_and_deduplicates_overlap() -> None:
    provider = StubProvider(sample_facts())
    run = run_chain(config=make_config(window_chars=300, window_overlap=60), provider=provider)

    stages = [stage.value for stage in (record.stage for record in run.stage_progress)]
    assert set(stages) == {"extract", "verify", "translate"}
    assert provider.calls[: len(run.windows)] == ["extract"] * len(run.windows)
    first_verify = provider.calls.index("verify") if "verify" in provider.calls else -1
    assert first_verify >= len(run.windows)
    assert len(run.facts) == 2  # one gene + one phenotype fact despite overlap
    assert {fact.field_id for fact in run.facts} == {"A.gene_symbol", "B.clinical_phenotypes"}
    assert {item.label.value for item in run.verifications} == {"supported"}
    english = {view.field_id: view for view in run.english}
    assert english["A.gene_symbol"].status.value == "preserved"
    assert english["B.clinical_phenotypes"].status.value == "translated"
    assert english["B.clinical_phenotypes"].english_text == "EN:severe hypotonia"
    rows = run.bilingual_rows()
    assert len(rows) == 2
    assert all(row.verification is not None for row in rows)
    assert run.provider_calls == len(provider.calls)


def test_extraction_rejects_quote_value_and_atomicity_violations() -> None:
    text = "BRCA1 appears twice here: BRCA1."
    facts = [
        {
            "field_id": "A.gene_symbol",
            "raw_value": "BRCA1",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": "BRCA1",
        },
        {
            "field_id": "B.clinical_phenotypes",
            "raw_value": "hypotonia; seizures",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": text,
        },
        {
            "field_id": "A.gene_symbol",
            "raw_value": "TP53",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": "TP53 is absent from this window.",
        },
    ]
    run = run_chain(
        text=text,
        config=make_config(window_chars=4000),
        provider=StubProvider(facts, filter_quotes=False),
    )

    assert run.facts == []
    reasons = {rejection.reason for rejection in run.rejections}
    assert {"quote_ambiguous", "non_atomic_value", "quote_not_in_source"} <= reasons


def test_unknown_subject_cannot_carry_an_identifier() -> None:
    fact = dict(sample_facts()[0])
    fact.update({"subject_status": "unknown", "subject_id": "patient_1"})
    run = run_chain(provider=StubProvider([fact]))
    assert run.facts == []
    assert run.rejections[0].reason == "subject_unknown_with_id"


def test_english_source_uses_passthrough_without_translation_call() -> None:
    provider = StubProvider([sample_facts()[1]])
    run = run_chain(text=PHENOTYPE_QUOTE, language="en", provider=provider)

    assert "translate" not in provider.calls
    view = run.english[0]
    assert view.status.value == "passthrough"
    assert view.english_text == "severe hypotonia"


def test_verification_failure_marks_every_fact_unverified() -> None:
    provider = StubProvider([sample_facts()[0]], fail_stage="verify")
    run = run_chain(text=GENE_QUOTE, provider=provider)

    assert len(run.facts) == 1
    assert run.verifications[0].label.value == "unverified"
    assert run.provider_calls == 3  # extract once, verify twice (first attempt failed)
    assert project_dual_result(run).original_result.evidence_items == []


def test_extraction_failure_stops_without_facts() -> None:
    provider = StubProvider(sample_facts(), fail_stage="extract")
    run = run_chain(text=GENE_QUOTE, provider=provider)

    assert run.facts == []
    extract_records = [record for record in run.stage_progress if record.stage.value == "extract"]
    assert [record.outcome.value for record in extract_records] == ["failure"]
    assert run.provider_calls == 2


def test_source_hash_mismatch_is_rejected_before_any_call() -> None:
    provider = StubProvider(sample_facts())
    document = SourceDocument(
        document_id="doc-1",
        text=GENE_QUOTE,
        language="zh",
        source_hash=sha256_text("different text"),
    )
    with pytest.raises(SourceHashMismatch):
        ChainRunner(provider, make_config()).run(document)
    assert provider.calls == []


def test_projection_keeps_original_and_fact_english_tracks_separate() -> None:
    run = run_chain()
    result = project_dual_result(
        run,
        target_gene="BRCA1",
        target_disease="breast cancer",
        target_variant="c.68_69del",
    )

    assert result.original_result.evidence_items
    original = {item.field_id: item.value for item in result.original_result.evidence_items}
    translated = {item.field_id: item.value for item in result.translated_result.evidence_items}
    assert original["A.gene_symbol"] == "BRCA1"
    assert original["B.clinical_phenotypes"] == "severe hypotonia"
    assert translated["A.gene_symbol"] == "BRCA1"  # preserved field
    assert translated["B.clinical_phenotypes"] == "EN:severe hypotonia"
    assert result.original_result.evidence_chains[0].gene_text == "BRCA1"
    assert result.original_result.evidence_chains[0].disease_text == "breast cancer"
    assert all("gene=BRCA1" in item.group_id for item in result.original_result.evidence_items)


def test_projection_drops_unsupported_facts() -> None:
    provider = StubProvider(sample_facts(), labels={"B.clinical_phenotypes": "unsupported"})
    run = run_chain(provider=provider)
    result = project_dual_result(run)

    assert [item.field_id for item in result.original_result.evidence_items] == ["A.gene_symbol"]


def test_projection_feeds_phase_four_standardization_input() -> None:
    from src.core.agents.standardization.adapters import DualResultAdapter
    from src.core.agents.standardization.contracts import EntityType

    run = run_chain()
    result = project_dual_result(run, target_gene="BRCA1", target_disease="breast cancer")
    payload = DualResultAdapter().to_standardization_input(
        result,
        source_document_id="source-doc",
        processing_run_id="run-1",
    )

    gene_candidates = [c for c in payload.candidates if c.entity_type is EntityType.GENE]
    assert [c.raw_text for c in gene_candidates] == ["BRCA1"]
    assert payload.extraction_target is None  # projection does not invent a target
    values = {str(item.value) for item in payload.evidence_items}
    assert "severe hypotonia" in values
    assert "EN:severe hypotonia" in values
    phenotype_facts = [item for item in payload.evidence_items if item.field_id == "B.clinical_phenotypes"]
    assert len(phenotype_facts) == 2  # original and fact-English tracks


def multi_gene_facts() -> tuple[str, list[dict[str, object]]]:
    text = (
        "The proband carried a BRCA1 variant. "
        "The BRCA1 change was c.1A>G in the proband. "
        "Another patient carried a TP53 variant. "
        "The TP53 change was c.2C>T in that patient."
    )
    facts = [
        {
            "field_id": "A.gene_symbol",
            "raw_value": "BRCA1",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": "The proband carried a BRCA1 variant.",
        },
        {
            "field_id": "A.variant_hgvs_c",
            "raw_value": "c.1A>G",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": "The BRCA1 change was c.1A>G in the proband.",
        },
        {
            "field_id": "A.gene_symbol",
            "raw_value": "TP53",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": "Another patient carried a TP53 variant.",
        },
        {
            "field_id": "A.variant_hgvs_c",
            "raw_value": "c.2C>T",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": "The TP53 change was c.2C>T in that patient.",
        },
    ]
    return text, facts


def test_projection_keeps_each_gene_with_its_own_variant() -> None:
    text, facts = multi_gene_facts()
    run = run_chain(text=text, provider=StubProvider(facts))
    result = project_dual_result(run)

    by_fact = {(item.field_id, item.value): item for item in result.original_result.evidence_items}
    assert by_fact[("A.gene_symbol", "BRCA1")].group_id == "gene=BRCA1|variant=c.1A>G"
    assert by_fact[("A.variant_hgvs_c", "c.1A>G")].group_id == "gene=BRCA1|variant=c.1A>G"
    assert by_fact[("A.gene_symbol", "TP53")].group_id == "gene=TP53|variant=c.2C>T"
    assert by_fact[("A.variant_hgvs_c", "c.2C>T")].group_id == "gene=TP53|variant=c.2C>T"
    chains = result.original_result.evidence_chains
    assert {(chain.gene_text, chain.variant_text) for chain in chains} == {
        ("BRCA1", "c.1A>G"),
        ("TP53", "c.2C>T"),
    }


def test_projection_target_guard_keeps_off_target_facts_out_of_phase_four() -> None:
    from src.core.agents.standardization.adapters import DualResultAdapter
    from src.core.agents.standardization.contracts import EntityType

    text, facts = multi_gene_facts()
    run = run_chain(text=text, provider=StubProvider(facts))
    result = project_dual_result(run, target_gene="TP53")

    target_chain_values = {item.value for item in result.original_result.evidence_items if item.status == "found"}
    assert target_chain_values == {"TP53", "c.2C>T"}
    off_target = [item for item in result.original_result.evidence_items if item.status == "context_contamination"]
    assert {item.value for item in off_target} == {"BRCA1", "c.1A>G"}
    assert all("target_guard:off_target_gene=BRCA1" in item.notes for item in off_target)

    payload = DualResultAdapter().to_standardization_input(
        result,
        source_document_id="source-doc",
        processing_run_id="run-1",
    )
    genes = [c.raw_text for c in payload.candidates if c.entity_type is EntityType.GENE]
    assert genes == ["TP53"]


def test_projection_marks_document_not_relevant_when_target_gene_is_absent() -> None:
    run = run_chain()
    result = project_dual_result(run, target_gene="TP53")

    assert result.original_result.status.value == "not_relevant"
    assert result.original_result.evidence_chains == []
    assert all(item.status.value == "context_contamination" for item in result.original_result.evidence_items)


def test_quote_and_value_with_html_entities_are_accepted() -> None:
    text = "The proband carried c.1A&gt;G and had severe hypotonia &amp; feeding difficulty."
    facts = [
        {
            "field_id": "A.variant_hgvs_c",
            "raw_value": "c.1A&gt;G",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": "The proband carried c.1A&gt;G",
        },
        {
            "field_id": "B.clinical_phenotypes",
            "raw_value": "severe hypotonia &amp; feeding difficulty",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": "had severe hypotonia &amp; feeding difficulty",
        },
    ]
    run = run_chain(text=text, language="en", provider=StubProvider(facts))

    assert run.rejections == []
    assert {fact.raw_value for fact in run.facts} == {
        "c.1A&gt;G",
        "severe hypotonia &amp; feeding difficulty",
    }
    assert {text[fact.span_start : fact.span_end] for fact in run.facts} == {
        "The proband carried c.1A&gt;G",
        "had severe hypotonia &amp; feeding difficulty",
    }


def test_quote_ambiguity_uses_whitespace_normalized_matches() -> None:
    text = "The patient had severe  hypotonia. Later, severe hypotonia."
    facts = [
        {
            "field_id": "B.clinical_phenotypes",
            "raw_value": "hypotonia",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": "severe hypotonia",
        }
    ]
    run = run_chain(text=text, language="en", provider=StubProvider(facts))

    assert run.facts == []
    assert run.rejections[0].reason == "quote_ambiguous"


def test_non_atomic_value_cannot_hide_entity_semicolons() -> None:
    text = "The patient had hypotonia&#59; seizures."
    facts = [
        {
            "field_id": "B.clinical_phenotypes",
            "raw_value": "hypotonia&#59; seizures",
            "polarity": "positive",
            "subject_status": "unknown",
            "subject_id": None,
            "quote": text,
        }
    ]
    run = run_chain(text=text, language="en", provider=StubProvider(facts))

    assert run.facts == []
    assert run.rejections[0].reason == "non_atomic_value"


def test_candidate_rejections_name_each_contract() -> None:
    from src.core.shared.tools.fact_chain.contracts import ChainContractError, DocumentWindow
    from src.core.shared.tools.fact_chain.core import candidate_to_fact

    text = "The patient had severe hypotonia."
    document = make_document(text, language="en")
    window = DocumentWindow(window_id=0, text=text, start_offset=0, end_offset=len(text))
    valid = {
        "field_id": "B.clinical_phenotypes",
        "raw_value": "severe hypotonia",
        "polarity": "positive",
        "subject_status": "unknown",
        "subject_id": None,
        "quote": text,
    }

    def reject(overrides: dict[str, object], reason: str) -> None:
        candidate = {**valid, **overrides}
        with pytest.raises(ChainContractError) as error:
            candidate_to_fact(candidate, document=document, window=window)
        assert error.value.reason == reason

    with pytest.raises(ChainContractError) as error:
        candidate_to_fact("not-an-object", document=document, window=window)
    assert error.value.reason == "candidate_not_object"

    with pytest.raises(ChainContractError) as error:
        candidate_to_fact({k: v for k, v in valid.items() if k != "quote"}, document=document, window=window)
    assert error.value.reason == "candidate_missing_key"

    reject({"field_id": "Z.unknown"}, "unknown_field")
    reject({"raw_value": "   "}, "empty_value")
    reject({"quote": "  "}, "quote_missing")
    reject({"raw_value": "hypotonia; seizures"}, "non_atomic_value")
    reject({"raw_value": "absent phenotype"}, "value_not_in_quote")
    reject({"polarity": "maybe"}, "invalid_polarity")
    reject({"subject_status": "other"}, "invalid_subject_status")
    reject({"subject_id": "patient_1"}, "subject_unknown_with_id")
    reject({"subject_status": "known", "subject_id": None}, "subject_known_without_id")
    reject({"quote": "The patient had severe hypotonia. Extra claim."}, "quote_not_in_source")

    mismatched = SourceDocument(
        document_id="doc-1",
        text="XXXX",
        language="en",
        source_hash=sha256_text("XXXX"),
    )
    with pytest.raises(ChainContractError) as error:
        candidate_to_fact(valid, document=mismatched, window=window)
    assert error.value.reason == "span_quote_mismatch"


def test_budget_exhaustion_stops_before_the_next_provider_call() -> None:
    text = sample_text()
    provider = StubProvider(sample_facts())
    runner = ChainRunner(provider, make_config(window_chars=120, window_overlap=20, max_provider_calls=1))
    with pytest.raises(BudgetExhausted):
        runner.run(make_document(text))
    assert len(provider.calls) == 1


def test_langchain_provider_routes_tiers_and_rejects_empty_replies(monkeypatch: pytest.MonkeyPatch) -> None:
    from types import SimpleNamespace

    from src.pipeline.skills.runtime import llm as provider_module

    created: list[dict[str, object]] = []

    class FakeClient:
        def __init__(self, content: object) -> None:
            self.content = content

        def invoke(self, messages: object) -> object:
            return SimpleNamespace(content=self.content)

    def fake_create(**kwargs: object) -> FakeClient:
        created.append(kwargs)
        return FakeClient("ok")

    monkeypatch.setattr(provider_module, "create_llm_client", fake_create)
    cfg = SimpleNamespace(
        llm=SimpleNamespace(model="fast-model", base_url="http://fast", all_api_keys=["k1"], max_tokens=128, timeout=5),
        reasoning=SimpleNamespace(
            model="reasoning-model",
            base_url="http://reasoning",
            all_api_keys=["k2"],
            max_tokens=256,
            timeout=10,
            reasoning_effort="high",
        ),
    )
    provider = provider_module.ChatModelProvider(cfg)

    assert provider.invoke(stage="extract", model_id="fast-model", prompt="p", payload="{}") == "ok"
    assert provider.invoke(stage="verify", model_id="reasoning-model", prompt="p", payload="{}") == "ok"
    assert [entry["model"] for entry in created] == ["fast-model", "reasoning-model"]
    assert created[1]["model_kwargs"] == {"reasoning_effort": "high"}

    provider._clients["fast"] = FakeClient("")
    with pytest.raises(ProviderError):
        provider.invoke(stage="extract", model_id="fast-model", prompt="p", payload="{}")

    class BrokenClient:
        def invoke(self, messages: object) -> object:
            raise RuntimeError("transport down")

    provider._clients["fast"] = BrokenClient()
    with pytest.raises(ProviderError):
        provider.invoke(stage="extract", model_id="fast-model", prompt="p", payload="{}")

    provider._clients["fast"] = FakeClient([{"text": "part1"}, "part2"])
    assert provider.invoke(stage="extract", model_id="fast-model", prompt="p", payload="{}") == "part1part2"
