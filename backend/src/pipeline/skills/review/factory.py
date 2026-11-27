"""Phase 5 service factory — thin delegate between API and core services.

Phase 5 (evidence review, chat, audit, source linking) is interactive
request-response, not a LangGraph pipeline node.  This factory provides
the agents-layer boundary so API routes never import core services directly.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger

from src.core.tools.review.delta_audit_service import DeltaAuditService
from src.pipeline.skills.review.chat_service import ChatService
from src.pipeline.skills.review.providers import ChatLLMProvider
from src.pipeline.skills.review.supervisor import Supervisor

if TYPE_CHECKING:
    from src.ports.review import ReviewStores, SourceLinkStore


class ReviewServiceFactory:
    """Creates Phase 5 services from injected store factories.

    Persistence stores are injected by the composition root so this module
    never imports database implementations.
    """

    def __init__(self, *, stores: ReviewStores | None = None):
        self._stores = stores
        self._delta_audit = DeltaAuditService()
        self._chat_provider = ChatLLMProvider()

    @property
    def chat_provider(self) -> ChatLLMProvider:
        return self._chat_provider

    def create_chat_service(self) -> ChatService:
        if self._stores is None:
            raise RuntimeError("ChatService requires configured review stores")
        return ChatService(
            store=self._stores.chat_store(),
            chat_provider=self._chat_provider,
            feedback_store=self._stores.feedback_store(),
        )

    def create_supervisor(self) -> Supervisor:
        """Create the user-facing supervisor with routing and permissions."""
        return Supervisor(
            chat=self.create_chat_service(),
            chat_provider=self._chat_provider,
        )

    def schedule_session_title_generation(
        self,
        *,
        session_id: UUID,
        user_message: str,
    ) -> None:
        """Generate a chat title in a separate DB session without blocking chat."""
        if self._stores is None:
            logger.warning("Chat session title generation skipped: review stores are not configured")
            return

        task = asyncio.create_task(
            self._generate_session_title_in_background(
                session_id=session_id,
                user_message=user_message,
            )
        )
        task.add_done_callback(self._log_background_title_failure)

    async def _generate_session_title_in_background(
        self,
        *,
        session_id: UUID,
        user_message: str,
    ) -> None:
        """Generate and persist a chat title after the message transaction commits."""
        if self._stores is None:
            return

        service = self.create_chat_service()
        await service.generate_session_title(
            session_id=session_id,
            user_message=user_message,
        )

    @staticmethod
    def _log_background_title_failure(task: asyncio.Task[None]) -> None:
        try:
            task.result()
        except asyncio.CancelledError:
            logger.debug("Chat session title generation task was cancelled")
        except Exception as exc:
            logger.warning("Chat session title generation background task failed: {}", exc)

    def create_source_linker(self) -> "SourceLinkStore":
        if self._stores is None:
            raise RuntimeError("Source linking requires configured review stores")
        return self._stores.source_link_store()

    @property
    def delta_audit(self) -> DeltaAuditService:
        return self._delta_audit

    async def close(self) -> None:
        """Close long-lived resources (httpx client)."""
        await self._chat_provider.close()
