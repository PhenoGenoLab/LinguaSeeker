"""Public facade for the source fact chain (Phase 3 cutover).

The pipeline calls ``SourceFactChainService.run`` once per parsed document.
The service owns configuration, provider construction and artifact writing;
stage semantics stay in ``runner`` and ``core``.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from loguru import logger

from src.core.evidence_extraction.contracts import DualEvidenceExtractionResult

from src.pipeline.mcp.registry import build_memory_client
from src.pipeline.mcp.reme.client import MemoryClient
from src.pipeline.tools.fact_chain.contracts import (
    ChainConfig,
    ChainRun,
    PromptVersions,
    SourceDocument,
    canonical_json,
    sha256_text,
)
from src.pipeline.tools.fact_chain.projection import project_dual_result, supported_facts
from src.pipeline.skills.fact_chain.prompts import PRESENTATION_VERSION, current_prompt_versions
from src.pipeline.skills.fact_chain.runner import ChainRunner
from src.pipeline.skills.runtime.llm import LangChainChainProvider, Provider

DEFAULT_WINDOW_CHARS = 4000
DEFAULT_WINDOW_OVERLAP = 200


@dataclass(frozen=True)
class ChainArtifacts:
    """Paths written for one document's chain run."""

    run_json: str
    facts_jsonl: str
    verifications_jsonl: str
    english_jsonl: str
    bilingual_jsonl: str


def _build_provider(cfg: Any, memory: MemoryClient) -> Provider:
    """Build the stage provider; AgentScope loads only for shadow/agentscope."""
    legacy = LangChainChainProvider(cfg)
    mode = getattr(getattr(cfg, "pipeline", None), "agent_runtime", "legacy")
    if mode not in ("shadow", "agentscope"):
        if mode != "legacy":
            logger.warning("unknown pipeline.agent_runtime={!r}; using legacy provider", mode)
        return legacy
    from src.pipeline.skills.fact_chain.extract import ExtractSkill
    from src.pipeline.skills.fact_chain.router import StageRouterProvider
    from src.pipeline.skills.fact_chain.translate import TranslateSkill
    from src.pipeline.skills.fact_chain.verify import VerifySkill

    skills = {skill.stage: skill for skill in (ExtractSkill(cfg, memory=memory), VerifySkill(cfg), TranslateSkill(cfg))}
    return StageRouterProvider(legacy=legacy, skills=skills, mode=mode)


class SourceFactChainService:
    """Runs window -> extract -> verify -> fact-English -> bilingual rows."""

    def __init__(
        self,
        cfg: Any,
        *,
        provider: Provider | None = None,
        window_chars: int = DEFAULT_WINDOW_CHARS,
        window_overlap: int = DEFAULT_WINDOW_OVERLAP,
        max_provider_calls: int = 0,
        memory: MemoryClient | None = None,
    ):
        self._cfg = cfg
        self._memory = memory if memory is not None else build_memory_client(cfg)
        self._provider = provider if provider is not None else _build_provider(cfg, self._memory)
        self._window_chars = window_chars
        self._window_overlap = window_overlap
        self._max_provider_calls = max_provider_calls
        self._config: ChainConfig | None = None

    @property
    def config(self) -> ChainConfig:
        if self._config is None:
            cfg = self._cfg
            self._config = ChainConfig(
                extract_model=cfg.llm.model,
                verify_model=cfg.reasoning.model or cfg.llm.model,
                translate_model=cfg.llm.model,
                window_chars=self._window_chars,
                window_overlap=self._window_overlap,
                max_provider_calls=self._max_provider_calls,
            )
        return self._config

    @property
    def prompt_versions(self) -> PromptVersions:
        """Prompt/presentation identities that a persisted run must match."""
        return current_prompt_versions(PRESENTATION_VERSION)

    def reuse_blocker(self, run: ChainRun | None, *, source_hash: str) -> str | None:
        """Return why a persisted run cannot be reused, or ``None`` if it can.

        Reuse requires the same source bytes, the same chain configuration and
        the same prompt/presentation versions. Runs with zero facts are never
        reused: an empty provider reply may be a transient extraction accident
        and must be retryable.
        """
        if run is None:
            return "missing"
        if run.source_hash != source_hash:
            return "source_hash_changed"
        if run.config != self.config:
            return "config_changed"
        if run.prompt_versions != self.prompt_versions:
            return "prompt_version_changed"
        if not run.facts:
            return "empty_run"
        return None

    def build_document(self, *, document_id: str, text: str, language: str) -> SourceDocument:
        return SourceDocument(
            document_id=document_id,
            text=text,
            language=language or "unknown",
            source_hash=sha256_text(text),
        )

    def run(self, document: SourceDocument) -> ChainRun:
        run = ChainRunner(self._provider, self.config).run(document)
        self._remember(run)
        return run

    def _remember(self, run: ChainRun) -> None:
        """Best-effort run summary; counts and field ids only, never raw text."""
        labels: dict[str, int] = {}
        for verification in run.verifications:
            key = verification.label.value
            labels[key] = labels.get(key, 0) + 1
        summary = canonical_json(
            {
                "language": run.language,
                "windows": len(run.windows),
                "facts": len(run.facts),
                "field_ids": sorted({fact.field_id for fact in run.facts}),
                "verifications": labels,
                "rejections": sorted({rejection.reason for rejection in run.rejections}),
                "prompt_versions": run.prompt_versions.model_dump() if run.prompt_versions else {},
            }
        )
        receipt = self._memory.auto_memory(session_id=run.document_id, text=summary)
        if not receipt.accepted:
            logger.debug("run memory not written: {}", receipt.detail)

    async def run_async(self, document: SourceDocument) -> ChainRun:
        """Run the synchronous model chain without blocking the event loop."""
        return await asyncio.to_thread(self.run, document)

    def write_outputs(self, run: ChainRun, out_dir: str | Path) -> ChainArtifacts:
        directory = Path(out_dir)
        directory.mkdir(parents=True, exist_ok=True)
        run_path = directory / "chain_run.json"
        facts_path = directory / "facts.jsonl"
        verifications_path = directory / "verifications.jsonl"
        english_path = directory / "english.jsonl"
        bilingual_path = directory / "bilingual.jsonl"

        run_path.write_text(run.model_dump_json(indent=2), encoding="utf-8")
        _write_jsonl(facts_path, [fact.model_dump(mode="json") for fact in run.facts])
        _write_jsonl(verifications_path, [item.model_dump(mode="json") for item in run.verifications])
        _write_jsonl(english_path, [view.model_dump(mode="json") for view in run.english])
        _write_jsonl(bilingual_path, [row.model_dump(mode="json") for row in run.bilingual_rows()])
        return ChainArtifacts(
            run_json=str(run_path),
            facts_jsonl=str(facts_path),
            verifications_jsonl=str(verifications_path),
            english_jsonl=str(english_path),
            bilingual_jsonl=str(bilingual_path),
        )

    def project_dual_result(
        self,
        run: ChainRun,
        *,
        extraction_target: Any | None = None,
        page_ranges: list[tuple[int, int, int]] | None = None,
        target_gene: str = "",
        target_disease: str = "",
        target_variant: str = "",
    ) -> DualEvidenceExtractionResult:
        return project_dual_result(
            run,
            extraction_target=extraction_target,
            page_ranges=page_ranges,
            target_gene=target_gene,
            target_disease=target_disease,
            target_variant=target_variant,
        )

    @staticmethod
    def supported_fact_count(run: ChainRun) -> int:
        return len(supported_facts(run))


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


__all__ = ["ChainArtifacts", "SourceFactChainService"]
