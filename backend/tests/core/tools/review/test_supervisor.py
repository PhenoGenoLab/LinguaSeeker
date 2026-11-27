"""Tests for Supervisor action permissions."""

from __future__ import annotations

from src.core.tools.review.contracts import ChatAction
from src.pipeline.skills.review.supervisor import validate_supervisor_action


def test_allows_registered_read_only_action() -> None:
    action = ChatAction(intent="graph-qa", slots={"question": "What diseases relate to GLA?"})
    assert validate_supervisor_action(action) == action


def test_rejects_deprecated_intent() -> None:
    action = ChatAction(intent="start-pipeline", slots={"query": "BRCA1"})
    assert validate_supervisor_action(action) is None


def test_rejects_search_without_slots() -> None:
    action = ChatAction(intent="search-evidence", slots={})
    assert validate_supervisor_action(action) is None


def test_rejects_graph_without_question() -> None:
    action = ChatAction(intent="graph-qa", slots={})
    assert validate_supervisor_action(action) is None


def test_rejects_pipeline_without_source_type() -> None:
    action = ChatAction(intent="confirm-pipeline", slots={"identifiers": "PMID:1"})
    assert validate_supervisor_action(action) is None


def test_allows_valid_pipeline_action() -> None:
    action = ChatAction(
        intent="confirm-pipeline",
        slots={"source_type": "online", "identifiers": "PMID:1"},
    )
    assert validate_supervisor_action(action) == action
