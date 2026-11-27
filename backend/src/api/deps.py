"""API dependencies."""

from __future__ import annotations

from src.api.wiring import (
    get_neo4j_repository as _get_wiring_neo4j_repository,
    make_annotation_store,
    make_audit_store,
    make_evidence_store,
    make_feedback_store,
    make_literature_store,
    make_run_state_store,
    make_standardization_runner,
    make_user_store,
)
from src.pipeline.skills.review.factory import ReviewServiceFactory
from src.runs import RunStateStore
from src.ports.graph import GraphRepository
from src.ports.review import (
    AnnotationStore,
    AuditStore,
    EvidenceQueryStore,
    FeedbackStore,
    LiteratureStore,
)
from src.ports.standardization import StandardizationRunner
from src.ports.users import UserStore

_review_factory: ReviewServiceFactory | None = None


def get_neo4j_repository() -> GraphRepository:
    """Return the global graph repository (raises if not initialized)."""
    repository = _get_wiring_neo4j_repository()
    if repository is None:
        raise RuntimeError("Neo4j repository not initialized")
    return repository


def set_review_factory(factory: ReviewServiceFactory) -> None:
    """Set the global ReviewServiceFactory (called from lifespan startup)."""
    global _review_factory
    _review_factory = factory


def get_review_factory() -> ReviewServiceFactory:
    """Return the global ReviewServiceFactory (raises if not initialized)."""
    if _review_factory is None:
        raise RuntimeError("ReviewServiceFactory not initialized")
    return _review_factory


def get_user_store() -> UserStore:
    """Return a user store bound to the configured session factory."""
    return make_user_store()


def get_evidence_store() -> EvidenceQueryStore:
    """Return a read-only evidence query store for the current session factory."""
    return make_evidence_store()


def get_feedback_store() -> FeedbackStore:
    """Return a feedback store that owns the patch transaction."""
    return make_feedback_store()


def get_audit_store() -> AuditStore:
    """Return a read-only audit store for the current session factory."""
    return make_audit_store()


def get_literature_store() -> LiteratureStore:
    """Return a literature profile store for the current session factory."""
    return make_literature_store()


def get_annotation_store() -> AnnotationStore:
    """Return an annotation store for the current session factory."""
    return make_annotation_store()


def get_run_state_store() -> RunStateStore:
    """Return a run state store for the current session factory."""
    return make_run_state_store()


def get_standardization_runner() -> StandardizationRunner:
    """Return the PostgreSQL-backed standardization runner."""
    return make_standardization_runner()
