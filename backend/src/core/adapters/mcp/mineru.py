"""MinerU parsing through an external MCP server.

Expected tool contract (JSON object result):

    {"documents": [{"source_path": "...", "md_path": "...",
                    "metadata_path": "...", "images_dir": "...", "pages": 12}],
     "failed": ["name.pdf"]}

``source_path``/``md_path``/``metadata_path`` are required per document;
``images_dir`` and ``pages`` are optional. The tool receives ``files`` and
``output_dir``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.adapters.mcp.server import McpToolClient, McpToolError
from src.core.config import Settings


@dataclass(frozen=True)
class McpParsedDocument:
    """One parsed artifact set returned by the MCP MinerU tool."""

    source_path: str
    md_path: str
    metadata_path: str
    images_dir: str | None = None
    pages: int | None = None


@dataclass(frozen=True)
class McpMineruResult:
    """Decoded result of one MinerU parse call."""

    documents: tuple[McpParsedDocument, ...]
    failed: tuple[str, ...] = ()


class McpMineruClient:
    """Thin adapter over the MinerU MCP server."""

    def __init__(self, cfg: Settings):
        self._client = McpToolClient(cfg.mcp.mineru, name="mineru")

    async def parse(self, *, files: list[str], output_dir: str) -> McpMineruResult:
        """Parse the given files through the MCP tool."""
        payload = await self._client.call({"files": files, "output_dir": output_dir})
        return _decode(payload)


def _decode(payload: dict[str, Any]) -> McpMineruResult:
    raw_documents = payload.get("documents") or []
    if not isinstance(raw_documents, list):
        raise McpToolError("mineru MCP result 'documents' must be a list")

    documents: list[McpParsedDocument] = []
    for raw in raw_documents:
        if not isinstance(raw, dict):
            raise McpToolError("mineru MCP result contains a non-object document")
        source_path = str(raw.get("source_path") or "").strip()
        md_path = str(raw.get("md_path") or "").strip()
        metadata_path = str(raw.get("metadata_path") or "").strip()
        if not (source_path and md_path and metadata_path):
            raise McpToolError("mineru MCP document requires source_path, md_path, and metadata_path")
        pages = raw.get("pages")
        documents.append(
            McpParsedDocument(
                source_path=source_path,
                md_path=md_path,
                metadata_path=metadata_path,
                images_dir=_optional(raw.get("images_dir")),
                pages=int(pages) if isinstance(pages, int) else None,
            )
        )

    raw_failed = payload.get("failed") or []
    failed = tuple(str(item) for item in raw_failed) if isinstance(raw_failed, list) else ()
    return McpMineruResult(documents=tuple(documents), failed=failed)


def _optional(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
