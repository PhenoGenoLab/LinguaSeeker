"""Agent layer: one package per agent, each owning its business logic.

Phase numbering is not modelled here — ``src.pipeline.graph`` owns the phases
and decides which agent runs when.  A package here answers "what can this agent
do", not "where in the pipeline does it sit".

Import boundary: may import ``src.core.foundation``, ``src.core.shared`` and
other agent packages (agents are peers). Never imports ``src.pipeline``; the
graph calls into an agent, not the other way round.
"""
