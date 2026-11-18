"""Deterministic pipeline tools.

Import boundary: tools must not import ``agentscope`` (no agent decisions) and
must not import ``src.pipeline.skills`` or ``src.pipeline.graph``.  The same
functions are callable directly by domain code and tests, and can be exposed to
agents as tools without changing their behaviour.
"""
