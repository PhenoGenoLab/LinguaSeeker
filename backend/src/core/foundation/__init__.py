"""Foundation layer: cross-cutting primitives with no domain knowledge.

Import boundary: may import only ``src.core.config`` and third-party packages.
Never imports ``src.core.shared``, ``src.core.adapters``, ``src.core.agents`` or
``src.pipeline``.
"""
