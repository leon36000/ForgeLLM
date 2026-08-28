#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from forgellm_governance.validation import validate_lifecycle


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ForgeLLM task lifecycle and derived state projections.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    issues = validate_lifecycle(args.root)
    if issues:
        for issue in issues:
            print(issue.render())
        print(f"FAILED: {len(issues)} issue(s)")
        return 1
    print("OK: ForgeLLM lifecycle state is semantically valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
