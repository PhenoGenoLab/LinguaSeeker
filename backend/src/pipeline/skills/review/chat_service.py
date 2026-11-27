"""Conversation persistence service for evidence review chat sessions."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger

from src.core.tools.review.contracts import (
    ChatAction,
    ChatMessageResponse,
    ChatSessionResponse,
)
from src.ports.chat import ChatStore
from src.ports.review import FeedbackStore

if TYPE_CHECKING:
    from src.pipeline.skills.review.providers import ChatLLMProvider

_SESSION_TITLE_MAX_CHARS = 80
_SESSION_TITLE_SYSTEM_PROMPT = (
    "Generate a concise chat session title for Lingua Seeker. "
    "Use the same language as the user message. Return only the title, "
    "without quotes, markdown, trailing punctuation, or explanation. "
    "Keep it under 8 words."
)


class ChatService:
    """Persist chat sessions and messages; generate session titles."""

    def __init__(
        self,
        store: ChatStore,
        chat_provider: ChatLLMProvider | None = None,
        feedback_store: FeedbackStore | None = None,
    ):
        self._store = store
        self._chat_provider = chat_provider
        self._feedback_store = feedback_store

    async def create_session(
        self,
        *,
        processing_run_id: UUID | None,
        user_id: UUID | None = None,
    ) -> ChatSessionResponse:
        """Create a new chat session, optionally bound to a processing run."""
        return await self._store.create_session(
            processing_run_id=processing_run_id,
            user_id=user_id,
        )

    async def ensure_session(
        self,
        *,
        session_id: UUID,
        owner_user_id: UUID | None = None,
    ) -> None:
        """Ensure a chat session exists and belongs to the caller."""
        await self._store.require_session(session_id=session_id, owner_user_id=owner_user_id)

    async def get_session(
        self,
        *,
        session_id: UUID,
        owner_user_id: UUID | None = None,
    ) -> ChatSessionResponse:
        """Fetch one chat session with its message count."""
        return await self._store.get_session(session_id=session_id, owner_user_id=owner_user_id)

    async def append_message(
        self,
        *,
        session_id: UUID,
        role: str,
        content: str,
        evidence_id: UUID | None = None,
        entity_id: UUID | None = None,
        action: ChatAction | None = None,
        owner_user_id: UUID | None = None,
    ) -> ChatMessageResponse:
        """Append a message to a chat session."""
        return await self._store.append_message(
            session_id=session_id,
            role=role,
            content=content,
            evidence_id=evidence_id,
            entity_id=entity_id,
            action=action,
            owner_user_id=owner_user_id,
        )

    async def generate_session_title(
        self,
        *,
        session_id: UUID,
        user_message: str,
    ) -> None:
        """Generate a title for a session that does not already have one."""
        chat_session = await self._store.get_session(session_id=session_id)
        if chat_session.title:
            return

        provider = self._chat_provider
        if provider is None:
            logger.warning(
                "ChatService session title generation skipped without injected provider. "
                "Fix: inject via ReviewServiceFactory.create_chat_service()"
            )
            return

        try:
            raw_title = await provider.generate(
                system_prompt=_SESSION_TITLE_SYSTEM_PROMPT,
                user_message=user_message[:1000],
            )
        except Exception as exc:
            logger.warning("Chat session title generation failed: {}", exc)
            return

        title = self._clean_session_title(raw_title)
        if not title:
            return
        await self._store.set_title(session_id=session_id, title=title)

    async def list_messages(
        self,
        *,
        session_id: UUID,
        limit: int = 100,
        owner_user_id: UUID | None = None,
    ) -> list[ChatMessageResponse]:
        """List messages in a session, ordered chronologically."""
        return await self._store.list_messages(
            session_id=session_id,
            limit=limit,
            owner_user_id=owner_user_id,
        )

    async def list_sessions(
        self,
        *,
        processing_run_id: UUID,
        owner_user_id: UUID | None = None,
    ) -> list[ChatSessionResponse]:
        """List all chat sessions for a processing run."""
        return await self._store.list_sessions(
            processing_run_id=processing_run_id,
            owner_user_id=owner_user_id,
        )

    async def recent_history(
        self,
        *,
        session_id: UUID,
        limit: int = 10,
    ):
        """Return recent messages for routing context."""
        return await self._store.recent_history(session_id=session_id, limit=limit)

    @staticmethod
    def _clean_session_title(raw_title: str) -> str:
        """Normalize an LLM-generated session title for sidebar display."""
        title = raw_title.strip()
        title = re.sub(r"^#+\s*", "", title)
        title = re.sub(r"^(title|标题)\s*[:：]\s*", "", title, flags=re.IGNORECASE)
        title = title.strip(" \t\r\n\"'`“”‘’。.!！")
        title = re.sub(r"\s+", " ", title)
        if len(title) > _SESSION_TITLE_MAX_CHARS:
            title = title[:_SESSION_TITLE_MAX_CHARS].rstrip()
        return title

    async def build_evidence_context(
        self,
        *,
        canonical_evidence_id: UUID,
        owner_user_id: UUID | None = None,
    ) -> str:
        """Build the evidence context block for the supervisor."""
        return await self._store.evidence_context(
            canonical_evidence_id=canonical_evidence_id,
            owner_user_id=owner_user_id,
        )

    _CORRECTION_FIELD_ALIASES: dict[str, str] = {
        "gene": "gene",
        "基因": "gene",
        "variant": "variant",
        "变异": "variant",
        "突变": "variant",
        "disease": "disease",
        "疾病": "disease",
        "classification": "classification",
        "分类": "classification",
        "phenotype": "phenotype",
        "表型": "phenotype",
        "evidence_strength": "evidence_strength",
        "evidence_type": "evidence_type",
        "functional_impact": "functional_impact",
        "inheritance_pattern": "inheritance_pattern",
        "zygosity": "zygosity",
        "summary": "summary",
        "摘要": "summary",
        "references": "references",
    }

    _CORRECTION_PATTERNS_PARSE: list[re.Pattern[str]] = [
        re.compile(
            r"(?:change|update|correct|set|modify)\s+"
            r"(?P<field>[a-z_\u4e00-\u9fff]+)\s+"
            r"(?:to|as|=)\s+"
            r"(?P<value>.+)",
            re.IGNORECASE,
        ),
        re.compile(
            r"(?:把|将)?\s*"
            r"(?P<field>[a-z_\u4e00-\u9fff]+)\s*"
            r"(?:改为|修改为|改成|设为|更新为)\s*"
            r"(?P<value>.+)",
        ),
    ]

    @classmethod
    def _parse_correction_message(cls, message: str) -> dict[str, str]:
        """Parse a correction message into {card_field: new_value}."""
        for pattern in cls._CORRECTION_PATTERNS_PARSE:
            match = pattern.search(message)
            if match:
                raw_field = match.group("field").strip().lower()
                value = match.group("value").strip().rstrip(".,;。；")
                card_field = cls._CORRECTION_FIELD_ALIASES.get(raw_field)
                if card_field and value:
                    return {card_field: value}
        return {}

    async def apply_correction(
        self,
        *,
        evidence_id: UUID,
        user_message: str,
        reviewer_id: UUID | None = None,
        owner_user_id: UUID | None = None,
    ) -> str:
        """Parse the user message and apply a correction through the feedback port."""
        from src.core.tools.review.contracts import EvidencePatchRequest
        from src.utils.exceptions import RecordNotFoundError

        fields = self._parse_correction_message(user_message)
        if not fields:
            return (
                "I couldn't parse a field correction from your message. "
                'Try: "change gene to BRCA2" or "把分类改为 pathogenic". '
                "You can also use the Edit button on the evidence detail page."
            )

        try:
            patch = EvidencePatchRequest(
                fields=fields,
                change_reason=f"Chat correction: {user_message[:200]}",
            )
            if self._feedback_store is None:
                raise RuntimeError("ChatService requires a feedback store for corrections")
            result = await self._feedback_store.patch_evidence(
                canonical_evidence_id=evidence_id,
                patch=patch,
                reviewer_id=reviewer_id,
                owner_user_id=owner_user_id,
            )
        except RecordNotFoundError:
            return "Correction not applied: that evidence card is not available for this account."
        except ValueError:
            logger.warning("Chat correction rejected for evidence {}", evidence_id)
            return "Correction rejected: the requested field or value is not editable."
        except Exception:
            logger.exception("Chat correction failed for evidence {}", evidence_id)
            return "Correction failed due to an internal error. Use the Edit button on the evidence detail page."

        delta_parts = [f"**{d.field}**: ~~{d.old_value}~~ → {d.new_value}" for d in result.field_deltas]
        summary = "\n".join(delta_parts) if delta_parts else "Status updated."
        return (
            f"Correction applied to evidence `{str(evidence_id)[:8]}…`.\n\n"
            f"{summary}\n\n"
            f"Status: {result.old_status.value} → {result.new_status.value}"
        )
