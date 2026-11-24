"""Tests for v2 directory scanning and the agent job worker."""

from __future__ import annotations

import asyncio
import uuid

import pytest

from src.api.v2.directory import resolve_directory
from src.dao.postgresql.agent_jobs import AgentJobRow
from src.runs.agent_worker import AgentJobFailure, AgentJobWorker


def test_resolve_directory_matches_patterns(tmp_path):
    (tmp_path / "a.pdf").write_bytes(b"a")
    (tmp_path / "notes.txt").write_text("x")
    nested = tmp_path / "sub"
    nested.mkdir()
    (nested / "b.PDF").write_bytes(b"b")

    matches = resolve_directory("", recursive=True, patterns=["*.pdf"], max_documents=10, root=tmp_path)

    assert [item.relative_path for item in matches] == ["a.pdf"]


def test_resolve_directory_recursive_and_relative_paths(tmp_path):
    nested = tmp_path / "dir" / "sub"
    nested.mkdir(parents=True)
    (nested / "doc.pdf").write_bytes(b"x")

    matches = resolve_directory("dir", recursive=True, patterns=["*.pdf"], max_documents=10, root=tmp_path)

    assert [item.relative_path for item in matches] == ["dir/sub/doc.pdf"]


def test_resolve_directory_rejects_escape(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        resolve_directory("../outside", recursive=True, patterns=["*.pdf"], max_documents=10, root=tmp_path)


def test_resolve_directory_rejects_overflow(tmp_path):
    for index in range(3):
        (tmp_path / f"{index}.pdf").write_bytes(b"x")
    with pytest.raises(OverflowError):
        resolve_directory("", recursive=True, patterns=["*.pdf"], max_documents=2, root=tmp_path)


def test_resolve_directory_requires_matches(tmp_path):
    (tmp_path / "empty").mkdir()
    with pytest.raises(ValueError, match="no files"):
        resolve_directory("empty", recursive=True, patterns=["*.pdf"], max_documents=10, root=tmp_path)


def _job(agent: str = "acquisition") -> AgentJobRow:
    return AgentJobRow(
        job_id=uuid.uuid4(),
        agent=agent,
        action=None,
        status="running",
        request_data={},
        result=None,
        error_message=None,
        error_kind=None,
        owner_user_id=None,
        created_at=None,
        started_at=None,
        finished_at=None,
    )


class _FakeRepository:
    def __init__(self) -> None:
        self.completed: list[tuple[uuid.UUID, dict[str, object]]] = []
        self.failed: list[tuple[uuid.UUID, str, str]] = []

    async def complete(self, job_id, result):
        self.completed.append((job_id, result))

    async def fail(self, job_id, message, *, kind="permanent"):
        self.failed.append((job_id, message, kind))


class _Executor:
    def __init__(self, error: Exception | None = None):
        self._error = error

    async def execute(self, job: AgentJobRow) -> dict[str, object]:
        if self._error:
            raise self._error
        return {"kind": "acquisition", "agent": "acquisition", "documents": [], "skipped": 0}


def test_worker_records_success():
    repository = _FakeRepository()
    worker = AgentJobWorker(repository, _Executor())  # type: ignore[arg-type]
    job = _job()

    asyncio.run(worker._execute(job))

    assert repository.completed == [(job.job_id, {"kind": "acquisition", "agent": "acquisition", "documents": [], "skipped": 0})]
    assert repository.failed == []


def test_worker_classifies_failures():
    repository = _FakeRepository()
    worker = AgentJobWorker(repository, _Executor(AgentJobFailure("boom", kind="transient")))  # type: ignore[arg-type]
    job = _job()

    asyncio.run(worker._execute(job))

    assert repository.completed == []
    assert repository.failed == [(job.job_id, "boom", "transient")]


def test_worker_marks_unexpected_errors_permanent():
    repository = _FakeRepository()
    worker = AgentJobWorker(repository, _Executor(RuntimeError("kaboom")))  # type: ignore[arg-type]
    job = _job()

    asyncio.run(worker._execute(job))

    assert repository.failed == [(job.job_id, "kaboom", "permanent")]


def test_acquisition_executor_resolves_local_files(tmp_path, monkeypatch):
    from src.api.v2.contracts import AcquisitionRequest
    from src.api.v2.executors import AgentExecutor

    monkeypatch.setenv("PIPELINE_INPUT_ROOT", str(tmp_path))
    (tmp_path / "paper.pdf").write_bytes(b"pdf-bytes")
    job = _job("acquisition")
    job = AgentJobRow(
        job_id=job.job_id,
        agent="acquisition",
        action="files",
        status="running",
        request_data=AcquisitionRequest(mode="files", files=["paper.pdf"]).model_dump(mode="json"),
        result=None,
        error_message=None,
        error_kind=None,
        owner_user_id=None,
        created_at=None,
        started_at=None,
        finished_at=None,
    )

    result = asyncio.run(AgentExecutor(None).execute(job))

    assert result["kind"] == "acquisition"
    assert len(result["documents"]) == 1
    document = result["documents"][0]
    assert document["path"].endswith("paper.pdf")
    assert document["sha256"] is not None
    assert document["source"] == "local"
