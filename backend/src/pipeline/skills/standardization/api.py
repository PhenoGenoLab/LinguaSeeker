"""Presentation helpers for Phase 3 standardization results."""

from __future__ import annotations

from typing import Any

from src.core.tools.standardization.contracts import EntityMatch


def serialize_matches(matches: tuple[EntityMatch, ...]) -> list[dict[str, Any]]:
    """Serialize EntityMatch tuple into auditable JSON-serializable dicts."""
    entries: list[dict[str, Any]] = []
    for match in matches:
        entry: dict[str, Any] = {
            "candidate_id": match.candidate.candidate_id,
            "raw_text": match.candidate.raw_text,
            "entity_type": match.candidate.entity_type.value,
            "chain_id": match.candidate.chain_id,
            "track": match.candidate.track,
            "field_id": match.candidate.field_id,
            "status": match.status.value,
            "external_id": match.external_id,
            "display_name": match.display_name,
            "rationale": match.rationale,
            "match_method": match.match_method.value,
            "similarity_score": match.similarity_score,
        }
        if match.terminology_candidates:
            entry["terminology_candidates"] = [
                {
                    "external_id": tc.external_id,
                    "display_name": tc.display_name,
                    "source_db": tc.source_db,
                    "alias_type": tc.alias_type,
                }
                for tc in match.terminology_candidates
            ]
        entries.append(entry)
    return entries


def build_summary_metadata(
    *,
    imported_terminology: bool,
    terminology_sources: list[str],
    terminology_version: str,
    terminology_entry_count: int = 0,
    embedding_available: bool = False,
) -> dict[str, Any]:
    """Build truthful summary metadata with terminology health indicators."""
    return {
        "imported_terminology": imported_terminology,
        "terminology_sources": terminology_sources,
        "terminology_version": terminology_version,
        "terminology_entry_count": terminology_entry_count,
        "embedding_available": embedding_available,
    }


__all__ = ["build_summary_metadata", "serialize_matches"]
