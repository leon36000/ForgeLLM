#!/usr/bin/env python3
"""Run one deterministic synthetic ForgeLLM placement simulation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from forgellm_governance.components import ComponentValidationError
from forgellm_governance.planner import PlacementPlanningError
from forgellm_governance.simulation import SimulationError, run_simulation
from forgellm_governance.topology import TopologyValidationError

EXPECTED_ERRORS = (
    ComponentValidationError,
    PlacementPlanningError,
    SimulationError,
    TopologyValidationError,
    ValueError,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--topology", type=Path, required=True)
    parser.add_argument("--components", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    try:
        output = run_simulation(args.root, args.topology, args.components, args.output)
    except EXPECTED_ERRORS as exc:
        issues = getattr(exc, "issues", None)
        if issues:
            for issue in issues:
                print(f"ERROR: {issue.render()}", file=sys.stderr)
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
