#!/usr/bin/env python3
"""Apply minimal ForgeLLM main-branch protection after CI has produced the required check."""
from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import tempfile


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    payload = {
        "required_status_checks": {"strict": True, "contexts": ["Validate and test"]},
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "dismiss_stale_reviews": True,
            "require_code_owner_reviews": False,
            "required_approving_review_count": 1,
            "require_last_push_approval": True,
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
    command = [
        "gh", "api", "--method", "PUT", f"repos/{args.repo}/branches/main/protection",
        "-H", "Accept: application/vnd.github+json",
        "-H", "X-GitHub-Api-Version: 2022-11-28",
        "--input", "PAYLOAD.json",
    ]
    print(shlex.join(command))
    print(json.dumps(payload, indent=2))
    if not args.apply:
        print("Dry-run only. First run Phase 0 CI, then audit the exact check name.")
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
