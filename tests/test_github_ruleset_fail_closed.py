from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from forgellm_governance.github_ruleset import (
    CONFIRMATION_ENV,
    REQUIRED_CHECK,
    RULESET_NAME,
    RulesetError,
    apply_ruleset,
    command_preview,
    load_payload,
    validate_repository,
    validate_solo_payload,
)

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "tasks/open/P0-T03-main-ruleset-payload.json"
REPO = "leon36000/ForgeLLM"


def completed(stdout: object, *, returncode: int = 0, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["gh", "api"],
        returncode=returncode,
        stdout=json.dumps(stdout) if not isinstance(stdout, str) else stdout,
        stderr=stderr,
    )


def remote_detail(payload: dict[str, object], ruleset_id: int = 41) -> dict[str, object]:
    return {"id": ruleset_id, **deepcopy(payload)}


def test_repository_identifier_is_strict() -> None:
    assert validate_repository(REPO) == REPO
    for invalid in ("owner", "owner/repo/extra", "/repo", "owner/", "owner repo/name"):
        with pytest.raises(RulesetError):
            validate_repository(invalid)


def test_payload_rejects_extra_top_level_key() -> None:
    payload = deepcopy(load_payload(PAYLOAD))
    payload["unexpected"] = True
    with pytest.raises(RulesetError, match="unexpected top-level"):
        validate_solo_payload(payload)


def test_payload_rejects_extra_rule_type() -> None:
    payload = deepcopy(load_payload(PAYLOAD))
    payload["rules"].append({"type": "required_signatures"})
    with pytest.raises(RulesetError, match="unexpected rule types"):
        validate_solo_payload(payload)


def test_payload_rejects_extra_pull_request_parameter() -> None:
    payload = deepcopy(load_payload(PAYLOAD))
    pull_request = next(rule for rule in payload["rules"] if rule["type"] == "pull_request")
    pull_request["parameters"]["unexpected"] = True
    with pytest.raises(RulesetError, match="unexpected pull_request parameters"):
        validate_solo_payload(payload)


def test_command_preview_performs_no_write() -> None:
    commands = command_preview(REPO, PAYLOAD)
    assert commands["list"][:4] == ["gh", "api", "--method", "GET"]
    assert commands["create"][:4] == ["gh", "api", "--method", "POST"]


def test_apply_requires_both_confirmations() -> None:
    with pytest.raises(RulesetError, match="--confirm-repo"):
        apply_ruleset(repo=REPO, payload_path=PAYLOAD, confirm_repo=None, environment={CONFIRMATION_ENV: "YES"})
    with pytest.raises(RulesetError, match=CONFIRMATION_ENV):
        apply_ruleset(repo=REPO, payload_path=PAYLOAD, confirm_repo=REPO, environment={})


def test_apply_fails_closed_on_github_error() -> None:
    def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return completed("", returncode=1, stderr="permission denied")

    with pytest.raises(RulesetError, match="permission denied"):
        apply_ruleset(
            repo=REPO,
            payload_path=PAYLOAD,
            confirm_repo=REPO,
            environment={CONFIRMATION_ENV: "YES"},
            runner=runner,
        )


def test_apply_requires_verified_readback_before_audit(tmp_path: Path) -> None:
    payload = load_payload(PAYLOAD)
    responses = iter(
        [
            completed([]),
            completed({"id": 41, "name": RULESET_NAME, "enforcement": "active"}),
            completed({**remote_detail(payload), "enforcement": "evaluate"}),
        ]
    )

    def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return next(responses)

    audit = tmp_path / "audit.json"
    with pytest.raises(RulesetError, match="readback"):
        apply_ruleset(
            repo=REPO,
            payload_path=PAYLOAD,
            confirm_repo=REPO,
            environment={CONFIRMATION_ENV: "YES"},
            runner=runner,
            audit_path=audit,
        )
    assert not audit.exists()


def test_apply_creates_and_verifies_ruleset(tmp_path: Path) -> None:
    payload = load_payload(PAYLOAD)
    calls: list[list[str]] = []
    responses = iter(
        [
            completed([]),
            completed({"id": 41, "name": RULESET_NAME, "enforcement": "active"}),
            completed(remote_detail(payload)),
        ]
    )

    def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return next(responses)

    audit = tmp_path / "audit.json"
    result = apply_ruleset(
        repo=REPO,
        payload_path=PAYLOAD,
        confirm_repo=REPO,
        environment={CONFIRMATION_ENV: "YES"},
        runner=runner,
        audit_path=audit,
    )
    assert result.action == "created"
    assert result.ruleset_id == 41
    assert result.verified is True
    assert calls[-1][2:4] == ["--method", "GET"]
    audit_data = json.loads(audit.read_text(encoding="utf-8"))
    assert audit_data["verified"] is True
    assert audit_data["required_check"] == REQUIRED_CHECK
