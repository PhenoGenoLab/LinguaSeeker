"""External service protocol adapters (for example ReMe).

Import boundary: MCP adapters must not import ``src.pipeline.skills`` or
``src.pipeline.tools``.  They depend only on ``src.pipeline.contracts`` and
configuration so an unavailable external service can be disabled as a whole.
"""
