"""Terminology import and alias lookup persistence."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.core.tools.standardization.contracts import EntityType, TerminologyCandidate
from src.core.tools.standardization.importers import ImportBatch
from src.core.tools.standardization.normalizers import normalize_lookup_text
from ._shared import normalize_entity_text
from src.dao.postgresql.models import (
    TerminologyAlias,
    TerminologyEntry,
    TerminologyRelationship,
)

RELATIONSHIP_SUBJECT_TYPE = {
    "gene_associated_with_disease": EntityType.GENE,
    "phenotype_associated_with_gene": EntityType.PHENOTYPE,
    "phenotype_associated_with_disease": EntityType.PHENOTYPE,
    "variant_associated_with_disease": EntityType.VARIANT,
    "variant_has_clinical_significance": EntityType.VARIANT,
    "gene_has_dosage_sensitivity": EntityType.GENE,
}

RELATIONSHIP_OBJECT_TYPE = {
    "gene_associated_with_disease": EntityType.DISEASE,
    "phenotype_associated_with_gene": EntityType.GENE,
    "phenotype_associated_with_disease": EntityType.DISEASE,
    "variant_associated_with_disease": EntityType.DISEASE,
    "variant_has_clinical_significance": None,
    "gene_has_dosage_sensitivity": None,
}

# Conflict targets and updatable columns per terminology table. Both the
# RETURNING-based bulk path and the COPY staging path build their upserts from
# these, so a schema change is a single edit.
_ENTRY_CONFLICT_CONSTRAINT = "uq_terminology_entries_source_external_id"
_ENTRY_UPDATABLE_COLUMNS = (
    "entity_type",
    "display_name",
    "normalized_name",
    "aliases",
    "raw_payload",
    "version",
)
_ALIAS_CONFLICT_CONSTRAINT = "uq_terminology_aliases_entry_alias_type"
_ALIAS_UPDATABLE_COLUMNS = ("entity_type", "alias_text", "source_db")
_RELATIONSHIP_CONFLICT_COLUMNS = ("subject_entry_id", "object_entry_id", "relationship_type", "source_db")
_RELATIONSHIP_UPDATABLE_COLUMNS = ("evidence_level", "raw_payload")


def _excluded_assignments(columns: tuple[str, ...]) -> str:
    """Render ``column = EXCLUDED.column`` assignments for raw upsert SQL."""
    return ",\n                    ".join(f"{column} = EXCLUDED.{column}" for column in columns)


class TerminologyImportRepository:
    """Persist terminology entries, aliases, and relationships."""

    def __init__(self, session: Any) -> None:
        self.session = session

    async def find_alias_candidates(
        self,
        entity_type: EntityType,
        raw_text: str,
    ) -> tuple[TerminologyCandidate, ...]:
        """Query terminology aliases by normalized alias text and entity type."""
        normalized_alias = normalize_entity_text(entity_type, raw_text)
        statement = (
            select(
                TerminologyEntry.entry_id,
                TerminologyEntry.entity_type,
                TerminologyEntry.source_db,
                TerminologyEntry.external_id,
                TerminologyEntry.display_name,
                TerminologyAlias.normalized_alias,
                TerminologyAlias.alias_type,
                TerminologyEntry.raw_payload,
            )
            .join(TerminologyAlias, TerminologyAlias.entry_id == TerminologyEntry.entry_id)
            .where(TerminologyAlias.entity_type == entity_type.value)
            .where(TerminologyAlias.normalized_alias == normalized_alias)
        )
        result = await self.session.execute(statement)
        rows = result.mappings().all()
        return tuple(
            TerminologyCandidate(
                entry_id=str(row["entry_id"]),
                entity_type=EntityType(row["entity_type"]),
                source_db=str(row["source_db"]),
                external_id=str(row["external_id"]),
                display_name=str(row["display_name"]),
                normalized_alias=str(row["normalized_alias"]),
                alias_type=str(row["alias_type"]),
                raw_payload=dict(row["raw_payload"] or {}),
            )
            for row in rows
        )

    async def upsert_terminology_batch(self, batch: ImportBatch) -> None:
        """Persist a parsed terminology batch."""
        if self._supports_bulk_terminology_upsert():
            await self._bulk_upsert_terminology_batch(batch)
            return

        entries_by_external_id: dict[str, TerminologyEntry] = {}

        for entry in batch.entries:
            existing = await self._find_entry_by_external_id(entry.external_id)
            if existing is None:
                existing = TerminologyEntry(
                    entity_type=entry.entity_type.value,
                    source_db=entry.source_db,
                    external_id=entry.external_id,
                    display_name=entry.display_name,
                    normalized_name=entry.normalized_name,
                    aliases=list(entry.aliases),
                    raw_payload=entry.raw_payload,
                    version=entry.version,
                )
                self.session.add(existing)
            else:
                existing.entity_type = entry.entity_type.value
                existing.source_db = entry.source_db
                existing.display_name = entry.display_name
                existing.normalized_name = entry.normalized_name
                existing.aliases = list(entry.aliases)
                existing.raw_payload = entry.raw_payload
                existing.version = entry.version
            entries_by_external_id[entry.external_id] = existing

        await self.session.flush()

        for alias in batch.aliases:
            entry = entries_by_external_id.get(alias.external_id)
            if entry is None:
                entry = await self._resolve_entry_by_reference(alias.external_id, alias.entity_type)
            if entry is None:
                continue
            existing_alias = await self._find_alias(entry.entry_id, alias.normalized_alias, alias.alias_type)
            if existing_alias is None:
                self.session.add(
                    TerminologyAlias(
                        entry_id=entry.entry_id,
                        entity_type=alias.entity_type.value,
                        alias_text=alias.alias_text,
                        normalized_alias=alias.normalized_alias,
                        alias_type=alias.alias_type,
                        source_db=alias.source_db,
                    ),
                )
            else:
                existing_alias.alias_text = alias.alias_text
                existing_alias.entity_type = alias.entity_type.value
                existing_alias.source_db = alias.source_db

        await self.session.flush()

        for relationship in batch.relationships:
            subject_type = RELATIONSHIP_SUBJECT_TYPE.get(relationship.relationship_type)
            object_type = RELATIONSHIP_OBJECT_TYPE.get(relationship.relationship_type)
            subject_entry = await self._resolve_entry_by_reference(relationship.subject_external_id, subject_type)
            if subject_entry is None:
                continue
            object_entry = None
            if relationship.object_external_id:
                object_entry = await self._resolve_entry_by_reference(relationship.object_external_id, object_type)
                if object_entry is None:
                    continue

            existing_relationship = await self._find_relationship(
                subject_entry_id=subject_entry.entry_id,
                object_entry_id=object_entry.entry_id if object_entry else None,
                relationship_type=relationship.relationship_type,
                source_db=relationship.source_db,
            )
            if existing_relationship is None:
                self.session.add(
                    TerminologyRelationship(
                        subject_entry_id=subject_entry.entry_id,
                        object_entry_id=object_entry.entry_id if object_entry else None,
                        relationship_type=relationship.relationship_type,
                        source_db=relationship.source_db,
                        evidence_level=relationship.evidence_level,
                        raw_payload=relationship.raw_payload,
                    ),
                )
            else:
                existing_relationship.evidence_level = relationship.evidence_level
                existing_relationship.raw_payload = relationship.raw_payload

    async def _bulk_upsert_terminology_batch(self, batch: ImportBatch) -> None:
        """Persist one terminology batch through PostgreSQL bulk upserts."""
        copy_driver = await self._get_copy_driver_connection()
        if copy_driver is not None:
            entry_id_map = await self._copy_upsert_entries(batch.entries, copy_driver=copy_driver)
            entry_id_map.update(await self._fetch_entry_ids_for_batch(batch, known_external_ids=entry_id_map))
            alias_reference_map = await self._resolve_alias_reference_ids(batch.relationships)
            await self._copy_upsert_aliases(batch.aliases, entry_id_map, copy_driver=copy_driver)
            await self._copy_upsert_relationships(
                batch.relationships,
                entry_id_map,
                alias_reference_map,
                copy_driver=copy_driver,
            )
            return

        entry_id_map = await self._bulk_upsert_entries(batch.entries)
        entry_id_map.update(await self._fetch_entry_ids_for_batch(batch, known_external_ids=entry_id_map))
        alias_reference_map = await self._resolve_alias_reference_ids(batch.relationships)
        await self._bulk_upsert_aliases(batch.aliases, entry_id_map)
        await self._bulk_upsert_relationships(batch.relationships, entry_id_map, alias_reference_map)

    def _supports_bulk_terminology_upsert(self) -> bool:
        """Return whether the bound session speaks PostgreSQL.

        The COPY/bulk path relies on PostgreSQL-only statements, so detect the
        dialect rather than guessing from the session class.
        """
        get_bind = getattr(self.session, "get_bind", None)
        bind = get_bind() if callable(get_bind) else None
        dialect_name = getattr(getattr(bind, "dialect", None), "name", "")
        return dialect_name == "postgresql"

    async def _bulk_upsert_entries(self, entries: tuple[Any, ...]) -> dict[str, Any]:
        """Bulk upsert terminology entries by (source_db, external_id) and return resolved IDs."""
        if not entries:
            return {}
        values = [
            {
                "entity_type": entry.entity_type.value,
                "source_db": entry.source_db,
                "external_id": entry.external_id,
                "display_name": entry.display_name,
                "normalized_name": entry.normalized_name,
                "aliases": list(entry.aliases),
                "raw_payload": entry.raw_payload,
                "version": entry.version,
            }
            for entry in entries
        ]
        statement = pg_insert(TerminologyEntry).values(values)
        statement = statement.on_conflict_do_update(
            constraint=_ENTRY_CONFLICT_CONSTRAINT,
            set_={
                column: getattr(statement.excluded, column)
                for column in _ENTRY_UPDATABLE_COLUMNS
            },
        )
        statement = statement.returning(TerminologyEntry.entry_id, TerminologyEntry.external_id)
        result = await self.session.execute(statement)
        rows = result.all()
        return {external_id: entry_id for entry_id, external_id in rows}

    async def _bulk_upsert_aliases(
        self,
        aliases: tuple[Any, ...],
        entry_id_map: dict[str, Any],
    ) -> None:
        """Bulk upsert terminology aliases by (entry_id, normalized_alias, alias_type)."""
        if not aliases:
            return
        values = []
        for alias in aliases:
            entry_id = entry_id_map.get(alias.external_id)
            if entry_id is None:
                continue
            values.append(
                {
                    "entry_id": entry_id,
                    "entity_type": alias.entity_type.value,
                    "alias_text": alias.alias_text,
                    "normalized_alias": alias.normalized_alias,
                    "alias_type": alias.alias_type,
                    "source_db": alias.source_db,
                },
            )
        if not values:
            return
        statement = pg_insert(TerminologyAlias).values(values)
        statement = statement.on_conflict_do_update(
            constraint=_ALIAS_CONFLICT_CONSTRAINT,
            set_={
                column: getattr(statement.excluded, column)
                for column in _ALIAS_UPDATABLE_COLUMNS
            },
        )
        await self.session.execute(statement)

    async def _bulk_upsert_relationships(
        self,
        relationships: tuple[Any, ...],
        entry_id_map: dict[str, Any],
        alias_reference_map: dict[tuple[str, str], Any],
    ) -> None:
        """Bulk upsert terminology relationships by unique identity tuple."""
        if not relationships:
            return
        values = []
        for relationship in relationships:
            subject_entry_id = self._resolve_bulk_reference_id(
                relationship.subject_external_id,
                RELATIONSHIP_SUBJECT_TYPE.get(relationship.relationship_type),
                entry_id_map,
                alias_reference_map,
            )
            if subject_entry_id is None:
                continue
            object_entry_id = None
            if relationship.object_external_id:
                object_entry_id = self._resolve_bulk_reference_id(
                    relationship.object_external_id,
                    RELATIONSHIP_OBJECT_TYPE.get(relationship.relationship_type),
                    entry_id_map,
                    alias_reference_map,
                )
                if object_entry_id is None:
                    continue
            values.append(
                {
                    "subject_entry_id": subject_entry_id,
                    "object_entry_id": object_entry_id,
                    "relationship_type": relationship.relationship_type,
                    "source_db": relationship.source_db,
                    "evidence_level": relationship.evidence_level,
                    "raw_payload": relationship.raw_payload,
                },
            )
        if not values:
            return
        statement = pg_insert(TerminologyRelationship).values(values)
        statement = statement.on_conflict_do_update(
            index_elements=[
                getattr(TerminologyRelationship, column)
                for column in _RELATIONSHIP_CONFLICT_COLUMNS
            ],
            set_={
                column: getattr(statement.excluded, column)
                for column in _RELATIONSHIP_UPDATABLE_COLUMNS
            },
        )
        await self.session.execute(statement)

    async def _copy_upsert_entries(
        self,
        entries: tuple[Any, ...],
        *,
        copy_driver: Any,
    ) -> dict[str, Any]:
        """Stage terminology entries through COPY into a temp table before upsert."""
        if not entries:
            return {}
        temp_table = self._temp_table_name("tmp_terminology_entries")
        await self.session.execute(
            text(
                f"""
                CREATE TEMP TABLE {temp_table} (
                    entry_id text NOT NULL,
                    entity_type text NOT NULL,
                    source_db text NOT NULL,
                    external_id text NOT NULL,
                    display_name text NOT NULL,
                    normalized_name text NOT NULL,
                    aliases_json text NOT NULL,
                    raw_payload_json text NOT NULL,
                    version text NOT NULL
                ) ON COMMIT DROP
                """,
            ),
        )
        records = [
            (
                str(uuid4()),
                entry.entity_type.value,
                entry.source_db,
                entry.external_id,
                entry.display_name,
                entry.normalized_name,
                self._json_text(list(entry.aliases)),
                self._json_text(entry.raw_payload),
                entry.version,
            )
            for entry in entries
        ]
        await copy_driver.copy_records_to_table(
            temp_table,
            records=records,
            columns=(
                "entry_id",
                "entity_type",
                "source_db",
                "external_id",
                "display_name",
                "normalized_name",
                "aliases_json",
                "raw_payload_json",
                "version",
            ),
        )
        statement = text(
            f"""
            INSERT INTO terminology_entries (
                entry_id,
                entity_type,
                source_db,
                external_id,
                display_name,
                normalized_name,
                aliases,
                raw_payload,
                version
            )
            SELECT
                entry_id::uuid,
                entity_type,
                source_db,
                external_id,
                display_name,
                normalized_name,
                aliases_json::jsonb,
                raw_payload_json::jsonb,
                version
            FROM {temp_table}
            ON CONFLICT ON CONSTRAINT {_ENTRY_CONFLICT_CONSTRAINT}
            DO UPDATE SET
                {_excluded_assignments(_ENTRY_UPDATABLE_COLUMNS)}
            RETURNING entry_id, external_id
            """,
        )
        result = await self.session.execute(statement)
        rows = result.all()
        return {external_id: entry_id for entry_id, external_id in rows}

    async def _copy_upsert_aliases(
        self,
        aliases: tuple[Any, ...],
        entry_id_map: dict[str, Any],
        *,
        copy_driver: Any,
    ) -> None:
        """Stage terminology aliases through COPY before the real upsert."""
        if not aliases:
            return
        records = []
        seen_conflict_keys: set[tuple[str, str, str]] = set()
        for alias in aliases:
            entry_id = entry_id_map.get(alias.external_id)
            if entry_id is None:
                continue
            conflict_key = (str(entry_id), alias.normalized_alias, alias.alias_type)
            if conflict_key in seen_conflict_keys:
                continue
            seen_conflict_keys.add(conflict_key)
            records.append(
                (
                    str(uuid4()),
                    str(entry_id),
                    alias.entity_type.value,
                    alias.alias_text,
                    alias.normalized_alias,
                    alias.alias_type,
                    alias.source_db,
                ),
            )
        if not records:
            return
        temp_table = self._temp_table_name("tmp_terminology_aliases")
        await self.session.execute(
            text(
                f"""
                CREATE TEMP TABLE {temp_table} (
                    alias_id text NOT NULL,
                    entry_id text NOT NULL,
                    entity_type text NOT NULL,
                    alias_text text NOT NULL,
                    normalized_alias text NOT NULL,
                    alias_type text NOT NULL,
                    source_db text NOT NULL
                ) ON COMMIT DROP
                """,
            ),
        )
        await copy_driver.copy_records_to_table(
            temp_table,
            records=records,
            columns=(
                "alias_id",
                "entry_id",
                "entity_type",
                "alias_text",
                "normalized_alias",
                "alias_type",
                "source_db",
            ),
        )
        await self.session.execute(
            text(
                f"""
                INSERT INTO terminology_aliases (
                    alias_id,
                    entry_id,
                    entity_type,
                    alias_text,
                    normalized_alias,
                    alias_type,
                    source_db
                )
                SELECT
                    alias_id::uuid,
                    entry_id::uuid,
                    entity_type,
                    alias_text,
                    normalized_alias,
                    alias_type,
                    source_db
                FROM {temp_table}
                ON CONFLICT ON CONSTRAINT {_ALIAS_CONFLICT_CONSTRAINT}
                DO UPDATE SET
                    {_excluded_assignments(_ALIAS_UPDATABLE_COLUMNS)}
                """,
            ),
        )

    async def _copy_upsert_relationships(
        self,
        relationships: tuple[Any, ...],
        entry_id_map: dict[str, Any],
        alias_reference_map: dict[tuple[str, str], Any],
        *,
        copy_driver: Any,
    ) -> None:
        """Stage terminology relationships through COPY before the real upsert."""
        if not relationships:
            return
        records = []
        seen_conflict_keys: set[tuple[str, str | None, str, str]] = set()
        for relationship in relationships:
            subject_entry_id = self._resolve_bulk_reference_id(
                relationship.subject_external_id,
                RELATIONSHIP_SUBJECT_TYPE.get(relationship.relationship_type),
                entry_id_map,
                alias_reference_map,
            )
            if subject_entry_id is None:
                continue
            object_entry_id = None
            if relationship.object_external_id:
                object_entry_id = self._resolve_bulk_reference_id(
                    relationship.object_external_id,
                    RELATIONSHIP_OBJECT_TYPE.get(relationship.relationship_type),
                    entry_id_map,
                    alias_reference_map,
                )
                if object_entry_id is None:
                    continue
            conflict_key = (
                str(subject_entry_id),
                str(object_entry_id) if object_entry_id is not None else None,
                relationship.relationship_type,
                relationship.source_db,
            )
            if conflict_key in seen_conflict_keys:
                continue
            seen_conflict_keys.add(conflict_key)
            records.append(
                (
                    str(uuid4()),
                    str(subject_entry_id),
                    str(object_entry_id) if object_entry_id is not None else None,
                    relationship.relationship_type,
                    relationship.source_db,
                    relationship.evidence_level,
                    self._json_text(relationship.raw_payload),
                ),
            )
        if not records:
            return
        temp_table = self._temp_table_name("tmp_terminology_relationships")
        await self.session.execute(
            text(
                f"""
                CREATE TEMP TABLE {temp_table} (
                    relationship_id text NOT NULL,
                    subject_entry_id text NOT NULL,
                    object_entry_id text NULL,
                    relationship_type text NOT NULL,
                    source_db text NOT NULL,
                    evidence_level text NULL,
                    raw_payload_json text NOT NULL
                ) ON COMMIT DROP
                """,
            ),
        )
        await copy_driver.copy_records_to_table(
            temp_table,
            records=records,
            columns=(
                "relationship_id",
                "subject_entry_id",
                "object_entry_id",
                "relationship_type",
                "source_db",
                "evidence_level",
                "raw_payload_json",
            ),
        )
        await self.session.execute(
            text(
                f"""
                INSERT INTO terminology_relationships (
                    relationship_id,
                    subject_entry_id,
                    object_entry_id,
                    relationship_type,
                    source_db,
                    evidence_level,
                    raw_payload
                )
                SELECT
                    relationship_id::uuid,
                    subject_entry_id::uuid,
                    CASE
                        WHEN object_entry_id IS NULL OR object_entry_id = '' THEN NULL
                        ELSE object_entry_id::uuid
                    END,
                    relationship_type,
                    source_db,
                    evidence_level,
                    raw_payload_json::jsonb
                FROM {temp_table}
                ON CONFLICT ({", ".join(_RELATIONSHIP_CONFLICT_COLUMNS)})
                DO UPDATE SET
                    {_excluded_assignments(_RELATIONSHIP_UPDATABLE_COLUMNS)}
                """,
            ),
        )

    async def _fetch_entry_ids_for_batch(
        self,
        batch: ImportBatch,
        *,
        known_external_ids: dict[str, Any],
    ) -> dict[str, Any]:
        """Resolve DB entry IDs for all external references present in a batch."""
        references = {entry.external_id for entry in batch.entries}
        references.update(alias.external_id for alias in batch.aliases)
        references.update(relationship.subject_external_id for relationship in batch.relationships)
        references.update(
            relationship.object_external_id
            for relationship in batch.relationships
            if relationship.object_external_id is not None and ":" in relationship.object_external_id
        )
        references = {reference for reference in references if reference and reference not in known_external_ids}
        if not references:
            return {}
        statement = select(TerminologyEntry.entry_id, TerminologyEntry.external_id).where(
            TerminologyEntry.external_id.in_(sorted(references)),
        )
        result = await self.session.execute(statement)
        rows = result.all()
        return {external_id: entry_id for entry_id, external_id in rows}

    async def _resolve_alias_reference_ids(
        self,
        relationships: tuple[Any, ...],
    ) -> dict[tuple[str, str], Any]:
        """Resolve non-external relationship references through terminology aliases."""
        refs_by_type: dict[EntityType, dict[str, str]] = defaultdict(dict)
        for relationship in relationships:
            self._collect_alias_reference(
                refs_by_type,
                relationship.subject_external_id,
                RELATIONSHIP_SUBJECT_TYPE.get(relationship.relationship_type),
            )
            if relationship.object_external_id:
                self._collect_alias_reference(
                    refs_by_type,
                    relationship.object_external_id,
                    RELATIONSHIP_OBJECT_TYPE.get(relationship.relationship_type),
                )

        resolved: dict[tuple[str, str], Any] = {}
        for entity_type, originals_by_normalized in refs_by_type.items():
            statement = (
                select(TerminologyAlias.normalized_alias, TerminologyAlias.entry_id)
                .where(TerminologyAlias.entity_type == entity_type.value)
                .where(TerminologyAlias.normalized_alias.in_(sorted(originals_by_normalized)))
            )
            result = await self.session.execute(statement)
            for normalized_alias, entry_id in result.all():
                original_reference = originals_by_normalized.get(str(normalized_alias))
                if original_reference is None:
                    continue
                resolved.setdefault((original_reference, entity_type.value), entry_id)
        return resolved

    async def _get_copy_driver_connection(self) -> Any | None:
        """Return the underlying asyncpg driver connection when COPY is available."""
        if not hasattr(self.session, "connection"):
            return None
        async_connection = await self.session.connection()
        if async_connection is None or not hasattr(async_connection, "get_raw_connection"):
            return None
        raw_connection = await async_connection.get_raw_connection()
        driver_connection = getattr(raw_connection, "driver_connection", None)
        if driver_connection is None:
            return None
        if not hasattr(driver_connection, "copy_records_to_table"):
            return None
        return driver_connection

    async def _find_entry_by_external_id(self, external_id: str) -> TerminologyEntry | None:
        """Return an existing terminology entry by external ID."""
        statement = select(TerminologyEntry).where(TerminologyEntry.external_id == external_id)
        return (await self.session.execute(statement)).scalars().first()

    async def _find_alias(
        self,
        entry_id,
        normalized_alias: str,
        alias_type: str,
    ) -> TerminologyAlias | None:
        """Return an existing terminology alias row when present."""
        statement = select(TerminologyAlias).where(
            TerminologyAlias.entry_id == entry_id,
            TerminologyAlias.normalized_alias == normalized_alias,
            TerminologyAlias.alias_type == alias_type,
        )
        return (await self.session.execute(statement)).scalars().first()

    async def _find_relationship(
        self,
        *,
        subject_entry_id,
        object_entry_id,
        relationship_type: str,
        source_db: str,
    ) -> TerminologyRelationship | None:
        """Return an existing terminology relationship row when present."""
        statement = select(TerminologyRelationship).where(
            TerminologyRelationship.subject_entry_id == subject_entry_id,
            TerminologyRelationship.object_entry_id == object_entry_id,
            TerminologyRelationship.relationship_type == relationship_type,
            TerminologyRelationship.source_db == source_db,
        )
        return (await self.session.execute(statement)).scalars().first()

    async def _resolve_entry_by_reference(
        self,
        reference: str,
        entity_type: EntityType | None,
    ) -> TerminologyEntry | None:
        """Resolve an entry by external ID or by terminology alias."""
        if ":" in reference:
            return await self._find_entry_by_external_id(reference)

        normalized_reference = (
            normalize_entity_text(entity_type, reference) if entity_type is not None else normalize_lookup_text(reference)
        )
        statement = (
            select(TerminologyEntry)
            .join(TerminologyAlias, TerminologyAlias.entry_id == TerminologyEntry.entry_id)
            .where(TerminologyAlias.normalized_alias == normalized_reference)
        )
        if entity_type is not None:
            statement = statement.where(TerminologyAlias.entity_type == entity_type.value)
        return (await self.session.execute(statement)).scalars().first()

    def _collect_alias_reference(
        self,
        refs_by_type: dict[EntityType, dict[str, str]],
        reference: str,
        entity_type: EntityType | None,
    ) -> None:
        """Collect one unresolved alias reference keyed by normalized text and type."""
        if not reference or ":" in reference or entity_type is None:
            return
        normalized_reference = normalize_entity_text(entity_type, reference)
        refs_by_type[entity_type].setdefault(normalized_reference, reference)

    def _resolve_bulk_reference_id(
        self,
        reference: str,
        entity_type: EntityType | None,
        entry_id_map: dict[str, Any],
        alias_reference_map: dict[tuple[str, str], Any],
    ) -> Any | None:
        """Resolve one bulk-reference ID from external-ID and alias lookup maps."""
        if not reference:
            return None
        if ":" in reference:
            return entry_id_map.get(reference)
        if entity_type is None:
            return None
        return alias_reference_map.get((reference, entity_type.value))

    def _temp_table_name(self, prefix: str) -> str:
        """Return a unique temporary table name with a stable prefix."""
        return f"{prefix}_{uuid4().hex}"

    def _json_text(self, payload: Any) -> str:
        """Serialize staging payloads for COPY temp tables."""
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
