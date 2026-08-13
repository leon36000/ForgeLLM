#!/usr/bin/env python3
"""Read-only audit of a GitHub repository against ForgeLLM repository policy."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_HTTP_STATUS = re.compile(r"HTTP\s+([0-9]{3})")


def gh_api(endpoint: str) -> dict[str, Any]:
    completed = subprocess.run(
        ["gh", "api", endpoint],
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if completed.returncode != 0:
        match = _HTTP_STATUS.search(completed.stderr)
        return {
            "status": "unavailable",
            "endpoint": endpoint,
            "http_status": int(match.group(1)) if match else None,
            "stderr": completed.stderr.strip(),
        }
    if not completed.stdout.strip():
        return {"status": "ok", "endpoint": endpoint, "http_status": 200, "data": None}
    try:
        data = json.loads(completed.stdout)
    except json.JSONDecodeError:
        data = completed.stdout.strip()
    return {"status": "ok", "endpoint": endpoint, "http_status": 200, "data": data}


def _result(check_id: str, status: str, detail: str) -> dict[str, str]:
    return {"id": check_id, "status": status, "detail": detail}


def check_report(snapshots: dict[str, Any], *, expected_visibility: str) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    repository = snapshots["repository"]
    if repository["status"] != "ok" or not isinstance(repository.get("data"), dict):
        return [_result("repository-access", "fail", repository.get("stderr", "unavailable"))]

    data = repository["data"]
    visibility = data.get("visibility")
    checks.append(
        _result(
            "repository-visibility",
            "pass" if visibility == expected_visibility else "fail",
            f"expected={expected_visibility}; observed={visibility}",
        )
    )
    checks.append(
        _result(
            "default-branch-main",
            "pass" if data.get("default_branch") == "main" else "fail",
            f"default_branch={data.get('default_branch')}",
        )
    )

    branch = snapshots["branch"]
    branch_protected = (
        branch["status"] == "ok"
        and isinstance(branch.get("data"), dict)
        and branch["data"].get("protected") is True
    )
    rulesets = snapshots["rulesets"]
    ruleset_count = len(rulesets.get("data", [])) if rulesets["status"] == "ok" and isinstance(rulesets.get("data"), list) else 0
    protection = snapshots["branch_protection"]
    if branch_protected or ruleset_count > 0:
        detail = f"branch.protected={branch_protected}; rulesets={ruleset_count}; protection_endpoint={protection['status']}"
        checks.append(_result("main-protection", "pass", detail))
    else:
        detail = (
            f"branch.protected={branch_protected}; rulesets={ruleset_count}; "
            f"protection_endpoint={protection['status']}; http={protection.get('http_status')}"
        )
        checks.append(_result("main-protection", "fail", detail))

    actions = snapshots["actions_permissions"]
    if actions["status"] == "ok" and isinstance(actions.get("data"), dict):
        default_permission = actions["data"].get("default_workflow_permissions")
        can_approve = actions["data"].get("can_approve_pull_request_reviews")
        passed = default_permission == "read" and can_approve is False
        checks.append(
            _result(
                "actions-minimum-permissions",
                "pass" if passed else "fail",
                f"default_workflow_permissions={default_permission}; can_approve_pull_request_reviews={can_approve}",
            )
        )
    else:
        checks.append(
            _result(
                "actions-minimum-permissions",
                "unknown",
                f"endpoint unavailable; http={actions.get('http_status')}; {actions.get('stderr', '')}",
            )
        )

    code_scanning = snapshots["code_scanning"]
    if code_scanning["status"] == "ok" and isinstance(code_scanning.get("data"), list):
        checks.append(_result("code-scanning-visibility", "pass", f"open_alerts={len(code_scanning['data'])}"))
    else:
        checks.append(
            _result(
                "code-scanning-visibility",
                "unknown",
                f"endpoint unavailable; http={code_scanning.get('http_status')}",
            )
        )

    return checks


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="owner/name")
    parser.add_argument("--expected-visibility", choices=("public", "private"), default="public")
    parser.add_argument("--output", type=Path, default=Path("artifacts/github-repository-audit.json"))
    parser.add_argument("--strict", action="store_true", help="return non-zero on failed or unknown controls")
    args = parser.parse_args()
    repo = args.repo
    snapshots = {
        "repository": gh_api(f"repos/{repo}"),
        "branch": gh_api(f"repos/{repo}/branches/main"),
        "branch_protection": gh_api(f"repos/{repo}/branches/main/protection"),
        "rulesets": gh_api(f"repos/{repo}/rulesets"),
        "actions_permissions": gh_api(f"repos/{repo}/actions/permissions/workflow"),
        "actions_allowed": gh_api(f"repos/{repo}/actions/permissions/selected-actions"),
        "vulnerability_alerts": gh_api(f"repos/{repo}/vulnerability-alerts"),
        "code_scanning": gh_api(f"repos/{repo}/code-scanning/alerts?state=open&per_page=100"),
        "secret_scanning": gh_api(f"repos/{repo}/secret-scanning/alerts?state=open&per_page=100"),
    }
    checks = check_report(snapshots, expected_visibility=args.expected_visibility)
    report = {
        "schema_version": "1.1",
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "repository": repo,
        "expected_visibility": args.expected_visibility,
        "read_only": True,
        "checks": checks,
        "snapshots": snapshots,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for check in checks:
        print(f"{check['status'].upper():7} {check['id']}: {check['detail']}")
    print(args.output)
    blocked = any(check["status"] in {"fail", "unknown"} for check in checks)
    return 1 if args.strict and blocked else 0


if __name__ == "__main__":
    raise SystemExit(main())
