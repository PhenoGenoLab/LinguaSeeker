"""Pure business rules for the source fact chain.

No I/O, no model access and no orchestration live here: candidate validation,
fact identity, quote anchoring and provider-reply reconciliation only.
"""

from __future__ import annotations

import html
import re
import unicodedata

from .contracts import (
    ALLOWED_FIELD_IDS,
    FIELD_MODES,
    POLARITIES,
    VERIFY_LABELS,
    ChainContractError,
    DocumentWindow,
    Polarity,
    SourceDocument,
    SourceFact,
    Subject,
    SubjectStatus,
    canonical_json,
    sha256_text,
)


class Reconciled:
    """Matched provider items plus explicit missing/duplicate/unexpected ids."""

    __slots__ = ("matched", "missing", "duplicates", "unexpected")

    def __init__(
        self,
        matched: dict[str, dict[str, object]],
        missing: list[str],
        duplicates: list[str],
        unexpected: list[str],
    ) -> None:
        self.matched = matched
        self.missing = missing
        self.duplicates = duplicates
        self.unexpected = unexpected


def compact(text: str) -> str:
    """Whitespace-insensitive, NFKC-normalised comparison form (never stored)."""
    return "".join(unicodedata.normalize("NFKC", text).split())


def has_semicolon_equivalent(value: str) -> bool:
    """True when any decoded character NFKC-normalises to ``;``.

    Decoding first prevents an entity terminator (``&gt;``) from being mistaken
    for a list separator, while ``&#59;`` still counts as one.
    """
    return any(unicodedata.normalize("NFKC", char) == ";" for char in html.unescape(value))


def is_atomic(value: str) -> bool:
    """Reject semicolon-joined lists; commas may be part of HGVS or phenotypes.

    HTML entities are decoded first so ``&#59;`` cannot smuggle a list
    separator past the check and ``&gt;`` is not a separator.
    """
    return ";" not in html.unescape(value)


_HTML_ENTITY_RE = re.compile(r"&(?:#[0-9]+|#[xX][0-9a-fA-F]+|[A-Za-z][A-Za-z0-9]+);")


def _comparison_needle(text: str) -> str:
    """Comparison form of a candidate value or quote (entities decoded, NFKC)."""
    return "".join(
        normalized
        for char in html.unescape(text)
        for normalized in unicodedata.normalize("NFKC", char)
        if not normalized.isspace()
    )


def _comparison_units(text: str) -> tuple[str, list[int], list[int]]:
    """NFKC/whitespace-compacted text with a source span for every unit.

    HTML entities are decoded as one comparison unit mapped back to the full
    entity range, so a quote may match either decoded or entity-encoded source
    without ever rewriting the frozen document.
    """
    characters: list[str] = []
    starts: list[int] = []
    ends: list[int] = []
    cursor = 0
    length = len(text)
    while cursor < length:
        entity = _HTML_ENTITY_RE.match(text, cursor)
        if entity is not None:
            decoded = html.unescape(entity.group())
            if decoded != entity.group():
                for normalized in unicodedata.normalize("NFKC", decoded):
                    if not normalized.isspace():
                        characters.append(normalized)
                        starts.append(entity.start())
                        ends.append(entity.end())
                cursor = entity.end()
                continue
        character = text[cursor]
        if not character.isspace():
            for normalized in unicodedata.normalize("NFKC", character):
                if not normalized.isspace():
                    characters.append(normalized)
                    starts.append(cursor)
                    ends.append(cursor + 1)
        cursor += 1
    return "".join(characters), starts, ends


def _locate_needle(
    compact_source: str,
    starts: list[int],
    ends: list[int],
    needle: str,
) -> tuple[int, int]:
    if not needle:
        raise ValueError("quote is absent from the frozen source")
    start = compact_source.find(needle)
    if start < 0:
        raise ValueError("quote is absent from the frozen source")
    return starts[start], ends[start + len(needle) - 1]


def locate_quote(source: str, quote: str) -> tuple[int, int]:
    """Locate a quote allowing Unicode/entity and whitespace differences.

    Returned offsets point into the exact frozen text, including when NFKC or
    HTML decoding expands one source unit into several comparison characters.
    """
    compact_source, starts, ends = _comparison_units(source)
    return _locate_needle(compact_source, starts, ends, _comparison_needle(quote))


def derive_fact_id(
    *,
    document_id: str,
    source_hash: str,
    field_id: str,
    raw_value: str,
    polarity: str,
    subject: Subject,
    span: tuple[int, int],
) -> str:
    """Stable identity over source content only.

    Window, model, prompt and English text are excluded, so overlapping
    windows that find the same span collapse to one fact.
    """
    identity = [
        document_id,
        source_hash,
        field_id,
        raw_value,
        polarity,
        subject.status.value,
        subject.subject_id,
        span[0],
        span[1],
    ]
    return "F-" + sha256_text(canonical_json(identity))[:16]


def candidate_to_fact(
    candidate: object,
    *,
    document: SourceDocument,
    window: DocumentWindow,
    allowed_field_ids: tuple[str, ...] = ALLOWED_FIELD_IDS,
) -> SourceFact:
    """Validate one extraction candidate into an immutable source fact.

    Rejects unknown fields, empty or non-atomic values, invalid polarity or
    subject attribution, and quotes that are missing or ambiguous in the window.
    """
    if not isinstance(candidate, dict):
        raise ChainContractError("candidate_not_object")
    keys = ("field_id", "raw_value", "polarity", "subject_status", "subject_id", "quote")
    missing = [key for key in keys if key not in candidate]
    if missing:
        raise ChainContractError("candidate_missing_key", ",".join(missing))

    field_id = candidate["field_id"]
    if not isinstance(field_id, str) or field_id not in allowed_field_ids:
        raise ChainContractError("unknown_field", str(field_id))
    if field_id not in FIELD_MODES:
        raise ChainContractError("unknown_field", field_id)

    raw_value = candidate["raw_value"]
    if not isinstance(raw_value, str) or not raw_value.strip():
        raise ChainContractError("empty_value")

    quote = candidate["quote"]
    if not isinstance(quote, str) or not quote.strip():
        raise ChainContractError("quote_missing")

    if not is_atomic(raw_value) or has_semicolon_equivalent(raw_value):
        raise ChainContractError("non_atomic_value", raw_value)
    value_needle = _comparison_needle(raw_value)
    quote_needle = _comparison_needle(quote)
    if not quote_needle:
        raise ChainContractError("quote_missing")
    if not value_needle or value_needle not in quote_needle:
        raise ChainContractError("value_not_in_quote", raw_value)

    polarity = candidate["polarity"]
    if not isinstance(polarity, str) or polarity not in POLARITIES:
        raise ChainContractError("invalid_polarity", str(polarity))

    subject_status = candidate["subject_status"]
    if subject_status not in {status.value for status in SubjectStatus}:
        raise ChainContractError("invalid_subject_status", str(subject_status))
    subject_id = candidate["subject_id"]
    if subject_status == SubjectStatus.UNKNOWN.value and subject_id is not None:
        raise ChainContractError("subject_unknown_with_id")
    if subject_status == SubjectStatus.KNOWN.value and not isinstance(subject_id, str):
        raise ChainContractError("subject_known_without_id")
    subject = Subject(status=SubjectStatus(subject_status), subject_id=subject_id)

    # A quote occurring twice in the window cannot be attributed to one location.
    # Compare in the same normalized form used for location so whitespace or
    # entity variants of the same sentence are treated as ambiguous.
    compact_window, window_starts, window_ends = _comparison_units(window.text)
    if compact_window.count(quote_needle) > 1:
        raise ChainContractError("quote_ambiguous", quote)
    try:
        local_start, local_end = _locate_needle(compact_window, window_starts, window_ends, quote_needle)
    except ValueError as exc:
        raise ChainContractError("quote_not_in_source", str(exc)) from exc

    span = (window.start_offset + local_start, window.start_offset + local_end)
    if _comparison_needle(document.text[span[0] : span[1]]) != quote_needle:
        raise ChainContractError("span_quote_mismatch", f"{span[0]}:{span[1]}")

    fact_id = derive_fact_id(
        document_id=document.document_id,
        source_hash=document.source_hash,
        field_id=field_id,
        raw_value=raw_value,
        polarity=polarity,
        subject=subject,
        span=span,
    )
    return SourceFact(
        fact_id=fact_id,
        document_id=document.document_id,
        source_hash=document.source_hash,
        field_id=field_id,
        raw_value=raw_value,
        polarity=Polarity(polarity),
        subject=subject,
        quote=quote,
        span_start=span[0],
        span_end=span[1],
        window_id=window.label,
    )


def reconcile(requested: list[str], items: list[object], key: str) -> Reconciled:
    """Match provider items to requested ids without admitting unknown ids."""
    wanted = set(requested)
    matched: dict[str, dict[str, object]] = {}
    duplicates: list[str] = []
    unexpected: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            unexpected.append(str(item))
            continue
        item_id = item.get(key)
        if not isinstance(item_id, str) or item_id not in wanted:
            unexpected.append(str(item_id))
            continue
        if item_id in matched:
            duplicates.append(item_id)
            continue
        matched[item_id] = item
    return Reconciled(
        matched=matched,
        missing=[fact_id for fact_id in requested if fact_id not in matched],
        duplicates=duplicates,
        unexpected=unexpected,
    )


def validate_reply_schema(reply: object, stage: str) -> None:
    """Validate raw provider JSON before it is cached or consumed."""
    field = {"extract": "facts", "verify": "verdicts", "translate": "translations"}[stage]
    if not isinstance(reply, dict) or not isinstance(reply.get(field), list):
        raise ChainContractError("reply_schema", f"{field} must be a list")
    strings = {
        "extract": ("field_id", "raw_value", "polarity", "subject_status", "quote"),
        "verify": ("fact_id", "label", "reason"),
        "translate": ("fact_id", "english_text"),
    }[stage]
    for item in reply[field]:
        if not isinstance(item, dict) or any(not isinstance(item.get(name), str) for name in strings):
            raise ChainContractError("reply_schema", f"{field} item has missing or non-string fields")
        if stage == "extract":
            if "subject_id" not in item or (item["subject_id"] is not None and not isinstance(item["subject_id"], str)):
                raise ChainContractError("reply_schema", "subject_id must be a string or null")
        elif not str(item["fact_id"]).strip():
            raise ChainContractError("reply_schema", "fact_id must be non-empty")
        if stage == "verify" and item["label"] not in VERIFY_LABELS:
            raise ChainContractError("reply_schema", "invalid verification label")
        if stage == "translate" and not str(item["english_text"]).strip():
            raise ChainContractError("reply_schema", "english_text must be non-empty")


__all__ = [
    "Reconciled",
    "candidate_to_fact",
    "compact",
    "derive_fact_id",
    "has_semicolon_equivalent",
    "is_atomic",
    "locate_quote",
    "reconcile",
    "validate_reply_schema",
]
