"""External service protocol adapters.

Current adapters:

- ``server.py`` / ``literature.py`` / ``mineru.py``: MCP clients for external
  MCP servers (literature acquisition and MinerU parsing).
- ``reme/``: ReMe memory HTTP client.

Import boundary: MCP adapters must not import ``src.pipeline`` or
``src.core.shared.tools``.  They depend only on ``src.core.shared.contracts``
and configuration so an unavailable external service can be disabled as a whole.
"""
