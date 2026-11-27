"""Chat PDF parsing routes through the remote MinerU batch parser."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_chat_pdf_uses_remote_mineru_batch(async_client: AsyncClient):
    """POST /api/v1/chat/files/parse calls the remote batch parser, not local VLM."""
    parsed = SimpleNamespace(full_markdown="# Parsed article", total_pages=2)
    batch = SimpleNamespace(results={"paper.pdf": parsed})
    fake_parser = SimpleNamespace(parse_local_files=AsyncMock(return_value=batch))

    with patch("src.api.v1.chat.get_remote_parser", return_value=fake_parser):
        response = await async_client.post(
            "/api/v1/chat/files/parse",
            files={"file": ("paper.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["content"] == "# Parsed article"
    assert data["page_count"] == 2
    fake_parser.parse_local_files.assert_awaited_once()
