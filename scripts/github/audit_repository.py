#!/usr/bin/env python3
"""Read-only audit of a GitHub repository against ForgeLLM's Phase 0 policy."""
from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


def gh_api(endpoint: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["gh", "api", endpoint],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        return {"status": "unavailable", "endpoint": endpoint, "stderr": completed.stderr.strip()}
    if not completed.stdout.strip():
        return {"status": "ok", "endpoint": endpoint, "data": None}
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        data = completed.stdout.strip()
    return {"status": "ok", "endpoint": endpoint, "data": data}


def check_report(snapshots: dict[str, Any]) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    repository = snapshots["repository"]
    if repository["status"] != "ok":
        return [{"id": "repository-access", "status": "fail", "detail": repository.get("stderr", "unavailable")}]
    data = repository["data"]
    checks.append({
        "id": "private-visibility",
        "status": "pass" if data.get("private") is True else "fail",
        "detail": f"visibility={data.get('visibility')}",
    })
    checks.append({
        "id": "default-branch-main",
        "status": "pass" if data.get("default_branch") == "main" else "fail",
        "detail": f"default_branch={data.get('default_branch')}",
    })
    protection = snapshots["branch_protection"]
    checks.append({
        "id": "branch-protection",
        "status": "pass" if protection["status"] == "ok" else "fail",
        "detail": "main protection readable" if protection["status"] == "ok" else protection.get("stderr", "missing"),
    })
    actions = snapshots["actions_permissions"]
    if actions["status"] == "ok" and isinstance(actions["data"], dict):
        default_permission = actions["data"].get("default_workflow_permissions")
        can_approve = actions["data"].get("can_approve_pull_request_reviews")
        passed = default_permission == "read" and can_approve is False
        detail = f"default_workflow_permissions={default_permission}; can_approve_pull_request_reviews={can_approve}"
    else:
        passed = False
        detail = actions.get("stderr", "unavailable")
    checks.append({"id": "actions-minimum-permissions", "status": "pass" if passed else "fail", "detail": detail})
    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--output", type=Path, default=Path("artifacts/github-repository-audit.json"))
    parser.add_argument("--strict", action="store_true", help="return non-zero when a policy check fails")
    args = parser.parse_args()
    repo = args.repo
    snapshots = {
        "repository": gh_api(f"repos/{repo}"),
        "branch_protection": gh_api(f"repos/{repo}/branches/main/protection"),
        "actions_permissions": gh_api(f"repos/{repo}/actions/permissions/workflow"),
        "actions_allowed": gh_api(f"repos/{repo}/actions/permissions/selected-actions"),
        "vulnerability_alerts": gh_api(f"repos/{repo}/vulnerability-alerts"),
        "code_scanning": gh_api(f"repos/{repo}/code-scanning/alerts?state=open&per_page=1"),
        "secret_scanning": gh_api(f"repos/{repo}/secret-scanning/alerts?state=open&per_page=1"),
    }
    checks = check_report(snapshots)
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "repository": repo,
        "read_only": True,
        "checks": checks,
        "snapshots": snapshots,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for check in checks:
        print(f"{check['status'].upper():4} {check['id']}: {check['detail']}")
    print(args.output)
    failed = any(check["status"] != "pass" for check in checks)
    return 1 if args.strict and failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
