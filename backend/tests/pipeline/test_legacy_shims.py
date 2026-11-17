"""Compatibility checks for the stage-1 legacy re-export shims."""

from __future__ import annotations

from src.agents import (
    orchestrator as legacy_orchestrator,
    phase_1_adapter as legacy_phase_1,
    phase_2_adapter as legacy_phase_2,
    phase_3_adapter as legacy_phase_3,
    phase_4_adapter as legacy_phase_4,
)
from src.pipeline.graph import topology as new_topology
from src.pipeline.graph.phases import (
    phase_1 as new_phase_1,
    phase_2 as new_phase_2,
    phase_3 as new_phase_3,
    phase_4 as new_phase_4,
)


def test_legacy_orchestrator_shim_reexports_topology() -> None:
    assert legacy_orchestrator.PipelineOrchestrator is new_topology.PipelineOrchestrator
    assert legacy_orchestrator.REQUIRED_UPSTREAM == new_topology.REQUIRED_UPSTREAM


def test_legacy_adapter_shims_reexport_phase_implementations() -> None:
    assert legacy_phase_1.Phase1Adapter is new_phase_1.Phase1Adapter
    assert legacy_phase_2.Phase2Adapter is new_phase_2.Phase2Adapter
    assert legacy_phase_3.Phase3Adapter is new_phase_3.Phase3Adapter
    assert legacy_phase_4.Phase4Adapter is new_phase_4.Phase4Adapter
