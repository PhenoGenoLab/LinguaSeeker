"""Tests for the shadow acceptance diff between legacy and agent chain runs."""

from __future__ import annotations

from src.pipeline.skills.extraction.shadow_diff import compare_chain_runs
from src.core.shared.tools.fact_chain.contracts import (
    ChainConfig,
    ChainRun,
    EnglishStatus,
    EnglishView,
    Polarity,
    PresentationMode,
    PromptVersions,
    Subject,
    SubjectStatus,
    SourceFact,
    Verification,
    VerificationLabel,
)

FACT_ID = "fact-1"
FIELD_ID = "B.clinical_phenotypes"


def _fact(raw_value: str = "severe hypotonia") -> SourceFact:
    return SourceFact(
        fact_id=FACT_ID,
        document_id="doc-1",
        source_hash="hash",
        field_id=FIELD_ID,
        raw_value=raw_value,
        polarity=Polarity.POSITIVE,
        subject=Subject(status=SubjectStatus.UNKNOWN),
        quote="severe hypotonia",
        span_start=0,
        span_end=16,
        window_id="w0",
    )


def _run(
    *,
    raw_value: str = "severe hypotonia",
    label: VerificationLabel = VerificationLabel.SUPPORTED,
    reason: str = "quote matches",
    english: str = "severe hypotonia",
    calls: int = 1,
    omit: bool = False,
    window_chars: int = 4000,
    extract_prompt: str | None = None,
) -> ChainRun:
    config = ChainConfig(
        extract_model="fast",
        verify_model="reasoning",
        translate_model="fast",
        window_chars=window_chars,
    )
    prompts = (
        PromptVersions(extract=extract_prompt, verify="verify:v1", translate="translate:v1", presentation="p:v1")
        if extract_prompt
        else None
    )
    facts = [] if omit else [_fact(raw_value)]
    verifications = [] if omit else [Verification(fact_id=FACT_ID, label=label, reason=reason)]
    english_views = (
        []
        if omit
        else [
            EnglishView(
                fact_id=FACT_ID,
                field_id=FIELD_ID,
                mode=PresentationMode.PRESENTED,
                status=EnglishStatus.TRANSLATED,
                english_text=english,
                polarity=Polarity.POSITIVE,
                subject=Subject(status=SubjectStatus.UNKNOWN),
                presentation_version="v1",
            )
        ]
    )
    return ChainRun(
        document_id="doc-1",
        source_hash="hash",
        language="zh",
        config=config,
        prompt_versions=prompts,
        facts=facts,
        verifications=verifications,
        english=english_views,
        provider_calls=calls,
    )


def test_identical_runs_pass_even_when_cost_differs() -> None:
    report = compare_chain_runs(_run(calls=2), _run(calls=5))

    assert report.identical
    assert report.legacy_provider_calls == 2
    assert report.agent_provider_calls == 5


def test_missing_fact_is_reported() -> None:
    report = compare_chain_runs(_run(), _run(omit=True))

    assert not report.identical
    assert report.facts_only_legacy == [FACT_ID]


def test_field_change_is_reported_by_name() -> None:
    report = compare_chain_runs(_run(), _run(raw_value="hypotonia"))

    assert not report.identical
    assert report.fact_field_diffs[0].fact_id == FACT_ID
    assert report.fact_field_diffs[0].fields == ["raw_value"]


def test_verification_label_and_reason_changes_are_reported() -> None:
    label_report = compare_chain_runs(_run(), _run(label=VerificationLabel.UNVERIFIED))
    reason_report = compare_chain_runs(_run(), _run(reason="different reason"))

    assert label_report.identical is False
    assert label_report.verification_diffs
    assert reason_report.identical is False
    assert reason_report.verification_diffs


def test_config_change_fails_the_comparison() -> None:
    report = compare_chain_runs(_run(), _run(window_chars=2000))

    assert not report.identical
    assert report.config_diffs[0].field == "window_chars"


def test_prompt_version_change_fails_the_comparison() -> None:
    report = compare_chain_runs(_run(extract_prompt="extract:v1"), _run(extract_prompt="extract:v2"))

    assert not report.identical
    assert report.prompt_version_diffs[0].field == "extract"


def test_missing_prompt_versions_are_reported() -> None:
    report = compare_chain_runs(_run(), _run(extract_prompt="extract:v1"))

    assert not report.identical
    assert {diff.field for diff in report.prompt_version_diffs} == {"extract", "presentation", "translate", "verify"}


def test_english_text_change_is_reported() -> None:
    report = compare_chain_runs(_run(), _run(english="severe low muscle tone"))

    assert not report.identical
    assert report.english_diffs
    assert report.english_diffs[0].startswith(f"{FACT_ID}/{FIELD_ID}/presented")


def test_cli_exit_codes(tmp_path) -> None:  # noqa: ANN001
    import subprocess
    import sys
    from pathlib import Path

    backend_root = Path(__file__).resolve().parents[2]
    legacy = tmp_path / "legacy.json"
    agent = tmp_path / "agent.json"
    agent_bad = tmp_path / "agent_bad.json"
    legacy.write_text(_run(calls=2).model_dump_json(), encoding="utf-8")
    agent.write_text(_run(calls=3).model_dump_json(), encoding="utf-8")
    agent_bad.write_text(_run(raw_value="other").model_dump_json(), encoding="utf-8")

    def run(left: Path, right: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/pipeline_shadow_compare.py", str(left), str(right)],
            cwd=backend_root,
            capture_output=True,
            text=True,
            timeout=120,
        )

    assert run(legacy, agent).returncode == 0
    diff = run(legacy, agent_bad)
    assert diff.returncode == 1
    assert '"raw_value"' in diff.stdout
