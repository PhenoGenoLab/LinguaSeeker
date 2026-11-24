"""Standalone agent job routes for the v2 API.

Every sub-agent can be invoked on its own; routes only validate the request,
enqueue a job, and expose polling/result endpoints. Execution lives in
``src.api.v2.executors`` and is driven by the agent job worker.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException

from src.api.auth import get_current_account
from src.api.v2.contracts import (
    AcquisitionRequest,
    AgentJobAccepted,
    AgentJobResultResponse,
    AgentJobStatus,
    FactChainRequest,
    GraphRetrievalRequest,
    ParsingRequest,
    ReviewChatRequest,
    ReviewFeedbackRequest,
    ReviewSearchRequest,
    StandardizationRequest,
)
from src.api.wiring import get_session_factory
from src.core.foundation.auth.contracts import AuthContext
from src.dao.postgresql.agent_jobs import AgentJobRepository

router = APIRouter()

_AGENT_STATUS = {
    "queued": "queued",
    "running": "running",
    "succeeded": "succeeded",
    "failed": "failed",
    "cancelled": "cancelled",
}


def _repository() -> AgentJobRepository:
    return AgentJobRepository(get_session_factory())


async def _enqueue(
    *,
    agent: str,
    action: str | None,
    request_data: dict[str, object],
    account: AuthContext,
) -> AgentJobAccepted:
    repository = _repository()
    job_id = uuid.uuid4()
    await repository.enqueue(
        job_id=job_id,
        agent=agent,
        action=action,
        request_data=request_data,
        owner_user_id=account.owner_user_id,
    )
    return AgentJobAccepted(
        job_id=str(job_id),
        agent=agent,  # type: ignore[arg-type]
        status="queued",
        status_url=f"/api/v2/agents/jobs/{job_id}",
        result_url=f"/api/v2/agents/jobs/{job_id}/result",
    )


@router.post("/agents/acquisition", response_model=AgentJobAccepted, status_code=202)
async def run_acquisition(
    body: AcquisitionRequest,
    account: AuthContext = Depends(get_current_account),
) -> AgentJobAccepted:
    """Acquire literature online or resolve local files."""
    return await _enqueue(
        agent="acquisition",
        action=body.mode,
        request_data=body.model_dump(mode="json"),
        account=account,
    )


@router.post("/agents/parsing", response_model=AgentJobAccepted, status_code=202)
async def run_parsing(
    body: ParsingRequest,
    account: AuthContext = Depends(get_current_account),
) -> AgentJobAccepted:
    """Parse files with MinerU."""
    return await _enqueue(
        agent="parsing",
        action="parse",
        request_data=body.model_dump(mode="json"),
        account=account,
    )


@router.post("/agents/fact-chain", response_model=AgentJobAccepted, status_code=202)
async def run_fact_chain(
    body: FactChainRequest,
    account: AuthContext = Depends(get_current_account),
) -> AgentJobAccepted:
    """Run extraction, verification, and fact English on one document."""
    return await _enqueue(
        agent="fact_chain",
        action="run",
        request_data=body.model_dump(mode="json"),
        account=account,
    )


@router.post("/agents/standardization", response_model=AgentJobAccepted, status_code=202)
async def run_standardization(
    body: StandardizationRequest,
    account: AuthContext = Depends(get_current_account),
) -> AgentJobAccepted:
    """Standardize entities from one extraction result."""
    return await _enqueue(
        agent="standardization",
        action="run",
        request_data=body.model_dump(mode="json"),
        account=account,
    )


@router.post("/agents/graph-retrieval", response_model=AgentJobAccepted, status_code=202)
async def run_graph_retrieval(
    body: GraphRetrievalRequest,
    account: AuthContext = Depends(get_current_account),
) -> AgentJobAccepted:
    """Retrieve context or answer a question over the literature graph."""
    return await _enqueue(
        agent="graph_retrieval",
        action=body.mode,
        request_data=body.model_dump(mode="json"),
        account=account,
    )


@router.post("/agents/review/search", response_model=AgentJobAccepted, status_code=202)
async def run_review_search(
    body: ReviewSearchRequest,
    account: AuthContext = Depends(get_current_account),
) -> AgentJobAccepted:
    """Search persisted evidence."""
    return await _enqueue(
        agent="review",
        action="search",
        request_data=body.model_dump(mode="json"),
        account=account,
    )


@router.post("/agents/review/feedback", response_model=AgentJobAccepted, status_code=202)
async def run_review_feedback(
    body: ReviewFeedbackRequest,
    account: AuthContext = Depends(get_current_account),
) -> AgentJobAccepted:
    """Apply expert feedback to one evidence item."""
    return await _enqueue(
        agent="review",
        action="feedback",
        request_data=body.model_dump(mode="json"),
        account=account,
    )


@router.post("/agents/review/chat", response_model=AgentJobAccepted, status_code=202)
async def run_review_chat(
    body: ReviewChatRequest,
    account: AuthContext = Depends(get_current_account),
) -> AgentJobAccepted:
    """Ask one chat turn grounded in reviewed evidence."""
    return await _enqueue(
        agent="review",
        action="chat",
        request_data=body.model_dump(mode="json"),
        account=account,
    )


@router.get("/agents/jobs/{job_id}", response_model=AgentJobStatus)
async def get_job(
    job_id: str,
    account: AuthContext = Depends(get_current_account),
) -> AgentJobStatus:
    """Poll one agent job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="job_id must be a UUID") from exc
    job = await _repository().get(job_uuid, owner_user_id=account.owner_user_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    error = None
    if job.error_message:
        error = {
            "kind": job.error_kind or "permanent",
            "message": job.error_message,
        }
    return AgentJobStatus(
        job_id=job_id,
        agent=job.agent,  # type: ignore[arg-type]
        status=_AGENT_STATUS.get(job.status, "queued"),  # type: ignore[arg-type]
        created_at=job.created_at.isoformat() if job.created_at else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        finished_at=job.finished_at.isoformat() if job.finished_at else None,
        error=error,  # type: ignore[arg-type]
        result_url=f"/api/v2/agents/jobs/{job_id}/result" if job.status == "succeeded" else None,
    )


@router.get("/agents/jobs/{job_id}/result", response_model=AgentJobResultResponse)
async def get_job_result(
    job_id: str,
    account: AuthContext = Depends(get_current_account),
) -> AgentJobResultResponse:
    """Return the typed result of a finished agent job."""
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="job_id must be a UUID") from exc
    job = await _repository().get(job_uuid, owner_user_id=account.owner_user_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if job.status != "succeeded" or job.result is None:
        raise HTTPException(status_code=409, detail=f"Job {job_id} has no result yet")
    return AgentJobResultResponse(job_id=job_uuid, result=job.result)  # type: ignore[arg-type]
