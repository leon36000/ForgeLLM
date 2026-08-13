from __future__ import annotations

from scripts.github.apply_branch_protection import build_payload
from scripts.github.audit_repository import check_report


def _ok(data: object) -> dict[str, object]:
    return {"status": "ok", "http_status": 200, "data": data}


def _unavailable(status: int = 403) -> dict[str, object]:
    return {"status": "unavailable", "http_status": status, "stderr": "unavailable"}


def test_public_protected_repository_passes_core_controls() -> None:
    snapshots = {
        "repository": _ok({"visibility": "public", "default_branch": "main"}),
        "branch": _ok({"protected": True}),
        "branch_protection": _ok({"required_status_checks": {}}),
        "rulesets": _ok([]),
        "actions_permissions": _ok(
            {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}
        ),
        "code_scanning": _ok([]),
    }
    checks = check_report(snapshots, expected_visibility="public")
    assert {check["status"] for check in checks} == {"pass"}


def test_unprotected_repository_and_inaccessible_admin_controls_are_not_a_pass() -> None:
    snapshots = {
        "repository": _ok({"visibility": "public", "default_branch": "main"}),
        "branch": _ok({"protected": False}),
        "branch_protection": _unavailable(),
        "rulesets": _ok([]),
        "actions_permissions": _unavailable(),
        "code_scanning": _unavailable(),
    }
    checks = {check["id"]: check for check in check_report(snapshots, expected_visibility="public")}
    assert checks["repository-visibility"]["status"] == "pass"
    assert checks["main-protection"]["status"] == "fail"
    assert checks["actions-minimum-permissions"]["status"] == "unknown"
    assert checks["code-scanning-visibility"]["status"] == "unknown"


def test_unrelated_or_disabled_ruleset_cannot_fake_main_protection() -> None:
    snapshots = {
        "repository": _ok({"visibility": "public", "default_branch": "main"}),
        "branch": _ok({"protected": False}),
        "branch_protection": _unavailable(),
        "rulesets": _ok(
            [
                {
                    "name": "tag-only-rule",
                    "target": "tag",
                    "enforcement": "active",
                }
            ]
        ),
        "actions_permissions": _ok(
            {"default_workflow_permissions": "read", "can_approve_pull_request_reviews": False}
        ),
        "code_scanning": _ok([]),
    }
    checks = {check["id"]: check for check in check_report(snapshots, expected_visibility="public")}
    assert checks["main-protection"]["status"] == "fail"
    assert "rulesets_observed=1" in checks["main-protection"]["detail"]


def test_solo_branch_protection_requires_pr_and_ci_without_fake_human_approval() -> None:
    payload = build_payload(required_check="Validate and test", human_approvals=0)
    assert payload["enforce_admins"] is True
    assert payload["required_status_checks"] == {"strict": True, "contexts": ["Validate and test"]}
    reviews = payload["required_pull_request_reviews"]
    assert reviews["required_approving_review_count"] == 0
    assert reviews["require_last_push_approval"] is False
    assert payload["allow_force_pushes"] is False
    assert payload["allow_deletions"] is False
