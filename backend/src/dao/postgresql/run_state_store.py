"""PostgreSQL adapter for pipeline run state.

- ``SessionRunStateStore``: binds a single session (unit tests).
- ``PostgresRunStateStore``: session-per-operation (production).

Nothing outside ``src.dao`` may import this module.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import delete, func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError, ProgrammingError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.runs.contracts import (
    PipelineMode,
    RunSummary,
    derive_error_phase,
    PhaseStatus,
    PipelineGraphState,
    PipelineStatus,
    validate_all_phase_transitions,
    validate_pipeline_status_transition,
)
from src.dao.postgresql.models import (
    CanonicalEvidenceItem,
    EvidenceEntityBinding,
    LiteratureProfile,
    PipelineRunState,
    RunEvidenceItem,
    SourceDocument,
)
from src.utils.text.normalize import concat_document_text
from src.utils.text.render_quality import (
    is_likely_untranslated_render_blocks,
    is_likely_untranslated_render_payload,
)


async def _build_raw_metadata(state: PipelineGraphState) -> dict[str, object]:
    """Extract title/authors from Phase 2 metadata.json for SourceDocument.raw_metadata."""
    meta: dict[str, object] = {}
    if not state.parsing_output or not state.parsing_output.metadata_path:
        return meta
    try:

        def _read() -> dict:
            with open(state.parsing_output.metadata_path, encoding="utf-8") as f:
                return json.load(f)

        acquisition_meta = await asyncio.to_thread(_read)
        if isinstance(acquisition_meta, dict):
            title = acquisition_meta.get("title")
            if title and isinstance(title, str):
                meta["title"] = title
            authors = acquisition_meta.get("authors")
            if authors and isinstance(authors, list):
                meta["authors"] = authors
            journal = acquisition_meta.get("journal")
            if journal and isinstance(journal, str):
                meta["journal"] = journal
    except (OSError, json.JSONDecodeError):
        pass
    return meta


async def _read_doc_json(path: str) -> str | None:
    """Read a Phase 3 JSON file and return concatenated document text."""
    try:

        def _read() -> dict:
            with open(path, encoding="utf-8") as f:
                return json.load(f)

        data = await asyncio.to_thread(_read)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return concat_document_text(data)


async def load_document_text_from_paths(
    original_json_path: str,
    translated_json_path: str,
) -> tuple[str | None, str | None]:
    """Load document text from explicit file paths.

    Use this variant when you have the paths directly (e.g. in the Phase 3
    adapter right after files are written and guaranteed to exist).
    """
    return await _read_doc_json(original_json_path), await _read_doc_json(translated_json_path)


async def _load_phase3_document_text(state: PipelineGraphState) -> tuple[str | None, str | None]:
    """Read Phase 3 JSON files from state and return (original_text, translated_text).

    Returns (None, None) when Phase 3 output is missing or files are unreadable.
    """
    p3 = state.fact_chain_output
    if p3 is None:
        return None, None
    return await load_document_text_from_paths(p3.original_json_path, p3.translated_json_path)


def _is_phase3_rerun(state: PipelineGraphState) -> bool:
    """Return True when a save belongs to a Phase 3-or-earlier rerun."""
    return state.mode == PipelineMode.PHASE and state.target_phase is not None and state.target_phase <= 3


async def _persist_phase3_document_text(
    session: AsyncSession,
    state: PipelineGraphState,
    sd_id: UUID,
) -> None:
    """Write Phase 3 document text and structured blocks to SourceDocument.

    Shared by both SessionRunStateStore and PostgresRunStateStore.
    Only writes when Phase 3 is COMPLETED and the DB doesn't already have text.
    """
    if not (state.fact_chain_output and state.fact_chain_status.status == PhaseStatus.COMPLETED):
        return
    sd = await session.get(SourceDocument, sd_id)
    if sd is None:
        return
    p3 = state.fact_chain_output
    replace_existing = _is_phase3_rerun(state)
    source_language = p3.source_language if p3 is not None else None
    existing_translated_is_stale = is_likely_untranslated_render_payload(
        source_language=source_language,
        original_text=sd.original_text or (p3.original_text if p3 is not None else None),
        translated_text=sd.translated_text,
    )
    existing_translated_blocks_are_stale = is_likely_untranslated_render_blocks(
        source_language=source_language,
        original_blocks=sd.original_blocks or (p3.original_blocks if p3 is not None else None),
        translated_blocks=sd.translated_blocks,
    )
    # The source-fact route retires whole-document translation: clearing a previous
    # full translation on a Phase 3 rerun prevents stale bilingual display payloads.
    if replace_existing and p3.chain_run_path and not p3.translated_text:
        sd.translated_text = None
        sd.translated_blocks = []
        existing_translated_is_stale = False
        existing_translated_blocks_are_stale = False
    needs_original = replace_existing or not sd.original_text
    needs_translated = replace_existing or not sd.translated_text or existing_translated_is_stale
    if needs_original or needs_translated:
        original_text = p3.original_text
        translated_text = p3.translated_text
        if original_text is None and translated_text is None:
            original_text, translated_text = await _load_phase3_document_text(state)
        if needs_original and original_text:
            sd.original_text = original_text
        if needs_translated and translated_text:
            sd.translated_text = translated_text
    if p3.original_blocks and (replace_existing or not sd.original_blocks):
        sd.original_blocks = p3.original_blocks
    if p3.translated_blocks and (replace_existing or not sd.translated_blocks or existing_translated_blocks_are_stale):
        sd.translated_blocks = p3.translated_blocks


def _state_json_without_inline_phase3_data(state: PipelineGraphState) -> dict[str, object]:  # noqa  # dict-return: PipelineGraphState JSONB snapshot.
    """Serialize state for JSONB without mutating the live pipeline state."""
    persisted_state = state.model_copy(deep=True)
    if persisted_state.fact_chain_output is not None:
        persisted_state.fact_chain_output.original_text = None
        persisted_state.fact_chain_output.translated_text = None
        persisted_state.fact_chain_output.original_blocks = None
        persisted_state.fact_chain_output.translated_blocks = None
    return persisted_state.model_dump(mode="json")


async def _reset_phase_rerun_artifacts(
    session: AsyncSession,
    *,
    processing_run_id: str,
    source_document_id: str,
    owner_user_id: str | None = None,
    target_phase: int,
) -> None:
    """Clear stale DB artifacts before re-running a phase in-place."""
    run_id = UUID(processing_run_id)
    doc_id = UUID(source_document_id)
    owner_id = UUID(owner_user_id) if owner_user_id else None
    canonical_owner_filter = (
        CanonicalEvidenceItem.owner_user_id.is_(None)
        if owner_id is None
        else CanonicalEvidenceItem.owner_user_id == owner_id
    )
    profile_owner_filter = (
        LiteratureProfile.owner_user_id.is_(None) if owner_id is None else LiteratureProfile.owner_user_id == owner_id
    )

    if target_phase <= 3:
        source_document = await session.get(SourceDocument, doc_id)
        if source_document is not None:
            source_document.original_text = None
            source_document.translated_text = None
            source_document.original_blocks = None
            source_document.translated_blocks = None

    if target_phase <= 4:
        try:
            from src.dao.postgresql.search_index_repo import frontend_search_index

            canonical_ids = select(CanonicalEvidenceItem.canonical_evidence_id).where(
                CanonicalEvidenceItem.source_document_id == doc_id,
                canonical_owner_filter,
            )
            await session.execute(
                delete(frontend_search_index).where(frontend_search_index.c.canonical_evidence_id.in_(canonical_ids))
            )
        except ProgrammingError:
            # Older deployments may lack the optional search index table. Any
            # other database error must surface: silently keeping stale index
            # rows would make the rerun return deleted evidence.
            logger.warning(
                "frontend_search_index missing; skipped cleanup for run={}",
                run_id,
            )

        run_item_ids = select(RunEvidenceItem.run_evidence_item_id).where(RunEvidenceItem.processing_run_id == run_id)
        await session.execute(
            update(CanonicalEvidenceItem)
            .where(CanonicalEvidenceItem.current_best_run_evidence_id.in_(run_item_ids))
            .values(current_best_run_evidence_id=None)
        )
        await session.execute(
            delete(EvidenceEntityBinding).where(EvidenceEntityBinding.run_evidence_item_id.in_(run_item_ids))
        )
        await session.execute(delete(RunEvidenceItem).where(RunEvidenceItem.processing_run_id == run_id))
        await session.execute(
            delete(CanonicalEvidenceItem).where(
                CanonicalEvidenceItem.source_document_id == doc_id,
                canonical_owner_filter,
                CanonicalEvidenceItem.review_status == "provisional",
            )
        )
        await session.execute(
            delete(LiteratureProfile).where(
                LiteratureProfile.source_document_id == doc_id,
                profile_owner_filter,
            )
        )


_TERMINAL_PHASE_STATUSES = frozenset({"completed", "skipped"})
_PHASE_KEYS = ("acquisition", "parsing", "fact_chain", "standardization")


def _derive_run_title(sj: dict) -> str | None:
    """Derive a human-readable title from state_json fields."""
    query = sj.get("query")
    if query and isinstance(query, str):
        return query[:120]
    identifiers = sj.get("identifiers")
    if identifiers and isinstance(identifiers, list) and identifiers:
        return ", ".join(str(i) for i in identifiers[:5])
    source_key = sj.get("source_key")
    if source_key and isinstance(source_key, str):
        return source_key[:120]
    upload_path = sj.get("upload_file_path")
    if upload_path and isinstance(upload_path, str):
        from pathlib import PurePosixPath

        return PurePosixPath(upload_path.replace("\\", "/")).name
    return None


def _stage_status_details(sj: dict) -> dict[str, object]:
    """Return current stage-name status details, translating legacy keys."""
    if not any(str(key).startswith("phase_") for key in sj):
        return {key: sj.get(f"{key}_status") for key in _PHASE_KEYS}
    if "phase_4_status" in sj:
        return {
            "acquisition": sj.get("phase_1_status"),
            "parsing": sj.get("phase_2_status"),
            "fact_chain": sj.get("phase_3_status"),
            "standardization": sj.get("phase_4_status"),
        }
    return {
        "acquisition": sj.get("phase_1_status"),
        "parsing": sj.get("phase_1_status"),
        "fact_chain": sj.get("phase_2_status"),
        "standardization": sj.get("phase_3_status"),
    }


def _derive_current_phase(sj: dict) -> str | None:
    """Return the phase key that is currently 'running', or None."""
    for pk, phase_detail in _stage_status_details(sj).items():
        if isinstance(phase_detail, dict) and phase_detail.get("status") == "running":
            return pk
    return None


def _count_completed_phases(sj: dict) -> tuple[int, int]:
    """Count completed/skipped phases and return (completed, total)."""
    total = len(_PHASE_KEYS)
    completed = 0
    for detail in _stage_status_details(sj).values():
        if isinstance(detail, dict) and detail.get("status") in _TERMINAL_PHASE_STATUSES:
            completed += 1
    return completed, total


class SessionRunStateStore:
    """Save/load PipelineGraphState with a fixed session.

    Intended for unit tests with short-lived sessions only.
    """

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(
        self,
        state: PipelineGraphState,
        *,
        owner_worker_id: str | None = None,
        heartbeat_at: datetime | None = None,
    ) -> None:
        # Ensure source_document exists (FK requirement for pipeline_run_states)
        sd_id = UUID(state.source_document_id)
        existing_sd = await self._session.get(SourceDocument, sd_id)
        if not existing_sd:
            raw_meta = await _build_raw_metadata(state)
            self._session.add(SourceDocument(source_document_id=sd_id, raw_metadata=raw_meta))
            await self._session.flush()
        elif state.parsing_output:
            # Update metadata if Phase 2 (parsing) just completed
            new_meta = await _build_raw_metadata(state)
            if new_meta.get("title"):
                existing_sd.raw_metadata = {**existing_sd.raw_metadata, **new_meta}

        await _persist_phase3_document_text(self._session, state, sd_id)

        existing = await self._session.get(PipelineRunState, UUID(state.processing_run_id))
        # ── State transition guard ──
        if existing is not None:
            old_state = PipelineGraphState.model_validate(existing.state_json)
            ctx = f"run={state.processing_run_id}"
            validate_pipeline_status_transition(
                old_state.pipeline_status,
                state.pipeline_status,
                context=ctx,
            )
            validate_all_phase_transitions(old_state, state, context=ctx)
        # ── End state transition guard ──

        state_json = _state_json_without_inline_phase3_data(state)
        owner_id = UUID(state.owner_user_id) if state.owner_user_id else None
        if existing:
            existing.state_json = state_json
            existing.pipeline_status = state.pipeline_status.value
            existing.owner_user_id = owner_id
            if state.source_key is not None:
                existing.source_key = state.source_key
            if owner_worker_id is not None:
                existing.owner_worker_id = owner_worker_id
            if heartbeat_at is not None:
                existing.heartbeat_at = heartbeat_at
        else:
            new_record = PipelineRunState(
                processing_run_id=UUID(state.processing_run_id),
                source_document_id=UUID(state.source_document_id),
                state_json=state_json,
                pipeline_status=state.pipeline_status.value,
                source_key=state.source_key,
                owner_user_id=owner_id,
                owner_worker_id=owner_worker_id,
                heartbeat_at=heartbeat_at,
                batch_id=UUID(state.batch_id) if state.batch_id else None,
                source_directory=state.source_directory,
                relative_path=state.relative_path,
            )
            self._session.add(new_record)
        await self._session.commit()

    async def reset_phase_rerun_artifacts(
        self,
        *,
        processing_run_id: str,
        source_document_id: str,
        owner_user_id: str | None = None,
        target_phase: int,
    ) -> None:
        """Clear stale downstream artifacts before an in-place phase rerun."""
        await _reset_phase_rerun_artifacts(
            self._session,
            processing_run_id=processing_run_id,
            source_document_id=source_document_id,
            owner_user_id=owner_user_id,
            target_phase=target_phase,
        )
        await self._session.commit()

    async def load(self, processing_run_id: str) -> Optional[PipelineGraphState]:
        record = await self._session.get(PipelineRunState, UUID(processing_run_id))
        if record is None:
            return None
        return PipelineGraphState.model_validate(record.state_json)

    async def recover_orphaned_runs(self, *, heartbeat_timeout_seconds: int = 300) -> int:
        """Not supported in unit-test persistence — raises on misuse."""
        raise NotImplementedError(
            "recover_orphaned_runs is not available in SessionRunStateStore; "
            "use PostgresRunStateStore for crash recovery."
        )

    async def heartbeat(self, processing_run_id: str, owner_worker_id: str) -> bool:
        """Not supported in unit-test persistence — raises on misuse."""
        raise NotImplementedError(
            "heartbeat is not available in SessionRunStateStore; "
            "use PostgresRunStateStore for heartbeat refresh."
        )

    async def has_active_source_key(self, source_key: str, owner_user_id: str | None = None) -> bool:
        """Not supported in unit-test persistence — raises on misuse."""
        del owner_user_id
        raise NotImplementedError(
            "has_active_source_key is not available in SessionRunStateStore; "
            "use PostgresRunStateStore for source dedup."
        )

    async def finalize_review(self, processing_run_id: str) -> PipelineGraphState | None:
        """Not supported in unit-test persistence — raises on misuse."""
        raise NotImplementedError(
            "finalize_review is not available in SessionRunStateStore; "
            "use PostgresRunStateStore for review finalization."
        )


class PostgresRunStateStore:
    """Save/load PipelineGraphState with session-per-operation.

    Creates a fresh session for each save()/load() call, avoiding
    stale-session bugs in long-lived contexts (production lifespan).
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def save(
        self,
        state: PipelineGraphState,
        *,
        owner_worker_id: str | None = None,
        heartbeat_at: datetime | None = None,
    ) -> None:
        async with self._session_factory() as session:
            # Ensure source_document exists (FK requirement for pipeline_run_states).
            # Use ON CONFLICT DO_UPDATE to merge metadata in a single round-trip
            # instead of upsert-nothing + conditional get + update (#7 fix).
            sd_id = UUID(state.source_document_id)
            raw_meta = await _build_raw_metadata(state)
            sd_upsert = (
                pg_insert(SourceDocument)
                .values(source_document_id=sd_id, raw_metadata=raw_meta)
                .on_conflict_do_update(
                    index_elements=["source_document_id"],
                    set_={
                        "raw_metadata": SourceDocument.raw_metadata.op("||")(raw_meta),
                    },
                )
            )
            await session.execute(sd_upsert)

            await _persist_phase3_document_text(session, state, sd_id)

            # ── State transition guard ──
            # Load existing state (if any) to validate the transition is legal.
            # This is an extra read per save, but correctness in a medical
            # pipeline is worth the cost.
            existing = await session.get(PipelineRunState, UUID(state.processing_run_id))
            if existing is not None:
                old_state = PipelineGraphState.model_validate(existing.state_json)
                ctx = f"run={state.processing_run_id}"
                validate_pipeline_status_transition(
                    old_state.pipeline_status,
                    state.pipeline_status,
                    context=ctx,
                )
                validate_all_phase_transitions(old_state, state, context=ctx)
            # ── End state transition guard ──

            state_json = _state_json_without_inline_phase3_data(state)
            owner_id = UUID(state.owner_user_id) if state.owner_user_id else None
            upsert_set: dict[str, object] = {
                "state_json": state_json,
                "pipeline_status": state.pipeline_status.value,
                "updated_at": func.now(),
                "owner_user_id": owner_id,
            }
            if state.source_key is not None:
                upsert_set["source_key"] = state.source_key
            if owner_worker_id is not None:
                upsert_set["owner_worker_id"] = owner_worker_id
            if heartbeat_at is not None:
                upsert_set["heartbeat_at"] = heartbeat_at

            stmt = (
                pg_insert(PipelineRunState)
                .values(
                    processing_run_id=UUID(state.processing_run_id),
                    source_document_id=UUID(state.source_document_id),
                    state_json=state_json,
                    pipeline_status=state.pipeline_status.value,
                    source_key=state.source_key,
                    owner_user_id=owner_id,
                    owner_worker_id=owner_worker_id,
                    heartbeat_at=heartbeat_at,
                    batch_id=UUID(state.batch_id) if state.batch_id else None,
                    source_directory=state.source_directory,
                    relative_path=state.relative_path,
                )
                .on_conflict_do_update(
                    index_elements=["processing_run_id"],
                    set_=upsert_set,
                )
            )
            await session.execute(stmt)
            try:
                await session.commit()
            except IntegrityError as exc:
                await session.rollback()
                from src.utils.exceptions import DuplicateRunError

                raise DuplicateRunError(
                    f"A pipeline run is already in progress for source {state.source_key or state.processing_run_id}"
                ) from exc

    async def reset_phase_rerun_artifacts(
        self,
        *,
        processing_run_id: str,
        source_document_id: str,
        owner_user_id: str | None = None,
        target_phase: int,
    ) -> None:
        """Clear stale downstream artifacts before an in-place phase rerun."""
        async with self._session_factory() as session:
            await _reset_phase_rerun_artifacts(
                session,
                processing_run_id=processing_run_id,
                source_document_id=source_document_id,
                owner_user_id=owner_user_id,
                target_phase=target_phase,
            )
            await session.commit()

    async def load(self, processing_run_id: str) -> Optional[PipelineGraphState]:
        async with self._session_factory() as session:
            record = await session.get(PipelineRunState, UUID(processing_run_id))
            if record is None:
                return None
            return PipelineGraphState.model_validate(record.state_json)

    async def recover_orphaned_runs(self, *, heartbeat_timeout_seconds: int = 300) -> int:
        """Mark pipeline runs stuck in non-terminal states as FAILED.

        Only fails runs whose heartbeat is older than the timeout (default 5 minutes).
        Legacy rows without a heartbeat use updated_at as fallback.
        """
        async with self._session_factory() as session:
            now = datetime.now(timezone.utc)
            timeout_cutoff = now - timedelta(seconds=heartbeat_timeout_seconds)

            # Select active runs where heartbeat is stale or missing
            result = await session.execute(
                select(PipelineRunState).where(
                    PipelineRunState.pipeline_status.in_(("pending", "running")),
                    (
                        (PipelineRunState.heartbeat_at < timeout_cutoff)
                        | ((PipelineRunState.heartbeat_at.is_(None)) & (PipelineRunState.updated_at < timeout_cutoff))
                    ),
                )
            )
            records = result.scalars().all()

            count = 0
            for record in records:
                state = PipelineGraphState.model_validate(record.state_json)
                state.pipeline_status = PipelineStatus.FAILED
                state.error_message = "Pipeline heartbeat expired"
                state.error_phase = derive_error_phase(state)
                state.completed_at = now.isoformat()
                record.state_json = state.model_dump(mode="json")
                record.pipeline_status = "failed"
                count += 1

            if count:
                await session.commit()
                logger.warning("Recovered {} orphaned pipeline run(s) with stale heartbeat", count)

            return count

    async def heartbeat(self, processing_run_id: str, owner_worker_id: str) -> bool:
        """Refresh heartbeat for an active run owned by this worker.

        Returns True if the heartbeat was updated (run exists and is owned by this worker).
        """
        async with self._session_factory() as session:
            result = await session.execute(
                update(PipelineRunState)
                .where(
                    PipelineRunState.processing_run_id == UUID(processing_run_id),
                    PipelineRunState.owner_worker_id == owner_worker_id,
                    PipelineRunState.pipeline_status.in_(("pending", "running")),
                )
                .values(heartbeat_at=func.now())
            )
            await session.commit()
            return result.rowcount > 0

    async def has_active_source_key(self, source_key: str, owner_user_id: str | None = None) -> bool:
        """Return True when any pending/running run owns this source key."""
        owner_id = UUID(owner_user_id) if owner_user_id else None
        owner_filter = (
            PipelineRunState.owner_user_id.is_(None) if owner_id is None else PipelineRunState.owner_user_id == owner_id
        )
        async with self._session_factory() as session:
            result = await session.execute(
                select(PipelineRunState.processing_run_id)
                .where(
                    PipelineRunState.source_key == source_key,
                    owner_filter,
                    PipelineRunState.pipeline_status.in_(("pending", "running")),
                )
                .limit(1)
            )
            return result.scalar_one_or_none() is not None

    async def latest_state_for_document(self, source_document_id: str) -> PipelineGraphState | None:
        """Return the newest state for one source document."""
        async with self._session_factory() as session:
            stmt = (
                select(PipelineRunState)
                .where(PipelineRunState.source_document_id == UUID(source_document_id))
                .order_by(PipelineRunState.created_at.desc())
                .limit(1)
            )
            record = (await session.execute(stmt)).scalar_one_or_none()
        if record is None or not record.state_json:
            return None
        return PipelineGraphState.model_validate(record.state_json)

    async def states_for_batch(self, batch_id: str) -> list[PipelineGraphState]:
        """Return every state that belongs to one directory batch."""
        async with self._session_factory() as session:
            stmt = select(PipelineRunState).where(PipelineRunState.batch_id == UUID(batch_id))
            records = (await session.execute(stmt)).scalars().all()
        return [PipelineGraphState.model_validate(r.state_json) for r in records if r.state_json]

    async def list_runs(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        search: str | None = None,
        owner_user_id: str | None = None,
    ) -> tuple[list[RunSummary], int]:
        """List pipeline run summaries ordered by creation time (newest first).

        Returns a (items, total) tuple. Extracts summary fields from the
        JSONB state_json column to avoid full state deserialization.

        Args:
            status: Filter by pipeline_status value.
            search: Case-insensitive substring match on title (state_json).
        """
        from sqlalchemy import String, cast

        owner_id = UUID(owner_user_id) if owner_user_id else None
        owner_filter = (
            PipelineRunState.owner_user_id.is_(None) if owner_id is None else PipelineRunState.owner_user_id == owner_id
        )
        async with self._session_factory() as session:
            base = select(PipelineRunState).where(owner_filter)
            if status:
                base = base.where(PipelineRunState.pipeline_status == status)
            if search:
                pattern = f"%{search}%"
                base = base.where(
                    cast(PipelineRunState.state_json["query"], String).ilike(pattern)
                    | cast(PipelineRunState.state_json["identifiers"], String).ilike(pattern)
                    | cast(PipelineRunState.source_key, String).ilike(pattern)
                )

            count_result = await session.execute(select(func.count()).select_from(base.subquery()))
            total = count_result.scalar() or 0

            stmt = base.order_by(PipelineRunState.created_at.desc()).limit(limit).offset(offset)
            result = await session.execute(stmt)
            records = result.scalars().all()

            items: list[RunSummary] = []
            for record in records:
                sj = record.state_json

                title = _derive_run_title(sj)
                current_phase = _derive_current_phase(sj)
                completed, total_phases = _count_completed_phases(sj)

                items.append(
                    RunSummary(
                        processing_run_id=str(record.processing_run_id),
                        owner_user_id=str(record.owner_user_id) if record.owner_user_id else None,
                        pipeline_status=record.pipeline_status,
                        source_key=record.source_key,
                        started_at=sj.get("started_at"),
                        completed_at=sj.get("completed_at"),
                        title=title,
                        current_phase=current_phase,
                        completed_phases=completed,
                        total_phases=total_phases,
                    )
                )

            return items, total
