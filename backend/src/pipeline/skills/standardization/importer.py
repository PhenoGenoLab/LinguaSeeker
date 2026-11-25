"""Offline terminology import and embedding build.

These entry points run from operator scripts, not from the request path; the
request-path facade lives in :mod:`src.pipeline.skills.standardization.api`.
"""

from __future__ import annotations

import inspect
import time
from pathlib import Path
from typing import Any

from loguru import logger

from src.core.tools.standardization.contracts import EntityType
from src.core.tools.standardization.importers import (
    ImportBatch,
    build_clinvar_core_tsv,
    iter_clinvar_batches,
    parse_clingen_rows,
    parse_hgnc_rows,
    parse_hpo_rows,
    parse_omim_rows,
)
from src.core.tools.standardization.repositories import (
    StandardizationRepository,
)
from src.dao.postgresql import async_session_factory, build_async_engine, get_async_session


async def _maybe_await(value: Any) -> Any:
    """Await helper results only when they are actually awaitable."""
    if inspect.isawaitable(value):
        return await value
    return value


async def import_terminology(
    *,
    cfg: Any,
    terminology_root: Path,
    version: str,
    sources: list[str],
) -> None:
    """Import local terminology sources through the repository facade."""
    started_at = time.perf_counter()
    source_names = tuple(source.lower() for source in sources)
    logger.info(
        "Starting terminology import: root={}, version={}, sources={}",
        terminology_root,
        version,
        list(source_names),
    )
    batches = _load_import_batches(terminology_root=terminology_root, version=version, sources=source_names)
    total_entries = sum(len(batch.entries) for batch in batches)
    total_aliases = sum(len(batch.aliases) for batch in batches)
    total_relationships = sum(len(batch.relationships) for batch in batches)
    logger.info(
        "Parsed terminology batches: batches={}, entries={}, aliases={}, relationships={}",
        len(batches),
        total_entries,
        total_aliases,
        total_relationships,
    )
    engine = build_async_engine(cfg)
    session_factory = async_session_factory(engine)
    try:
        async with get_async_session(session_factory) as session:
            repository = StandardizationRepository(session)
            for index, batch in enumerate(batches, start=1):
                source_db = _describe_batch_source(batch)
                logger.info(
                    "Importing batch {}/{} [{}]: entries={}, aliases={}, relationships={}",
                    index,
                    len(batches),
                    source_db,
                    len(batch.entries),
                    len(batch.aliases),
                    len(batch.relationships),
                )
                await repository.upsert_terminology_batch(batch)
                logger.info("Imported batch {}/{} [{}]", index, len(batches), source_db)
            if "clinvar" in source_names:
                clinvar_path = _ensure_clinvar_core_path(Path(terminology_root) / "clinvar" / "variant_summary.txt")
                await _maybe_await(
                    _import_clinvar_stream(
                        repository=repository,
                        path=clinvar_path,
                        version=version,
                        chunk_size=10_000,
                    ),
                )
            await session.commit()
            logger.info("Committed terminology import transaction")
    finally:
        await engine.dispose()
    logger.info("Terminology import completed in {:.2f}s", time.perf_counter() - started_at)


async def build_terminology_embeddings(
    *,
    cfg: Any,
    entity_types: set[EntityType] | None = None,
    source_dbs: set[str] | None = None,
) -> int:
    """Build pgvector embeddings for imported terminology entries."""
    from src.core.tools.standardization.similarity_match.indexer import (
        TerminologyEmbeddingIndexer,
    )
    from src.core.tools.standardization.similarity_match.providers import (
        EmbeddingHttpProvider,
        FallbackEmbeddingProvider,
    )

    engine = build_async_engine(cfg)
    session_factory = async_session_factory(engine)
    try:
        async with get_async_session(session_factory) as session:
            local = EmbeddingHttpProvider(
                base_url=cfg.embedding.base_url,
                model=cfg.embedding.model,
                api_key=cfg.embedding.api_key,
                api_style=cfg.embedding.api_style,
            )
            remote = (
                EmbeddingHttpProvider(
                    base_url=cfg.embedding.remote_base_url,
                    model=cfg.embedding.remote_model or cfg.embedding.model,
                    api_keys=cfg.embedding.remote_all_api_keys,
                )
                if cfg.embedding.remote_base_url
                else None
            )

            provider = FallbackEmbeddingProvider(local, remote)
            count = await TerminologyEmbeddingIndexer(session, provider).build(
                embedding_model=cfg.embedding.model,
                batch_size=cfg.embedding.batch_size,
                entity_types=entity_types,
                source_dbs=source_dbs,
            )
            await session.commit()
            return count
    finally:
        await engine.dispose()


def _load_import_batches(
    *,
    terminology_root: Path,
    version: str,
    sources: tuple[str, ...],
) -> tuple[ImportBatch, ...]:
    """Load parsed import batches for the selected source set."""
    batches: list[ImportBatch] = []
    source_root = Path(terminology_root)

    if "hgnc" in sources:
        batches.append(parse_hgnc_rows(source_root / "hgnc" / "hgnc_complete_set.txt", version=version))
    if "omim" in sources:
        batches.append(parse_omim_rows(source_root / "omim", version=version))
    if "hpo" in sources:
        batches.append(parse_hpo_rows(source_root / "hpo", version=version))
    if "clingen" in sources:
        batches.append(parse_clingen_rows(source_root / "clingen", version=version))

    return tuple(batches)


def _describe_batch_source(batch: ImportBatch) -> str:
    """Return a human-readable source label for one parsed batch."""
    if batch.entries:
        return batch.entries[0].source_db
    if batch.aliases:
        return batch.aliases[0].source_db
    if batch.relationships:
        return batch.relationships[0].source_db
    return "empty"


async def _import_clinvar_stream(
    *,
    repository: StandardizationRepository,
    path: Path,
    version: str,
    chunk_size: int,
) -> None:
    """Import ClinVar in bounded chunks to avoid monolithic memory growth."""
    logger.info("Streaming ClinVar import: path={}, chunk_size={}", path, chunk_size)
    chunk_count = 0
    total_entries = 0
    total_aliases = 0
    total_relationships = 0
    for chunk_count, batch in enumerate(
        iter_clinvar_batches(path=path, version=version, chunk_size=chunk_size),
        start=1,
    ):
        total_entries += len(batch.entries)
        total_aliases += len(batch.aliases)
        total_relationships += len(batch.relationships)
        logger.info(
            "Importing ClinVar chunk {}: entries={}, aliases={}, relationships={}",
            chunk_count,
            len(batch.entries),
            len(batch.aliases),
            len(batch.relationships),
        )
        await repository.upsert_terminology_batch(batch)
        await repository.session.commit()
    logger.info(
        "Completed ClinVar streaming import: chunks={}, entries={}, aliases={}, relationships={}",
        chunk_count,
        total_entries,
        total_aliases,
        total_relationships,
    )


def _ensure_clinvar_core_path(path: Path) -> Path:
    """Return the reduced ClinVar TSV path, generating it from raw export when needed."""
    core_path = path.with_name("variant_summary.core.tsv")
    if core_path.exists() and core_path.stat().st_mtime >= path.stat().st_mtime:
        return core_path
    logger.info("Building ClinVar core TSV: source={}, target={}", path, core_path)
    rows_written = build_clinvar_core_tsv(path, core_path)
    logger.info("Built ClinVar core TSV: rows={}", rows_written)
    return core_path
