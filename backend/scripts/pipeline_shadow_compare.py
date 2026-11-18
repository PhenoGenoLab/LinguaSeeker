#!/usr/bin/env python
"""Compare legacy and AgentScope chain runs for shadow acceptance.

Usage:
    python scripts/pipeline_shadow_compare.py legacy/chain_run.json agent/chain_run.json

Exit code 0 when facts, verifications and English views are identical; 1
otherwise.  Provider-call counts are reported but never fail the gate.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.pipeline.skills.fact_chain.shadow_diff import compare_chain_runs
from src.pipeline.tools.fact_chain.contracts import ChainRun


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("legacy", type=Path, help="chain_run.json from the legacy provider")
    parser.add_argument("agent", type=Path, help="chain_run.json from the AgentScope runtime")
    args = parser.parse_args(argv)

    legacy = ChainRun.model_validate_json(args.legacy.read_text(encoding="utf-8"))
    agent = ChainRun.model_validate_json(args.agent.read_text(encoding="utf-8"))
    report = compare_chain_runs(legacy, agent)
    print(report.model_dump_json(indent=2))
    return 0 if report.identical else 1


if __name__ == "__main__":
    sys.exit(main())
