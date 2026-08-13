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
    validate_solo_payload,
)

ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT / "tasks/open/P0-T03-main-ruleset-payload.json"
REPO = "leon36000/ForgeLLM"


def completed(stdout: object) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=["gh", "api"],
        returncode=0,
        stdout=json.dumps(stdout),
        stderr="",
    )


def test_repository_payload_satisfies_solo_policy() -> None:
    payload = load_payload(PAYLOAD)
    validate_solo_payload(payload)
    rules = {rule["type"]: rule for rule in payload["rules"]}
    checks = rules["required_status_checks"]["parameters"]
    assert checks["required_status_checks"] == [{"context": REQUIRED_CHECK}]


def test_payload_rejects_fabricated_approval_gate() -> None:
    payload = deepcopy(load_payload(PAYLOAD))
    pull_request = next(
        rule for rule in payload["rules"] if rule["type"] == "pull_request"
    )
    pull_request["parameters"]["required_approving_review_count"] = 1
    with pytest.raises(RulesetError, match="zero GitHub approving reviews"):
        validate_solo_payload(payload)


def test_command_preview_is_read_only() -> None:
    read_command, create_command = command_preview(REPO, PAYLOAD)
    assert read_command[:4] == ["gh", "api", "--method", "GET"]
    assert "repos/leon36000/ForgeLLM/rulesets" in read_command
    assert create_command[:4] == ["gh", "api", "--method", "POST"]
    assert str(PAYLOAD) in create_command


def test_apply_requires_both_owner_confirmations() -> None:
    with pytest.raises(RulesetError, match="--confirm-repo"):
        apply_ruleset(
            repo=REPO,
            payload_path=PAYLOAD,
            confirm_repo=None,
            environment={CONFIRMATION_ENV: "YES"},
        )
    with pytest.raises(RulesetError, match=CONFIRMATION_ENV):
        apply_ruleset(
            repo=REPO,
            payload_path=PAYLOAD,
            confirm_repo=REPO,
            environment={},
        )


def test_apply_creates_ruleset_when_absent() -> None:
    calls: list[list[str]] = []
    responses = iter(
        [
            completed([]),
            completed({"id": 41, "name": RULESET_NAME, "enforcement": "active"}),
        ]
    )

    def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return next(responses)

    result = apply_ruleset(
        repo=REPO,
        payload_path=PAYLOAD,
        confirm_repo=REPO,
        environment={CONFIRMATION_ENV: "YES"},
        runner=runner,
    )

    assert result.action == "created"
    assert result.ruleset_id == 41
    assert calls[0][2:4] == ["--method", "GET"]
    assert calls[1][2:4] == ["--method", "POST"]


def test_apply_updates_existing_named_ruleset() -> None:
    calls: list[list[str]] = []
    responses = iter(
        [
            completed([{"id": 84, "name": RULESET_NAME}]),
            completed({"id": 84, "name": RULESET_NAME, "enforcement": "active"}),
        ]
    )

    def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        calls.append(command)
        return next(responses)

    result = apply_ruleset(
        repo=REPO,
        payload_path=PAYLOAD,
        confirm_repo=REPO,
        environment={CONFIRMATION_ENV: "YES"},
        runner=runner,
    )

    assert result.action == "updated"
    assert result.ruleset_id == 84
    assert calls[1][2:4] == ["--method", "PUT"]
    assert "repos/leon36000/ForgeLLM/rulesets/84" in calls[1]
