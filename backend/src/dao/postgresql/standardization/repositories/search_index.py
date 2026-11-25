"""Read-model refresh hooks used after standardization persistence."""

from __future__ import annotations

from typing import Any
from uuid import UUID


class SearchIndexRepository:
    """Refresh profile and search read models for a standardized document."""

    def __init__(self, session: Any) -> None:
        self.session = session

    async def refresh_literature_profile(
        self,
        source_document_id: str,
        owner_user_id: str | None = None,
    ) -> None:
        """Refresh the literature_profiles read model for a document."""
        from src.dao.postgresql.literature_profile_repo import LiteratureProfileRepository

        profile_repo = LiteratureProfileRepository(self.session)
        await profile_repo.refresh_for_document(UUID(source_document_id), owner_user_id=owner_user_id)

    async def refresh_search_index(self) -> None:
        """Refresh the frontend_search_index read model."""
        from src.dao.postgresql.search_index_repo import SearchIndexRepository as SearchIndexReadModel

        index_repo = SearchIndexReadModel(self.session)
        await index_repo.refresh()
