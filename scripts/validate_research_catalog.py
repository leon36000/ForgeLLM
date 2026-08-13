#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from forgellm_governance.validation import validate_research_catalogs


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate ForgeLLM source and claim cross-references.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    issues = validate_research_catalogs(args.root)
    for issue in issues:
        print(issue.render())
    if issues:
        print(f"FAILED: {len(issues)} issue(s)")
        return 1
    print("OK: ForgeLLM research catalogs are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
