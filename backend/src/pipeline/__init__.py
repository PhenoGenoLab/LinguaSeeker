"""Pipeline domain layer.

Organises the pipeline implementation by responsibility instead of by feature:

- ``graph/``: LangGraph topology and phase adapters.
- ``skills/``: bounded AgentScope agents (prompt and model ownership).
- ``tools/``: deterministic capabilities (no agent decisions).
- ``mcp/``: external service protocol adapters (for example ReMe).
- ``contracts/``: DTOs shared across the layers above.

The outer service layer (HTTP routes, runner, dispatcher, persistence, database
schema) stays in ``src/agents``, ``src/api`` and ``src/dao``.  Legacy module
paths stay importable as transitional re-export shims while callers migrate.
"""
