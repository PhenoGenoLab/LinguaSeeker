"""Knowledge-graph read/write ports."""

from __future__ import annotations

from typing import Any, Protocol

from src.core.tools.graph_retrieval.contracts import (
    GraphNode,
    GraphWriteSummary,
    LiteratureGraphBatch,
    SubgraphContext,
)


class GraphRepository(Protocol):
    """Read and write rows in the knowledge graph store."""

    async def execute_write(self, query: str, **parameters: Any) -> list[dict[str, Any]]: ...

    async def get_subgraph(
        self,
        seed_node_ids: list[str],
        hops: int = 2,
        limit: int = 200,
    ) -> SubgraphContext: ...

    async def get_biomedical_subgraph(
        self,
        seed_node_ids: list[str],
        hops: int = 2,
        limit: int = 200,
    ) -> SubgraphContext: ...

    async def get_evidence_bridge_subgraph(
        self,
        gene_names: list[str],
        variant_limit: int = 120,
    ) -> SubgraphContext: ...

    async def find_node_ids_by_name(
        self,
        label: str,
        names: list[str],
        limit: int = 50,
    ) -> list[str]: ...

    async def find_nodes(
        self,
        labels: tuple[str, ...] | None = None,
        property_filter: dict[str, object] | None = None,
        limit: int = 100,
    ) -> list[GraphNode]: ...


class GraphWriter(Protocol):
    """Persist literature graph batches into the store."""

    async def write_batch(
        self,
        batch: LiteratureGraphBatch,
        chunk_size: int = 500,
    ) -> GraphWriteSummary: ...
