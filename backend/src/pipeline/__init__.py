"""Pipeline orchestration layer.

The pipeline owns *how* phases run and *which* agent executes a phase. It holds
no concrete capability: tools, protocol adapters and DTOs live in ``src.core``.

- ``graph/``: LangGraph topology and phase adapters.
- ``skills/``: bounded AgentScope agents (prompt and model ownership).

Concrete dependencies (imported, never re-exported):
- ``src.core.shared.tools``: deterministic capabilities (no agent decisions).
- ``src.core.adapters.mcp``: external service protocol adapters (for example ReMe).
- ``src.core.shared.contracts``: DTOs shared across the layers.
- ``src.pipeline.skills``: the agent implementations the adapters delegate to.

The outer service layer (HTTP routes, runner, dispatcher, persistence, database
schema) stays in ``src.runs``, ``src.api`` and ``src.dao``.
"""
