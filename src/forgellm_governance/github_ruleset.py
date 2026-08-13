"""Safe, idempotent GitHub ruleset planning and application for ForgeLLM."""

from __future__ import annotations

import json
import os
import subprocess
from collections.abc import Callable, Mapping, MutableMapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CONFIRMATION_ENV = "FORGELLM_CONFIRM_GITHUB_ADMIN_WRITE"
REQUIRED_CHECK = "Validate and test"
RULESET_NAME = "ForgeLLM main"
TARGET_REF = "refs/heads/main"


class RulesetError(ValueError):
    """Raised when a ruleset or administrative operation violates policy."""


@dataclass(frozen=True, slots=True)
class ApplyResult:
    """Normalized result of creating or updating the ForgeLLM ruleset."""

    action: str
    ruleset_id: int
    name: str
    enforcement: str


Runner = Callable[..., subprocess.CompletedProcess[str]]


def load_payload(path: Path | str) -> dict[str, Any]:
    """Load one JSON ruleset payload as a mutable mapping."""

    payload_path = Path(path)
    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RulesetError(f"ruleset payload does not exist: {payload_path}") from exc
    except json.JSONDecodeError as exc:
        raise RulesetError(
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}"
        ) from exc
    if not isinstance(payload, dict):
        raise RulesetError("ruleset payload root must be an object")
    return payload


def _rules_by_type(payload: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rules = payload.get("rules")
    if not isinstance(rules, list):
        raise RulesetError("rules must be an array")

    indexed: dict[str, Mapping[str, Any]] = {}
    for rule in rules:
        if not isinstance(rule, Mapping):
            raise RulesetError("every rule must be an object")
        rule_type = rule.get("type")
        if not isinstance(rule_type, str) or not rule_type:
            raise RulesetError("every rule requires a non-empty type")
        if rule_type in indexed:
            raise RulesetError(f"duplicate rule type: {rule_type}")
        indexed[rule_type] = rule
    return indexed


def validate_solo_payload(payload: Mapping[str, Any]) -> None:
    """Enforce the accepted ADR-0003 solo-maintainer ruleset invariants."""

    if payload.get("name") != RULESET_NAME:
        raise RulesetError(f"ruleset name must be {RULESET_NAME!r}")
    if payload.get("target") != "branch":
        raise RulesetError("ruleset target must be 'branch'")
    if payload.get("enforcement") != "active":
        raise RulesetError("ruleset enforcement must be 'active'")
    if payload.get("bypass_actors") != []:
        raise RulesetError("solo mode forbids ruleset bypass actors")

    conditions = payload.get("conditions")
    if not isinstance(conditions, Mapping):
        raise RulesetError("conditions must be an object")
    ref_name = conditions.get("ref_name")
    if not isinstance(ref_name, Mapping):
        raise RulesetError("conditions.ref_name must be an object")
    if ref_name.get("include") != [TARGET_REF] or ref_name.get("exclude") != []:
        raise RulesetError(f"ruleset must target only {TARGET_REF!r}")

    rules = _rules_by_type(payload)
    required_types = {
        "deletion",
        "non_fast_forward",
        "required_linear_history",
        "pull_request",
        "required_status_checks",
    }
    missing = required_types - set(rules)
    if missing:
        raise RulesetError(f"missing required rule types: {', '.join(sorted(missing))}")

    pull_request = rules["pull_request"].get("parameters")
    if not isinstance(pull_request, Mapping):
        raise RulesetError("pull_request.parameters must be an object")
    if pull_request.get("required_approving_review_count") != 0:
        raise RulesetError("solo mode requires zero GitHub approving reviews")
    if pull_request.get("require_code_owner_review") is not False:
        raise RulesetError("solo mode forbids required CODEOWNERS review")
    if pull_request.get("require_last_push_approval") is not False:
        raise RulesetError("solo mode forbids a fabricated last-push approval gate")
    if pull_request.get("required_review_thread_resolution") is not True:
        raise RulesetError("review-thread resolution must be required")
    if pull_request.get("allowed_merge_methods") != ["squash"]:
        raise RulesetError("ForgeLLM main currently permits squash merge only")

    status_checks = rules["required_status_checks"].get("parameters")
    if not isinstance(status_checks, Mapping):
        raise RulesetError("required_status_checks.parameters must be an object")
    if status_checks.get("strict_required_status_checks_policy") is not True:
        raise RulesetError("strict required-status-check policy must be enabled")
    checks = status_checks.get("required_status_checks")
    if checks != [{"context": REQUIRED_CHECK}]:
        raise RulesetError(f"the only required check must be {REQUIRED_CHECK!r}")


def _gh_command(*arguments: str) -> list[str]:
    return [
        "gh",
        "api",
        *arguments,
        "-H",
        "Accept: application/vnd.github+json",
        "-H",
        "X-GitHub-Api-Version: 2022-11-28",
    ]


def _run_json(command: Sequence[str], runner: Runner) -> Any:
    completed = runner(
        list(command),
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    try:
        return json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RulesetError("GitHub CLI returned invalid JSON") from exc


def command_preview(repo: str, payload_path: Path | str) -> tuple[list[str], list[str]]:
    """Return the read and create command templates without executing them."""

    payload = load_payload(payload_path)
    validate_solo_payload(payload)
    read = _gh_command("--method", "GET", f"repos/{repo}/rulesets")
    create = _gh_command(
        "--method",
        "POST",
        f"repos/{repo}/rulesets",
        "--input",
        str(Path(payload_path)),
    )
    return read, create


def apply_ruleset(
    *,
    repo: str,
    payload_path: Path | str,
    confirm_repo: str | None,
    environment: Mapping[str, str] | None = None,
    runner: Runner = subprocess.run,
) -> ApplyResult:
    """Create or update the named ruleset after two explicit owner confirmations."""

    environment = os.environ if environment is None else environment
    if confirm_repo != repo:
        raise RulesetError("--confirm-repo must exactly match --repo")
    if environment.get(CONFIRMATION_ENV) != "YES":
        raise RulesetError(f"set {CONFIRMATION_ENV}=YES after reviewing the target")

    payload = load_payload(payload_path)
    validate_solo_payload(payload)

    listing = _run_json(
        _gh_command("--method", "GET", f"repos/{repo}/rulesets"), runner
    )
    if not isinstance(listing, list):
        raise RulesetError("GitHub ruleset listing must be an array")
    matching = [
        item
        for item in listing
        if isinstance(item, Mapping) and item.get("name") == RULESET_NAME
    ]
    if len(matching) > 1:
        raise RulesetError(f"multiple GitHub rulesets are named {RULESET_NAME!r}")

    payload_file = str(Path(payload_path))
    if matching:
        ruleset_id = matching[0].get("id")
        if not isinstance(ruleset_id, int):
            raise RulesetError("existing ruleset is missing an integer id")
        action = "updated"
        command = _gh_command(
            "--method",
            "PUT",
            f"repos/{repo}/rulesets/{ruleset_id}",
            "--input",
            payload_file,
        )
    else:
        action = "created"
        command = _gh_command(
            "--method",
            "POST",
            f"repos/{repo}/rulesets",
            "--input",
            payload_file,
        )

    response = _run_json(command, runner)
    if not isinstance(response, MutableMapping):
        raise RulesetError("GitHub ruleset response must be an object")
    ruleset_id = response.get("id")
    if not isinstance(ruleset_id, int):
        raise RulesetError("GitHub ruleset response is missing an integer id")
    if response.get("name") != RULESET_NAME:
        raise RulesetError("GitHub returned an unexpected ruleset name")
    if response.get("enforcement") != "active":
        raise RulesetError("GitHub did not return an active ruleset")

    return ApplyResult(
        action=action,
        ruleset_id=ruleset_id,
        name=RULESET_NAME,
        enforcement="active",
    )
