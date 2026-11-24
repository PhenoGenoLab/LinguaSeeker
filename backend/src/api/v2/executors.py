"""Executors for standalone agent jobs (API v2).

Each handler adapts one v2 request model to the existing feature services.
Jobs are executed by :class:`src.runs.agent_worker.AgentJobWorker`; failures
must raise :class:`AgentJobFailure` with a stable classification.
"""

from __future__ import annotations

import asyncio
import hashlib
import uuid
from pathlib import Path
from typing import Any, Awaitable, Callable

from pydantic import ValidationError
from sqlalchemy import select

from src.api.v2.contracts import (
    AcquiredDocument,
    AcquisitionRequest,
    AcquisitionResult,
    FactChainRequest,
    FactChainResult,
    GraphEdge,
    GraphNode,
    GraphRetrievalRequest,
    GraphRetrievalResult,
    ParsedDocument,
    ParsingRequest,
    ParsingResult,
    ReviewChatRequest,
    ReviewChatResult,
    ReviewEvidenceHit,
    ReviewFeedbackRequest,
    ReviewFeedbackResult,
    ReviewSearchRequest,
    ReviewSearchResult,
    StandardizationRequest,
    StandardizationResult,
)
from src.api.v2.directory import ScannedFile, resolve_directory, input_root
from src.dao.postgresql.agent_jobs import AgentJobRow
from src.runs.agent_worker import AgentJobFailure


class AgentExecutor:
    """Dispatch a claimed agent job to its feature service."""

    def __init__(
        self,
        cfg: Any,
        *,
        session_factory: Any = None,
        neo4j_repository: Any = None,
        review_factory: Any = None,
    ):
        self._cfg = cfg
        self._session_factory = session_factory
        self._neo4j = neo4j_repository
        self._review_factory = review_factory

    async def execute(self, job: AgentJobRow) -> dict[str, object]:
        handler: Callable[[AgentJobRow], Awaitable[dict[str, object]]]
        if job.agent == "acquisition":
            handler = self._acquisition
        elif job.agent == "parsing":
            handler = self._parsing
        elif job.agent == "fact_chain":
            handler = self._fact_chain
        elif job.agent == "standardization":
            handler = self._standardization
        elif job.agent == "graph_retrieval":
            handler = self._graph_retrieval
        elif job.agent == "review":
            handler = self._review
        else:
            raise AgentJobFailure(f"unknown agent: {job.agent}")
        try:
            return await handler(job)
        except ValidationError as exc:
            raise AgentJobFailure(f"invalid request: {exc}") from exc

    # ── acquisition ─────────────────────────────────────────────────────

    async def _acquisition(self, job: AgentJobRow) -> dict[str, object]:
        request = AcquisitionRequest.model_validate(job.request_data)
        if request.mode in {"files", "directory"}:
            scanned = self._resolve_inputs(
                files=request.files,
                directory=request.directory,
                recursive=request.recursive,
                patterns=["*.pdf", "*.docx", "*.txt", "*.md"],
                max_documents=200,
            )
            documents = [
                AcquiredDocument(
                    path=str(item.absolute_path),
                    sha256=_sha256(item.absolute_path),
                    source="local" if request.mode == "files" else "directory",
                )
                for item in scanned
            ]
            return AcquisitionResult(documents=documents).model_dump(mode="json")

        from src.core.tools.acquisition.contracts import (
            AcquisitionSource,
            DocumentAcquisitionRequest,
        )
        from src.core.tools.acquisition.service import DocumentAcquisitionService

        download_dir = _work_dir(job.job_id) / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)
        result = await DocumentAcquisitionService().acquire(
            DocumentAcquisitionRequest(
                source=AcquisitionSource.ONLINE,
                action="download" if request.download_pdfs else "search",
                query=request.query,
                identifiers=request.identifiers,
                download_path=str(download_dir),
                relevance_gate=request.relevance_gate,
                literature_types=request.literature_types,
            )
        )
        if not result.success:
            raise AgentJobFailure(result.error or "online acquisition failed", kind="transient")
        documents = [
            AcquiredDocument(path=entry.file_path, source="online")
            for entry in result.downloads
            if entry.file_path
        ]
        return AcquisitionResult(documents=documents).model_dump(mode="json")

    # ── parsing ─────────────────────────────────────────────────────────

    async def _parsing(self, job: AgentJobRow) -> dict[str, object]:
        request = ParsingRequest.model_validate(job.request_data)
        scanned = self._resolve_inputs(
            files=request.files,
            directory=request.directory,
            recursive=request.recursive,
            patterns=["*.pdf", "*.docx", "*.txt", "*.md"],
            max_documents=200,
        )
        output_dir = Path(request.output_dir) if request.output_dir else _work_dir(job.job_id) / "parsed"
        output_dir.mkdir(parents=True, exist_ok=True)

        from src.core.tools.parsing import create_parse_service

        service = create_parse_service()
        batch = await service.parse_local_files_and_save(
            file_paths=[str(item.absolute_path) for item in scanned],
            output_dir=str(output_dir),
        )
        by_name = {item.absolute_path.name: item for item in scanned}
        documents: list[ParsedDocument] = []
        failed: list[str] = []
        for name, saved in batch.saved_files.items():
            source = by_name.get(name)
            if saved is None:
                failed.append(name)
                continue
            documents.append(
                ParsedDocument(
                    source_path=str(source.absolute_path) if source else name,
                    md_path=str(saved.md_path),
                    metadata_path=str(saved.metadata_path),
                    images_dir=str(saved.images_dir) if saved.images_dir else None,
                    pages=None,
                )
            )
        for name in batch.parse_result.results:
            if name not in batch.saved_files:
                failed.append(name)
        return ParsingResult(documents=documents, failed=failed).model_dump(mode="json")

    # ── fact_chain ──────────────────────────────────────────────────────

    async def _fact_chain(self, job: AgentJobRow) -> dict[str, object]:
        request = FactChainRequest.model_validate(job.request_data)
        if request.source.md_path:
            md_path = Path(request.source.md_path)
            if not md_path.is_file():
                raise AgentJobFailure(f"markdown file not found: {md_path}")
            text = md_path.read_text(encoding="utf-8")
            document_id = request.source.document_id or md_path.stem
        else:
            document_id = request.source.document_id or ""
            text, md_path = await self._load_document_text(document_id)
            if not text:
                raise AgentJobFailure(f"document not found or empty: {document_id}")

        from src.core.tools.translation.translate.language_detector import detect_language
        from src.pipeline.skills.extraction.service import SourceFactChainService

        language = detect_language(text) or "en"
        service = SourceFactChainService(
            self._cfg,
            window_chars=request.window_chars,
            window_overlap=request.window_overlap,
            max_provider_calls=request.max_provider_calls,
        )
        document = service.build_document(document_id=document_id, text=text, language=language)
        run = await asyncio.to_thread(service.run, document)
        out_dir = _work_dir(job.job_id) / "fact_chain"
        artifacts = service.write_outputs(run, out_dir)

        verifications: dict[str, int] = {}
        for verification in run.verifications:
            key = getattr(verification, "verdict", None) or getattr(verification, "status", "unknown")
            key = str(key)
            verifications[key] = verifications.get(key, 0) + 1
        return FactChainResult(
            document_id=document_id,
            chain_run_path=artifacts.run_json,
            facts=len(run.facts),
            verifications=verifications,
            rejections=[r.reason for r in run.rejections if getattr(r, "reason", None)],
            prompt_versions=run.prompt_versions.model_dump(mode="json") if run.prompt_versions else {},
        ).model_dump(mode="json")

    # ── standardization ─────────────────────────────────────────────────

    async def _standardization(self, job: AgentJobRow) -> dict[str, object]:
        request = StandardizationRequest.model_validate(job.request_data)
        dual_path = request.source.dual_result_path
        document_id = request.source.document_id
        if not dual_path:
            dual_path = await self._resolve_dual_result_path(document_id or "")
        if not dual_path or not Path(dual_path).is_file():
            raise AgentJobFailure("cannot resolve a dual evidence extraction result for this document")

        if self._session_factory is None:
            raise AgentJobFailure("standardization requires a database session", kind="transient")

        from src.core.tools.extraction.contracts import DualEvidenceExtractionResult
        from src.pipeline.skills.standardization.api import EntityStandardizationService

        dual = DualEvidenceExtractionResult.model_validate_json(Path(dual_path).read_text(encoding="utf-8"))
        async with self._session_factory() as session:
            service = EntityStandardizationService(self._cfg)
            result = await service.run_dual_result(
                session,
                dual,
                source_document_id=document_id or str(job.job_id),
                processing_run_id=str(job.job_id),
            )
            await session.commit()

        return StandardizationResult(
            document_id=document_id,
            standardized=result.standardized_count,
            unstandardized=result.unmapped_count,
            ambiguous=result.ambiguous_count,
        ).model_dump(mode="json")

    # ── graph_retrieval ─────────────────────────────────────────────────

    async def _graph_retrieval(self, job: AgentJobRow) -> dict[str, object]:
        request = GraphRetrievalRequest.model_validate(job.request_data)
        if self._neo4j is None:
            raise AgentJobFailure("Neo4j repository is not configured", kind="transient")

        if request.mode == "qa":
            from src.pipeline.skills.graph_retrieval.core.qa_engine import GraphRagQaEngine

            response = await GraphRagQaEngine(self._neo4j).query(request.query, hops=request.hops)
            return GraphRetrievalResult(
                answer=response.answer,
                nodes=[
                    GraphNode(
                        node_id=node.id,
                        node_type=node.type,
                        label=node.label,
                        properties=dict(node.properties or {}),
                    )
                    for node in response.subgraph.nodes
                ],
                edges=[
                    GraphEdge(
                        source_id=edge.source,
                        target_id=edge.target,
                        relation=edge.type,
                        properties=dict(edge.properties or {}),
                    )
                    for edge in response.subgraph.edges
                ],
                sources=list(response.source_evidence_ids),
            ).model_dump(mode="json")

        if request.extraction_target is None:
            raise AgentJobFailure("mode='retrieve' requires extraction_target")
        from src.pipeline.skills.graph_retrieval.api import GraphRagService

        context = await GraphRagService(self._neo4j).retrieve_context_for_target(
            request.extraction_target, hops=request.hops
        )
        return GraphRetrievalResult(context=context).model_dump(mode="json")

    # ── review ──────────────────────────────────────────────────────────

    async def _review(self, job: AgentJobRow) -> dict[str, object]:
        action = job.action or "search"
        if action == "search":
            return await self._review_search(job)
        if action == "feedback":
            return await self._review_feedback(job)
        if action == "chat":
            return await self._review_chat(job)
        raise AgentJobFailure(f"unknown review action: {action}")

    async def _review_search(self, job: AgentJobRow) -> dict[str, object]:
        request = ReviewSearchRequest.model_validate(job.request_data)
        if self._session_factory is None:
            raise AgentJobFailure("review search requires a database session", kind="transient")
        from src.core.tools.review.search_service import SearchService

        async with self._session_factory() as session:
            response = await SearchService(session).search_evidence(page=1, page_size=200)
        needle = request.query.strip().lower()
        hits: list[ReviewEvidenceHit] = []
        for row in response.items:
            text = " ".join(str(value) for value in (row.gene, row.variant, row.disease, row.title) if value)
            if needle and needle not in text.lower():
                continue
            if request.document_id and str(row.source_document_id) != request.document_id:
                continue
            if request.group_id and row.group_id != request.group_id:
                continue
            hits.append(
                ReviewEvidenceHit(
                    evidence_id=row.group_id,
                    document_id=str(row.source_document_id),
                    group_id=row.group_id,
                    snippet=text or None,
                )
            )
        total = len(hits)
        page = hits[request.offset : request.offset + request.limit]
        return ReviewSearchResult(hits=page, total=total).model_dump(mode="json")

    async def _review_feedback(self, job: AgentJobRow) -> dict[str, object]:
        request = ReviewFeedbackRequest.model_validate(job.request_data)
        if self._session_factory is None:
            raise AgentJobFailure("review feedback requires a database session", kind="transient")
        from src.core.tools.review.contracts import EvidencePatchRequest, ReviewStatus
        from src.core.tools.review.feedback_service import FeedbackService

        fields: dict[str, str | None] = {}
        if request.action == "correct":
            fields[request.field_name or ""] = request.corrected_value
        new_status = {
            "confirm": ReviewStatus.APPROVED,
            "reject": ReviewStatus.REJECTED,
            "correct": ReviewStatus.CORRECTED,
        }[request.action]
        patch = EvidencePatchRequest(fields=fields, change_reason=request.note, new_status=new_status)
        async with self._session_factory() as session:
            result = await FeedbackService(session).patch_evidence(
                canonical_evidence_id=uuid.UUID(request.evidence_id),
                patch=patch,
            )
            await session.commit()
        return ReviewFeedbackResult(
            evidence_id=request.evidence_id,
            status=result.new_status.value,
        ).model_dump(mode="json")

    async def _review_chat(self, job: AgentJobRow) -> dict[str, object]:
        request = ReviewChatRequest.model_validate(job.request_data)
        if self._session_factory is None:
            raise AgentJobFailure("review chat requires a database session", kind="transient")
        if self._review_factory is None:
            raise AgentJobFailure("review chat requires the chat LLM provider", kind="transient")

        async with self._session_factory() as session:
            service = self._review_factory.create_chat_service(session)
            session_id = uuid.UUID(request.session_id) if request.session_id else None
            if session_id is None:
                created = await service.create_session(processing_run_id=None)
                session_id = created.chat_session_id
            await service.append_message(
                session_id=session_id,
                role="user",
                content=request.message,
            )
            reply = await service.generate_reply(
                session_id=session_id,
                user_message=request.message,
            )
            if not reply:
                raise AgentJobFailure("chat provider returned an empty reply", kind="transient")
            await service.append_message(
                session_id=session_id,
                role="assistant",
                content=reply,
            )
            await session.commit()
        return ReviewChatResult(
            session_id=str(session_id),
            reply=reply,
        ).model_dump(mode="json")

    # ── helpers ─────────────────────────────────────────────────────────

    def _resolve_inputs(
        self,
        *,
        files: list[str] | None,
        directory: str | None,
        recursive: bool,
        patterns: list[str],
        max_documents: int,
    ) -> list[ScannedFile]:
        if directory:
            return resolve_directory(
                directory,
                recursive=recursive,
                patterns=patterns,
                max_documents=max_documents,
            )
        base = input_root()
        scanned: list[ScannedFile] = []
        for raw in files or []:
            path = (base / raw).resolve()
            if base not in path.parents:
                raise AgentJobFailure(f"file escapes the pipeline input root: {raw}")
            if not path.is_file():
                raise AgentJobFailure(f"file not found: {raw}")
            scanned.append(ScannedFile(relative_path=path.relative_to(base).as_posix(), absolute_path=path))
        return scanned

    async def _load_document_text(self, document_id: str) -> tuple[str, Path | None]:
        """Load parsed markdown for a stored document by run state."""
        if self._session_factory is None or not document_id:
            return "", None
        from src.dao.postgresql.models import PipelineRunState

        async with self._session_factory() as session:
            stmt = (
                select(PipelineRunState)
                .where(PipelineRunState.source_document_id == uuid.UUID(document_id))
                .order_by(PipelineRunState.created_at.desc())
                .limit(1)
            )
            state = (await session.execute(stmt)).scalar_one_or_none()
        if state is None:
            return "", None
        payload = state.state_json or {}
        parsing = payload.get("parsing_output") or {}
        md_path = parsing.get("md_path") or payload.get("markdown_path")
        if not md_path or not Path(md_path).is_file():
            return "", None
        return Path(md_path).read_text(encoding="utf-8"), Path(md_path)

    async def _resolve_dual_result_path(self, document_id: str) -> str | None:
        if self._session_factory is None or not document_id:
            return None
        from src.dao.postgresql.models import PipelineRunState

        async with self._session_factory() as session:
            stmt = (
                select(PipelineRunState)
                .where(PipelineRunState.source_document_id == uuid.UUID(document_id))
                .order_by(PipelineRunState.created_at.desc())
                .limit(1)
            )
            state = (await session.execute(stmt)).scalar_one_or_none()
        if state is None:
            return None
        output = (state.state_json or {}).get("fact_chain_output") or {}
        return output.get("extraction_result_path")


def _work_dir(job_id: uuid.UUID) -> Path:
    """Per-job scratch directory under the pipeline data root."""
    root = input_root().parent / "jobs"
    path = root / str(job_id)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
