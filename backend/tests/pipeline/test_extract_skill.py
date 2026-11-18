"""Tests for the AgentScope Phase 3 skills and the shadow router.

The model is a local fake: no network, no API key, deterministic replies.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from agentscope.credential import OpenAICredential
from agentscope.formatter import OpenAIChatFormatter
from agentscope.message import Msg, TextBlock, ToolCallBlock
from agentscope.model import ChatModelBase, ChatResponse

from src.core.config import PipelineConfig
from src.pipeline.contracts.skill_io import SkillError, SkillRequest
from src.pipeline.skills.fact_chain.extract import ExtractSkill, window_tools
from src.pipeline.skills.fact_chain.prompts import EXTRACT_PROMPT, TRANSLATE_PROMPT, VERIFY_PROMPT
from src.pipeline.skills.fact_chain.router import StageRouterProvider, compare_stage_replies
from src.pipeline.skills.fact_chain.translate import TranslateSkill
from src.pipeline.skills.fact_chain.verify import VerifySkill
from src.pipeline.skills.runtime.llm import ProviderError
from src.pipeline.tools.fact_chain.contracts import canonical_json

FACT = {
    "field_id": "B.clinical_phenotypes",
    "raw_value": "severe hypotonia",
    "polarity": "positive",
    "subject_status": "unknown",
    "subject_id": None,
    "quote": "The patient had severe hypotonia.",
}
VERDICT = {"fact_id": "fact-1", "label": "supported", "reason": "quote matches"}
TRANSLATION = {"fact_id": "fact-1", "english_text": "severe hypotonia"}
WINDOW = "The patient had severe hypotonia. No seizures were reported."
PAYLOAD = canonical_json({"document_id": "doc-1", "language": "en", "window_id": "0:60", "window_text": WINDOW})


class FakeChatModel(ChatModelBase):
    """Return the structured-output tool call exactly like a real model would."""

    def __init__(self, structured: dict | None = None) -> None:
        super().__init__(
            credential=OpenAICredential(api_key="test-key", base_url="http://localhost"),
            model="fake-model",
            parameters=None,
            stream=False,
        )
        self.formatter = OpenAIChatFormatter()
        self.structured = {"facts": [FACT]} if structured is None else structured
        self.calls = 0

    async def _call_api(self, model_name, messages, tools=None, tool_choice=None, **kwargs):  # noqa: ANN001
        self.calls += 1
        names = [(tool.get("function") or {}).get("name") for tool in (tools or [])]
        if "GenerateStructuredOutput" in names:
            return ChatResponse(
                content=[
                    ToolCallBlock(
                        id="call-1",
                        name="GenerateStructuredOutput",
                        input=json.dumps(self.structured),
                    )
                ],
                is_last=True,
            )
        return ChatResponse(content=[TextBlock(text="done")], is_last=True)


class FakeAgent:
    """Minimal duck-typed agent for skill error paths."""

    def __init__(self, structured_output: dict | None) -> None:
        self.structured_output = structured_output

    async def reply(self, inputs, structured_schema=None):  # noqa: ANN001
        return Msg(
            name="stage",
            role="assistant",
            content=[TextBlock(text="ok")],
            structured_output=self.structured_output,
        )


class StubProvider:
    def __init__(self, reply: str | Exception) -> None:
        self.reply = reply
        self.calls: list[dict[str, str]] = []

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        self.calls.append({"stage": stage, "model_id": model_id})
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


class StubSkill:
    def __init__(self, reply: str | Exception) -> None:
        self.reply = reply
        self.calls: list[dict[str, str]] = []

    def invoke(self, *, stage: str, model_id: str, prompt: str, payload: str) -> str:
        self.calls.append({"stage": stage, "model_id": model_id})
        if isinstance(self.reply, Exception):
            raise self.reply
        return self.reply


def _request(stage: str, prompt: str, payload: str = PAYLOAD) -> SkillRequest:
    return SkillRequest(stage=stage, model_id="fast-model", window_id="0:60", prompt=prompt, payload=payload)


def test_pipeline_agent_runtime_defaults_to_legacy() -> None:
    assert PipelineConfig().agent_runtime == "legacy"


def test_extract_skill_runs_agent_and_returns_validated_reply() -> None:
    model = FakeChatModel()
    skill = ExtractSkill(SimpleNamespace(), model=model)

    result = skill.call(_request("extract", EXTRACT_PROMPT))

    assert result.data == {"facts": [FACT]}
    assert model.calls == 1
    assert skill.invoke(
        stage="extract", model_id="fast-model", prompt=EXTRACT_PROMPT, payload=PAYLOAD
    ) == canonical_json({"facts": [FACT]})


def test_extract_skill_exposes_window_tools_to_the_agent() -> None:
    seen: dict[str, list[str]] = {}

    def factory(payload: dict) -> FakeAgent:
        tools = window_tools(str(payload["window_text"]))
        seen["names"] = [tool.__name__ for tool in tools]
        return FakeAgent({"facts": []})

    skill = ExtractSkill(SimpleNamespace(), agent_factory=factory)
    skill.call(_request("extract", EXTRACT_PROMPT))

    assert seen["names"] == ["quote_in_window", "atomic_value"]


def test_extract_skill_maps_missing_structured_output_to_skill_error() -> None:
    skill = ExtractSkill(SimpleNamespace(), agent_factory=lambda _: FakeAgent(None))

    with pytest.raises(SkillError):
        skill.call(_request("extract", EXTRACT_PROMPT))


def test_extract_skill_rejects_non_json_payload() -> None:
    skill = ExtractSkill(SimpleNamespace(), agent_factory=lambda _: FakeAgent({"facts": []}))

    with pytest.raises(SkillError):
        skill.call(_request("extract", EXTRACT_PROMPT, payload="not-json"))


def test_verify_skill_returns_validated_verdicts() -> None:
    model = FakeChatModel({"verdicts": [VERDICT]})
    skill = VerifySkill(SimpleNamespace(), model=model)

    result = skill.call(_request("verify", VERIFY_PROMPT))

    assert result.data == {"verdicts": [VERDICT]}
    assert skill.tier == "reasoning"


def test_verify_skill_rejects_unknown_label() -> None:
    model = FakeChatModel({"verdicts": [dict(VERDICT, label="maybe")]})
    skill = VerifySkill(SimpleNamespace(), model=model)

    with pytest.raises(SkillError):
        skill.call(_request("verify", VERIFY_PROMPT))


def test_translate_skill_returns_validated_translations() -> None:
    model = FakeChatModel({"translations": [TRANSLATION]})
    skill = TranslateSkill(SimpleNamespace(), model=model)

    result = skill.call(_request("translate", TRANSLATE_PROMPT))

    assert result.data == {"translations": [TRANSLATION]}
    assert result.stage == "translate"


def test_skills_reject_foreign_stage_requests() -> None:
    skill = TranslateSkill(SimpleNamespace(), agent_factory=lambda _: FakeAgent({}))

    with pytest.raises(SkillError):
        skill.call(_request("extract", TRANSLATE_PROMPT))


def test_compare_stage_replies_ignores_order() -> None:
    first = canonical_json({"facts": [FACT]})
    second = canonical_json({"facts": [dict(FACT, raw_value="seizures", quote="No seizures were reported.")]})

    assert compare_stage_replies("extract", first, first) == []
    assert compare_stage_replies("extract", first, second) != []
    assert compare_stage_replies("translate", canonical_json({"translations": [TRANSLATION]}), "{}") != []


def test_shadow_router_returns_legacy_reply_and_counts_mismatch() -> None:
    legacy = StubProvider(canonical_json({"facts": [FACT]}))
    router = StageRouterProvider(
        legacy=legacy,
        skills={"extract": StubSkill(canonical_json({"facts": []}))},
        mode="shadow",
    )

    result = router.invoke(stage="extract", model_id="fast-model", prompt=EXTRACT_PROMPT, payload=PAYLOAD)

    assert result == canonical_json({"facts": [FACT]})
    assert router.stats.calls == 1
    assert router.stats.mismatches == 1
    assert router.stats.agent_failures == 0


def test_shadow_router_keeps_legacy_when_agent_fails() -> None:
    legacy = StubProvider(canonical_json({"facts": [FACT]}))
    router = StageRouterProvider(
        legacy=legacy,
        skills={"extract": StubSkill(ProviderError("boom"))},
        mode="shadow",
    )

    result = router.invoke(stage="extract", model_id="fast-model", prompt=EXTRACT_PROMPT, payload=PAYLOAD)

    assert result == canonical_json({"facts": [FACT]})
    assert router.stats.agent_failures == 1
    assert router.stats.mismatches == 0


def test_agentscope_router_routes_only_registered_stages() -> None:
    legacy = StubProvider("legacy-reply")
    skill = StubSkill(canonical_json({"facts": [FACT]}))
    router = StageRouterProvider(legacy=legacy, skills={"extract": skill}, mode="agentscope")

    extract = router.invoke(stage="extract", model_id="fast-model", prompt=EXTRACT_PROMPT, payload=PAYLOAD)
    verify = router.invoke(stage="verify", model_id="reasoning-model", prompt="p", payload="{}")
    translate = router.invoke(stage="translate", model_id="fast-model", prompt="p", payload="{}")

    assert extract == canonical_json({"facts": [FACT]})
    assert verify == "legacy-reply"
    assert translate == "legacy-reply"
    assert [call["stage"] for call in legacy.calls] == ["verify", "translate"]
    assert [call["stage"] for call in skill.calls] == ["extract"]


def test_agentscope_router_covers_all_three_phase3_stages() -> None:
    legacy = StubProvider("legacy-reply")
    router = StageRouterProvider(
        legacy=legacy,
        skills={
            "extract": StubSkill(canonical_json({"facts": []})),
            "verify": StubSkill(canonical_json({"verdicts": []})),
            "translate": StubSkill(canonical_json({"translations": []})),
        },
        mode="agentscope",
    )

    for stage, prompt in (("extract", EXTRACT_PROMPT), ("verify", VERIFY_PROMPT), ("translate", TRANSLATE_PROMPT)):
        router.invoke(stage=stage, model_id="m", prompt=prompt, payload="{}")

    assert legacy.calls == []


def test_agentscope_router_maps_skill_errors_to_provider_errors() -> None:
    router = StageRouterProvider(
        legacy=StubProvider("legacy-reply"),
        skills={"extract": StubSkill(SkillError("agent schema failure"))},
        mode="agentscope",
    )

    with pytest.raises(ProviderError):
        router.invoke(stage="extract", model_id="fast-model", prompt=EXTRACT_PROMPT, payload=PAYLOAD)


def test_rotating_model_prefers_the_next_credential() -> None:
    from src.pipeline.skills.runtime.agentscope_llm import RotatingOpenAIChatModel

    model = RotatingOpenAIChatModel(
        credentials=[
            OpenAICredential(api_key="k1", base_url="http://first"),
            OpenAICredential(api_key="k2", base_url="http://second"),
        ],
        model="fake-model",
        stream=False,
    )

    model._use_credential(1)

    assert model.credential.api_key.get_secret_value() == "k2"
    assert str(model.client.base_url).rstrip("/") == "http://second"


def test_rotating_model_retries_with_next_key_after_auth_failure(monkeypatch) -> None:  # noqa: ANN001
    import asyncio

    import httpx
    import openai
    from agentscope.model import ChatResponse

    from src.pipeline.skills.runtime.agentscope_llm import RotatingOpenAIChatModel

    model = RotatingOpenAIChatModel(
        credentials=[
            OpenAICredential(api_key="k1", base_url="http://first"),
            OpenAICredential(api_key="k2", base_url="http://second"),
        ],
        model="fake-model",
        stream=False,
    )
    attempts: list[int] = []

    async def fake_call(self, model_name, messages, tools=None, tool_choice=None, **kwargs):  # noqa: ANN001
        attempts.append(self._credential_index)
        if len(attempts) == 1:
            raise openai.AuthenticationError(
                "bad key",
                response=httpx.Response(401, request=httpx.Request("POST", "http://first")),
                body=None,
            )
        return ChatResponse(content=[], is_last=True)

    monkeypatch.setattr("agentscope.model.OpenAIChatModel._call_api", fake_call)

    asyncio.run(model._call_api("fake-model", []))

    assert attempts == [0, 1]
    assert model.credential.api_key.get_secret_value() == "k2"


def test_build_chat_model_reads_every_configured_key() -> None:
    from src.pipeline.skills.runtime.agentscope_llm import build_chat_model

    cfg = SimpleNamespace(
        llm=SimpleNamespace(
            model="fast-model",
            base_url="http://fast",
            all_api_keys=["k1", "k2"],
            max_tokens=128,
            max_retries=0,
            timeout=5,
        ),
        reasoning=SimpleNamespace(model="reasoning-model", base_url="http://reasoning", all_api_keys=["k3"]),
    )

    model = build_chat_model(cfg, tier="fast")

    assert [credential.api_key.get_secret_value() for credential in model._credentials] == ["k1", "k2"]
