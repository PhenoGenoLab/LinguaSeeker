"""Document block/text resolution for evidence display.

Loads structured blocks, full text, translation alignment, and the body-only
excerpt from the database-independent sources: persisted pipeline output
directories and the legacy ``output/cross_lingual`` tree.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from uuid import UUID

from loguru import logger

from src.core.tools.translation.contracts import TranslationAlignmentChunk
from src.core.tools.translation.translate.language_detector import detect_language
from src.utils.text_normalize import block_text_from_dict, concat_document_text

_BODY_START_PATTERNS = (
    r"^［?摘要］?",
    r"^摘\s*要\b",
    r"^abstract\b",
    r"^资料与方法\b",
    r"^\d+(?:\.\d+)?\s*[　 ]*(?:资料与方法|材料与方法|方法|研究对象|结果|讨论)\b",
    r"^methods?\b",
    r"^results?\b",
    r"^discussion\b",
    r"^introduction\b",
)
_BODY_END_PATTERNS = (
    r"^［?\s*参\s*考\s*文\s*献\s*］?",
    r"^参考文献\b",
    r"^references?\b",
    r"^acknowledg(?:e)?ments?\b",
    r"^conflicts?\s+of\s+interest\b",
    r"^funding\b",
    r"^（?本文编辑",
)
_BLOCK_TEXT_COVERAGE_RATIO = 0.7


def row_fact_key(row: object) -> str:
    """Stable fact identity across tracks for bilingual trace pairing.

    Fact-chain rows carry ``source.span_id`` = ``"<track>-<fact_id>"``. Legacy
    rows without a fact id fall back to one trace per field, preserving the
    historical behavior.
    """
    payload = getattr(row, "active_payload", None) or {}
    source = payload.get("source") if isinstance(payload, dict) else None
    span_id = source.get("span_id") if isinstance(source, dict) else None
    if isinstance(span_id, str) and span_id:
        for prefix in ("original-", "translated-", "reconciled-"):
            if span_id.startswith(prefix):
                return span_id[len(prefix) :]
        return span_id
    return f"field:{getattr(row, 'field_id', '')}"


def coerce_str(value: Any) -> str | None:
    """Convert a payload value to a display string."""
    if value is None:
        return None
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)
    return str(value)


def normalize_language_code(value: Any) -> str | None:
    """Normalize a language value to the short code used by Evidence DB filters."""
    language_aliases = {
        "chinese": "zh",
        "deu": "de",
        "eng": "en",
        "english": "en",
        "fra": "fr",
        "fre": "fr",
        "french": "fr",
        "german": "de",
        "japanese": "ja",
        "jpn": "ja",
        "rus": "ru",
        "russian": "ru",
        "zho": "zh",
        "zh-cn": "zh",
        "zh-tw": "zh",
    }
    text = coerce_str(value)
    if not text or not text.strip():
        return None
    normalized = text.strip().lower().replace("_", "-")
    if normalized == "unknown":
        return None
    return language_aliases.get(normalized, normalized)


def extract_source_language(raw_metadata: Any) -> str | None:
    """Return the persisted source-language code from document metadata."""
    if not isinstance(raw_metadata, dict):
        return None
    for key in ("source_language", "article_language", "language"):
        language = normalize_language_code(raw_metadata.get(key))
        if language:
            return language
    return None


def extract_source_language_from_state(state_json: Any) -> str | None:
    """Return source language from persisted pipeline state JSON."""
    if not isinstance(state_json, dict):
        return None
    candidate_paths = (
        ("fact_chain_output", "source_language"),
        ("fact_chain_status", "summary", "source_language"),
        # Legacy pre-4-phase-split states stored translation output under parsing
        ("parsing_output", "source_language"),
        ("parsing_status", "summary", "source_language"),
        ("source_language",),
    )
    for path in candidate_paths:
        value: Any = state_json
        for key in path:
            if not isinstance(value, dict):
                value = None
                break
            value = value.get(key)
        language = normalize_language_code(value)
        if language:
            return language
    return None


def detect_source_language_from_text(text: str | None) -> str | None:
    """Infer source language from persisted original document text as a fallback."""
    if not text or not text.strip():
        return None
    language = normalize_language_code(detect_language(text))
    if language:
        return language
    return None


def _matches_any(patterns: tuple[str, ...], text: str) -> bool:
    """Return whether stripped text matches any compiled body-boundary pattern."""
    stripped = text.strip()
    return any(re.search(pattern, stripped, re.IGNORECASE) for pattern in patterns)


def _compact_len(text: str | None) -> int:
    """Return length after whitespace compaction for coarse coverage checks."""
    if not text:
        return 0
    return len(re.sub(r"\s+", "", text))


def filter_body_text(text: str | None) -> str | None:
    """Remove article metadata and trailing non-body sections from display text."""
    if not text or not text.strip():
        return None

    lines = text.splitlines()
    start = 0
    for index, line in enumerate(lines):
        if _matches_any(_BODY_START_PATTERNS, line):
            start = index
            break

    end = len(lines)
    for index in range(start, len(lines)):
        if _matches_any(_BODY_END_PATTERNS, lines[index]):
            end = index
            break

    filtered = "\n".join(lines[start:end]).strip()
    return filtered or text.strip()


def filter_body_blocks(blocks: list[dict] | None, text: str | None = None) -> list[dict] | None:
    """Return body-only blocks, rebuilding from fuller text when stored blocks are truncated."""
    body_text = filter_body_text(text)
    body_text_len = _compact_len(body_text)
    blocks_text = "\n\n".join(
        block_text_from_dict(block) for block in blocks or [] if isinstance(block, dict) and block_text_from_dict(block)
    )

    if body_text and (not blocks or _compact_len(blocks_text) < int(body_text_len * _BLOCK_TEXT_COVERAGE_RATIO)):
        return markdown_to_blocks(body_text)
    if not blocks:
        return None

    start = 0
    for index, block in enumerate(blocks):
        if isinstance(block, dict) and _matches_any(_BODY_START_PATTERNS, block_text_from_dict(block)):
            start = index
            break

    end = len(blocks)
    for index in range(start, len(blocks)):
        block = blocks[index]
        if isinstance(block, dict) and _matches_any(_BODY_END_PATTERNS, block_text_from_dict(block)):
            end = index
            break

    filtered_blocks = [block for block in blocks[start:end] if isinstance(block, dict)]
    return filtered_blocks or None


def _load_blocks_from_dir(doc_dir: Path, track: str) -> list[dict] | None:
    """Try to load structured blocks from a single document directory."""
    doc_file = doc_dir / f"{track}.json"
    if not doc_file.exists():
        return None
    try:
        with open(doc_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        logger.warning("Failed to load {} blocks from {}", track, doc_file)
        return None
    if not isinstance(data, dict):
        return None
    blocks = data.get("blocks")
    if isinstance(blocks, list) and blocks:
        return blocks
    return None


def load_full_document_blocks(
    source_document_id: str | UUID,
    track: str = "original",
    identifiers: dict[str, str] | None = None,
    known_output_dir: str | None = None,
) -> list[dict] | None:
    """Load structured blocks for a source document from pipeline output.

    Mirrors :func:`load_full_document_text` but returns the ``blocks``
    array from the JSON (each block has ``type``, ``bbox``, ``page_idx``,
    ``text``, etc.) instead of the concatenated text.
    """
    if known_output_dir:
        result = _load_blocks_from_dir(Path(known_output_dir), track)
        if result:
            return result

    backend_root = Path(__file__).resolve().parents[4]
    doc_id_str = str(source_document_id)

    pipeline_root = backend_root / "data" / "pipeline"
    if pipeline_root.exists():
        for pipeline_dir in pipeline_root.iterdir():
            if not pipeline_dir.is_dir():
                continue
            for phase_dir in ("fact_chain", "parsing"):
                doc_dir = pipeline_dir / phase_dir / doc_id_str
                result = _load_blocks_from_dir(doc_dir, track)
                if result:
                    return result

    legacy_root = backend_root / "output" / "cross_lingual"
    if legacy_root.exists():
        for lang_dir in legacy_root.iterdir():
            if not lang_dir.is_dir():
                continue
            result = _load_blocks_from_dir(lang_dir / doc_id_str, track)
            if result:
                return result

        if identifiers:
            search_keys = [v.replace("/", "_") for v in identifiers.values() if v]
            for lang_dir in legacy_root.iterdir():
                if not lang_dir.is_dir():
                    continue
                for child in lang_dir.iterdir():
                    if not child.is_dir():
                        continue
                    if child.name in search_keys or child.name.replace("/", "_") in search_keys:
                        result = _load_blocks_from_dir(child, track)
                        if result:
                            return result

    return None


def markdown_to_blocks(markdown: str) -> list[dict] | None:
    """Parse a markdown document into MinerU-style ContentBlock dicts.

    Used as a last-resort fallback when neither the database nor the
    pipeline output directory contains structured blocks. The resulting
    blocks carry ``type``, ``text``, ``text_level``, and ``img_path``
    (no ``bbox`` — that requires MinerU's PDF parsing), which is enough
    for the frontend ``StructuredBlockRenderer`` to render headings,
    paragraphs, images, and HTML tables with proper formatting.
    """
    if not markdown or not markdown.strip():
        return None
    blocks: list[dict] = []
    lines = markdown.split("\n")
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()
        # Heading: # / ## / ### ...
        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            blocks.append(
                {
                    "type": "title",
                    "text_level": len(heading.group(1)),
                    "text": heading.group(2).strip(),
                    "page_idx": 0,
                }
            )
            i += 1
            continue
        # Image: ![alt](path)
        image = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)\s*$", stripped)
        if image:
            blocks.append(
                {
                    "type": "image",
                    "img_path": image.group(2).strip(),
                    "image_caption": [image.group(1)] if image.group(1) else [],
                    "page_idx": 0,
                }
            )
            i += 1
            continue
        # HTML table: <table>...</table>
        if stripped.lower().startswith("<table"):
            table_lines = [line]
            i += 1
            while i < n and "</table>" not in lines[i].lower():
                table_lines.append(lines[i])
                i += 1
            if i < n:
                table_lines.append(lines[i])
                i += 1
            blocks.append(
                {
                    "type": "table",
                    "table_body": "\n".join(table_lines),
                    "text": "",
                    "page_idx": 0,
                }
            )
            continue
        # Markdown table: | ... | with separator row
        if stripped.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|?\s*$", lines[i + 1].strip()):
            table_lines = [line, lines[i + 1]]
            i += 2
            while i < n and lines[i].strip().startswith("|"):
                table_lines.append(lines[i])
                i += 1
            header_cells = [c.strip() for c in table_lines[0].strip("|").split("|")]
            rows = [[c.strip() for c in tl.strip("|").split("|")] for tl in table_lines[2:]]
            html = "<table><thead><tr>" + "".join(f"<th>{c}</th>" for c in header_cells) + "</tr></thead><tbody>"
            for row in rows:
                html += "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
            html += "</tbody></table>"
            blocks.append(
                {
                    "type": "table",
                    "table_body": html,
                    "text": "",
                    "page_idx": 0,
                }
            )
            continue
        # List items: - / * / 1.
        if re.match(r"^[-*]\s+", stripped) or re.match(r"^\d+\.\s+", stripped):
            items: list[str] = []
            while i < n and (re.match(r"^[-*]\s+", lines[i].strip()) or re.match(r"^\d+\.\s+", lines[i].strip())):
                items.append(re.sub(r"^[-*]\s+|^\d+\.\s+", "", lines[i].strip()))
                i += 1
            blocks.append(
                {
                    "type": "list",
                    "list_items": items,
                    "text": "\n".join(items),
                    "page_idx": 0,
                }
            )
            continue
        # Blank line: skip
        if not stripped:
            i += 1
            continue
        # Text paragraph: collect contiguous non-blank, non-special lines
        para_lines = [line]
        i += 1
        while i < n:
            nxt = lines[i].strip()
            if not nxt or re.match(r"^#{1,6}\s+", nxt) or re.match(r"^!\[", nxt):
                break
            if nxt.lower().startswith("<table"):
                break
            if nxt.startswith("|") and i + 1 < n and re.match(r"^\|[\s:|-]+\|?\s*$", lines[i + 1].strip()):
                break
            if re.match(r"^[-*]\s+", nxt) or re.match(r"^\d+\.\s+", nxt):
                break
            para_lines.append(lines[i])
            i += 1
        blocks.append(
            {
                "type": "text",
                "text": "\n".join(para_lines).strip(),
                "page_idx": 0,
            }
        )
    return blocks if blocks else None


def _load_from_dir(doc_dir: Path, track: str) -> str | None:
    """Try to load and concatenate text from a single document directory."""
    doc_file = doc_dir / f"{track}.json"
    if not doc_file.exists():
        return None
    try:
        with open(doc_file, "r", encoding="utf-8") as f:
            return concat_document_text(json.load(f))
    except Exception:
        logger.warning("Failed to load full {} text from {}", track, doc_file)
        return None


def parse_translation_alignment(raw: Any) -> list[TranslationAlignmentChunk]:
    """Parse persisted translation alignment chunks."""
    if not isinstance(raw, list):
        return []

    chunks: list[TranslationAlignmentChunk] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            chunks.append(TranslationAlignmentChunk.model_validate(item))
        except ValueError:
            logger.warning("Skipping invalid translation alignment chunk: {}", item)
    return chunks


def _load_translation_alignment_from_dir(doc_dir: Path) -> list[TranslationAlignmentChunk]:
    """Load translation alignment metadata from one persisted document directory."""
    for filename in ("metadata.json", "translated.json"):
        path = doc_dir / filename
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            logger.warning("Failed to load translation alignment from {}", path)
            continue
        if not isinstance(data, dict):
            continue
        raw = data.get("translation_alignment")
        metadata = data.get("metadata")
        if raw is None and isinstance(metadata, dict):
            raw = metadata.get("translation_alignment")
        chunks = parse_translation_alignment(raw)
        if chunks:
            return chunks
    return []


def load_translation_alignment(
    source_document_id: str | UUID,
    raw_metadata: Any,
    identifiers: dict[str, str] | None = None,
    known_output_dir: str | None = None,
) -> list[TranslationAlignmentChunk]:
    """Load validated translation alignment for an evidence detail response."""
    if isinstance(raw_metadata, dict):
        chunks = parse_translation_alignment(raw_metadata.get("translation_alignment"))
        if chunks:
            return chunks

    if known_output_dir:
        chunks = _load_translation_alignment_from_dir(Path(known_output_dir))
        if chunks:
            return chunks

    backend_root = Path(__file__).resolve().parents[4]
    doc_id_str = str(source_document_id)
    pipeline_root = backend_root / "data" / "pipeline"
    if pipeline_root.exists():
        for pipeline_dir in pipeline_root.iterdir():
            if not pipeline_dir.is_dir():
                continue
            for phase_dir in ("fact_chain", "parsing"):
                chunks = _load_translation_alignment_from_dir(pipeline_dir / phase_dir / doc_id_str)
                if chunks:
                    return chunks

    legacy_root = backend_root / "output" / "cross_lingual"
    if legacy_root.exists():
        for lang_dir in legacy_root.iterdir():
            if not lang_dir.is_dir():
                continue
            chunks = _load_translation_alignment_from_dir(lang_dir / doc_id_str)
            if chunks:
                return chunks

        if identifiers:
            search_keys = [value.replace("/", "_") for value in identifiers.values() if value]
            for lang_dir in legacy_root.iterdir():
                if not lang_dir.is_dir():
                    continue
                for child in lang_dir.iterdir():
                    if not child.is_dir():
                        continue
                    if child.name in search_keys or child.name.replace("/", "_") in search_keys:
                        chunks = _load_translation_alignment_from_dir(child)
                        if chunks:
                            return chunks

    return []


def load_full_document_text(
    source_document_id: str | UUID,
    track: str = "original",
    identifiers: dict[str, str] | None = None,
    known_output_dir: str | None = None,
) -> str | None:
    """Load full text content for a source document from pipeline output.

    Searches in order:
    1. ``known_output_dir`` — exact path from pipeline_run_states.state_json.
    2. ``data/pipeline/*/fact_chain/{doc_id}/`` — scan current pipeline output.
    3. ``backend/output/cross_lingual/**/`` — legacy output (by UUID or identifiers).

    Returns concatenated text from all blocks, or None if not found.
    """
    # 1. Exact path from persisted pipeline state
    if known_output_dir:
        result = _load_from_dir(Path(known_output_dir), track)
        if result:
            return result

    backend_root = Path(__file__).resolve().parents[4]
    doc_id_str = str(source_document_id)

    # 2. Current pipeline output: data/pipeline/{run_id}/fact_chain/{doc_id}/
    pipeline_root = backend_root / "data" / "pipeline"
    if pipeline_root.exists():
        for pipeline_dir in pipeline_root.iterdir():
            if not pipeline_dir.is_dir():
                continue
            for phase_dir in ("fact_chain", "parsing"):
                doc_dir = pipeline_dir / phase_dir / doc_id_str
                result = _load_from_dir(doc_dir, track)
                if result:
                    return result

    # 3. Legacy output: backend/output/cross_lingual/{lang}/{doc_id}/
    legacy_root = backend_root / "output" / "cross_lingual"
    if legacy_root.exists():
        for lang_dir in legacy_root.iterdir():
            if not lang_dir.is_dir():
                continue
            result = _load_from_dir(lang_dir / doc_id_str, track)
            if result:
                return result

        if identifiers:
            search_keys = [v.replace("/", "_") for v in identifiers.values() if v]
            for lang_dir in legacy_root.iterdir():
                if not lang_dir.is_dir():
                    continue
                for child in lang_dir.iterdir():
                    if not child.is_dir():
                        continue
                    if child.name in search_keys or child.name.replace("/", "_") in search_keys:
                        result = _load_from_dir(child, track)
                        if result:
                            return result

    return None
