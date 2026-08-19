"""ForgeLLM bounded Loop Engineering public validation surface."""

from __future__ import annotations

import re
import shlex
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from . import loop_engineering_legacy as _legacy

REQUIRED_LOOP_FIELDS = _legacy.REQUIRED_LOOP_FIELDS
SHADOW_STATE_PATHS = _legacy.SHADOW_STATE_PATHS
PRIVILEGED_OPERATION_POLICY = _legacy.PRIVILEGED_OPERATION_POLICY
EXPECTED_UPSTREAM_REPOSITORY = _legacy.EXPECTED_UPSTREAM_REPOSITORY
EXPECTED_UPSTREAM_COMMIT = _legacy.EXPECTED_UPSTREAM_COMMIT
EXPECTED_LICENSE_BLOB = _legacy.EXPECTED_LICENSE_BLOB
EXPECTED_VENDOR_FILES = _legacy.EXPECTED_VENDOR_FILES
EXPECTED_EXCLUDED_EXECUTABLE_SURFACES = _legacy.EXPECTED_EXCLUDED_EXECUTABLE_SURFACES
EXPECTED_EXCLUDED_SHADOW_TEMPLATES = _legacy.EXPECTED_EXCLUDED_SHADOW_TEMPLATES

validate_vendor_provenance = _legacy.validate_vendor_provenance

_SHELL_PUNCTUATION = "();&|<>"
_ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=.*$")
_GIT_READ_ONLY_SUBCOMMANDS = {
    "cat-file",
    "diff",
    "grep",
    "log",
    "ls-files",
    "ls-tree",
    "rev-parse",
    "show",
    "status",
}
_GIT_EXTERNAL_EXECUTION_FLAGS = {"--ext-diff", "--textconv", "--open-files-in-pager", "-O"}
_GH_READ_ONLY_COMMANDS = {
    ("issue", "list"),
    ("issue", "status"),
    ("issue", "view"),
    ("pr", "checks"),
    ("pr", "diff"),
    ("pr", "list"),
    ("pr", "status"),
    ("pr", "view"),
    ("repo", "list"),
    ("repo", "view"),
    ("run", "list"),
    ("run", "view"),
    ("workflow", "list"),
    ("workflow", "view"),
}
_FORBIDDEN_LONG_RUNNING_FLAGS = {"--follow", "--watch"}
_EXECUTION_WRAPPERS = {
    ".",
    "command",
    "env",
    "eval",
    "exec",
    "find",
    "nice",
    "parallel",
    "setsid",
    "source",
    "stdbuf",
    "timeout",
    "xargs",
}
_FILE_MUTATION_TOOLS = {
    "chmod",
    "chown",
    "chgrp",
    "cp",
    "dd",
    "install",
    "ln",
    "mv",
    "rm",
    "rmdir",
    "tee",
    "touch",
    "truncate",
    "unlink",
}
_HTTP_MUTATION_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
_HTTP_READ_ONLY_METHODS = {"GET", "HEAD", "OPTIONS"}
_CURL_LONG_MUTATION_FLAGS = {
    "--data",
    "--data-ascii",
    "--data-binary",
    "--data-raw",
    "--data-urlencode",
    "--form",
    "--upload-file",
}
_CURL_CONFIG_FLAGS = {"-K", "--config"}


def _shell_lex(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=_SHELL_PUNCTUATION)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _shell_composition_issue(command: str) -> str | None:
    try:
        tokens = _shell_lex(command)
    except ValueError as exc:
        return f"VERIFY command cannot be parsed safely: {exc}"
    if any(token and all(character in _SHELL_PUNCTUATION for character in token) for token in tokens):
        return "VERIFY command composes shell commands or redirects I/O and must stop_and_escalate"
    return None


def _parameter_expansion_issue(command: str) -> str | None:
    quote: str | None = None
    escaped = False
    for character in command:
        if escaped:
            escaped = False
            continue
        if character == "\\" and quote != "'":
            escaped = True
            continue
        if quote is None and character in {"'", '"'}:
            quote = character
            continue
        if quote == character:
            quote = None
            continue
        if character == "$" and quote != "'":
            return "VERIFY command uses shell parameter expansion and must stop_and_escalate"
    return None


def _executable_name(token: str) -> str:
    return Path(token).name or token


def _environment_wrapper_issue(tokens: Sequence[str]) -> str | None:
    executable = _executable_name(tokens[0])
    if executable == "env" or _ENV_ASSIGNMENT.fullmatch(tokens[0]) is not None:
        return "VERIFY command uses environment indirection and must stop_and_escalate"
    return None


def _dispatch_wrapper_issue(tokens: Sequence[str]) -> str | None:
    executable = _executable_name(tokens[0])
    if executable in _EXECUTION_WRAPPERS:
        return f"VERIFY command uses execution wrapper {executable!r} and must stop_and_escalate"
    return None


def _file_mutation_issue(tokens: Sequence[str]) -> str | None:
    executable = _executable_name(tokens[0])
    if executable in _FILE_MUTATION_TOOLS:
        return f"VERIFY command uses file mutation tool {executable!r} and must stop_and_escalate"
    return None


def _git_external_flag(token: str) -> bool:
    return (
        token in {"--ext-diff", "--textconv", "-O"}
        or token.startswith("--open-files-in-pager")
        or token.startswith("-O")
    )


def _git_command_issue(tokens: Sequence[str]) -> str | None:
    if _executable_name(tokens[0]) != "git":
        return None
    if len(tokens) < 2 or tokens[1] not in _GIT_READ_ONLY_SUBCOMMANDS:
        return "VERIFY command uses a non-read-only or globally configured Git form and must stop_and_escalate"
    if any(_git_external_flag(token) for token in tokens[2:]):
        return "VERIFY command permits Git to execute an external helper and must stop_and_escalate"
    return None


def _gh_forbidden_mode(token: str) -> bool:
    return token in {"--follow", "--watch", "--web", "-w"} or token.startswith(
        ("--follow=", "--watch=", "--web=")
    )


def _gh_command_issue(tokens: Sequence[str]) -> str | None:
    if _executable_name(tokens[0]) != "gh":
        return None
    if len(tokens) == 2 and tokens[1] == "status":
        return None
    if len(tokens) < 3 or (tokens[1], tokens[2]) not in _GH_READ_ONLY_COMMANDS:
        return "VERIFY command uses a non-read-only GitHub CLI form and must stop_and_escalate"
    if any(_gh_forbidden_mode(token) for token in tokens[3:]):
        return "VERIFY command uses an interactive or unbounded GitHub CLI mode and must stop_and_escalate"
    return None


def _make_command_issue(tokens: Sequence[str]) -> str | None:
    if _executable_name(tokens[0]) != "make":
        return None
    if any(token.startswith("-") or "=" in token for token in tokens[1:]):
        return "VERIFY command changes Make configuration or evaluation and must stop_and_escalate"
    return None


def _curl_short_option_issue(token: str, next_token: str | None) -> str | None:
    if not token.startswith("-") or token.startswith("--") or token == "-":
        return None
    cluster = token[1:]
    if any(flag in cluster for flag in "dFTK"):
        return "VERIFY command performs or configures an HTTP mutation and must stop_and_escalate"
    if "X" not in cluster:
        return None
    method = cluster.split("X", 1)[1] or (next_token or "")
    if method.upper() not in _HTTP_READ_ONLY_METHODS:
        return "VERIFY command performs an HTTP mutation and must stop_and_escalate"
    return None


def _curl_mutation_issue(tokens: Sequence[str]) -> str | None:
    if _executable_name(tokens[0]) != "curl":
        return None
    for index, token in enumerate(tokens[1:], start=1):
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        if token in _legacy._CURL_MUTATION_FLAGS:
            return "VERIFY command performs an HTTP mutation and must stop_and_escalate"
        if token in _CURL_CONFIG_FLAGS or token.startswith(("-K", "--config=")):
            return "VERIFY command loads external curl configuration and must stop_and_escalate"
        if any(token.startswith(flag + "=") for flag in _CURL_LONG_MUTATION_FLAGS):
            return "VERIFY command performs an HTTP mutation and must stop_and_escalate"
        short_issue = _curl_short_option_issue(token, next_token)
        if short_issue is not None:
            return short_issue
        if token in {"-X", "--request"} and next_token is not None:
            if next_token.upper() not in _HTTP_READ_ONLY_METHODS:
                return "VERIFY command performs an HTTP mutation and must stop_and_escalate"
        if token.startswith("--request="):
            method = token.split("=", 1)[1].upper()
            if method not in _HTTP_READ_ONLY_METHODS:
                return "VERIFY command performs an HTTP mutation and must stop_and_escalate"
    return None


def _wget_mutation_issue(tokens: Sequence[str]) -> str | None:
    if _executable_name(tokens[0]) != "wget":
        return None
    for index, token in enumerate(tokens[1:], start=1):
        lowered = token.lower()
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None
        if lowered.startswith(("--post-data", "--post-file", "--config=")) or token == "--config":
            return "VERIFY command performs or configures an HTTP mutation and must stop_and_escalate"
        if token == "--method" and next_token is not None:
            if next_token.upper() not in _HTTP_READ_ONLY_METHODS:
                return "VERIFY command performs an HTTP mutation and must stop_and_escalate"
        if lowered.startswith("--method="):
            method = lowered.split("=", 1)[1].upper()
            if method not in _HTTP_READ_ONLY_METHODS:
                return "VERIFY command performs an HTTP mutation and must stop_and_escalate"
    return None


def _privileged_tool_issue(tokens: Sequence[str]) -> str | None:
    executable = _executable_name(tokens[0])
    if executable in {"kubectl", "terraform"}:
        return f"VERIFY command uses privileged external tool {executable!r} and must stop_and_escalate"
    return None


def _hardened_verify_issue(command: Any) -> str | None:
    if not isinstance(command, str) or not command.strip():
        return None
    for raw_check in (_shell_composition_issue, _parameter_expansion_issue):
        issue = raw_check(command)
        if issue is not None:
            return issue
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError as exc:
        return f"VERIFY command cannot be parsed safely: {exc}"
    if not tokens:
        return "VERIFY command must be non-empty after parsing"
    for check in (
        _environment_wrapper_issue,
        _dispatch_wrapper_issue,
        _file_mutation_issue,
        _git_command_issue,
        _gh_command_issue,
        _make_command_issue,
        _curl_mutation_issue,
        _wget_mutation_issue,
        _privileged_tool_issue,
    ):
        issue = check(tokens)
        if issue is not None:
            return issue
    return None


def validate_loop_verify_command(command: Any) -> list[str]:
    """Reject VERIFY commands that widen authority through shell or tool-specific indirection."""

    legacy_issues = _legacy.validate_loop_verify_command(command)
    if legacy_issues:
        return legacy_issues
    issue = _hardened_verify_issue(command)
    return [issue] if issue is not None else []


def validate_loop_declaration(declaration: Mapping[str, Any], task_packet: Mapping[str, Any]) -> list[str]:
    """Validate a declaration and apply the hardened public VERIFY firewall."""

    issues = _legacy.validate_loop_declaration(declaration, task_packet)
    verify = declaration.get("VERIFY") if isinstance(declaration, Mapping) else None
    authorized = task_packet.get("verification_commands") if isinstance(task_packet, Mapping) else None
    if _legacy._is_sequence(verify) and _legacy._is_sequence(authorized):
        for command in verify:
            if isinstance(command, str) and command in authorized:
                issue = _hardened_verify_issue(command)
                if issue is not None and issue not in issues:
                    issues.append(issue)
    return issues


_REQUIRED_RECEIPT_FIELDS = {
    "schema_version",
    "project",
    "task_id",
    "plan",
    "base_commit",
    "final_commit",
    "iterations",
    "identical_failures_at_stop",
    "stop_reason",
    "changed_paths",
    "scope_check",
    "verify_commands",
    "verification",
}
_REQUIRED_VERIFICATION_FIELDS = {"verifier", "verified_commit", "disposition", "evidence"}
_VALID_VERIFICATION_DISPOSITIONS = {"pass", "failed", "not_run"}
_TEMPLATE_FINAL_COMMIT = "REPLACE_WITH_FINAL_COMMIT"
_TEMPLATE_VERIFIED_COMMIT = "TEMPLATE: replace with final commit"
_TEMPLATE_PREFIX = "TEMPLATE:"


def _exact_keys(value: Mapping[str, Any], required: set[str], label: str) -> list[str]:
    missing = sorted(required - set(value))
    extra = sorted(set(value) - required)
    if not missing and not extra:
        return []
    return [f"{label} requires exact fields; missing={missing}, extra={extra}"]


def _validate_receipt_identity(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if receipt.get("schema_version") != "1.1":
        issues.append("receipt schema_version must be exactly '1.1'")
    if receipt.get("project") != declaration.get("project") or receipt.get("project") != "ForgeLLM":
        issues.append("receipt project must match ForgeLLM loop declaration")
    if receipt.get("task_id") != declaration.get("task_id"):
        issues.append("receipt task_id must match loop declaration task_id")
    return issues


def _validate_receipt_counts(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    issues = _legacy._validate_receipt_counts(receipt, declaration)
    if receipt.get("stop_reason") == "verify_pass" and receipt.get("iterations") == 0:
        issues.append("receipt verify_pass requires iterations >= 1")
    return issues


def _validate_verification(receipt: Mapping[str, Any]) -> list[str]:
    verification = receipt.get("verification")
    if not isinstance(verification, Mapping):
        return ["receipt verification must be a mapping with structured verifier evidence"]

    issues = _exact_keys(verification, _REQUIRED_VERIFICATION_FIELDS, "receipt verification")
    verifier = verification.get("verifier")
    if not isinstance(verifier, str) or not verifier.strip() or verifier.startswith(_TEMPLATE_PREFIX):
        issues.append(
            "receipt verification.verifier must identify the execution verifier and cannot be a template marker"
        )

    verified_commit = verification.get("verified_commit")
    if not _legacy._is_nonzero_full_sha(verified_commit):
        issues.append("receipt verification.verified_commit must be a non-zero 40-character lowercase Git SHA")
    elif verified_commit != receipt.get("final_commit"):
        issues.append("receipt verification.verified_commit must equal receipt final_commit")

    disposition = verification.get("disposition")
    if disposition not in _VALID_VERIFICATION_DISPOSITIONS:
        issues.append(f"receipt verification.disposition must be one of {sorted(_VALID_VERIFICATION_DISPOSITIONS)}")
    if receipt.get("stop_reason") == "verify_pass" and disposition != "pass":
        issues.append("receipt verify_pass requires verification.disposition pass")

    evidence = verification.get("evidence")
    if not _legacy._is_sequence(evidence) or not evidence:
        issues.append("receipt verification.evidence must be a non-empty array of evidence strings")
    elif not all(isinstance(item, str) and item and not item.startswith(_TEMPLATE_PREFIX) for item in evidence):
        issues.append("receipt verification.evidence must contain non-template evidence strings")
    return issues


def validate_loop_receipt(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    """Validate final schema-1.1 execution evidence bound to the verified commit."""

    if not isinstance(receipt, Mapping):
        return ["receipt must be a mapping"]
    if not isinstance(declaration, Mapping):
        return ["loop declaration must be a mapping before validating its receipt"]

    issues = _exact_keys(receipt, _REQUIRED_RECEIPT_FIELDS, "receipt")
    issues.extend(_validate_receipt_identity(receipt, declaration))
    issues.extend(_legacy._validate_receipt_commits(receipt, declaration))
    issues.extend(_validate_receipt_counts(receipt, declaration))
    issues.extend(_legacy._validate_receipt_scope(receipt, declaration))
    if receipt.get("verify_commands") != declaration.get("VERIFY"):
        issues.append("receipt verify_commands must exactly equal declared VERIFY")
    issues.extend(_validate_verification(receipt))
    plan = receipt.get("plan")
    if not isinstance(plan, str) or not plan.strip():
        issues.append("receipt plan must identify the controlling plan")
    stop_reason = receipt.get("stop_reason")
    if stop_reason not in _legacy._VALID_FINAL_STOP_REASONS:
        issues.append(f"receipt stop_reason must be one of {sorted(_legacy._VALID_FINAL_STOP_REASONS)}")
    return issues


def _validate_template_verification(receipt: Mapping[str, Any]) -> list[str]:
    verification = receipt.get("verification")
    if not isinstance(verification, Mapping):
        return ["receipt template verification must be a mapping"]

    issues = _exact_keys(verification, _REQUIRED_VERIFICATION_FIELDS, "receipt template verification")
    verifier = verification.get("verifier")
    if not isinstance(verifier, str) or not verifier.startswith(_TEMPLATE_PREFIX):
        issues.append("receipt template verification.verifier must start with TEMPLATE:")
    if verification.get("verified_commit") != _TEMPLATE_VERIFIED_COMMIT:
        issues.append(f"receipt template verification.verified_commit must be exactly {_TEMPLATE_VERIFIED_COMMIT}")
    if verification.get("disposition") != "template":
        issues.append("receipt template verification.disposition must be exactly template")
    evidence = verification.get("evidence")
    if not _legacy._is_sequence(evidence) or not evidence:
        issues.append("receipt template verification.evidence must be a non-empty array")
    elif not all(isinstance(item, str) and item.startswith(_TEMPLATE_PREFIX) for item in evidence):
        issues.append("receipt template verification.evidence entries must start with TEMPLATE:")
    return issues


def validate_loop_receipt_template(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    """Validate the inert schema-1.1 template without promoting it to final evidence."""

    if not isinstance(receipt, Mapping):
        return ["receipt template must be a mapping"]
    if not isinstance(declaration, Mapping):
        return ["loop declaration must be a mapping before validating its receipt template"]

    issues = _exact_keys(receipt, _REQUIRED_RECEIPT_FIELDS, "receipt template")
    issues.extend(_validate_receipt_identity(receipt, declaration))
    if not _legacy._is_nonzero_full_sha(receipt.get("base_commit")):
        issues.append("receipt template base_commit must be a non-zero full Git SHA")
    if receipt.get("base_commit") != declaration.get("base_commit"):
        issues.append("receipt template base_commit must equal the loop declaration base_commit")
    if receipt.get("final_commit") != _TEMPLATE_FINAL_COMMIT:
        issues.append(f"receipt template final_commit must be exactly {_TEMPLATE_FINAL_COMMIT}")
    expected_state = {
        "iterations": 0,
        "identical_failures_at_stop": 0,
        "stop_reason": "template",
        "changed_paths": [],
        "scope_check": "pass",
    }
    for field, value in expected_state.items():
        if receipt.get(field) != value:
            issues.append(f"receipt template {field} must be {value!r}")
    if receipt.get("verify_commands") != declaration.get("VERIFY"):
        issues.append("receipt template verify_commands must exactly equal declared VERIFY")
    issues.extend(_validate_template_verification(receipt))
    plan = receipt.get("plan")
    if not isinstance(plan, str) or not plan.strip():
        issues.append("receipt template plan must identify the controlling plan")
    return issues
