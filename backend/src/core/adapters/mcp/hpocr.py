"""HPO concept recognition through the FastHPOCR MCP server.

Expected ``annotate`` result::

    {"result": [{"hpo_uri": "HP:0001250", "hpo_label": "Seizures",
                 "start": 0, "end": 8, "text_span": "seizures"}]}

The client validates the boundary payload and raises ``McpToolError`` when the
service returns a malformed annotation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.core.adapters.mcp.server import McpToolClient, McpToolError
from src.core.config import Settings


@dataclass(frozen=True)
class HpoAnnotation:
    """One HPO concept recognized in the submitted text."""

    hpo_uri: str
    hpo_label: str
    start: int
    end: int
    text_span: str


class McpHpocrClient:
    """Thin adapter over the FastHPOCR MCP ``annotate`` tool."""

    def __init__(self, cfg: Settings):
        self._client = McpToolClient(cfg.mcp.hpocr, name="hpocr")

    async def annotate(self, text: str, *, longest_match: bool = True) -> tuple[HpoAnnotation, ...]:
        """Return HPO annotations for one text."""
        payload = await self._client.call({"text": text, "longest_match": longest_match})
        return _decode(payload)


def _decode(payload: dict[str, Any]) -> tuple[HpoAnnotation, ...]:
    raw_annotations = payload.get("result")
    if raw_annotations is None:
        raise McpToolError("hpocr MCP result is missing 'result'")
    if not isinstance(raw_annotations, list):
        raise McpToolError("hpocr MCP result 'result' must be a list")

    annotations: list[HpoAnnotation] = []
    for raw in raw_annotations:
        if not isinstance(raw, dict):
            raise McpToolError("hpocr MCP result contains a non-object annotation")
        hpo_uri = str(raw.get("hpo_uri") or "").strip()
        hpo_label = str(raw.get("hpo_label") or "").strip()
        text_span = str(raw.get("text_span") or "").strip()
        start = raw.get("start")
        end = raw.get("end")
        if not (hpo_uri.startswith("HP:") and hpo_label and text_span):
            raise McpToolError("hpocr MCP annotation requires hpo_uri, hpo_label, and text_span")
        if not isinstance(start, int) or not isinstance(end, int):
            raise McpToolError("hpocr MCP annotation offsets must be integers")
        annotations.append(
            HpoAnnotation(
                hpo_uri=hpo_uri,
                hpo_label=hpo_label,
                start=start,
                end=end,
                text_span=text_span,
            )
        )
    return tuple(annotations)
