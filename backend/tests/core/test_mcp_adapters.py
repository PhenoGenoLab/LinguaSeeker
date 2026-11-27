"""MCP adapter decoding, client calls, and routing from the service layer."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.core.adapters.mcp.literature import McpLiteratureDocument, McpLiteratureResult
from src.core.adapters.mcp.mineru import McpMineruResult, McpParsedDocument
from src.core.adapters.mcp.server import McpToolClient, McpToolError
from src.core.config import McpServerConfig, Settings


def _settings(**kwargs) -> Settings:
    return Settings(**kwargs)


def _server_config(**kwargs) -> McpServerConfig:
    base = {
        "enabled": True,
        "transport": "streamable_http",
        "url": "http://127.0.0.1:9000/mcp",
        "tool": "run",
        "timeout": 5.0,
    }
    base.update(kwargs)
    return McpServerConfig(**base)


class _FakeResult:
    def __init__(self, *, structured=None, text=None, is_error=False):
        self.structured_content = structured
        self.content = [SimpleNamespace(text=text)] if text is not None else []
        self.is_error = is_error


class _FakeClient:
    result: _FakeResult

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc_info):
        return False

    async def call_tool(self, name, arguments):
        return self.result


def test_tool_client_prefers_structured_content(monkeypatch):
    _FakeClient.result = _FakeResult(structured={"documents": []})
    monkeypatch.setattr("src.core.adapters.mcp.server.Client", _FakeClient)

    payload = asyncio.run(McpToolClient(_server_config()).call({"query": "x"}))

    assert payload == {"documents": []}


def test_tool_client_decodes_json_text(monkeypatch):
    _FakeClient.result = _FakeResult(text='{"documents": [{"path": "a.pdf"}]}')
    monkeypatch.setattr("src.core.adapters.mcp.server.Client", _FakeClient)

    payload = asyncio.run(McpToolClient(_server_config()).call({}))

    assert payload["documents"][0]["path"] == "a.pdf"


def test_tool_client_rejects_non_json_text(monkeypatch):
    _FakeClient.result = _FakeResult(text="not json")
    monkeypatch.setattr("src.core.adapters.mcp.server.Client", _FakeClient)

    with pytest.raises(McpToolError, match="did not return JSON"):
        asyncio.run(McpToolClient(_server_config()).call({}))


def test_tool_client_requires_enabled_server():
    with pytest.raises(McpToolError, match="not enabled"):
        asyncio.run(McpToolClient(_server_config(enabled=False)).call({}))


def test_literature_decode_requires_path():
    with pytest.raises(McpToolError, match="missing 'path'"):
        from src.core.adapters.mcp.literature import _decode

        _decode({"documents": [{"title": "x"}]})


def test_mineru_decode_requires_artifact_paths():
    from src.core.adapters.mcp.mineru import _decode

    with pytest.raises(McpToolError, match="requires source_path"):
        _decode({"documents": [{"md_path": "a.md"}]})


def test_acquisition_service_routes_online_mode_to_mcp(monkeypatch):
    settings = _settings(mcp_literature_enabled=True)
    monkeypatch.setattr("src.core.config.get_config", lambda: settings)
    fetch = AsyncMock(return_value=McpLiteratureResult(documents=(McpLiteratureDocument(path="/tmp/a.pdf"),)))
    monkeypatch.setattr("src.core.adapters.mcp.literature.McpLiteratureClient.fetch", fetch)

    from src.core.tools.acquisition.contracts import AcquisitionSource, DocumentAcquisitionRequest
    from src.core.tools.acquisition.service import DocumentAcquisitionService

    result = asyncio.run(
        DocumentAcquisitionService().acquire(
            DocumentAcquisitionRequest(source=AcquisitionSource.ONLINE, action="search", query="BRCA1")
        )
    )

    assert result.success is True
    assert result.downloads[0].file_path == "/tmp/a.pdf"
    fetch.assert_awaited_once()


def test_parsing_service_routes_to_mcp(monkeypatch, tmp_path):
    settings = _settings(mcp_mineru_enabled=True)
    monkeypatch.setattr("src.core.config.get_config", lambda: settings)
    parse = AsyncMock(
        return_value=McpMineruResult(
            documents=(
                McpParsedDocument(
                    source_path="/in/a.pdf",
                    md_path=str(tmp_path / "a.md"),
                    metadata_path=str(tmp_path / "a.json"),
                ),
            )
        )
    )
    monkeypatch.setattr("src.core.adapters.mcp.mineru.McpMineruClient.parse", parse)

    from src.core.tools.parsing.service import ParseDocumentService

    service = ParseDocumentService(MagicMock())
    batch = asyncio.run(
        service.parse_local_files_and_save(["/in/a.pdf"], str(tmp_path))
    )

    assert list(batch.saved_files) == ["a.pdf"]
    assert batch.saved_files["a.pdf"].md_path == tmp_path / "a.md"
    parse.assert_awaited_once_with(files=["/in/a.pdf"], output_dir=str(tmp_path))


def test_hpocr_settings_build_nested_mcp_config():
    settings = _settings(
        mcp_hpocr_enabled=True,
        mcp_hpocr_url="http://127.0.0.1:36545/mcp",
        mcp_hpocr_tool="annotate",
    )

    assert settings.mcp.hpocr.enabled is True
    assert settings.mcp.hpocr.url == "http://127.0.0.1:36545/mcp"
    assert settings.mcp.hpocr.tool == "annotate"


def test_hpocr_decode_requires_result_list():
    from src.core.adapters.mcp.hpocr import _decode

    with pytest.raises(McpToolError, match="missing 'result'"):
        _decode({})
    with pytest.raises(McpToolError, match="must be a list"):
        _decode({"result": {}})


def test_hpocr_decode_returns_annotations():
    from src.core.adapters.mcp.hpocr import _decode

    annotations = _decode(
        {
            "result": [
                {
                    "hpo_uri": "HP:0001250",
                    "hpo_label": "Seizures",
                    "start": 0,
                    "end": 8,
                    "text_span": "seizures",
                }
            ]
        }
    )

    assert annotations[0].hpo_uri == "HP:0001250"
    assert annotations[0].text_span == "seizures"
