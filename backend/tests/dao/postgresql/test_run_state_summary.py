"""Tests for run-list summary helpers."""

from __future__ import annotations

from src.dao.postgresql.run_state_store import (
    _count_completed_phases,
    _derive_current_phase,
)


def test_legacy_three_phase_snapshot_counts_all_stages() -> None:
    """A completed pre-4-phase row reports 4/4 completed stages."""
    snapshot = {
        "phase_1_status": {"status": "completed"},
        "phase_2_status": {"status": "completed"},
        "phase_3_status": {"status": "completed"},
    }

    assert _count_completed_phases(snapshot) == (4, 4)
    assert _derive_current_phase(snapshot) is None


def test_legacy_four_phase_running_snapshot_maps_current_stage() -> None:
    """A legacy four-phase running stage maps to the current stage name."""
    snapshot = {
        "phase_1_status": {"status": "completed"},
        "phase_2_status": {"status": "completed"},
        "phase_3_status": {"status": "running"},
        "phase_4_status": {"status": "pending"},
    }

    assert _count_completed_phases(snapshot) == (2, 4)
    assert _derive_current_phase(snapshot) == "fact_chain"
