"""Evidence projection persistence: run items, bindings, and canonical rows."""

from __future__ import annotations

from collections import defaultdict
from typing import Any
from uuid import UUID

from loguru import logger
from sqlalchemy import String, cast, select, tuple_

from src.core.tools.standardization.contracts import (
    EntityMatch,
    EntityType,
    MatchStatus,
    StandardizationInput,
)
from src.core.tools.standardization.db_ready_gate import (
    DEFAULT_DB_READY_GATE_POLICY,
    DbReadyCandidate,
    DbReadyDecision,
    DbReadyGatePolicy,
    DbReadyGateReport,
    evaluate_db_ready_candidates,
)
from src.core.tools.standardization.normalizers import (
    make_entity_scope_hash,
    make_target_scope_bindings,
)
from src.core.tools.standardization.repositories._shared import (
    CANONICAL_ELIGIBLE_STATUSES,
    CANONICAL_STATUS_PRIORITY,
    CLINVAR_ASSERTION_REVIEW_STATUS,
    CLINVAR_AUTHORITY_RE,
    CanonicalIdentityKey,
    RunItemEntityBindings,
    RunItemSpec,
    hash_payload,
    normalize_enum_like_string,
    sanitize_jsonb_value,
)
from src.dao.postgresql.models import (
    CanonicalEvidenceItem,
    EvidenceEntityBinding,
    NormalizedEntity,
    ProcessingRun,
    RunEvidenceItem,
    SourceDocument,
)


class EvidenceProjectionRepository:
    """Persist run evidence rows, entity bindings, and canonical evidence."""

    # Identity fields that can persist without variant co-location.
    # These represent core facts extractable independently of variant evidence.
    _GATE_IDENTITY_FIELDS: frozenset[str] = frozenset(
        {
            "A.gene_symbol",
            "A.gene_disease_relationship",
            "A.variant_type",
            "A.variant_hgvs_c",
            "A.variant_hgvs_p",
            "B.disease_diagnosis",
            "B.clinical_phenotypes",
            "B.sex",
            "B.age_of_onset",
            "B.case_count",
            "B.mode_of_inheritance_reported",
            "C.inheritance_source",
            "C.de_novo_status",
            "J.clinvar_assertion",
        }
    )

    # Only these fields can make a group passable for identity-field survival.
    # Variant alone (without gene or disease) does not qualify.
    _GATE_ANCHOR_FIELDS: frozenset[str] = frozenset(
        {
            "A.gene_symbol",
            "B.disease_diagnosis",
        }
    )

    def __init__(self, session: Any) -> None:
        self.session = session
        self._run_item_rows: list[tuple[RunEvidenceItem, RunItemSpec]] = []
        self._db_ready_gate_report: DbReadyGateReport | None = None

    @property
    def db_ready_gate_report(self) -> DbReadyGateReport | None:
        """Return the latest DB-ready gate audit report for this repository instance."""
        return self._db_ready_gate_report

    async def ensure_run_parents(
        self,
        *,
        source_document_id: str,
        processing_run_id: str,
        owner_user_id: str | None = None,
    ) -> None:
        """Ensure source document and processing run parent rows exist for FK-safe E2E persistence."""
        owner_id = UUID(owner_user_id) if owner_user_id else None
        source_document = await self.session.get(SourceDocument, source_document_id)
        if source_document is None:
            source_document = SourceDocument(
                source_document_id=source_document_id,
                raw_metadata={},
                latest_processing_run_id=None,
            )
            self.session.add(source_document)
            await self.session.flush()

        processing_run = await self.session.get(ProcessingRun, processing_run_id)
        if processing_run is None:
            processing_run = ProcessingRun(
                processing_run_id=processing_run_id,
                source_document_id=source_document_id,
                owner_user_id=owner_id,
                standardization_version="standardization_e2e",
                input_artifacts={"source": "standardize_entities_e2e"},
                output_artifacts={},
                run_status="completed",
            )
            self.session.add(processing_run)
            await self.session.flush()
        elif processing_run.owner_user_id != owner_id:
            processing_run.owner_user_id = owner_id

        if source_document.latest_processing_run_id != processing_run.processing_run_id:
            source_document.latest_processing_run_id = processing_run.processing_run_id

    async def insert_run_evidence_items(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
    ) -> tuple[str, ...]:
        """Insert run-level evidence items."""
        self._run_item_rows = []
        scope_hashes = self._build_chain_scope_hashes(input_data, matches)
        record_specs = self._build_run_item_specs(input_data, matches, scope_hashes)
        run_items: list[RunEvidenceItem] = []
        owner_id = UUID(input_data.owner_user_id) if input_data.owner_user_id else None

        for spec in record_specs:
            run_item = RunEvidenceItem(
                processing_run_id=input_data.processing_run_id,
                source_document_id=input_data.source_document_id,
                owner_user_id=owner_id,
                track=spec.track,
                field_id=spec.field_id,
                status=spec.status,
                value=sanitize_jsonb_value(spec.value),
                confidence=spec.confidence,
                position_hash=spec.position_hash,
                text_hash=spec.text_hash,
                source_span=sanitize_jsonb_value(spec.source_span),
                entity_scope_hash=spec.entity_scope_hash,
                raw_payload=sanitize_jsonb_value(spec.raw_payload),
            )
            self.session.add(run_item)
            run_items.append(run_item)
            self._run_item_rows.append((run_item, spec))

        await self.session.flush()
        return tuple(str(item.run_evidence_item_id) for item in run_items)

    async def insert_entity_bindings(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
        entity_ids: tuple[str, ...],
    ) -> None:
        """Insert evidence-to-entity bindings."""
        for match, entity_id in zip(matches, entity_ids, strict=False):
            related_rows = self._related_run_rows(match)
            for row in related_rows:
                self.session.add(
                    EvidenceEntityBinding(
                        run_evidence_item_id=row.run_evidence_item_id,
                        entity_id=entity_id,
                        entity_type=match.candidate.entity_type.value,
                        role=match.candidate.role.value,
                        binding_rank=0,
                        raw_entity_text=match.candidate.raw_text,
                    ),
                )
        await self.session.flush()

    @staticmethod
    def _canonical_identity_key(
        source_document_id: object,
        owner_user_id: object,
        field_id: str,
        position_hash: str,
        entity_scope_hash: str,
    ) -> CanonicalIdentityKey:
        """Normalize canonical identity values for in-memory lookup keys."""
        return (
            str(source_document_id),
            str(owner_user_id) if owner_user_id else "",
            field_id,
            position_hash,
            entity_scope_hash,
        )

    async def upsert_canonical_evidence(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
        entity_ids: tuple[str, ...],
    ) -> None:
        """Upsert canonical evidence state."""
        entity_ids_by_candidate_id = {
            match.candidate.candidate_id: entity_id for match, entity_id in zip(matches, entity_ids, strict=False)
        }

        # Batch-load existing canonical items to avoid N+1 SELECT.
        # Chunked to stay under PostgreSQL's 65535 parameter limit
        # (4 cols per tuple → max ~16K tuples; 5000 is a safe margin).
        _BATCH_SIZE = 5000
        eligible_rows = [row for row, _ in self._run_item_rows if row.status in CANONICAL_ELIGIBLE_STATUSES]
        existing_lookup: dict[tuple, CanonicalEvidenceItem] = {}
        owner_id = UUID(input_data.owner_user_id) if input_data.owner_user_id else None
        owner_filter = (
            CanonicalEvidenceItem.owner_user_id.is_(None)
            if owner_id is None
            else CanonicalEvidenceItem.owner_user_id == owner_id
        )
        if eligible_rows:
            identity_tuples = [
                (row.source_document_id, row.field_id, row.position_hash, row.entity_scope_hash)
                for row in eligible_rows
            ]
            for start in range(0, len(identity_tuples), _BATCH_SIZE):
                chunk = identity_tuples[start : start + _BATCH_SIZE]
                batch_stmt = select(CanonicalEvidenceItem).where(
                    owner_filter,
                    tuple_(
                        CanonicalEvidenceItem.source_document_id,
                        CanonicalEvidenceItem.field_id,
                        CanonicalEvidenceItem.position_hash,
                        CanonicalEvidenceItem.entity_scope_hash,
                    ).in_(chunk),
                )
                batch_result = await self.session.execute(batch_stmt)
                for item in batch_result.scalars().all():
                    existing_lookup[
                        self._canonical_identity_key(
                            item.source_document_id,
                            item.owner_user_id,
                            item.field_id,
                            item.position_hash,
                            item.entity_scope_hash,
                        )
                    ] = item

        # Batch-load normalized-entity externals so each canonical payload can
        # populate variant_ids/gene_ids/entity_ids/search_text without an N+1
        # lookup. Chunked to stay under PostgreSQL's parameter limit.
        entity_id_values = [eid for eid in entity_ids_by_candidate_id.values() if eid]
        entity_externals_by_id: dict[str, tuple[str | None, str, str]] = {}
        for start in range(0, len(entity_id_values), _BATCH_SIZE):
            chunk = entity_id_values[start : start + _BATCH_SIZE]
            entity_stmt = select(NormalizedEntity).where(cast(NormalizedEntity.entity_id, String).in_(chunk))
            entity_result = await self.session.execute(entity_stmt)
            for entity in entity_result.scalars().all():
                entity_externals_by_id[str(entity.entity_id)] = (
                    entity.external_id,
                    entity.entity_type,
                    entity.display_name,
                )

        eligible_run_item_rows = tuple(
            (row, spec) for row, spec in self._run_item_rows if row.status in CANONICAL_ELIGIBLE_STATUSES
        )
        if input_data.track_payloads:
            eligible_run_item_rows = self._filter_db_ready_run_item_rows(
                input_data=input_data,
                run_item_rows=eligible_run_item_rows,
                matches=matches,
                entity_ids=entity_ids,
                entity_externals_by_id=entity_externals_by_id,
            )
        else:
            self._db_ready_gate_report = None

        for row, spec in eligible_run_item_rows:
            existing = existing_lookup.get(
                self._canonical_identity_key(
                    row.source_document_id,
                    row.owner_user_id,
                    row.field_id,
                    row.position_hash,
                    row.entity_scope_hash,
                )
            )
            bindings = self._run_item_entity_bindings(
                spec,
                matches,
                entity_ids,
                entity_externals_by_id,
            )
            entity_id = bindings.primary_entity_id
            external_id = bindings.primary_external_id
            entity_tuple = bindings.primary_entity_tuple
            variant_ids = list(bindings.variant_ids)
            gene_ids = list(bindings.gene_ids)
            entity_ids_list = list(bindings.external_ids)
            search_text = self._build_search_text(row, external_id, entity_tuple)
            payload = {
                **row.raw_payload,
                "track": row.track,
                "entity_id": entity_id,
                "variant_id": variant_ids[0] if variant_ids else None,
                "variant_ids": variant_ids,
                "gene_ids": gene_ids,
                "entity_ids": entity_ids_list,
                "search_text": search_text,
            }
            if existing is None:
                new_item = CanonicalEvidenceItem(
                    source_document_id=row.source_document_id,
                    owner_user_id=row.owner_user_id,
                    field_id=row.field_id,
                    position_hash=row.position_hash,
                    text_hash=row.text_hash,
                    entity_scope_hash=row.entity_scope_hash,
                    current_best_run_evidence_id=row.run_evidence_item_id,
                    current_best_status=row.status,
                    current_best_confidence=row.confidence,
                    conflict_flag=False,
                    active_payload=payload,
                )
                self.session.add(new_item)
                # Update lookup so subsequent rows with same identity
                # in this batch go through the update path instead of
                # triggering a duplicate-key IntegrityError.
                existing_lookup[
                    self._canonical_identity_key(
                        row.source_document_id,
                        row.owner_user_id,
                        row.field_id,
                        row.position_hash,
                        row.entity_scope_hash,
                    )
                ] = new_item
                continue

            incoming_priority = CANONICAL_STATUS_PRIORITY.get(row.status, -1)
            current_priority = CANONICAL_STATUS_PRIORITY.get(existing.current_best_status, -1)
            better_status = incoming_priority > current_priority
            better_confidence = incoming_priority == current_priority and (row.confidence or 0) > (
                existing.current_best_confidence or 0
            )
            if better_status or better_confidence:
                existing.current_best_run_evidence_id = row.run_evidence_item_id
                existing.current_best_status = row.status
                existing.current_best_confidence = row.confidence
                existing.text_hash = row.text_hash
                existing.active_payload = payload
            if existing.current_best_status != row.status or existing.text_hash != row.text_hash:
                existing.conflict_flag = True

        await self.session.flush()

    def _filter_db_ready_run_item_rows(
        self,
        *,
        input_data: StandardizationInput,
        run_item_rows: tuple[tuple[RunEvidenceItem, RunItemSpec], ...],
        matches: tuple[EntityMatch, ...],
        entity_ids: tuple[str, ...],
        entity_externals_by_id: dict[str, tuple[str | None, str, str]],
        policy: DbReadyGatePolicy = DEFAULT_DB_READY_GATE_POLICY,
    ) -> tuple[tuple[RunEvidenceItem, RunItemSpec], ...]:
        """Filter canonical candidates through the DB-ready gate."""
        candidates: list[DbReadyCandidate] = []
        for row, spec in run_item_rows:
            bindings = self._run_item_entity_bindings(
                spec,
                matches,
                entity_ids,
                entity_externals_by_id,
            )
            candidates.append(self._db_ready_candidate_from_run_item(input_data, row, spec, bindings))

        report = evaluate_db_ready_candidates(candidates, policy)
        self._db_ready_gate_report = report
        if report.rejected_count:
            reason_summary = ", ".join(f"{entry.reason.value}={entry.count}" for entry in report.rejection_counts)
            logger.info(
                "DB-ready gate accepted {} and rejected {} canonical candidate(s) for document={} reasons=[{}]",
                report.accepted_count,
                report.rejected_count,
                input_data.document_id,
                reason_summary,
            )

        return tuple(
            pair
            for pair, result in zip(run_item_rows, report.results, strict=False)
            if result.decision == DbReadyDecision.ACCEPTED
        )

    def _db_ready_candidate_from_run_item(
        self,
        input_data: StandardizationInput,
        row: RunEvidenceItem,
        spec: RunItemSpec,
        bindings: RunItemEntityBindings,
    ) -> DbReadyCandidate:
        """Adapt one staged run item into the pure DB-ready gate contract."""
        raw_payload = spec.raw_payload
        return DbReadyCandidate(
            candidate_id=spec.candidate_id
            or hash_payload(
                {
                    "track": spec.track,
                    "field_id": spec.field_id,
                    "group_id": spec.group_id,
                    "position_hash": spec.position_hash,
                },
            ),
            source_document_id=input_data.source_document_id,
            processing_run_id=input_data.processing_run_id,
            field_id=spec.field_id,
            group_id=spec.group_id,
            status=row.status,
            track=row.track,
            value_text=self._run_item_value_text(spec.value),
            source_span=spec.source_span or None,
            gene_id=bindings.gene_ids[0] if bindings.gene_ids else None,
            variant_id=bindings.variant_ids[0] if bindings.variant_ids else None,
            disease_id=bindings.disease_ids[0] if bindings.disease_ids else None,
            normalized_entity_ids=bindings.normalized_entity_ids,
            review_status=self._raw_review_status(raw_payload),
            expert_override=raw_payload.get("expert_override") is True,
        )

    def _run_item_entity_bindings(
        self,
        spec: RunItemSpec,
        matches: tuple[EntityMatch, ...],
        entity_ids: tuple[str, ...],
        entity_externals_by_id: dict[str, tuple[str | None, str, str]],
    ) -> RunItemEntityBindings:
        """Resolve normalized bindings related to one run item spec."""
        primary_entity_id: str | None = None
        primary_external_id: str | None = None
        primary_entity_tuple: tuple[str | None, str, str] | None = None
        external_ids: list[str] = []
        gene_ids: list[str] = []
        variant_ids: list[str] = []
        disease_ids: list[str] = []
        normalized_entity_ids: list[str] = []

        for match, entity_id in zip(matches, entity_ids, strict=False):
            if not entity_id or not self._spec_related_to_match(spec, match):
                continue
            entity_tuple = entity_externals_by_id.get(str(entity_id))
            if entity_tuple is None:
                entity_tuple = (match.external_id, match.candidate.entity_type.value, match.display_name)
            external_id, entity_type, _display_name = entity_tuple

            self._append_unique(normalized_entity_ids, str(entity_id))
            if external_id:
                self._append_unique(external_ids, external_id)
                if entity_type == EntityType.GENE.value:
                    self._append_unique(gene_ids, external_id)
                elif entity_type == EntityType.VARIANT.value:
                    self._append_unique(variant_ids, external_id)
                elif entity_type == EntityType.DISEASE.value:
                    self._append_unique(disease_ids, external_id)

            if primary_entity_id is None or spec.candidate_id == match.candidate.candidate_id:
                primary_entity_id = str(entity_id)
                primary_external_id = external_id
                primary_entity_tuple = entity_tuple

        return RunItemEntityBindings(
            primary_entity_id=primary_entity_id,
            primary_external_id=primary_external_id,
            primary_entity_tuple=primary_entity_tuple,
            external_ids=tuple(external_ids),
            gene_ids=tuple(gene_ids),
            variant_ids=tuple(variant_ids),
            disease_ids=tuple(disease_ids),
            normalized_entity_ids=tuple(normalized_entity_ids),
        )

    @staticmethod
    def _spec_related_to_match(spec: RunItemSpec, match: EntityMatch) -> bool:
        """Return whether a run item spec and entity match share the same evidence chain."""
        return spec.track == match.candidate.track and (
            spec.candidate_id == match.candidate.candidate_id
            or spec.group_id == match.candidate.chain_id
            or bool(
                match.candidate.field_id
                and spec.group_id == match.candidate.chain_id
                and spec.field_id == match.candidate.field_id,
            )
        )

    @staticmethod
    def _append_unique(values: list[str], value: str) -> None:
        """Append a non-empty value once while preserving order."""
        if value and value not in values:
            values.append(value)

    @staticmethod
    def _run_item_value_text(value: dict[str, Any]) -> str | None:
        """Extract a compact text value from a run item value payload."""
        for key in ("value", "text", "display_name"):
            entry = value.get(key)
            if entry not in (None, ""):
                return str(entry)
        return None

    @staticmethod
    def _raw_review_status(raw_payload: dict[str, Any]) -> str | None:
        """Extract review status from known raw payload keys."""
        for key in ("review_status", "human_review_status", "expert_review_status"):
            value = raw_payload.get(key)
            if isinstance(value, str) and value.strip():
                return value
        return None

    def _build_search_text(
        self,
        row: RunEvidenceItem,
        external_id: str | None,
        entity_tuple: tuple[str | None, str, str] | None,
    ) -> str:
        """Build a lowercase search-text blob for the search index.

        Concatenates the field value text with the entity display name and
        external id so the ``frontend_search_index.search_text`` column has
        non-empty, queryable content. Returns ``""`` when no text is present.
        """
        parts: list[str] = []
        value = getattr(row, "value", None)
        if isinstance(value, dict):
            field_text = value.get("value") or value.get("text") or value.get("display_name")
            if field_text:
                parts.append(str(field_text))
        raw_payload = getattr(row, "raw_payload", None)
        if isinstance(raw_payload, dict):
            raw_value = raw_payload.get("value")
            if isinstance(raw_value, str) and raw_value.strip():
                parts.append(raw_value)
        if entity_tuple is not None and len(entity_tuple) > 2:
            display_name = entity_tuple[2]
            if display_name:
                parts.append(str(display_name))
        if external_id:
            parts.append(str(external_id))
        return " ".join(" ".join(parts).split()).lower()

    async def persist_run_evidence(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
    ) -> tuple[str, ...]:
        """Compatibility wrapper used by the service layer plan."""
        return await self.insert_run_evidence_items(input_data, matches)

    async def persist_bindings(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
        entity_ids: tuple[str, ...],
    ) -> None:
        """Compatibility wrapper used by the service layer plan."""
        await self.insert_entity_bindings(input_data, matches, entity_ids)

    def _build_chain_scope_hashes(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
    ) -> dict[str, str]:
        """Build chain-level scope hashes from the current entity matches."""
        target_bindings = make_target_scope_bindings(input_data.extraction_target)
        grouped: dict[str, list[tuple[str, str]]] = defaultdict(list)
        for match in matches:
            identity = match.external_id or match.candidate.raw_text
            grouped[match.candidate.chain_id].append((match.candidate.role.value, identity))
        return {
            chain_id: make_entity_scope_hash([*target_bindings, *bindings]) for chain_id, bindings in grouped.items()
        }

    @staticmethod
    def _find_gene_variant_complete_groups(track_payloads: dict[str, Any]) -> set[str] | None:
        """Return group_ids that have both gene and variant in FOUND status.

        Returns ``None`` when no groups qualify, meaning all items should be
        persisted (no gate applied).  Returns an empty set when groups exist
        but none have both gene and variant — effectively blocking all items.
        """
        group_fields: dict[str, set[str]] = defaultdict(set)
        for payload in track_payloads.values():
            if not isinstance(payload, dict) or payload.get("audit_only") is True:
                continue
            for item in payload.get("evidence_items", []):
                if not isinstance(item, dict):
                    continue
                if item.get("status") != "found":
                    continue
                group_id = str(item.get("group_id", ""))
                if not group_id:
                    continue
                field_id = str(item.get("field_id", ""))
                group_fields[group_id].add(field_id)

        if not group_fields:
            return None

        return {
            gid
            for gid, fields in group_fields.items()
            if "A.gene_symbol" in fields and ("A.variant_hgvs_c" in fields or "A.variant_hgvs_p" in fields)
        }

    @staticmethod
    def _group_id_has_gene_anchor(group_id: str) -> bool:
        """Return whether a deterministic group_id carries a non-missing gene token."""
        parts: dict[str, str] = {}
        for token in group_id.split("|"):
            if "=" not in token:
                continue
            key, value = token.split("=", maxsplit=1)
            parts[key] = value.strip()
        gene = parts.get("gene", "")
        return bool(gene and gene.lower() != "__missing__")

    @staticmethod
    def _find_identity_passable_groups(track_payloads: dict[str, Any]) -> set[str]:
        """Return group_ids with at least one anchor identity field in FOUND status.

        A group is "identity passable" when it has ``A.gene_symbol`` or
        ``B.disease_diagnosis`` in FOUND status, or when its deterministic
        group_id carries a non-missing gene token.  This allows identity
        fields (gene, disease, variant, clinical context) to persist even
        without variant co-location, while still blocking groups that have
        neither gene nor disease (e.g. variant-only noise).
        """
        anchor_fields = EvidenceProjectionRepository._GATE_ANCHOR_FIELDS
        passable: set[str] = set()
        for payload in track_payloads.values():
            if not isinstance(payload, dict) or payload.get("audit_only") is True:
                continue
            for item in payload.get("evidence_items", []):
                if not isinstance(item, dict):
                    continue
                if item.get("status") != "found":
                    continue
                group_id = str(item.get("group_id", ""))
                if not group_id:
                    continue
                field_id = str(item.get("field_id", ""))
                if field_id in anchor_fields or EvidenceProjectionRepository._group_id_has_gene_anchor(group_id):
                    passable.add(group_id)
        return passable

    def _build_run_item_specs(
        self,
        input_data: StandardizationInput,
        matches: tuple[EntityMatch, ...],
        scope_hashes: dict[str, str],
    ) -> list[RunItemSpec]:
        """Build run-item persistence specs from track payloads or match fallbacks.

        Applies a two-tier gene-variant coexistence gate:

        1. **Full gate**: items from groups with both ``A.gene_symbol`` and at
           least one variant in FOUND status are always persisted (all fields).
        2. **Identity gate**: identity fields (gene, disease, variant HGVS,
           clinical phenotypes, sex, age of onset, inheritance, de novo) from
           groups anchored by ``A.gene_symbol`` or ``B.disease_diagnosis`` in
           FOUND status are persisted even without variant co-location.

        Variant-dependent downstream evidence (functional, segregation,
        pathogenicity) still requires the full gene+variant co-location.
        The fallback match-based path is not gated.
        """
        target_scope_hash = make_entity_scope_hash(make_target_scope_bindings(input_data.extraction_target))
        specs: list[RunItemSpec] = []

        allowed_groups = self._find_gene_variant_complete_groups(input_data.track_payloads)
        identity_passable: set[str] = set()
        if allowed_groups is not None:
            identity_passable = self._find_identity_passable_groups(input_data.track_payloads)
            if len(allowed_groups) == 0:
                if identity_passable:
                    logger.info(
                        "Persistence gate: no group has gene+variant; "
                        "allowing identity fields from {} group(s) for document={}",
                        len(identity_passable),
                        input_data.document_id,
                    )
                else:
                    logger.warning(
                        "Persistence gate: no group has both gene and variant in FOUND status; "
                        "skipping all track payload items for document={}",
                        input_data.document_id,
                    )

        identity_fields = self._GATE_IDENTITY_FIELDS
        for payload in input_data.track_payloads.values():
            if not isinstance(payload, dict):
                continue
            if payload.get("audit_only") is True:
                continue
            track = normalize_enum_like_string(payload.get("track"))
            for item in payload.get("evidence_items", []):
                if not isinstance(item, dict):
                    continue
                group_id = str(item.get("group_id", ""))
                field_id = str(item.get("field_id", ""))
                # Full gate: gene+variant complete groups accept all fields.
                if allowed_groups is not None and group_id not in allowed_groups:
                    # Identity gate: allow identity fields from passable groups.
                    if group_id not in identity_passable or field_id not in identity_fields:
                        continue
                value = {"value": item.get("value")}
                raw_source_span = item.get("source")
                source_span: dict[str, Any] = dict(raw_source_span) if isinstance(raw_source_span, dict) else {}
                raw_source = item.get("raw_source")
                if self._is_translation_traceback_source(raw_source):
                    source_span["original_source_span"] = raw_source
                item_status = self._admission_status_for_item(item)
                specs.append(
                    RunItemSpec(
                        candidate_id="",
                        track=track,
                        field_id=str(item.get("field_id", "")),
                        group_id=group_id,
                        status=item_status,
                        value=value,
                        confidence=item.get("confidence"),
                        position_hash=hash_payload(
                            {
                                "track": track,
                                "field_id": item.get("field_id"),
                                "group_id": group_id,
                                "source": item.get("source"),
                            },
                        ),
                        text_hash=hash_payload(item.get("value")),
                        source_span=source_span,
                        entity_scope_hash=scope_hashes.get(group_id, target_scope_hash),
                        raw_payload=item,
                    ),
                )
        if specs:
            return specs
        for match in matches:
            status = "found" if match.status == MatchStatus.STANDARDIZED else "not_found"
            value = {
                "text": match.candidate.raw_text,
                "display_name": match.display_name,
                "external_id": match.external_id,
            }
            specs.append(
                RunItemSpec(
                    candidate_id=match.candidate.candidate_id,
                    track=match.candidate.track,
                    field_id=match.candidate.field_id or f"{match.candidate.entity_type.value}_mention",
                    group_id=match.candidate.chain_id,
                    status=status,
                    value=value,
                    confidence=1.0 if match.status == MatchStatus.STANDARDIZED else 0.0,
                    position_hash=hash_payload({"candidate_id": match.candidate.candidate_id}),
                    text_hash=hash_payload(match.candidate.raw_text),
                    source_span={},
                    entity_scope_hash=scope_hashes.get(match.candidate.chain_id, target_scope_hash),
                    raw_payload={
                        "candidate_id": match.candidate.candidate_id,
                        "rationale": match.rationale,
                    },
                ),
            )
        return specs

    @staticmethod
    def _is_translation_traceback_source(raw_source: object) -> bool:
        """Return whether a raw source came from deterministic translation traceback."""
        if not isinstance(raw_source, dict):
            return False
        return "translation_traceback" in str(raw_source.get("context_ref", ""))

    def _admission_status_for_item(self, item: dict[str, Any]) -> str:
        """Return the DB admission status for one Phase 2 evidence item."""
        status = normalize_enum_like_string(item.get("status"))
        if item.get("field_id") != "J.clinvar_assertion" or status != "found":
            return status
        if self._has_clinvar_assertion_authority(item):
            return status
        return CLINVAR_ASSERTION_REVIEW_STATUS

    @staticmethod
    def _has_clinvar_assertion_authority(item: dict[str, Any]) -> bool:
        """Return whether an assertion is explicitly tied to ClinVar/ACMG authority."""
        snippets: list[str] = []
        for key in ("value", "source_database"):
            value = item.get(key)
            if value not in (None, ""):
                snippets.append(str(value))
        for key in ("source", "raw_source"):
            value = item.get(key)
            if isinstance(value, dict):
                snippet = value.get("text_snippet")
                if snippet not in (None, ""):
                    snippets.append(str(snippet))
        return any(CLINVAR_AUTHORITY_RE.search(snippet) for snippet in snippets)

    def _related_run_rows(self, match: EntityMatch) -> list[RunEvidenceItem]:
        """Return run evidence rows related to the current entity match."""
        related = [
            row
            for row, spec in self._run_item_rows
            if spec.track == match.candidate.track
            and (
                spec.candidate_id == match.candidate.candidate_id
                or spec.group_id == match.candidate.chain_id
                or (
                    match.candidate.field_id
                    and spec.group_id == match.candidate.chain_id
                    and spec.field_id == match.candidate.field_id
                )
            )
        ]
        return related
