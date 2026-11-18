"""Tests for the AgentScope extract skill and shadow router.

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
from src.core.contracts.skill_io import SkillError, SkillRequest
from src.pipeline.skills.fact_chain.extract import (
    ExtractSkill,
    StageRouterProvider,
    compare_extract_replies,
    window_tools,
)
from src.pipeline.skills.fact_chain.prompts import EXTRACT_PROMPT
from src.pipeline.skills.runtime.llm import ProviderError
from src.core.tools.fact_chain.contracts import canonical_json

FACT = {
    "field_id": "B.clinical_phenotypes",
    "raw_value": "severe hypotonia",
    "polarity": "positive",
    "subject_status": "unknown",
    "subject_id": None,
    "quote": "The patient had severe hypotonia.",
}
WINDOW = "The patient had severe hypotonia. No seizures were reported."
PAYLOAD = canonical_json({"document_id": "doc-1", "language": "en", "window_id": "0:60", "window_text": WINDOW})


class FakeChatModel(ChatModelBase):
    """Return the structured-output tool call exactly like a real model would."""

    def __init__(self, facts: list[dict] | None = None) -> None:
        super().__init__(
            credential=OpenAICredential(api_key="test-key", base_url="http://localhost"),
            model="fake-model",
            parameters=None,
            stream=False,
        )
        self.formatter = OpenAIChatFormatter()
        self.facts = [FACT] if facts is None else facts
        self.calls = 0

    async def _call_api(self, model_name, messages, tools=None, tool_choice=None, **kwargs):  # noqa: ANN001
        self.calls += 1
        names = [(tool.get("function") or {}).get("name") for tool in (tools or [])]
        if "GenerateStructuredOutput" in names:
            payload = json.dumps({"facts": self.facts})
            return ChatResponse(
                content=[ToolCallBlock(id="call-1", name="GenerateStructuredOutput", input=payload)],
                is_last=True,
            )
        return ChatResponse(content=[TextBlock(text="done")], is_last=True)


class FakeAgent:
    """Minimal duck-typed agent for skill error paths."""

    def __init__(self, structured_output: dict | None) -> None:
        self.structured_output = structured_output

    async def reply(self, inputs, structured_schema=None):  # noqa: ANN001
        return Msg(
            name="extract",
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


def _request(payload: str = PAYLOAD) -> SkillRequest:
    return SkillRequest(
        stage="extract", model_id="fast-model", window_id="0:60", prompt=EXTRACT_PROMPT, payload=payload
    )


def test_pipeline_agent_runtime_defaults_to_legacy() -> None:
    assert PipelineConfig().agent_runtime == "legacy"


def test_extract_skill_runs_agent_and_returns_validated_reply() -> None:
    model = FakeChatModel()
    skill = ExtractSkill(SimpleNamespace(), model=model)

    result = skill.call(_request())

    assert result.data == {"facts": [FACT]}
    assert model.calls == 1
    assert skill.invoke(
        stage="extract", model_id="fast-model", prompt=EXTRACT_PROMPT, payload=PAYLOAD
    ) == canonical_json({"facts": [FACT]})


def test_extract_skill_exposes_window_tools_to_the_agent() -> None:
    seen: dict[str, list[str]] = {}

    def factory(window_text: str):
        tools = window_tools(window_text)
        seen["names"] = [tool.__name__ for tool in tools]
        return FakeAgent({"facts": []})

    skill = ExtractSkill(SimpleNamespace(), agent_factory=factory)
    skill.call(_request())

    assert seen["names"] == ["quote_in_window", "atomic_value"]


def test_extract_skill_maps_missing_structured_output_to_skill_error() -> None:
    skill = ExtractSkill(SimpleNamespace(), agent_factory=lambda _: FakeAgent(None))

    with pytest.raises(SkillError):
        skill.call(_request())


def test_extract_skill_rejects_non_json_payload() -> None:
    skill = ExtractSkill(SimpleNamespace(), agent_factory=lambda _: FakeAgent({"facts": []}))

    with pytest.raises(SkillError):
        skill.call(_request(payload="not-json"))


def test_compare_extract_replies_ignores_order() -> None:
    first = canonical_json({"facts": [FACT]})
    second = canonical_json({"facts": [dict(FACT, raw_value="seizures", quote="No seizures were reported.")]})

    assert compare_extract_replies(first, first) == []
    assert compare_extract_replies(first, second) != []


def test_shadow_router_returns_legacy_reply_and_counts_mismatch() -> None:
    legacy = StubProvider(canonical_json({"facts": [FACT]}))
    agent_reply = canonical_json({"facts": []})
    router = StageRouterProvider(legacy=legacy, extract=StubSkill(agent_reply), mode="shadow")

    result = router.invoke(stage="extract", model_id="fast-model", prompt=EXTRACT_PROMPT, payload=PAYLOAD)

    assert result == canonical_json({"facts": [FACT]})
    assert router.stats.calls == 1
    assert router.stats.mismatches == 1
    assert router.stats.agent_failures == 0


def test_shadow_router_keeps_legacy_when_agent_fails() -> None:
    legacy = StubProvider(canonical_json({"facts": [FACT]}))
    router = StageRouterProvider(
        legacy=legacy,
        extract=StubSkill(ProviderError("boom")),
        mode="shadow",
    )

    result = router.invoke(stage="extract", model_id="fast-model", prompt=EXTRACT_PROMPT, payload=PAYLOAD)

    assert result == canonical_json({"facts": [FACT]})
    assert router.stats.agent_failures == 1
    assert router.stats.mismatches == 0


def test_agentscope_router_only_replaces_extract() -> None:
    legacy = StubProvider("legacy-reply")
    skill = StubSkill(canonical_json({"facts": [FACT]}))
    router = StageRouterProvider(legacy=legacy, extract=skill, mode="agentscope")

    extract = router.invoke(stage="extract", model_id="fast-model", prompt=EXTRACT_PROMPT, payload=PAYLOAD)
    verify = router.invoke(stage="verify", model_id="reasoning-model", prompt="p", payload="{}")
    translate = router.invoke(stage="translate", model_id="fast-model", prompt="p", payload="{}")

    assert extract == canonical_json({"facts": [FACT]})
    assert verify == "legacy-reply"
    assert translate == "legacy-reply"
    assert [call["stage"] for call in legacy.calls] == ["verify", "translate"]
    assert [call["stage"] for call in skill.calls] == ["extract"]


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
