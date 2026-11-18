"""Phase layer: one package per pipeline phase, each owning its business logic.

Import boundary: may import ``src.core.foundation``, ``src.core.shared`` and
other phase packages (phases are peers). Never imports ``src.pipeline``; the
graph calls into a phase, not the other way round.
"""
