#!/usr/bin/env python3
"""Plan or apply the ForgeLLM main-branch ruleset."""

from __future__ import annotations

import argparse
import json
import shlex
from pathlib import Path

from forgellm_governance.github_ruleset import (
    RulesetError,
    apply_ruleset,
    command_preview,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Dry-run or idempotently apply the ForgeLLM solo-maintainer main ruleset."
        )
    )
    parser.add_argument("--repo", required=True, help="GitHub repository as owner/name")
    parser.add_argument(
        "--payload",
        type=Path,
        default=Path("tasks/open/P0-T03-main-ruleset-payload.json"),
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--confirm-repo",
        help="Second confirmation; must exactly match --repo when --apply is used",
    )
    args = parser.parse_args()

    try:
        read_command, create_command = command_preview(args.repo, args.payload)
        print("Read-only discovery command:")
        print(shlex.join(read_command))
        print("Create command used when no matching ruleset exists:")
        print(shlex.join(create_command))
        if not args.apply:
            print(
                "Dry-run only. To apply, add --apply --confirm-repo and set "
                "FORGELLM_CONFIRM_GITHUB_ADMIN_WRITE=YES."
            )
            return 0

        result = apply_ruleset(
            repo=args.repo,
            payload_path=args.payload,
            confirm_repo=args.confirm_repo,
        )
    except RulesetError as exc:
        print(f"ERROR: {exc}")
        return 2

    print(
        json.dumps(
            {
                "action": result.action,
                "ruleset_id": result.ruleset_id,
                "name": result.name,
                "enforcement": result.enforcement,
            },
            indent=2,
            sort_keys=True,
        )
    )
    print("Read back the ruleset and main branch before updating ForgeLLM state.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
