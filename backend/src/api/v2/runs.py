"""Directory runs for the v2 API.

One batch id groups one pipeline run per document. Document runs reuse the
existing pipeline job queue and dispatcher; v2 only adds batch metadata and a
stage-oriented read model.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query

from src.api.auth import get_current_account
from src.api.deps import get_run_state_store
from src.api.v1.pipeline import get_job_queue, get_pipeline_runner
from src.api.v2.contracts import (
    BatchCounts,
    BatchStatusResponse,
    DirectoryRunRequest,
    DirectoryRunResponse,
    RunHandle,
    RunListResponse,
    RunStatusResponse,
    StagesResponse,
    StageStatusResponse,
    StageSummaryResponse,
    StageNodeResponse,
    StageErrorResponse,
    StageRerunRequest,
)
from src.api.v2.directory import resolve_directory
from src.core.foundation.auth.contracts import AuthContext
from src.runs.contracts import (
    PhaseStatus,
    PipelineGraphState,
    PipelineStatus,
    STAGE_NAMES,
)

router = APIRouter()

_RUN_STATUS = {
    PipelineStatus.PENDING: "pending",
    PipelineStatus.RUNNING: "running",
    PipelineStatus.COMPLETED: "completed",
    PipelineStatus.FAILED: "failed",
}


def _now() -> str:
    return datetime.now().isoformat()


def _owns(state: PipelineGraphState, account: AuthContext) -> bool:
    owner = str(account.owner_user_id) if account.owner_user_id else None
    return state.owner_user_id == owner


def _stage_response(detail: Any) -> StageStatusResponse:
    error = None
    if detail.error:
        error = StageErrorResponse(
            message=detail.error.message,
            retryable=detail.error.retryable,
            attempt=detail.error.attempt,
            max_retries=detail.error.max_retries,
        )
    summary = detail.summary
    nodes: list[StageNodeResponse] = []
    if isinstance(summary, dict) and isinstance(summary.get("nodes"), list):
        for raw in summary["nodes"]:
            if isinstance(raw, dict) and raw.get("node_id"):
                nodes.append(StageNodeResponse.model_validate(raw))
    return StageStatusResponse(
        status=detail.status.value,
        started_at=detail.started_at,
        completed_at=detail.completed_at,
        duration_seconds=detail.duration_seconds,
        error=error,
        summary=StageSummaryResponse.model_validate(summary) if summary else None,
        nodes=nodes,
        count=summary.get("count") if isinstance(summary, dict) and isinstance(summary.get("count"), int) else None,
    )


def _status_response(state: PipelineGraphState, *, status_url: str | None = None) -> RunStatusResponse:
    stages = StagesResponse(
        acquisition=_stage_response(state.acquisition_status),
        parsing=_stage_response(state.parsing_status),
        fact_chain=_stage_response(state.fact_chain_status),
        standardization=_stage_response(state.standardization_status),
    )
    current = next(
        (name for number, name in STAGE_NAMES.items() if getattr(state, f"{name}_status").status != PhaseStatus.COMPLETED),
        None,
    )
    return RunStatusResponse(
        processing_run_id=state.processing_run_id,
        source_document_id=state.source_document_id,
        batch_id=state.batch_id,
        relative_path=state.relative_path,
        pipeline_status=_RUN_STATUS.get(state.pipeline_status, "pending"),
        current_stage=current,
        stages=stages,
        status_url=status_url,
    )


def _request_data(
    *,
    body: DirectoryRunRequest,
    batch_id: str,
    relative_path: str,
    upload_file_path: str,
    owner_user_id: str | None,
    processing_run_id: str | None = None,
    source_document_id: str | None = None,
) -> dict[str, Any]:
    return {
        "processing_run_id": processing_run_id or str(uuid.uuid4()),
        "source_document_id": source_document_id or str(uuid.uuid4()),
        "owner_user_id": owner_user_id,
        "batch_id": batch_id,
        "source_directory": body.directory,
        "relative_path": relative_path,
        "mode": "full",
        "source_type": "local",
        "source_key": relative_path,
        "upload_file_path": upload_file_path,
        "created_at": _now(),
        "extraction_target": body.extraction_target.model_dump(mode="json") if body.extraction_target else None,
        "extraction_profile": body.extraction_profile,
        "extraction_mode": body.extraction_mode,
        "ablation_disable_review": body.ablation_disable_review,
        "ablation_disable_target_guard": body.ablation_disable_target_guard,
        "ablation_disable_grounding": body.ablation_disable_grounding,
        "ablation_original_only": body.ablation_original_only,
        "review_reject_policy": body.review_reject_policy,
        "extraction_track_mode": body.extraction_track_mode,
    }


async def _enqueue(request_data: dict[str, Any], account: AuthContext) -> None:
    """Queue one document run through the shared job queue (or start it)."""
    runner = get_pipeline_runner()
    queue = get_job_queue()
    if queue is not None:
        await queue.enqueue(
            job_id=uuid.uuid4(),
            processing_run_id=uuid.UUID(request_data["processing_run_id"]),
            source_document_id=uuid.UUID(request_data["source_document_id"]),
            owner_user_id=account.owner_user_id,
            request_data=request_data,
        )
        return
    await runner.start(PipelineGraphState.from_request_data(request_data))


@router.post("/runs", response_model=DirectoryRunResponse, status_code=202)
async def create_directory_run(
    body: DirectoryRunRequest,
    account: AuthContext = Depends(get_current_account),
) -> DirectoryRunResponse:
    """Start one run per matching document in a server-side directory."""
    try:
        files = resolve_directory(
            body.directory,
            recursive=body.recursive,
            patterns=body.filename_patterns,
            max_documents=body.max_documents,
        )
    except OverflowError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    batch_id = str(uuid.uuid4())
    owner_user_id = str(account.owner_user_id) if account.owner_user_id else None
    handles: list[RunHandle] = []
    for item in files:
        request_data = _request_data(
            body=body,
            batch_id=batch_id,
            relative_path=item.relative_path,
            upload_file_path=str(item.absolute_path),
            owner_user_id=owner_user_id,
        )
        if not body.dry_run:
            await _enqueue(request_data, account)
        handles.append(
            RunHandle(
                processing_run_id=request_data["processing_run_id"],
                source_document_id=request_data["source_document_id"],
                relative_path=item.relative_path,
                status="pending" if body.dry_run else "queued",
                status_url=f"/api/v2/runs/{request_data['processing_run_id']}/status",
            )
        )
    return DirectoryRunResponse(
        batch_id=batch_id,
        status="dry_run" if body.dry_run else "queued",
        directory=body.directory,
        documents=handles,
        status_url=f"/api/v2/runs/batches/{batch_id}",
    )


@router.get("/runs", response_model=RunListResponse)
async def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    account: AuthContext = Depends(get_current_account),
) -> RunListResponse:
    """List the caller's most recent pipeline runs."""
    runner = get_pipeline_runner()
    rows, total = await runner.list_runs(limit=limit, offset=offset, owner_user_id=account.owner_user_id)
    states: list[PipelineGraphState] = []
    for row in rows:
        state = await runner.get_last_state(row.processing_run_id)
        if state is not None:
            states.append(state)
    return RunListResponse(
        items=[_status_response(state) for state in states],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/runs/batches/{batch_id}", response_model=BatchStatusResponse)
async def get_batch(
    batch_id: str,
    account: AuthContext = Depends(get_current_account),
) -> BatchStatusResponse:
    """Aggregate status of one directory batch."""
    try:
        uuid.UUID(batch_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="batch_id must be a UUID") from exc

    states = await get_run_state_store().states_for_batch(batch_id)
    states = [state for state in states if _owns(state, account)]
    if not states:
        raise HTTPException(status_code=404, detail=f"Batch {batch_id} not found")

    counts = BatchCounts(total=len(states))
    created: list[str] = []
    completed: list[str] = []
    for state in states:
        created.append(state.created_at or "")
        if state.pipeline_status in (PipelineStatus.COMPLETED, PipelineStatus.FAILED):
            finished = state.standardization_status.completed_at or state.parsing_status.completed_at
            if finished:
                completed.append(finished)
        if state.pipeline_status == PipelineStatus.COMPLETED:
            counts.completed += 1
        elif state.pipeline_status == PipelineStatus.FAILED:
            counts.failed += 1
        elif state.pipeline_status == PipelineStatus.RUNNING:
            counts.running += 1
        else:
            counts.queued += 1
    if counts.completed == counts.total:
        overall = "completed"
    elif counts.failed == counts.total:
        overall = "failed"
    elif counts.queued == counts.total:
        overall = "queued"
    else:
        overall = "running"
    return BatchStatusResponse(
        batch_id=batch_id,
        directory=states[0].source_directory or "",
        status=overall,
        counts=counts,
        created_at=min((value for value in created if value), default=None),
        completed_at=max(completed, default=None) if completed else None,
        documents=[
            RunHandle(
                processing_run_id=state.processing_run_id,
                source_document_id=state.source_document_id,
                relative_path=state.relative_path or "",
                status=_RUN_STATUS.get(state.pipeline_status, "pending"),
                status_url=f"/api/v2/runs/{state.processing_run_id}/status",
            )
            for state in states
        ],
    )


@router.get("/runs/{processing_run_id}/status", response_model=RunStatusResponse)
async def get_run_status(
    processing_run_id: str,
    account: AuthContext = Depends(get_current_account),
) -> RunStatusResponse:
    """Return one document run's stage-oriented status."""
    runner = get_pipeline_runner()
    state = await runner.get_last_state(processing_run_id)
    if state is None or not _owns(state, account):
        raise HTTPException(status_code=404, detail=f"Run {processing_run_id} not found")
    return _status_response(state, status_url=f"/api/v2/runs/{processing_run_id}/status")


@router.post("/runs/{processing_run_id}/rerun", response_model=RunHandle, status_code=202)
async def rerun_stage(
    processing_run_id: str,
    body: StageRerunRequest,
    account: AuthContext = Depends(get_current_account),
) -> RunHandle:
    """Re-run one stage of an existing document run."""
    runner = get_pipeline_runner()
    state = await runner.get_last_state(processing_run_id)
    if state is None or not _owns(state, account):
        raise HTTPException(status_code=404, detail=f"Run {processing_run_id} not found")
    if state.pipeline_status in (PipelineStatus.PENDING, PipelineStatus.RUNNING):
        raise HTTPException(status_code=409, detail=f"Run {processing_run_id} is still active")

    target_phase = _stage_number(body.stage)
    request_data: dict[str, Any] = {
        "processing_run_id": state.processing_run_id,
        "source_document_id": state.source_document_id,
        "owner_user_id": str(account.owner_user_id) if account.owner_user_id else None,
        "mode": "phase",
        "source_type": state.source_type.value,
        "target_phase": target_phase,
        "processing_run_id_ref": state.processing_run_id,
        "created_at": _now(),
    }
    await _enqueue(request_data, account)
    return RunHandle(
        processing_run_id=state.processing_run_id,
        source_document_id=state.source_document_id,
        relative_path=state.relative_path or "",
        status="queued",
        status_url=f"/api/v2/runs/{state.processing_run_id}/status",
    )


def _stage_number(name: str) -> int:
    for number, stage in STAGE_NAMES.items():
        if stage == name:
            return number
    raise HTTPException(status_code=400, detail=f"Unknown stage: {name}")
