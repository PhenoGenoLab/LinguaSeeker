"""Shared contracts, constants, and pure helpers for standardization repositories."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from src.core.tools.standardization.contracts import EntityType
from src.core.tools.standardization.normalizers import (
    normalize_disease_lookup_text,
    normalize_gene_symbol,
    normalize_lookup_text,
    normalize_variant_text,
)

CANONICAL_STATUS_PRIORITY = {
    "found": 4,
    "source_invalid": 3,
    "ocr_gap": 2,
    "table_ungrounded": 1,
    "not_found": 0,
}

CANONICAL_ELIGIBLE_STATUSES = {"found", "source_invalid", "ocr_gap", "table_ungrounded"}
CLINVAR_ASSERTION_REVIEW_STATUS = "context_contamination"
CLINVAR_AUTHORITY_RE = re.compile(
    r"\b(?:ClinVar|ClinGen|ACMG|PVS\d?|PS\d?|PM\d?|PP\d?|BA\d?|BS\d?|BP\d?)\b",
    re.IGNORECASE,
)

CanonicalIdentityKey = tuple[str, str, str, str, str]


@dataclass(frozen=True)
class RunItemSpec:
    """Internal repository contract for staging one run-evidence row."""

    candidate_id: str
    track: str
    field_id: str
    group_id: str
    status: str
    value: dict[str, Any]
    confidence: float | None
    position_hash: str
    text_hash: str
    source_span: dict[str, Any]
    entity_scope_hash: str
    raw_payload: dict[str, Any]


@dataclass(frozen=True)
class RunItemEntityBindings:
    """Resolved normalized entity bindings for one run evidence row."""

    primary_entity_id: str | None
    primary_external_id: str | None
    primary_entity_tuple: tuple[str | None, str, str] | None
    external_ids: tuple[str, ...]
    gene_ids: tuple[str, ...]
    variant_ids: tuple[str, ...]
    disease_ids: tuple[str, ...]
    normalized_entity_ids: tuple[str, ...]


def sanitize_jsonb_value(value: Any) -> Any:
    """Remove characters PostgreSQL JSONB cannot store from nested payloads."""
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, dict):
        return {
            sanitize_jsonb_value(str(key)): sanitize_jsonb_value(nested_value)
            for key, nested_value in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize_jsonb_value(item) for item in value]
    return value


def normalize_entity_text(entity_type: EntityType, raw_text: str) -> str:
    """Normalize lookup text using entity-type-specific rules."""
    if entity_type == EntityType.GENE:
        return normalize_gene_symbol(raw_text)
    if entity_type == EntityType.VARIANT:
        return normalize_variant_text(raw_text)
    if entity_type == EntityType.DISEASE:
        return normalize_disease_lookup_text(raw_text)
    return normalize_lookup_text(raw_text)


def hash_payload(value: Any) -> str:
    """Hash arbitrary JSON-serializable payloads into stable identity strings."""
    serialized = json.dumps(value, sort_keys=True, default=str, ensure_ascii=False)
    return sha256(serialized.encode("utf-8")).hexdigest()


def normalize_enum_like_string(value: Any) -> str:
    """Normalize enum repr strings like `Track.ORIGINAL` into lowercase values."""
    text = str(value or "")
    if "." in text:
        _, _, suffix = text.rpartition(".")
        if suffix:
            return suffix.lower()
    return text.lower()
