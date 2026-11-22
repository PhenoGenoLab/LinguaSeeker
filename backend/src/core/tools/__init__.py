"""Concrete tools that skills hand to agents.

Layering (one direction only)::

    pipeline/graph   orchestrates the run (topology, phases, routing)
    graph/agents     portals - thin nodes that delegate to one skill
    pipeline/skills  agent implementations (prompts, model calls, controls)
    core/tools       the concrete tools those skills expose

This package is the ``core`` end of that chain. Everything here is a plain
AgentScope tool object, so the same instance works inside a model loop, inside
a test, and inside a skill that calls it directly.

Import boundary: this is the only ``core`` package allowed to import
``agentscope``. It must not import ``src.pipeline`` - ``core`` stays a
dependency leaf, and the direction above is enforced by
``tests/pipeline/test_import_boundaries.py``.

Category packages mirror the AgentScope tool layout:

* :mod:`src.core.tools.builtin` - shell, file and interaction tools
* :mod:`src.core.tools.task` - task list tools
"""

from src.core.tools import builtin, task

__all__ = ["builtin", "task"]
