"""Quality validation and target entity guarding."""

from __future__ import annotations

import ast

from src.core.tools.standardization.hgvs_normalizer import expand_hgvs_aliases

from src.core.tools.extraction.domain.catalog import EVIDENCE_FIELD_SPECS, EvidenceFieldSpec
from src.core.tools.extraction.contracts import EvidenceChain, EvidenceItem, EvidenceStatus, ExtractionTarget, QualityIssue, QualityReport, SourcePrecision, SpecialEvidenceRecord


class TargetEntityGuard:
    """Validates primary entity fields against the extraction target."""

    _GENE_FIELD = "A.gene_symbol"
    _TARGET_VARIANT_FIELDS: tuple[str, ...] = ("A.variant_hgvs_c", "A.variant_hgvs_p")

    def apply(
        self,
        items: list[EvidenceItem],
        extraction_target: ExtractionTarget | None,
    ) -> list[EvidenceItem]:
        if extraction_target is None:
            return items
        return [self._guard_one(item, extraction_target) for item in items]

    def _guard_one(self, item: EvidenceItem, target: ExtractionTarget) -> EvidenceItem:
        if item.status != EvidenceStatus.FOUND:
            return item
        if item.field_id == self._GENE_FIELD:
            return self._guard_gene(item, target)
        if item.field_id == "A.variant_hgvs_c" and target.variant_hgvs_c:
            return self._guard_variant(item, target.variant_hgvs_c)
        if item.field_id == "A.variant_hgvs_p" and target.variant_hgvs_p:
            return self._guard_variant(item, target.variant_hgvs_p)
        return item

    def _guard_gene(self, item: EvidenceItem, target: ExtractionTarget) -> EvidenceItem:
        values = self._extract_gene_values(item.value)
        if len(values) > 1:
            if target.gene_symbol in values:
                return item.model_copy(
                    update={
                        "value": target.gene_symbol,
                        "notes": self._append_note(item.notes, "target_guard:list_to_target"),
                    }
                )
            return self._contaminated(
                item,
                f"target gene {target.gene_symbol} not in extracted gene list {values}",
            )
        actual = values[0] if values else str(item.value or "").strip().upper()
        if actual != target.gene_symbol:
            return self._contaminated(
                item,
                f"extracted {actual}, expected {target.gene_symbol}",
            )
        return item.model_copy(update={"value": target.gene_symbol})

    def _guard_variant(self, item: EvidenceItem, target_variant: str) -> EvidenceItem:
        target_aliases = self._variant_aliases(target_variant)
        if not target_aliases:
            return item
        values = self._extract_string_values(item.value)
        for value in values:
            if self._variant_aliases(value) & target_aliases:
                return item.model_copy(
                    update={
                        "value": target_variant,
                        "notes": self._append_note(item.notes, "target_guard:variant_to_target"),
                    }
                )
        return self._contaminated(
            item,
            f"extracted variant {values or [item.value]}, expected {target_variant}",
        )

    @staticmethod
    def _contaminated(item: EvidenceItem, reason: str) -> EvidenceItem:
        return item.model_copy(
            update={
                "status": EvidenceStatus.CONTEXT_CONTAMINATION,
                "notes": (f"{item.notes}; target_guard:{reason}" if item.notes else f"target_guard:{reason}"),
                "assigned_acmg_codes": [],
                "assigned_clingen_modules": [],
            }
        )

    @staticmethod
    def _extract_gene_values(value: object) -> list[str]:
        if isinstance(value, list):
            return [str(entry).strip().upper() for entry in value if str(entry).strip()]
        text = str(value or "").strip()
        if text.startswith("["):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                return [text.upper()]
            if isinstance(parsed, list):
                return [str(entry).strip().upper() for entry in parsed if str(entry).strip()]
        return [text.upper()] if text else []

    @staticmethod
    def _extract_string_values(value: object) -> list[str]:
        if isinstance(value, list):
            return [str(entry).strip() for entry in value if str(entry).strip()]
        text = str(value or "").strip()
        if text.startswith("["):
            try:
                parsed = ast.literal_eval(text)
            except (SyntaxError, ValueError):
                return [text] if text else []
            if isinstance(parsed, list):
                return [str(entry).strip() for entry in parsed if str(entry).strip()]
        return [text] if text else []

    @staticmethod
    def _variant_aliases(value: str) -> set[str]:
        return {alias.casefold() for alias in expand_hgvs_aliases(value)}

    @staticmethod
    def _append_note(existing: str, note: str) -> str:
        return f"{existing}; {note}" if existing else note


class QualityValidator:
    """Rule-based quality validation for extracted evidence."""

    def __init__(
        self,
        required_field_ids: set[str] | None = None,
        catalog: tuple[EvidenceFieldSpec, ...] = EVIDENCE_FIELD_SPECS,
    ):
        if required_field_ids is not None:
            self._required = required_field_ids
        else:
            self._required = {s.field_id for s in catalog if s.required_for_scorable}

    def validate(
        self,
        items: list[EvidenceItem],
        contradictions: list[str],
        chains: list[EvidenceChain] | None = None,
        special_records: list[SpecialEvidenceRecord] | None = None,
        evidence_chain_count: int = 0,
    ) -> QualityReport:
        chains = chains or []
        special_records = special_records or []
        issues: list[QualityIssue] = []
        review_notes: list[tuple[str, str]] = []
        found_count = 0
        not_found_count = 0
        source_invalid_count = 0
        ocr_gap_count = 0
        table_ungrounded_count = 0
        ambiguous_source_count = 0
        context_contamination_count = 0

        for item in items:
            if item.status == EvidenceStatus.FOUND:
                found_count += 1
                if item.source is None:
                    if item.field_id == "B.case_count":
                        reason = f"{item.field_id} is inferred from document structure and has no traceable source"
                        review_notes.append(("workflow", reason))
                    else:
                        issues.append(
                            QualityIssue(
                                issue_type="missing_source",
                                field_id=item.field_id,
                                description=f"Found item {item.field_id} has no source",
                                severity="error",
                            )
                        )
                elif item.source.source_precision == SourcePrecision.AMBIGUOUS:
                    ambiguous_source_count += 1
                    reason = f"{item.field_id} has ambiguous source grounding"
                    review_notes.append(("source_grounding", reason))
            elif item.status == EvidenceStatus.NOT_FOUND:
                not_found_count += 1
            elif item.status == EvidenceStatus.SOURCE_INVALID:
                source_invalid_count += 1
                reason = f"{item.field_id} has invalid source grounding"
                review_notes.append(("source_grounding", reason))
            elif item.status == EvidenceStatus.OCR_GAP:
                ocr_gap_count += 1
                reason = f"{item.field_id} may require OCR/image review"
                review_notes.append(("source_grounding", reason))
            elif item.status == EvidenceStatus.TABLE_UNGROUNDED:
                table_ungrounded_count += 1
                reason = f"{item.field_id} may require table-path grounding"
                review_notes.append(("table_grounding", reason))
            elif item.status == EvidenceStatus.CONTEXT_CONTAMINATION:
                context_contamination_count += 1
                reason = f"{item.field_id} rejected as target context contamination: {item.notes}"
                issues.append(
                    QualityIssue(
                        issue_type="context_contamination",
                        field_id=item.field_id,
                        description=item.notes,
                        severity="error",
                    )
                )
                review_notes.append(("workflow", reason))
        missing_required = self._ungrounded_required(items)
        for field_id in missing_required:
            issues.append(
                QualityIssue(
                    issue_type="missing_required",
                    field_id=field_id,
                    description=f"Required field {field_id} is missing",
                    severity="warning",
                )
            )
            reason = f"{field_id} is required for scoring but is not grounded"
            review_notes.append(("scoring_gate", reason))

        for contradiction in contradictions:
            issues.append(
                QualityIssue(
                    issue_type="contradiction",
                    field_id="",
                    description=contradiction,
                    severity="warning",
                )
            )
            reason = f"Contradiction requires review: {contradiction}"
            review_notes.append(("contradictions", reason))

        for record in special_records:
            if record.raw_source is not None and record.source is None:
                reason = f"Special evidence {record.record_type} requires source grounding review"
                review_notes.append(("source_grounding", reason))

        passed = not any(issue.severity == "error" for issue in issues)
        full_chains, incomplete_chains, scorable = self._score_gate(items, chains)
        score_gate_passed = passed and scorable

        if incomplete_chains:
            reason = "Incomplete evidence chain requires review"
            review_notes.append(("workflow", reason))
        if passed and items and not full_chains and evidence_chain_count == 0:
            reason = "No full evidence chain was produced"
            review_notes.append(("workflow", reason))
        if passed and scorable and not chains and evidence_chain_count == 0:
            reason = "No grounded evidence chain was produced"
            review_notes.append(("workflow", reason))

        human_review_reasons = [reason for _category, reason in review_notes]
        human_review_by_category: dict[str, list[str]] = {
            "source_grounding": [],
            "table_grounding": [],
            "scoring_gate": [],
            "contradictions": [],
            "workflow": [],
        }
        for category, reason in review_notes:
            human_review_by_category[category].append(reason)

        return QualityReport(
            passed=passed,
            scorable=scorable,
            score_gate_passed=score_gate_passed,
            issues=issues,
            found_count=found_count,
            not_found_count=not_found_count,
            source_invalid_count=source_invalid_count,
            ocr_gap_count=ocr_gap_count,
            table_ungrounded_count=table_ungrounded_count,
            ambiguous_source_count=ambiguous_source_count,
            context_contamination_count=context_contamination_count,
            human_review_required=len(human_review_reasons) > 0,
            human_review_reasons=human_review_reasons,
            human_review_by_category=human_review_by_category,
        )

    def _ungrounded_required(self, items: list[EvidenceItem]) -> set[str]:
        """Return required fields without a grounded (non-ambiguous) FOUND item."""
        grounded = {
            item.field_id
            for item in items
            if item.status == EvidenceStatus.FOUND
            and item.source is not None
            and item.source.source_precision != SourcePrecision.AMBIGUOUS
        }
        return self._required - grounded

    def _score_gate(
        self,
        items: list[EvidenceItem],
        chains: list[EvidenceChain],
    ) -> tuple[list[EvidenceChain], list[EvidenceChain], bool]:
        """Return full chains, incomplete chains, and whether scoring is allowed."""
        full_chains = [chain for chain in chains if chain.chain_level == "full"]
        incomplete_chains = [chain for chain in chains if chain.chain_level in {"partial", "singleton"}]
        full_chain_group_ids = {chain.chain_id for chain in full_chains}
        full_chain_items = [item for item in items if item.group_id in full_chain_group_ids]

        scorable = len(full_chains) > 0 and not self._ungrounded_required(full_chain_items)
        degraded_statuses = {
            EvidenceStatus.SOURCE_INVALID,
            EvidenceStatus.OCR_GAP,
            EvidenceStatus.TABLE_UNGROUNDED,
            EvidenceStatus.CONTEXT_CONTAMINATION,
        }
        if any(item.status in degraded_statuses for item in full_chain_items):
            scorable = False
        if any(
            item.status == EvidenceStatus.FOUND
            and item.source is not None
            and item.source.source_precision == SourcePrecision.AMBIGUOUS
            for item in full_chain_items
        ):
            scorable = False
        return full_chains, incomplete_chains, scorable


class IntraTrackConflictChecker:
    """Checks for contradictions within a single track's evidence."""

    def check(self, items: list[EvidenceItem]) -> list[QualityIssue]:
        issues: list[QualityIssue] = []
        found_by_field: dict[str, list[EvidenceItem]] = {}

        for item in items:
            if item.status == EvidenceStatus.FOUND:
                found_by_field.setdefault(item.field_id, []).append(item)

        for field_id, field_items in found_by_field.items():
            if len(field_items) > 1:
                values = {str(item.value) for item in field_items}
                if len(values) > 1:
                    issues.append(
                        QualityIssue(
                            issue_type="contradiction",
                            field_id=field_id,
                            description=f"Multiple conflicting values for {field_id}: {values}",
                            severity="warning",
                        )
                    )

        return issues
