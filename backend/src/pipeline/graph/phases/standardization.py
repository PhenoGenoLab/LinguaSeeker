"""Standardization adapter: entity standardization and knowledge alignment.

Raises classified errors for orchestrator-level retry decisions.
Sets skip_standardization_reason when standardized_count == 0.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import aiofiles
from loguru import logger

from src.runs.contracts import (
    StandardizationOutput,
    PipelineGraphState,
    PermanentPhaseError,
    SkipStandardizationReason,
    build_retryable_errors,
    classify_phase_error,
)
from src.pipeline.graph.phases.lifecycle import begin_phase, complete_phase, skip_phase
from src.core.tools.extraction.contracts import DualEvidenceExtractionResult

if TYPE_CHECKING:
    from src.pipeline.skills.standardization import StandardizationSkill

_RETRYABLE_ERRORS = build_retryable_errors()


class StandardizationAdapter:
    """Thin adapter wrapping the standardization runner.

    Standardizes extracted entities against terminology databases,
    skipping when Phase 3 marked the document as not relevant.
    """

    def __init__(
        self,
        standardization_service: StandardizationSkill,
    ):
        self._standardization = standardization_service

    async def run(self, state: PipelineGraphState) -> PipelineGraphState:
        """Execute Phase 4: standardize entities.

        Returns updated state with standardization_output set on success.
        Returns state with SKIPPED status if skip_standardization_reason is set.
        Sets skip_standardization_reason=NO_CANDIDATES if standardized_count == 0.
        Raises RetryablePhaseError or PermanentPhaseError on failure.
        """
        logger.info("Phase 4 started: run={}", state.processing_run_id)

        # Skip if Phase 3 set a skip reason
        if state.skip_standardization_reason is not None:
            logger.info("Phase 4 skipped: reason={}", state.skip_standardization_reason.value)
            skip_phase(state, 4, summary={"reason": state.skip_standardization_reason.value})
            return state

        begin_phase(state, 4)

        try:
            # Load extraction result from Phase 3 output
            if state.fact_chain_output is None:
                raise PermanentPhaseError(
                    "Phase 3 output not found in state",
                    phase=3,
                )

            # Read the original extraction JSON
            extraction_path = state.fact_chain_output.extraction_result_path
            async with aiofiles.open(extraction_path, "r") as f:
                extraction_data = json.loads(await f.read())

            dual_result = DualEvidenceExtractionResult.model_validate(extraction_data)

            # Debug: log extraction result shape
            orig_chains = len(dual_result.original_result.evidence_chains)
            trans_chains = len(dual_result.translated_result.evidence_chains)
            orig_items = len(dual_result.original_result.evidence_items)
            trans_items = len(dual_result.translated_result.evidence_items)
            logger.info(
                "Phase 3 extraction loaded: orig_chains={}, trans_chains={}, orig_items={}, trans_items={}",
                orig_chains,
                trans_chains,
                orig_items,
                trans_items,
            )

            standardization_result = await self._standardization.run_dual_result(
                dual_result,
                source_document_id=state.source_document_id,
                processing_run_id=state.processing_run_id,
                owner_user_id=state.owner_user_id,
            )

            state.standardization_output = StandardizationOutput(
                match_count=standardization_result.match_count,
                standardized_count=standardization_result.standardized_count,
                ambiguous_count=standardization_result.ambiguous_count,
                unmapped_count=standardization_result.unmapped_count,
            )

            # D4 fix: Set skip reason if no candidates exist at all
            candidate_count = (
                standardization_result.standardized_count
                + standardization_result.ambiguous_count
                + standardization_result.unmapped_count
            )
            if candidate_count == 0:
                state.skip_standardization_reason = SkipStandardizationReason.NO_CANDIDATES
                complete_phase(
                    state,
                    4,
                    summary={
                        "match_count": standardization_result.match_count,
                        "standardized_count": standardization_result.standardized_count,
                        "ambiguous_count": standardization_result.ambiguous_count,
                        "unmapped_count": standardization_result.unmapped_count,
                        "skip_reason": "no_candidates",
                    },
                )
                logger.info(
                    "Phase 4 completed but no candidates: run={}",
                    state.processing_run_id,
                )
                return state

            complete_phase(
                state,
                4,
                summary={
                    "match_count": standardization_result.match_count,
                    "standardized_count": standardization_result.standardized_count,
                    "ambiguous_count": standardization_result.ambiguous_count,
                    "unmapped_count": standardization_result.unmapped_count,
                },
            )

            logger.info(
                "Phase 4 completed: run={}, matches={}",
                state.processing_run_id,
                standardization_result.match_count,
            )
            return state

        except Exception as e:
            classify_phase_error(4, e, _RETRYABLE_ERRORS)
