"""Delta computation for evidence review (pure)."""

from __future__ import annotations

from src.core.tools.review.contracts import DeltaEntry, EvidenceCardPayload


class DeltaAuditService:
    """Compute field-level deltas for evidence review."""

    @staticmethod
    def compute_deltas(
        old: EvidenceCardPayload,
        new: EvidenceCardPayload,
    ) -> list[DeltaEntry]:
        """Compute field-level differences between two payloads."""
        deltas: list[DeltaEntry] = []
        for field in EvidenceCardPayload.DIFF_FIELDS:
            old_value = getattr(old, field)
            new_value = getattr(new, field)
            if old_value != new_value:
                deltas.append(
                    DeltaEntry(
                        field=field,
                        old_value=old_value,
                        new_value=new_value,
                    )
                )
        return deltas
