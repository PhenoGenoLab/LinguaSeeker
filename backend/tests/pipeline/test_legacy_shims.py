"""Compatibility checks for the legacy re-export shims (stages 1–4b)."""

from __future__ import annotations

import importlib
import pkgutil

import pytest

from src.agents import (
    orchestrator as legacy_orchestrator,
    phase_1_adapter as legacy_phase_1,
    phase_2_adapter as legacy_phase_2,
    phase_3_adapter as legacy_phase_3,
    phase_4_adapter as legacy_phase_4,
)
from src.core import source_fact_chain as legacy_fact_chain
from src.core.terminology_shared import contracts as shared_contracts
from src.core.terminology_shared.context_pack import core as shared_context_pack
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
from src.pipeline.tools.terminology import api as new_terminology_api


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


def test_legacy_terminology_shims_reexport_new_implementation() -> None:
    from src.core.standardize_entities_and_align_knowledge import api as legacy_api
    from src.core.standardize_entities_and_align_knowledge import contracts as legacy_contracts
    from src.core.standardize_entities_and_align_knowledge.context_pack import core as legacy_context_pack

    assert legacy_api.EntityStandardizationService is new_terminology_api.EntityStandardizationService
    assert legacy_contracts.EntityType is shared_contracts.EntityType
    assert (
        legacy_context_pack.build_context_pack_from_runtime_target
        is shared_context_pack.build_context_pack_from_runtime_target
    )


_LEGACY_GRAPH_MODULES = (
    "src.agents.orchestrator",
    "src.agents.phase_1_adapter",
    "src.agents.phase_2_adapter",
    "src.agents.phase_3_adapter",
    "src.agents.phase_4_adapter",
)
_LEGACY_PACKAGES = (
    "src.core.source_fact_chain",
    "src.core.ingest_and_digitize_data.document_acquisition",
    "src.core.ingest_and_digitize_data.parse_document",
    "src.core.standardize_entities_and_align_knowledge",
)


def _legacy_module_names() -> list[str]:
    """Every module importable only through a legacy shim path."""
    names = set(_LEGACY_GRAPH_MODULES)
    for package in _LEGACY_PACKAGES:
        module = importlib.import_module(package)
        names.add(package)
        names.update(info.name for info in pkgutil.walk_packages(module.__path__, prefix=package + "."))
    return sorted(names)


@pytest.mark.parametrize("module_name", _legacy_module_names())
def test_every_legacy_shim_module_imports(module_name: str) -> None:
    importlib.import_module(module_name)
