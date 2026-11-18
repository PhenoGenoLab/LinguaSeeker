"""Wiring tests for the runtime switches.

These complement the stage-skill tests: they prove which provider the service
builds for each ``pipeline.agent_runtime`` value and that the legacy path never
imports AgentScope.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

from src.pipeline.mcp.reme.client import NullMemoryClient
from src.pipeline.skills.fact_chain.router import StageRouterProvider
from src.pipeline.skills.fact_chain.service import _build_provider
from src.pipeline.skills.runtime.llm import LangChainChainProvider

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def _cfg(mode: str) -> SimpleNamespace:
    return SimpleNamespace(
        llm=SimpleNamespace(model="fast-model", base_url="http://fast", all_api_keys=["k1"]),
        reasoning=SimpleNamespace(model="reasoning-model", base_url="http://reasoning", all_api_keys=["k1"]),
        pipeline=SimpleNamespace(agent_runtime=mode),
    )


def test_legacy_mode_builds_the_legacy_provider() -> None:
    assert isinstance(_build_provider(_cfg("legacy"), NullMemoryClient()), LangChainChainProvider)


def test_unknown_mode_falls_back_to_legacy() -> None:
    assert isinstance(_build_provider(_cfg("bogus"), NullMemoryClient()), LangChainChainProvider)


def test_agentscope_mode_routes_all_phase3_stages() -> None:
    provider = _build_provider(_cfg("agentscope"), NullMemoryClient())

    assert isinstance(provider, StageRouterProvider)
    assert set(provider.stages) == {"extract", "verify", "translate"}


def test_shadow_mode_routes_all_phase3_stages() -> None:
    provider = _build_provider(_cfg("shadow"), NullMemoryClient())

    assert isinstance(provider, StageRouterProvider)
    assert set(provider.stages) == {"extract", "verify", "translate"}


def test_legacy_mode_never_imports_agentscope() -> None:
    """Run in a fresh interpreter: importing the service must not load AgentScope."""
    script = (
        "import sys\n"
        "from types import SimpleNamespace\n"
        "from src.pipeline.mcp.reme.client import NullMemoryClient\n"
        "from src.pipeline.skills.fact_chain.service import _build_provider\n"
        "cfg = SimpleNamespace(\n"
        "    llm=SimpleNamespace(model='m'),\n"
        "    reasoning=SimpleNamespace(model='r'),\n"
        "    pipeline=SimpleNamespace(agent_runtime='legacy'),\n"
        ")\n"
        "provider = _build_provider(cfg, NullMemoryClient())\n"
        "assert type(provider).__name__ == 'LangChainChainProvider'\n"
        "assert 'agentscope' not in sys.modules, 'agentscope imported in legacy mode'\n"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert result.returncode == 0, result.stderr
