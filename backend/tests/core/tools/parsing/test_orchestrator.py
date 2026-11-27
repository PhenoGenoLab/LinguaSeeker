"""Tests for the remote-only parse orchestrator."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.core.tools.parsing.base import ParserStrategy
from src.core.tools.parsing.contracts import (
    DocumentMetadata,
    MinerULocalBatchOptions,
    PageContent,
    ParseResult,
)
from src.core.tools.parsing.exceptions import MinerUAPIError
from src.core.tools.parsing.orchestrator import DocumentParseOrchestrator
from src.utils.security.ssrf import validate_url_safe as _validate_url_safe


@pytest.fixture
def mock_remote():
    """Create mock remote parser."""
    parser = AsyncMock(spec=ParserStrategy)
    parser.name = "mineru-remote"
    return parser


@pytest.fixture
def sample_result():
    """Create sample parse result."""
    return ParseResult(
        metadata=DocumentMetadata(total_pages=1),
        pages=[PageContent(page_number=1, markdown="test")],
        parser_used="mineru-remote",
    )


@pytest.mark.asyncio
async def test_orchestrator_delegates_to_remote(mock_remote, sample_result):
    """The orchestrator delegates directly to the remote MinerU parser."""
    mock_remote.parse.return_value = sample_result

    orchestrator = DocumentParseOrchestrator(remote=mock_remote)
    result = await orchestrator.parse("test.pdf")

    mock_remote.parse.assert_called_once_with("test.pdf")
    assert result.parser_used == "mineru-remote"


@pytest.mark.asyncio
async def test_orchestrator_propagates_remote_failure(mock_remote):
    """Remote failures surface; there is no local VLM fallback."""
    mock_remote.parse.side_effect = MinerUAPIError("Remote failed")

    orchestrator = DocumentParseOrchestrator(remote=mock_remote)

    with pytest.raises(MinerUAPIError, match="Remote failed"):
        await orchestrator.parse("test.pdf")


@pytest.mark.asyncio
async def test_orchestrator_name(mock_remote):
    """Test orchestrator name property."""
    orchestrator = DocumentParseOrchestrator(remote=mock_remote)
    assert orchestrator.name == "orchestrator"


@pytest.mark.asyncio
async def test_parse_local_files_delegates_to_remote(mock_remote):
    """Regression: factory-created orchestrator.parse_local_files() works."""
    from src.core.tools.parsing.contracts import (
        MinerUBatchStatus,
        MinerULocalBatchParseResult,
    )

    expected = MinerULocalBatchParseResult(
        batch_id="b1",
        status=MinerUBatchStatus(batch_id="b1"),
        results={},
    )
    mock_remote.parse_local_files = AsyncMock(return_value=expected)

    orchestrator = DocumentParseOrchestrator(remote=mock_remote)
    result = await orchestrator.parse_local_files(["/tmp/a.pdf"], options=MinerULocalBatchOptions(data_ids=["a"]))

    assert result is expected
    mock_remote.parse_local_files.assert_awaited_once_with(
        ["/tmp/a.pdf"],
        options=MinerULocalBatchOptions(data_ids=["a"]),
    )


@pytest.mark.asyncio
async def test_parse_local_files_raises_if_remote_lacks_method(mock_remote):
    """Regression: clear error when remote parser doesn't support batch."""
    if hasattr(mock_remote, "parse_local_files"):
        del mock_remote.parse_local_files

    orchestrator = DocumentParseOrchestrator(remote=mock_remote)

    with pytest.raises(AttributeError, match="does not support parse_local_files"):
        await orchestrator.parse_local_files(["/tmp/a.pdf"], options=MinerULocalBatchOptions())


def test_validate_url_safe_rejects_loopback():
    with pytest.raises(ValueError, match="private/reserved"):
        _validate_url_safe("http://127.0.0.1/admin")


def test_validate_url_safe_rejects_private_10():
    with pytest.raises(ValueError, match="private/reserved"):
        _validate_url_safe("http://10.0.0.1/file.pdf")


def test_validate_url_safe_rejects_private_192():
    with pytest.raises(ValueError, match="private/reserved"):
        _validate_url_safe("http://192.168.1.1/file.pdf")


def test_validate_url_safe_rejects_private_172():
    with pytest.raises(ValueError, match="private/reserved"):
        _validate_url_safe("http://172.16.0.1/file.pdf")


def test_validate_url_safe_rejects_link_local():
    with pytest.raises(ValueError, match="private/reserved"):
        _validate_url_safe("http://169.254.169.254/latest/meta-data/")


def test_validate_url_safe_rejects_ipv6_loopback():
    with pytest.raises(ValueError, match="private/reserved"):
        _validate_url_safe("http://[::1]/file.pdf")


def test_validate_url_safe_rejects_unsupported_scheme():
    with pytest.raises(ValueError, match="Unsupported URL scheme"):
        _validate_url_safe("ftp://example.com/file.pdf")


def test_validate_url_safe_allows_public_url():
    """Public URLs should not raise."""
    _validate_url_safe("https://example.com/paper.pdf")
