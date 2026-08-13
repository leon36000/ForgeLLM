#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from forgellm_governance.validation import validate_benchmark_file


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate one ForgeLLM benchmark result.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    issues = validate_benchmark_file(args.path, root=args.root)
    for issue in issues:
        print(issue.render())
    if issues:
        print(f"FAILED: {len(issues)} issue(s)")
        return 1
    print(f"OK: {args.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
