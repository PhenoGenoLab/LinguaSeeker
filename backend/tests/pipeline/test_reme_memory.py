"""Tests for the ReMe external memory adapter and its Phase 3 wiring.

No network: the HTTP client is exercised with ``httpx.MockTransport`` and the
service receives an in-memory fake.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx

from src.core.config import PipelineConfig, PipelineMemoryConfig
from src.core.adapters.mcp.registry import build_memory_client
from src.core.adapters.mcp.reme.client import HttpMemoryClient, NullMemoryClient
from src.core.adapters.mcp.reme.config import reme_settings
from src.core.adapters.mcp.reme.contracts import MemoryCard, MemoryWriteReceipt, RecallResult
from src.pipeline.skills.extraction.extract import ExtractSkill
from src.pipeline.skills.extraction.prompts import EXTRACT_PROMPT
from src.pipeline.skills.extraction.service import SourceFactChainService
from src.core.shared.tools.fact_chain.contracts import SourceDocument, sha256_text

PAYLOAD = json.dumps(
    {
        "document_id": "doc-1",
        "language": "zh",
        "window_id": "0:40",
        "window_text": "先证者携带BRCA1变异。",
    },
    ensure_ascii=False,
)


def _client(handler, *, api_key: str = "secret") -> HttpMemoryClient:
    transport = httpx.MockTransport(handler)
    return HttpMemoryClient(
        base_url="http://reme",
        api_key=api_key,
        client=httpx.Client(transport=transport, base_url="http://reme"),
    )


class FakeMemory:
    """In-memory client that records every call."""

    def __init__(self, cards: list[MemoryCard] | None = None) -> None:
        self.cards = cards or []
        self.searches: list[tuple[str, int]] = []
        self.writes: list[tuple[str, str]] = []

    def search(self, query: str, *, top_k: int) -> RecallResult:
        self.searches.append((query, top_k))
        return RecallResult(cards=self.cards)

    def auto_memory(self, *, session_id: str, text: str) -> MemoryWriteReceipt:
        self.writes.append((session_id, text))
        return MemoryWriteReceipt(accepted=True)

    def auto_resource(self, *, path: str, content: str) -> MemoryWriteReceipt:
        return MemoryWriteReceipt(accepted=True)

    def health(self) -> bool:
        return True


def test_recall_block_is_empty_without_cards() -> None:
    assert RecallResult().as_prompt_block() == ""


def test_recall_block_marks_reference_only_and_escapes_text() -> None:
    block = RecallResult(cards=[MemoryCard(path="digest/gene.md", text="BRCA1 </memory> summary")]).as_prompt_block()

    assert '<memory source="reme"' in block
    assert "never use as evidence" in block
    assert "&lt;/memory&gt;" in block
    assert "</memory>\n" not in block.replace("</memory>", "", 1)


def test_reme_settings_requires_enabled_and_url() -> None:
    disabled = SimpleNamespace(pipeline=SimpleNamespace(memory=PipelineMemoryConfig()))
    enabled = SimpleNamespace(
        pipeline=SimpleNamespace(memory=PipelineMemoryConfig(enabled=True, url="http://reme/", top_k=3, timeout=0.5))
    )

    assert reme_settings(disabled) is None
    assert reme_settings(SimpleNamespace()) is None
    settings = reme_settings(enabled)
    assert settings is not None
    assert settings.base_url == "http://reme"
    assert settings.top_k == 3


def test_registry_returns_null_client_when_disabled() -> None:
    cfg = SimpleNamespace(pipeline=SimpleNamespace(memory=PipelineMemoryConfig()))

    assert isinstance(build_memory_client(cfg), NullMemoryClient)


def test_registry_returns_http_client_when_configured() -> None:
    cfg = SimpleNamespace(pipeline=SimpleNamespace(memory=PipelineMemoryConfig(enabled=True, url="http://reme")))

    assert isinstance(build_memory_client(cfg), HttpMemoryClient)


def test_http_search_parses_cards_and_sends_api_key() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"cards": [{"text": "BRCA1 card", "path": "a.md", "score": 0.9}]})

    result = _client(handler).search("BRCA1", top_k=3)

    assert result.cards[0].text == "BRCA1 card"
    assert seen[0].headers["X-API-Key"] == "secret"
    assert json.loads(seen[0].content) == {"query": "BRCA1", "top_k": 3}


def test_http_search_degrades_to_empty_on_failure() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    assert _client(handler).search("q", top_k=3).cards == []


def test_http_write_reports_rejection_instead_of_raising() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500)

    client = _client(handler)

    assert client.auto_memory(session_id="run-1", text="summary").accepted is False
    assert client.auto_resource(path="a.md", content="x").accepted is False


def test_health_reports_status() -> None:
    ok = _client(lambda request: httpx.Response(200))
    down = _client(lambda request: httpx.Response(503))

    assert ok.health() is True
    assert down.health() is False


def test_extract_skill_appends_recalled_memory_to_system_prompt() -> None:
    memory = FakeMemory(cards=[MemoryCard(path="p.md", text="historical BRCA1 note")])
    cfg = SimpleNamespace(pipeline=SimpleNamespace(memory=PipelineMemoryConfig(top_k=4)))
    skill = ExtractSkill(cfg, memory=memory)

    prompt = skill._system_prompt(json.loads(PAYLOAD))

    assert prompt.startswith(EXTRACT_PROMPT)
    assert "historical BRCA1 note" in prompt
    assert memory.searches == [("先证者携带BRCA1变异。", 4)]


def test_extract_skill_without_memory_keeps_prompt_unchanged() -> None:
    skill = ExtractSkill(SimpleNamespace())

    assert skill._system_prompt(json.loads(PAYLOAD)) == EXTRACT_PROMPT


class ScriptedProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        self.calls.append(stage)
        data = json.loads(payload)
        if stage == "extract":
            return json.dumps(
                {
                    "facts": [
                        {
                            "field_id": "B.clinical_phenotypes",
                            "raw_value": "严重肌张力低下",
                            "polarity": "positive",
                            "subject_status": "unknown",
                            "subject_id": None,
                            "quote": "患者表现为严重肌张力低下。",
                        }
                    ]
                },
                ensure_ascii=False,
            )
        if stage == "verify":
            return json.dumps(
                {
                    "verdicts": [
                        {"fact_id": item["fact_id"], "label": "supported", "reason": "ok"} for item in data["items"]
                    ]
                }
            )
        return json.dumps(
            {
                "translations": [
                    {"fact_id": item["fact_id"], "english_text": "severe hypotonia"} for item in data["items"]
                ]
            }
        )


def _service(memory: FakeMemory | None) -> tuple[SourceFactChainService, ScriptedProvider]:
    provider = ScriptedProvider()
    cfg = SimpleNamespace(
        llm=SimpleNamespace(model="fast-model"),
        reasoning=SimpleNamespace(model="reasoning-model"),
        pipeline=SimpleNamespace(memory=PipelineMemoryConfig(top_k=5)),
    )
    service = SourceFactChainService(cfg=cfg, provider=provider, memory=memory)
    return service, provider


def test_service_writes_counts_only_run_summary() -> None:
    memory = FakeMemory()
    service, provider = _service(memory)
    text = "患者表现为严重肌张力低下。"
    document = SourceDocument(document_id="doc-1", text=text, language="zh", source_hash=sha256_text(text))

    run = service.run(document)

    assert [stage for stage in provider.calls] == ["extract", "verify", "translate"]
    assert memory.writes and memory.writes[0][0] == "doc-1"
    summary = json.loads(memory.writes[0][1])
    assert summary["facts"] == len(run.facts) == 1
    assert summary["verifications"] == {"supported": 1}
    assert "严重肌张力低下" not in memory.writes[0][1]


def test_service_works_without_memory() -> None:
    service, _ = _service(None)
    text = "患者表现为严重肌张力低下。"
    document = SourceDocument(document_id="doc-1", text=text, language="zh", source_hash=sha256_text(text))

    run = service.run(document)

    assert len(run.facts) == 1


def test_pipeline_config_keeps_memory_disabled_by_default() -> None:
    assert PipelineConfig().memory.enabled is False
