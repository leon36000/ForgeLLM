#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from forgellm_governance.snapshot import create_session_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a portable ForgeLLM continuity snapshot.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path, default=Path("artifacts/session-snapshot.md"))
    args = parser.parse_args()
    print(create_session_snapshot(args.root, args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
