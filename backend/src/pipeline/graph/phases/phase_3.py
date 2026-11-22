"""Phase 3 adapter: source windows -> extraction -> verification -> fact English.

The approved route is a single source-fact chain. Full-document translation is
no longer part of Phase 3: only presentation fields of verified source facts
are translated, and English text never becomes extraction input.

Outputs per document:
- ``original.json`` / ``translated.json`` for the existing render layer
  (the translated document text is intentionally empty in this route)
- ``chain_run.json`` and JSONL artifacts (facts, verifications, English views,
  bilingual rows)
- ``extraction_result.json`` as a dual-track projection for Phase 4
  standardization: original track = source value, translated track = fact English
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path

import aiofiles
from loguru import logger

from src.runs.contracts import (
    PermanentPhaseError,
    PhaseStatus,
    PhaseStatusDetail,
    PipelineGraphState,
    SkipPhase4Reason,
    TranslationExtractionOutput,
    build_retryable_errors,
    classify_phase_error,
)
from src.pipeline.graph.agents.translation import detect_language
from src.pipeline.graph.agents.extraction import SourceFactChainService
from src.core.shared.tools.fact_chain.contracts import ChainRun, sha256_text
from src.pipeline.graph.agents.extraction import project_dual_result
from src.pipeline.skills.runtime.llm import ProviderError

_RETRYABLE_ERRORS = build_retryable_errors() + (ProviderError,)


def _join_pages(pages: list[dict]) -> tuple[str, list[tuple[int, int, int]]]:
    """Join page markdown exactly as ``ParseResult.full_markdown`` does.

    Returns the source text and ``(start, end, page_number)`` ranges so source
    spans can be attributed to a page without re-reading blocks.
    """
    parts: list[str] = []
    ranges: list[tuple[int, int, int]] = []
    cursor = 0
    for index, page in enumerate(pages, start=1):
        markdown = str(page.get("markdown", "") or "")
        page_number = int(page.get("page_number", index) or index)
        if parts:
            cursor += 2  # "\n\n" separator
        ranges.append((cursor, cursor + len(markdown), page_number))
        parts.append(markdown)
        cursor += len(markdown)
    return "\n\n".join(parts), ranges


def _blocks_for_render(content_blocks: list[dict], text: str, ranges: list[tuple[int, int, int]]) -> list[dict]:
    """Return MinerU blocks when present, otherwise a page-level fallback."""
    if content_blocks:
        return content_blocks
    blocks: list[dict] = []
    for start, end, page in ranges:
        page_text = text[start:end]
        if page_text.strip():
            blocks.append({"type": "text", "page_idx": page - 1, "text": page_text})
    return blocks


def _load_chain_run(path: Path) -> ChainRun | None:
    try:
        return ChainRun.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


class Phase3Adapter:
    """Run the source fact chain over the Phase 2 parsed document."""

    def __init__(self, chain_service: SourceFactChainService, output_root: Path | None = None):
        self._chain = chain_service
        self._output_root = output_root

    async def run(self, state: PipelineGraphState, *, force_rebuild: bool = False) -> PipelineGraphState:
        """Execute Phase 3 and persist the chain artifacts for Phase 4 and display.

        A persisted run is reused only when its source hash, chain config and
        prompt versions all match. Pass ``force_rebuild=True`` to ignore any
        persisted run and call the provider again.
        """
        logger.info("Phase 3 started: run={}", state.processing_run_id)
        state.phase_3_status = PhaseStatusDetail(
            status=PhaseStatus.RUNNING,
            started_at=datetime.now().isoformat(),
        )

        try:
            if state.phase_2_output is None:
                raise PermanentPhaseError("Phase 2 output not found in state", phase=3)

            async with aiofiles.open(state.phase_2_output.metadata_path, encoding="utf-8") as handle:
                parse_data = json.loads(await handle.read())
            pages = parse_data.get("pages", []) or []
            content_blocks = parse_data.get("content_blocks", []) or []

            source_text, page_ranges = _join_pages(pages)
            if not source_text.strip():
                source_text = await asyncio.to_thread(Path(state.phase_2_output.md_path).read_text, encoding="utf-8")
                page_ranges = [(0, len(source_text), 1)]
            if not source_text.strip():
                raise PermanentPhaseError("Phase 2 produced no document text", phase=3)

            language = detect_language(source_text)
            if language == "unknown":
                language = str(parse_data.get("source_language") or "unknown")

            base = self._output_root
            if base is None:
                base = Path(__file__).resolve().parents[5] / "data" / "pipeline"
            doc_dir = Path(base) / state.processing_run_id / "phase_3" / state.source_document_id
            doc_dir.mkdir(parents=True, exist_ok=True)

            chain_run_path = doc_dir / "chain_run.json"
            source_hash = sha256_text(source_text)
            run = None if force_rebuild else _load_chain_run(chain_run_path)
            blocker = "force_rebuild" if force_rebuild else self._chain.reuse_blocker(run, source_hash=source_hash)
            if run is not None and blocker is not None:
                logger.info("Phase 3 retry: rebuilding chain run ({})", blocker)
                run = None
            if run is not None:
                logger.info("Phase 3 retry: reusing persisted chain run (facts={})", len(run.facts))
            else:
                document = self._chain.build_document(
                    document_id=state.source_document_id,
                    text=source_text,
                    language=language,
                )
                run = await self._chain.run_async(document)
            # Always rewrite the full artifact set: a crash between
            # chain_run.json and the JSONL files must be recoverable on retry.
            self._chain.write_outputs(run, doc_dir)

            target = state.extraction_target
            dual_result = project_dual_result(
                run,
                extraction_target=target,
                page_ranges=page_ranges,
                target_gene=target.gene_symbol if target else "",
                target_disease=target.disease_name if target else "",
                target_variant=target.primary_variant if target else "",
            )
            extraction_path = doc_dir / "extraction_result.json"
            extraction_path.write_text(dual_result.model_dump_json(indent=2), encoding="utf-8")

            blocks = _blocks_for_render(content_blocks, source_text, page_ranges)
            original_path = doc_dir / "original.json"
            translated_path = doc_dir / "translated.json"
            original_path.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "doc_id": state.source_document_id,
                            "source_language": language,
                            "extraction_route": "source_fact_chain",
                        },
                        "formatted_text": source_text,
                        "blocks": blocks,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            translated_path.write_text(
                json.dumps(
                    {
                        "metadata": {
                            "doc_id": state.source_document_id,
                            "source_language": language,
                            "translation_skipped": "fact_level_presentation_only",
                        },
                        "formatted_text": "",
                        "blocks": [],
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            supported = self._chain.supported_fact_count(run)
            if supported == 0:
                state.skip_phase_4_reason = SkipPhase4Reason.NOT_RELEVANT
            else:
                # A retry may have produced supported facts after an earlier
                # empty run; a stale NOT_RELEVANT must not skip Phase 4.
                state.skip_phase_4_reason = None

            state.phase_3_output = TranslationExtractionOutput(
                output_dir=str(doc_dir),
                original_json_path=str(original_path),
                translated_json_path=str(translated_path),
                source_language=language,
                extraction_result_path=str(extraction_path),
                original_text=source_text,
                translated_text=None,
                original_blocks=blocks,
                translated_blocks=None,
                bilingual_rows_path=str(doc_dir / "bilingual.jsonl"),
                source_facts_path=str(doc_dir / "facts.jsonl"),
                chain_run_path=str(chain_run_path),
            )
            state.phase_3_status = PhaseStatusDetail.complete(
                started_at=state.phase_3_status.started_at,
                summary={
                    "route": "source_fact_chain",
                    "windows": len(run.windows),
                    "facts": len(run.facts),
                    "supported_facts": supported,
                    "provider_calls": run.provider_calls,
                    "source_language": language,
                },
            )
            logger.info(
                "Phase 3 completed: run={}, windows={}, facts={}, supported={}, calls={}",
                state.processing_run_id,
                len(run.windows),
                len(run.facts),
                supported,
                run.provider_calls,
            )
            return state

        except Exception as error:
            classify_phase_error(3, error, _RETRYABLE_ERRORS)
