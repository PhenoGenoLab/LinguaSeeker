"""Compatibility checks for the legacy re-export shims (stages 1 and 2)."""

from __future__ import annotations

from src.agents import (
    orchestrator as legacy_orchestrator,
    phase_1_adapter as legacy_phase_1,
    phase_2_adapter as legacy_phase_2,
    phase_3_adapter as legacy_phase_3,
    phase_4_adapter as legacy_phase_4,
)
from src.core import source_fact_chain as legacy_fact_chain
from src.pipeline.graph import topology as new_topology
from src.pipeline.graph.phases import (
    phase_1 as new_phase_1,
    phase_2 as new_phase_2,
    phase_3 as new_phase_3,
    phase_4 as new_phase_4,
)
from src.pipeline.skills.fact_chain import runner as new_runner
from src.pipeline.skills.fact_chain import service as new_service
from src.pipeline.tools.fact_chain import contracts as new_contracts
from src.pipeline.tools.fact_chain import projection as new_projection


def test_legacy_orchestrator_shim_reexports_topology() -> None:
    assert legacy_orchestrator.PipelineOrchestrator is new_topology.PipelineOrchestrator
    assert legacy_orchestrator.REQUIRED_UPSTREAM == new_topology.REQUIRED_UPSTREAM


def test_legacy_adapter_shims_reexport_phase_implementations() -> None:
    assert legacy_phase_1.Phase1Adapter is new_phase_1.Phase1Adapter
    assert legacy_phase_2.Phase2Adapter is new_phase_2.Phase2Adapter
    assert legacy_phase_3.Phase3Adapter is new_phase_3.Phase3Adapter
    assert legacy_phase_4.Phase4Adapter is new_phase_4.Phase4Adapter


def test_legacy_fact_chain_shims_reexport_new_implementation() -> None:
    assert legacy_fact_chain.SourceFactChainService is new_service.SourceFactChainService
    assert legacy_fact_chain.ChainRunner is new_runner.ChainRunner
    assert legacy_fact_chain.ChainRun is new_contracts.ChainRun
    assert legacy_fact_chain.project_dual_result is new_projection.project_dual_result
