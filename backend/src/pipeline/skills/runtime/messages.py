"""User-message construction for pipeline skills.

Kept in its own module so tests that inject a fake agent never import
AgentScope: they monkeypatch :func:`user_message` instead.
"""

from __future__ import annotations

from typing import Any


def user_message(text: str) -> Any:
    """Build an AgentScope user message carrying ``text``."""
    from agentscope.message import Msg, TextBlock

    return Msg(name="user", role="user", content=[TextBlock(text=text)])


__all__ = ["user_message"]
