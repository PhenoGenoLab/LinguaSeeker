"""Integration test for the full translation pipeline with mocked model calls."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.core.tools.translation.contracts import TranslationResult
from src.pipeline.skills.translation.api import TranslationService

_ASYNC_HELPER = "src.pipeline.skills.translation.translate.providers.ainvoke_model_text"
_SYNC_HELPER = "src.pipeline.skills.runtime.llm.invoke_model_text"
_MODEL_FACTORY = "src.pipeline.skills.runtime.agentscope_llm.create_chat_model"


@pytest.fixture
def mock_cfg():
    return SimpleNamespace(
        translation=SimpleNamespace(
            model="test-model",
            api_key="test-key",
            api_keys=["test-key"],
            all_api_keys=["test-key"],
            base_url="http://localhost:8001/v1",
            local_base_url="",
            local_target_lang="en",
            local_timeout=30.0,
            remote_base_url="",
            remote_api_key="",
            remote_api_keys=[],
            remote_model="",
            remote_all_api_keys=[],
            temperature=0.0,
            max_tokens=1024,
            timeout=1,
        )
    )


@pytest.fixture
def chinese_pages():
    return [
        {
            "page_number": 1,
            "markdown": "该患者携带BRCA1基因的新变异。该变异导致蛋白质功能丧失。",
        },
    ]


@pytest.fixture
def english_pages():
    return [
        {
            "page_number": 1,
            "markdown": "The patient carries a novel BRCA1 variant. This variant results in loss of protein function.",
        },
    ]


def test_full_pipeline_chinese(mock_cfg, chinese_pages):
    """Full pipeline: Chinese → English with the 3-stage pipeline."""
    _translate_response = (
        "The patient carries a novel BRCA1 gene variant. This variant leads to loss of protein function."
    )
    _sys_prompt = (
        "You are a biomedical translation engine. Translate from Chinese to English. Preserve markdown structure."
    )
    responses = [
        "基因:gene\n变异:variant",  # terminology
        _sys_prompt,  # system prompt generation
        _translate_response,  # full-document translate
        _translate_response,  # self-review
    ] * 2  # the pipeline runs twice (original + translated pass)
    calls: list[str] = []

    async def fake_async(model, content, **kwargs):
        calls.append(content)
        return responses.pop(0)

    with (
        patch(_MODEL_FACTORY, return_value=MagicMock()),
        patch(_ASYNC_HELPER, side_effect=fake_async),
        patch(_SYNC_HELPER, return_value=_translate_response),
    ):
        service = TranslationService(cfg=mock_cfg)
        result = service.run_sync(chinese_pages)

    assert isinstance(result, TranslationResult)
    assert result.source_language != "en"
    assert result.translated_english
    assert result.translated_english != result.formatted_original
    assert result.sentences
    assert calls


def test_pipeline_skip_english(mock_cfg, english_pages):
    """Pipeline should skip translation for English documents."""
    _english = (
        "The patient carries a novel BRCA1 variant. This variant results in loss of protein function."
    )

    async def fake_async(model, content, **kwargs):  # pragma: no cover - must not run
        raise AssertionError("no translation call expected for English input")

    with (
        patch(_MODEL_FACTORY, return_value=MagicMock()),
        patch(_ASYNC_HELPER, side_effect=fake_async),
        patch(_SYNC_HELPER, return_value=_english),
    ):
        service = TranslationService(cfg=mock_cfg)
        result = service.run_sync(english_pages)

    assert isinstance(result, TranslationResult)
    assert result.source_language == "en"
    assert result.formatted_original == result.translated_english
    assert len(result.segments) == 0
