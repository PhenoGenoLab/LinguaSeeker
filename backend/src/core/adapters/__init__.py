"""Adapters layer: protocol adapters for external services (for example ReMe).

Import boundary: depends only on ``src.core.shared.contracts`` and configuration
so an unavailable external service can be disabled as a whole. Never imports
``src.pipeline``.
"""
