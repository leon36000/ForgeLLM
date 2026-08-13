#!/usr/bin/env python3
"""Create ForgeLLM labels. Dry-run is the default; writes require two explicit gates."""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess

LABELS = [
    ("research", "Primary-source review and evidence", "1D76DB"),
    ("evidence", "Claim or reproduction evidence", "5319E7"),
    ("experiment", "Controlled experiment proposal or result", "FBCA04"),
    ("benchmark", "Benchmark method or artifact", "D4C5F9"),
    ("engineering", "Bounded implementation task", "0E8A16"),
    ("architecture", "Architecture and ADR work", "B60205"),
    ("adr", "Durable architecture decision", "D93F0B"),
    ("bug", "Reproducible defect", "D73A4A"),
    ("security", "Security-sensitive work without public exploit details", "8B0000"),
    ("dependencies", "Dependency or supply-chain change", "0366D6"),
    ("python", "Python governance or tooling", "3572A5"),
    ("github-actions", "GitHub Actions automation", "2088FF"),
    ("blocked", "Blocked by an explicit dependency or owner decision", "000000"),
    ("external-unreproduced", "Externally reported result not reproduced by ForgeLLM", "E99695"),
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    commands = [
        ["gh", "label", "create", name, "--repo", args.repo, "--description", description, "--color", color, "--force"]
        for name, description, color in LABELS
    ]
    for command in commands:
        print(shlex.join(command))
    if not args.apply:
        print("Dry-run only. Add --apply and FORGELLM_CONFIRM_GITHUB_WRITE=YES to create labels.")
        return 0
    if os.environ.get("FORGELLM_CONFIRM_GITHUB_WRITE") != "YES":
        print("Refusing write: set FORGELLM_CONFIRM_GITHUB_WRITE=YES after reviewing repository target.")
        return 2
    for command in commands:
        subprocess.run(command, check=True, timeout=30)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
