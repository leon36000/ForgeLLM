from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

from forgellm_governance.github_ruleset import (
    CONFIRMATION_ENV,
    RulesetError,
    apply_ruleset,
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


def test_payload_rejects_bypass_actor() -> None:
    payload = deepcopy(load_payload(PAYLOAD))
    payload["bypass_actors"] = [
        {"actor_id": 1, "actor_type": "RepositoryRole", "bypass_mode": "always"}
    ]
    with pytest.raises(RulesetError, match="forbids ruleset bypass actors"):
        validate_solo_payload(payload)


def test_payload_rejects_wrong_branch_target() -> None:
    payload = deepcopy(load_payload(PAYLOAD))
    payload["conditions"]["ref_name"]["include"] = ["refs/heads/develop"]
    with pytest.raises(RulesetError, match="target only"):
        validate_solo_payload(payload)


def test_payload_rejects_non_strict_status_check() -> None:
    payload = deepcopy(load_payload(PAYLOAD))
    status_rule = next(
        rule
        for rule in payload["rules"]
        if rule["type"] == "required_status_checks"
    )
    status_rule["parameters"]["strict_required_status_checks_policy"] = False
    with pytest.raises(RulesetError, match="strict required-status-check"):
        validate_solo_payload(payload)


def test_apply_rejects_non_array_ruleset_listing() -> None:
    def runner(
        command: list[str], **_: object
    ) -> subprocess.CompletedProcess[str]:
        return completed({"unexpected": "object"})

    with pytest.raises(RulesetError, match="listing must be an array"):
        apply_ruleset(
            repo=REPO,
            payload_path=PAYLOAD,
            confirm_repo=REPO,
            environment={CONFIRMATION_ENV: "YES"},
            runner=runner,
        )


def test_apply_rejects_incomplete_write_response() -> None:
    responses = iter([completed([]), completed({"name": "ForgeLLM main"})])

    def runner(
        command: list[str], **_: object
    ) -> subprocess.CompletedProcess[str]:
        return next(responses)

    with pytest.raises(RulesetError, match="missing an integer id"):
        apply_ruleset(
            repo=REPO,
            payload_path=PAYLOAD,
            confirm_repo=REPO,
            environment={CONFIRMATION_ENV: "YES"},
            runner=runner,
        )
