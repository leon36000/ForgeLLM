#!/usr/bin/env python3
"""Snapshot GitLab project-search candidates through the authenticated glab CLI."""
from __future__ import annotations

import argparse
import json
import subprocess
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("query")
    parser.add_argument("--output", type=Path, default=Path("artifacts/research/gitlab-search.json"))
    parser.add_argument("--per-page", type=int, default=20)
    args = parser.parse_args()
    encoded = urllib.parse.quote(args.query, safe="")
    result = subprocess.run(
        ["glab", "api", f"projects?search={encoded}&simple=true&per_page={args.per_page}&order_by=last_activity_at&sort=desc"],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        print(result.stderr.strip())
        return 1
    projects = json.loads(result.stdout)
    payload = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "query": args.query,
        "policy": "Discovery candidates only; do not infer quality or performance from activity metrics.",
        "projects": projects,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
