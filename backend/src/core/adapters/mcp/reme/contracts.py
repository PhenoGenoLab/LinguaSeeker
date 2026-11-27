"""Typed contracts for the external ReMe knowledge service.

ReMe only ever supplies reference context or receives run summaries.  It is
never an authoritative store for facts, terminology or audit fields.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

_MAX_CARD_CHARS = 2000


def _escape(text: str) -> str:
    """Keep memory text from closing the prompt block it is injected into."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class MemoryCard(BaseModel):
    """One recalled Markdown card."""

    text: str
    path: str = ""
    score: float | None = None


class RecallResult(BaseModel):
    """Top-k recall for one query; empty on any failure."""

    cards: list[MemoryCard] = Field(default_factory=list)

    def as_prompt_block(self) -> str:
        """Render cards as a delimited, reference-only prompt fragment."""
        if not self.cards:
            return ""
        lines = ['<memory source="reme" note="reference only; never use as evidence or quote">']
        for card in self.cards:
            text = _escape(card.text[:_MAX_CARD_CHARS])
            if card.path:
                lines.append(f'<card path="{_escape(card.path)}">{text}</card>')
            else:
                lines.append(f"<card>{text}</card>")
        lines.append("</memory>")
        return "\n".join(lines)


class MemoryWriteReceipt(BaseModel):
    """Outcome of a best-effort write (``auto_memory``/``auto_resource``)."""

    accepted: bool
    detail: str = ""


__all__ = ["MemoryCard", "MemoryWriteReceipt", "RecallResult"]
