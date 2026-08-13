#!/usr/bin/env python3
"""Apply ForgeLLM solo-owner protection to the public main branch."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import tempfile
from typing import Any


def build_payload(*, required_check: str, human_approvals: int) -> dict[str, Any]:
    return {
        "required_status_checks": {"strict": True, "contexts": [required_check]},
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
            "required_approving_review_count": human_approvals,
            "require_last_push_approval": human_approvals > 0,
        },
        "restrictions": None,
        "required_conversation_resolution": True,
        "required_linear_history": True,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "block_creations": False,
        "lock_branch": False,
        "allow_fork_syncing": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--required-check", default="Validate and test")
    parser.add_argument("--human-approvals", type=int, choices=range(0, 7), default=0)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    payload = build_payload(required_check=args.required_check, human_approvals=args.human_approvals)
    command = [
        "gh",
        "api",
        "--method",
        "PUT",
        f"repos/{args.repo}/branches/main/protection",
        "-H",
        "Accept: application/vnd.github+json",
        "-H",
        "X-GitHub-Api-Version: 2022-11-28",
        "--input",
        "PAYLOAD.json",
    ]
    print(shlex.join(command))
    print(json.dumps(payload, indent=2))
    if not args.apply:
        print("Dry-run only. Confirm the exact check name and owner-approved solo-review policy first.")
        return 0
    if os.environ.get("FORGELLM_CONFIRM_GITHUB_ADMIN_WRITE") != "YES":
        print("Refusing admin write: set FORGELLM_CONFIRM_GITHUB_ADMIN_WRITE=YES after owner review.")
        return 2
    with tempfile.NamedTemporaryFile("w", suffix=".json") as handle:
        json.dump(payload, handle)
        handle.flush()
        actual = [value if value != "PAYLOAD.json" else handle.name for value in command]
        subprocess.run(actual, check=True, timeout=30)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
