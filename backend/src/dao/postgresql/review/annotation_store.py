"""PostgreSQL adapter for document annotations."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.dao.postgresql import document_annotation_repo as repo
from src.ports.review import AnnotationRecord


def _record(row: object) -> AnnotationRecord:
    return AnnotationRecord(
        id=row.id,  # type: ignore[attr-defined]
        source_document_id=row.source_document_id,  # type: ignore[attr-defined]
        track=row.track,  # type: ignore[attr-defined]
        paragraph_id=row.paragraph_id,  # type: ignore[attr-defined]
        start_offset=row.start_offset,  # type: ignore[attr-defined]
        end_offset=row.end_offset,  # type: ignore[attr-defined]
        color=row.color,  # type: ignore[attr-defined]
        note=row.note,  # type: ignore[attr-defined]
        author=row.author,  # type: ignore[attr-defined]
        created_at=row.created_at,  # type: ignore[attr-defined]
        updated_at=row.updated_at,  # type: ignore[attr-defined]
    )


class PostgresAnnotationStore:
    """Session-per-operation; writes commit inside the adapter."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def list_annotations(
        self,
        source_document_id: UUID,
        *,
        track: str | None,
        owner_user_id: UUID | None,
    ) -> list[AnnotationRecord]:
        async with self._session_factory() as session:
            rows = await repo.list_annotations(
                session,
                source_document_id,
                track=track,
                owner_user_id=owner_user_id,
            )
            return [_record(row) for row in rows]

    async def get_annotation(
        self,
        annotation_id: UUID,
        *,
        owner_user_id: UUID | None,
    ) -> AnnotationRecord | None:
        async with self._session_factory() as session:
            row = await repo.get_annotation(session, annotation_id, owner_user_id=owner_user_id)
            return _record(row) if row is not None else None

    async def create_annotation(
        self,
        source_document_id: UUID,
        *,
        track: str,
        paragraph_id: str,
        start_offset: int,
        end_offset: int,
        color: str | None,
        note: str | None,
        author: str | None,
        owner_user_id: UUID | None,
    ) -> AnnotationRecord:
        async with self._session_factory() as session:
            row = await repo.create_annotation(
                session,
                source_document_id,
                track=track,
                paragraph_id=paragraph_id,
                start_offset=start_offset,
                end_offset=end_offset,
                color=color,
                note=note,
                author=author,
                owner_user_id=owner_user_id,
            )
            await session.commit()
            return _record(row)

    async def update_annotation(
        self,
        annotation_id: UUID,
        *,
        color: str | None,
        note: str | None,
        update_color: bool,
        update_note: bool,
        owner_user_id: UUID | None,
    ) -> AnnotationRecord:
        async with self._session_factory() as session:
            row = await repo.update_annotation(
                session,
                annotation_id,
                color=color,
                note=note,
                update_color=update_color,
                update_note=update_note,
                owner_user_id=owner_user_id,
            )
            await session.commit()
            return _record(row)

    async def delete_annotation(
        self,
        annotation_id: UUID,
        *,
        owner_user_id: UUID | None,
    ) -> None:
        async with self._session_factory() as session:
            await repo.delete_annotation(session, annotation_id, owner_user_id=owner_user_id)
            await session.commit()
