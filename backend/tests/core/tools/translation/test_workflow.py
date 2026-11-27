import pytest
from types import SimpleNamespace

from src.pipeline.skills.translation.config_context import TranslationConfigContext
from src.pipeline.skills.translation.api import TranslationService


def _translation_cfg(**overrides) -> SimpleNamespace:
    """Build an object shaped like the real ``TranslationLLMConfig``."""
    values = {
        "model": "test-model",
        "api_key": "test-key",
        "api_keys": ["test-key"],
        "all_api_keys": ["test-key"],
        "base_url": "http://localhost:8001/v1",
        "local_base_url": "",
        "local_target_lang": "en",
        "local_timeout": 30.0,
        "remote_base_url": "",
        "remote_api_key": "",
        "remote_api_keys": [],
        "remote_model": "",
        "remote_all_api_keys": [],
        "temperature": 0.0,
        "max_tokens": 1024,
        "timeout": 1,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


@pytest.fixture
def mock_config():
    return SimpleNamespace(translation=_translation_cfg())


@pytest.fixture
def sample_pages():
    return [
        {"page_number": 1, "markdown": "The patient carries a novel BRCA1 variant."},
    ]


def test_service_init(mock_config):
    service = TranslationService(cfg=mock_config)
    assert service._ctx.model == "test-model"


def test_service_has_formatter(mock_config):
    service = TranslationService(cfg=mock_config)
    assert service._formatter is not None


def test_service_has_translator(mock_config):
    service = TranslationService(cfg=mock_config)
    assert service._translator is not None


def test_service_has_router(mock_config):
    service = TranslationService(cfg=mock_config)
    assert service._router is not None


# ── TranslationConfigContext tests ────────────────────────────────────


def test_config_context_from_config(mock_config):
    mock_config.translation = _translation_cfg(
        model="translation-model",
        api_key="translation-key",
        all_api_keys=["translation-key"],
        base_url="https://remote.example/v1",
        local_base_url="http://localhost:59062/api",
        local_target_lang="en",
        local_timeout=30,
    )

    ctx = TranslationConfigContext.from_config(mock_config)
    assert ctx.model == "translation-model"
    assert ctx.api_key == "translation-key"
    assert ctx.base_url == "https://remote.example/v1"
    assert ctx.local_base_url == "http://localhost:59062/api"
    assert ctx.temperature == 0.0


def test_config_context_prefers_remote_override_for_fallback():
    cfg = SimpleNamespace(
        translation=_translation_cfg(
            model="local-default-model",
            api_key="default-key",
            all_api_keys=["default-key"],
            base_url="https://default.example/v1",
            local_base_url="http://localhost:59062/api",
            remote_base_url="https://remote.example/v1",
            remote_model="remote-model",
            remote_api_key="remote-key",
            remote_all_api_keys=["remote-key"],
        )
    )

    ctx = TranslationConfigContext.from_config(cfg)

    assert ctx.model == "remote-model"
    assert ctx.api_key == "remote-key"
    assert ctx.api_keys == ["remote-key"]
    assert ctx.base_url == "https://remote.example/v1"
    assert ctx.local_base_url == "http://localhost:59062/api"


def test_config_context_from_config_default_temperature():
    cfg = SimpleNamespace(translation=_translation_cfg(temperature=None))
    ctx = TranslationConfigContext.from_config(cfg)
    assert ctx.temperature == 0.0


# ── TranslationService.save() tests ───────────────────────────────────


def test_translation_service_save(tmp_path):
    """TranslationService.save() persists result and returns output."""
    from src.core.tools.translation.contracts import TranslationResult

    cfg = SimpleNamespace(translation=_translation_cfg())

    service = TranslationService(cfg=cfg)

    result = TranslationResult(
        formatted_original="原始文本",
        translated_english="Original text",
        source_language="zh",
        terminology_map={"基因": "gene"},
        translation_warnings=[],
        sentences=[],
        segments=[],
    )

    output = service.save(
        result,
        output_dir=str(tmp_path),
        doc_id="test_doc",
    )

    assert output.formatted_original == "原始文本"
    assert output.translated_english == "Original text"
    assert output.output_dir.startswith(str(tmp_path))
    assert output.original_json_path.endswith("original.json")


def test_translation_service_save_with_images(tmp_path):
    """TranslationService.save() forwards image_paths to persistence."""
    from src.core.tools.translation.contracts import TranslationResult

    # Create fake source images
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    img = src_dir / "fig1.png"
    img.write_bytes(b"fake_png")

    cfg = SimpleNamespace(translation=_translation_cfg())

    service = TranslationService(cfg=cfg)

    result = TranslationResult(
        formatted_original="原始文本",
        translated_english="Original text",
        source_language="zh",
        terminology_map={"基因": "gene"},
        translation_warnings=[],
        sentences=[],
        segments=[],
    )

    output = service.save(
        result,
        output_dir=str(tmp_path / "out"),
        doc_id="test_doc",
        image_paths=[str(img)],
    )

    assert len(output.image_paths) == 1
    assert output.image_paths[0].endswith("fig1.png")
