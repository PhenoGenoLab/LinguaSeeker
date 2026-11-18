"""External service protocol adapters (for example ReMe).

Import boundary: MCP adapters must not import ``src.pipeline`` or
``src.core.tools``.  They depend only on ``src.core.contracts`` and
configuration so an unavailable external service can be disabled as a whole.
"""
