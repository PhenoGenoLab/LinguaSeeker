"""Facade for source-grounded cross-track reconcile."""

from __future__ import annotations

from src.core.tools.extraction.contracts import (
    EvidenceExtractionResult,
)
from src.core.tools.extraction.reconcile.contracts import (
    ReconcileParams,
    ReconcileOutput,
)
from src.core.tools.extraction.reconcile.contextual import (
    reconcile_with_context,
)
from src.core.tools.extraction.reconcile.core import (
    reconcile_results,
)
from src.core.tools.standardization.context_pack.contracts import (
    TargetContextPack,
)


class CrossTrackReconcileService:
    """Run deterministic reconcile over original and translated extraction tracks."""

    def __init__(self, params: ReconcileParams = ReconcileParams()) -> None:
        self._params = params

    def run(
        self,
        original: EvidenceExtractionResult,
        translated: EvidenceExtractionResult,
        context_pack: TargetContextPack | None = None,
    ) -> EvidenceExtractionResult:
        """Return the reconciled extraction result."""
        return self.run_with_output(original, translated, context_pack=context_pack).result

    def run_with_output(
        self,
        original: EvidenceExtractionResult,
        translated: EvidenceExtractionResult,
        context_pack: TargetContextPack | None = None,
    ) -> ReconcileOutput:
        """Return the reconciled result plus auditable reconcile artifacts."""
        if context_pack is not None:
            return reconcile_with_context(original, translated, context_pack, self._params)
        return reconcile_results(original, translated, self._params)
