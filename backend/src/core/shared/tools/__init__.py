"""Deterministic domain tools.

Import boundary: this package (``core/shared/tools``) must not import
``agentscope`` (no agent decisions) and must not import ``src.pipeline`` (skills
and graph call tools, never the reverse).  AgentScope-backed tool definitions
live in ``src/core/tools`` instead.  The same functions here are callable
directly by domain code and tests, and can be exposed to agents as tools
without changing their behaviour.
"""
