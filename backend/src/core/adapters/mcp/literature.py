"""Literature acquisition through an external MCP server.

Expected tool contract (JSON object result):

    {"documents": [{"path": "...", "title": "...", "sha256": "...",
                    "pmid": "...", "doi": "..."}],
     "warnings": ["..."]}

Only ``path`` is required per document. The tool receives
``action``/``query``/``identifiers``/``limit``/``language``/``relevance_gate``/
``literature_types``/``download_dir``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.adapters.mcp.server import McpToolClient, McpToolError
from src.core.config import Settings


@dataclass(frozen=True)
class McpLiteratureDocument:
    """One acquired document returned by the MCP literature tool."""

    path: str
    title: str | None = None
    sha256: str | None = None
    pmid: str | None = None
    doi: str | None = None


@dataclass(frozen=True)
class McpLiteratureResult:
    """Decoded result of one literature acquisition call."""

    documents: tuple[McpLiteratureDocument, ...]
    warnings: tuple[str, ...] = ()


class McpLiteratureClient:
    """Thin adapter over the literature MCP server."""

    def __init__(self, cfg: Settings):
        self._client = McpToolClient(cfg.mcp.literature, name="literature")

    async def fetch(
        self,
        *,
        action: str,
        query: str | None,
        identifiers: list[str] | None,
        limit: int,
        language: str | None,
        relevance_gate: bool,
        literature_types: list[str] | None,
        download_dir: str,
    ) -> McpLiteratureResult:
        """Search or download literature through the MCP tool."""
        payload = await self._client.call(
            {
                "action": action,
                "query": query,
                "identifiers": identifiers,
                "limit": limit,
                "language": language,
                "relevance_gate": relevance_gate,
                "literature_types": literature_types,
                "download_dir": download_dir,
            }
        )
        return _decode(payload)


def _decode(payload: dict[str, Any]) -> McpLiteratureResult:
    raw_documents = payload.get("documents") or []
    if not isinstance(raw_documents, list):
        raise McpToolError("literature MCP result 'documents' must be a list")

    documents: list[McpLiteratureDocument] = []
    for raw in raw_documents:
        if not isinstance(raw, dict):
            raise McpToolError("literature MCP result contains a non-object document")
        path = str(raw.get("path") or raw.get("file_path") or "").strip()
        if not path:
            raise McpToolError("literature MCP document is missing 'path'")
        documents.append(
            McpLiteratureDocument(
                path=path,
                title=_optional(raw.get("title")),
                sha256=_optional(raw.get("sha256")),
                pmid=_optional(raw.get("pmid")),
                doi=_optional(raw.get("doi")),
            )
        )

    raw_warnings = payload.get("warnings") or []
    warnings = tuple(str(item) for item in raw_warnings) if isinstance(raw_warnings, list) else ()
    return McpLiteratureResult(documents=tuple(documents), warnings=warnings)


def _optional(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
