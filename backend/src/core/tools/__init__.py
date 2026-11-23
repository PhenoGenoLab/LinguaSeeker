"""Concrete tools that skills call.

Layering (one direction only)::

    pipeline/graph   orchestrates the run (topology, phases, routing)
    pipeline/skills  agent implementations (prompts, model calls, controls)
    core/tools       the concrete, deterministic tools those skills call

Import boundary: this package must not import ``agentscope`` - the AgentScope
framework (agents, toolkits, tool registration) belongs to ``pipeline/skills``.
It must not import ``src.pipeline`` either: ``core`` stays a dependency leaf.

Domain packages mirror the pipeline stages (``acquisition``, ``parsing``,
``extraction``, ``standardization``, ``translation``, ``review``,
``graph_retrieval``). They are not imported from this module, so importing
``core.tools`` never pulls a stage's SDKs.
"""

__all__: list[str] = []
