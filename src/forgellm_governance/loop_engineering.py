"""Pure validation helpers for the bounded Loop Engineering bridge."""

from __future__ import annotations

import hashlib
import math
import posixpath
import re
import shlex
from collections.abc import Mapping, Sequence
from numbers import Real
from pathlib import Path
from typing import Any

import yaml

_SHELL_TOKENS = frozenset({";", "&", "|", "<", ">"})
_WRAPPERS = frozenset({"env", "command", "exec", "xargs", "parallel", "timeout", "nice", "setsid"})
_FORBIDDEN_TOOLS = frozenset(
    {
        "aws",
        "az",
        "curl",
        "docker",
        "gcloud",
        "kubectl",
        "nc",
        "netcat",
        "npm",
        "pip",
        "pip3",
        "podman",
        "ssh",
        "sudo",
        "wget",
    }
)
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_DECLARATION_METADATA = frozenset({"schema_version", "project", "task_id", "base_commit"})
_DECLARATION_FIELDS = frozenset({"GOAL", "SCOPE", "VERIFY", "BUDGET", "STOP", "RECEIPT"})
_BUDGET_FIELDS = frozenset({"max_iterations", "max_identical_failures", "max_wall_minutes"})
_STOP_FIELDS = frozenset(
    {"on_verify_pass", "on_budget_exhausted", "on_identical_failure_limit", "privileged_operation"}
)
_RECEIPT_FIELDS = frozenset(
    {
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
        "verification",
        "verify_commands",
        "verify_evidence",
        "reviewer",
    }
)
_RECEIPT_PREFIX = "artifacts/governance/loop-engineering/receipts"
_SHADOW_STATE_BASENAMES = frozenset({"goals.md", "status.md", "project_brief.md", "project-brief.md"})
_STOP_REASONS = frozenset(
    {"verify_pass", "budget_exhausted", "identical_failure_limit", "stop_and_escalate", "manual_stop"}
)
_VERIFICATION_FIELDS = frozenset({"disposition"})
_VERIFICATION_DISPOSITIONS = frozenset(
    {"pass", "budget_exhausted", "identical_failure_limit", "stop_and_escalate", "manual_stop"}
)
_STOP_DISPOSITION = {
    "verify_pass": "pass",
    "budget_exhausted": "budget_exhausted",
    "identical_failure_limit": "identical_failure_limit",
    "stop_and_escalate": "stop_and_escalate",
    "manual_stop": "manual_stop",
}
_TEMPLATE_MARKERS = ("template", "replace_with", "<placeholder>", "tbd", "todo")
EXPECTED_UPSTREAM_REPOSITORY = "https://github.com/lcajigasm/loop-engineering"
EXPECTED_UPSTREAM_COMMIT = "ae2d610985064bb30c5013261988c813013c09e3"
EXPECTED_LICENSE_BLOB = "84524f23b209fccb02a8f239165f0444bfd70f3f"
EXPECTED_VENDOR_FILES = {
    "LICENSE": EXPECTED_LICENSE_BLOB,
    "core/METHODOLOGY.md": "c7094ca40c2257d653c4d48f6b87c40cb82b209b",
    "core/COMMANDS.md": "4de9e981ad89c04f28d94ea4ad5b97e1b513b578",
    "core/templates/PLAN.template.md": "3477e664b738a46b36e4b015b1b2ef502b5c6dd4",
    "core/templates/RECEIPT.template.md": "2f5da7d5736067c965b4fed2604982e00a79b024",
    "core/templates/INTEGRATION.template.md": "2f740b4dbc1f7ee63688abe570c179bd28fc4508",
    "core/templates/CAPABILITIES.template.md": "da89bdb92b2f61558babc7c699cd2c350904f07a",
}
EXPECTED_EXCLUDED_EXECUTABLE_SURFACES = ("install.sh", "core/scripts/", "claude-code/", "codex/")
EXPECTED_EXCLUDED_SHADOW_TEMPLATES = (
    "core/templates/GOALS.template.md",
    "core/templates/STATUS.template.md",
    "core/templates/PROJECT_BRIEF.template.md",
    "core/templates/ADR.template.md",
)
_PROVENANCE_FIELDS = frozenset(
    {
        "schema_version",
        "upstream_repository",
        "upstream_commit",
        "license",
        "license_blob_sha",
        "files",
        "excluded_executable_surfaces",
        "excluded_shadow_state_templates",
    }
)


def _split_verify_tokens(command: object) -> list[str] | None:
    if not isinstance(command, str) or not command.strip():
        return None
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        return list(lexer)
    except ValueError:
        return None


def _verify_shell_structure_issue(tokens: Sequence[str], command: str) -> str | None:
    if any(token in _SHELL_TOKENS or all(char in _SHELL_TOKENS for char in token) for token in tokens):
        return "shell composition or redirection is forbidden; stop_and_escalate"
    if "\n" in command or "\r" in command or "`" in command or "$((" in command:
        return "shell evaluation syntax is forbidden; stop_and_escalate"
    if "$(" in command:
        return "command substitution is forbidden; stop_and_escalate"
    return None


def _verify_wrapper_issue(tokens: Sequence[str]) -> str | None:
    if any(_ASSIGNMENT.match(token) for token in tokens):
        return "environment assignments are forbidden; stop_and_escalate"
    if tokens and tokens[0] in _WRAPPERS:
        return "command wrappers are forbidden; stop_and_escalate"
    return None


def _verify_tool_authority_issue(tokens: Sequence[str]) -> str | None:
    if not tokens:
        return "empty or invalid command is rejected; stop_and_escalate"
    tool = tokens[0].rsplit("/", 1)[-1]
    if tool in _FORBIDDEN_TOOLS:
        return "secret or infrastructure clients are forbidden; stop_and_escalate"
    if tool == "gh" and len(tokens) > 1 and tokens[1:3] == ["auth", "status"]:
        return "credential inspection is forbidden; stop_and_escalate"
    return None


def _is_allowed_git(tokens: Sequence[str]) -> bool:
    if not tokens or tokens[0] != "git" or len(tokens) < 2:
        return False
    subcommand = tokens[1]
    if subcommand == "status":
        return all(token in {"--short", "--porcelain", "--branch"} for token in tokens[2:])
    if subcommand == "diff":
        return all(token in {"--check", "--stat", "--name-only", "--name-status"} for token in tokens[2:])
    if subcommand == "log":
        return all(not token.startswith("-") or token in {"--oneline", "--decorate", "--stat"} for token in tokens[2:])
    if subcommand == "show":
        return all(not token.startswith("-") or token in {"--stat", "--oneline", "--name-only"} for token in tokens[2:])
    if subcommand == "rev-parse":
        return all(token in {"--show-toplevel", "--show-prefix", "HEAD"} for token in tokens[2:])
    if subcommand == "branch":
        return tokens[2:] == ["--show-current"]
    return False


def _is_allowed_make(tokens: Sequence[str]) -> bool:
    return (
        len(tokens) == 2
        and tokens[0] == "make"
        and tokens[1]
        in {
            "ci",
            "lint",
            "test",
            "validate",
            "validate-loop",
            "verify",
            "verify-speculative",
        }
    )


def _is_allowed_gh(tokens: Sequence[str]) -> bool:
    if len(tokens) < 3 or tokens[:3] != ["gh", "pr", "view"]:
        return False
    return all(token == "--json" or token.startswith("--json=") or not token.startswith("-") for token in tokens[3:])


def validate_loop_verify_command(command: object) -> list[str]:
    """Return diagnostics for a command proposed as a read-only verifier."""
    tokens = _split_verify_tokens(command)
    if tokens is None:
        return ["command cannot be safely tokenized; stop_and_escalate"]
    text = command if isinstance(command, str) else ""
    for check in (
        lambda: _verify_shell_structure_issue(tokens, text),
        lambda: _verify_wrapper_issue(tokens),
        lambda: _verify_tool_authority_issue(tokens),
    ):
        issue = check()
        if issue:
            return [issue]
    if _is_allowed_git(tokens) or _is_allowed_make(tokens) or _is_allowed_gh(tokens):
        return []
    return ["command is not on the read-only verifier allowlist; stop_and_escalate"]


def _key_set_issue(data: Mapping[str, Any], expected: frozenset[str], name: str) -> list[str]:
    actual = set(data)
    issues: list[str] = []
    missing = sorted(expected - actual)
    extra = sorted(actual - expected, key=str)
    if missing:
        issues.append(f"{name} is missing required fields: {', '.join(missing)}")
    if extra:
        issues.append(f"{name} contains unknown fields: {', '.join(map(str, extra))}")
    return issues


def _canonical_posix_path(value: object) -> tuple[str, bool] | None:
    """Return a safe relative POSIX path and its directory marker."""
    if not isinstance(value, str) or not value or "\x00" in value or "\\" in value:
        return None
    if value.startswith("/") or value.startswith("~"):
        return None
    directory = value.endswith("/")
    path = value[:-1] if directory else value
    if not path or path.startswith("/"):
        return None
    parts = path.split("/")
    if any(not part or part in {".", ".."} for part in parts):
        return None
    normalized = posixpath.normpath(path)
    if normalized in {"", ".", ".."} or normalized.startswith("../"):
        return None
    return normalized, directory


def _is_shadow_state_path(path: str) -> bool:
    return posixpath.basename(path).casefold() in _SHADOW_STATE_BASENAMES


def _path_is_contained(path: str, base: str, base_is_directory: bool) -> bool:
    return path == base or (base_is_directory and path.startswith(f"{base}/"))


def _validate_path_list(
    value: object,
    field: str,
    issues: list[str],
    *,
    allow_empty: bool,
) -> list[tuple[str, bool]]:
    if not isinstance(value, list) or (not allow_empty and not value):
        issues.append(f"{field} must be a {'non-empty ' if not allow_empty else ''}list of POSIX paths")
        return []
    paths: list[tuple[str, bool]] = []
    seen: set[tuple[str, bool]] = set()
    for index, item in enumerate(value):
        parsed = _canonical_posix_path(item)
        if parsed is None:
            suffix = " within allowed_paths" if field == "SCOPE" else ""
            issues.append(f"{field}[{index}] must be a safe relative POSIX path{suffix}")
            continue
        path, directory = parsed
        if _is_shadow_state_path(path):
            issues.append(f"{field}[{index}] targets forbidden shadow-state path {path}")
        if parsed in seen:
            issues.append(f"{field}[{index}] duplicates path {path}")
        seen.add(parsed)
        paths.append(parsed)
    return paths


def _validate_sha(value: object, field: str, issues: list[str], *, allow_template: bool = False) -> bool:
    if allow_template and isinstance(value, str) and _looks_like_template(value):
        return True
    if not isinstance(value, str) or not _FULL_SHA.fullmatch(value) or not any(char != "0" for char in value):
        issues.append(f"{field} must be a lowercase non-zero full 40-character SHA-1")
        return False
    return True


def _looks_like_template(value: object) -> bool:
    if not isinstance(value, str):
        return False
    lowered = value.casefold()
    return any(marker in lowered for marker in _TEMPLATE_MARKERS)


def _validate_positive_budget(value: object, field: str, issues: list[str], *, integer: bool) -> None:
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or value <= 0:
        issues.append(f"{field} must be a positive finite number")
    elif integer and not isinstance(value, int):
        issues.append(f"{field} must be a positive integer ceiling")


def _validate_declaration_header(declaration: Mapping[str, Any], issues: list[str]) -> None:
    issues.extend(_key_set_issue(declaration, _DECLARATION_METADATA | _DECLARATION_FIELDS, "declaration"))
    if declaration.get("schema_version") != "1.0":
        issues.append("schema_version must be '1.0'")
    if declaration.get("project") != "ForgeLLM":
        issues.append("project must bind the declaration to ForgeLLM")
    if not isinstance(declaration.get("task_id"), str) or not declaration.get("task_id"):
        issues.append("task_id must be a non-empty string")
    _validate_sha(declaration.get("base_commit"), "base_commit", issues)


def _validate_declaration_semantics(
    declaration: Mapping[str, Any], task_packet: Mapping[str, Any], issues: list[str]
) -> None:
    goal = declaration.get("GOAL")
    if not isinstance(goal, str) or not goal.strip() or _looks_like_template(goal):
        issues.append("GOAL must be a non-template, non-empty string")

    allowed_paths = _validate_path_list(task_packet.get("allowed_paths"), "allowed_paths", issues, allow_empty=False)
    scope_paths = _validate_path_list(declaration.get("SCOPE"), "SCOPE", issues, allow_empty=False)
    for scope, _scope_directory in scope_paths:
        if not any(
            _path_is_contained(scope, allowed, allowed_directory) for allowed, allowed_directory in allowed_paths
        ):
            issues.append(f"SCOPE path {scope!r} is outside task packet allowed_paths")

    packet_commands = task_packet.get("verification_commands")
    if not isinstance(packet_commands, list) or not packet_commands:
        issues.append("verification_commands must be a non-empty list")
        packet_commands = []
    verify = declaration.get("VERIFY")
    if not isinstance(verify, list) or not verify:
        issues.append("VERIFY must be a non-empty list")
        verify = []
    seen_commands: set[str] = set()
    for index, command in enumerate(verify):
        if not isinstance(command, str) or not command.strip():
            issues.append(f"VERIFY[{index}] must be a non-empty command")
            continue
        if command in seen_commands:
            issues.append(f"VERIFY[{index}] duplicates a command")
        seen_commands.add(command)
        firewall_issues = validate_loop_verify_command(command)
        if firewall_issues:
            issues.extend(f"VERIFY[{index}] rejected by verifier firewall: {message}" for message in firewall_issues)
        if command not in packet_commands:
            issues.append(f"VERIFY[{index}] is not authorized by task packet verification_commands")

    budget = declaration.get("BUDGET")
    if not isinstance(budget, Mapping):
        issues.append("BUDGET must be a mapping")
    else:
        issues.extend(_key_set_issue(budget, _BUDGET_FIELDS, "BUDGET"))
        _validate_positive_budget(budget.get("max_iterations"), "max_iterations", issues, integer=True)
        _validate_positive_budget(budget.get("max_identical_failures"), "max_identical_failures", issues, integer=True)
        _validate_positive_budget(budget.get("max_wall_minutes"), "max_wall_minutes", issues, integer=False)

    stop = declaration.get("STOP")
    if not isinstance(stop, Mapping):
        issues.append("STOP must be a mapping")
    else:
        issues.extend(_key_set_issue(stop, _STOP_FIELDS, "STOP"))
        for field in ("on_verify_pass", "on_budget_exhausted", "on_identical_failure_limit"):
            if stop.get(field) is not True:
                issues.append(f"STOP.{field} must be true for fail-closed stopping")
        if stop.get("privileged_operation") != "stop_and_escalate":
            issues.append("STOP.privileged_operation must be stop_and_escalate")

    receipt = _canonical_posix_path(declaration.get("RECEIPT"))
    if receipt is None or receipt[1]:
        issues.append("RECEIPT must be a relative POSIX file path")
    else:
        receipt_path = receipt[0]
        if not receipt_path.startswith(f"{_RECEIPT_PREFIX}/"):
            issues.append(f"RECEIPT must be contained under {_RECEIPT_PREFIX}/")
        elif not receipt_path.endswith((".yaml", ".yml")):
            issues.append("RECEIPT must name a YAML receipt file")


def validate_loop_declaration(declaration: Mapping[str, Any], task_packet: Mapping[str, Any]) -> list[str]:
    """Validate a bounded declaration against one ForgeLLM task packet."""
    issues: list[str] = []
    if not isinstance(declaration, Mapping):
        return ["declaration must be a mapping"]
    if not isinstance(task_packet, Mapping):
        return ["task_packet must be a mapping"]
    _validate_declaration_header(declaration, issues)
    expected_task_id = task_packet.get("task_id")
    if declaration.get("task_id") != expected_task_id:
        issues.append("task_id must match the task packet task_id")
    _validate_declaration_semantics(declaration, task_packet, issues)
    return issues


def _validate_receipt_header(
    receipt: Mapping[str, Any], declaration: Mapping[str, Any], issues: list[str], *, allow_template: bool
) -> None:
    issues.extend(_key_set_issue(receipt, _RECEIPT_FIELDS, "receipt"))
    if receipt.get("schema_version") != "1.0":
        issues.append("schema_version must be '1.0'")
    if receipt.get("project") != "ForgeLLM":
        issues.append("project must bind the receipt to ForgeLLM")
    if receipt.get("task_id") != declaration.get("task_id"):
        issues.append("task_id must match the declaration")
    plan = receipt.get("plan")
    if not isinstance(plan, str) or not plan.strip():
        issues.append("plan must be a non-empty string")
    elif _looks_like_template(plan) and not allow_template:
        issues.append("plan must not be template evidence")
    _validate_sha(receipt.get("base_commit"), "base_commit", issues, allow_template=allow_template)
    if not (allow_template and _looks_like_template(receipt.get("base_commit"))) and receipt.get(
        "base_commit"
    ) != declaration.get("base_commit"):
        issues.append("base_commit must match the declaration base_commit")


def _validate_receipt_common(
    receipt: Mapping[str, Any], declaration: Mapping[str, Any], *, allow_template: bool
) -> list[str]:
    issues: list[str] = []
    if not isinstance(receipt, Mapping):
        return ["receipt must be a mapping"]
    if not isinstance(declaration, Mapping):
        return ["declaration must be a mapping"]
    _validate_receipt_header(receipt, declaration, issues, allow_template=allow_template)
    _validate_sha(receipt.get("final_commit"), "final_commit", issues, allow_template=allow_template)

    iterations = receipt.get("iterations")
    if isinstance(iterations, bool) or not isinstance(iterations, int) or iterations < 0:
        issues.append("iterations must be a non-negative integer")
    identical_failures = receipt.get("identical_failures_at_stop")
    if isinstance(identical_failures, bool) or not isinstance(identical_failures, int) or identical_failures < 0:
        issues.append("identical_failures_at_stop must be a non-negative integer")

    budget = declaration.get("BUDGET")
    if isinstance(budget, Mapping):
        max_iterations = budget.get("max_iterations")
        max_identical = budget.get("max_identical_failures")
        if (
            isinstance(iterations, int)
            and not isinstance(iterations, bool)
            and isinstance(max_iterations, int)
            and iterations > max_iterations
        ):
            issues.append("iterations cannot exceed BUDGET.max_iterations")
        if (
            isinstance(identical_failures, int)
            and not isinstance(identical_failures, bool)
            and isinstance(max_identical, int)
            and identical_failures > max_identical
        ):
            issues.append("identical_failures_at_stop cannot exceed BUDGET.max_identical_failures")
        if isinstance(iterations, int) and isinstance(identical_failures, int) and identical_failures > iterations:
            issues.append("identical_failures_at_stop cannot exceed iterations")

    stop_reason = receipt.get("stop_reason")
    if allow_template:
        if stop_reason != "template":
            issues.append("template receipt stop_reason must be 'template'")
    elif not isinstance(stop_reason, str) or stop_reason not in _STOP_REASONS or _looks_like_template(stop_reason):
        issues.append("stop_reason must be a permitted final stop reason")
    elif isinstance(budget, Mapping):
        if stop_reason == "budget_exhausted" and receipt.get("iterations") != budget.get("max_iterations"):
            issues.append("budget_exhausted stop_reason requires iterations at its ceiling")
        if stop_reason == "identical_failure_limit" and receipt.get("identical_failures_at_stop") != budget.get(
            "max_identical_failures"
        ):
            issues.append("identical_failure_limit stop_reason requires identical_failures_at_stop at its ceiling")

    verification = receipt.get("verification")
    if not isinstance(verification, Mapping):
        issues.append("verification must be a mapping with one disposition")
    else:
        issues.extend(_key_set_issue(verification, _VERIFICATION_FIELDS, "verification"))
        disposition = verification.get("disposition")
        if allow_template:
            if disposition != "template":
                issues.append("template verification disposition must be 'template'")
        elif disposition not in _VERIFICATION_DISPOSITIONS:
            issues.append("verification.disposition must be a permitted final disposition")
        elif _STOP_DISPOSITION.get(stop_reason) != disposition:
            issues.append("verification.disposition must match stop_reason")

    changed_paths = _validate_path_list(receipt.get("changed_paths"), "changed_paths", issues, allow_empty=True)
    declared_scope = _validate_path_list(declaration.get("SCOPE"), "SCOPE", issues, allow_empty=False)
    for changed_path, _changed_directory in changed_paths:
        if not any(
            _path_is_contained(changed_path, scope, scope_directory) for scope, scope_directory in declared_scope
        ):
            issues.append(f"changed_paths path {changed_path!r} is outside declaration SCOPE")

    if receipt.get("scope_check") != "pass":
        issues.append("scope_check must be 'pass'")

    verify_commands = receipt.get("verify_commands")
    declared_verify = declaration.get("VERIFY")
    if not isinstance(verify_commands, list) or verify_commands != declared_verify:
        issues.append("verify_commands must exactly equal declaration VERIFY")
    elif isinstance(verify_commands, list):
        for index, command in enumerate(verify_commands):
            if not isinstance(command, str):
                continue
            for message in validate_loop_verify_command(command):
                issues.append(f"verify_commands[{index}] rejected by verifier firewall: {message}")

    evidence = receipt.get("verify_evidence")
    if not isinstance(evidence, list) or not evidence:
        issues.append("verify_evidence must be a non-empty list")
    else:
        for index, item in enumerate(evidence):
            if not isinstance(item, str) or not item.strip():
                issues.append(f"verify_evidence[{index}] must be a non-empty string")
            elif not allow_template and _looks_like_template(item):
                issues.append(f"verify_evidence[{index}] must not contain template evidence")

    reviewer = receipt.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip():
        issues.append("reviewer must identify an independent reviewer")
    elif not allow_template and (
        _looks_like_template(reviewer)
        or reviewer.casefold().strip() in {"self", "same-agent", "author", "loop", "automated"}
        or "self-assert" in reviewer.casefold()
    ):
        issues.append("reviewer must identify an independent reviewer, not template or self-asserted evidence")

    return issues


def validate_loop_receipt(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    """Validate committed final evidence against its bounded declaration."""
    return _validate_receipt_common(receipt, declaration, allow_template=False)


def validate_loop_receipt_template(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    """Validate receipt shape while permitting explicit template placeholders."""
    return _validate_receipt_common(receipt, declaration, allow_template=True)


def _git_blob_sha(data: bytes) -> str:
    payload = f"blob {len(data)}\0".encode("ascii") + data
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


def validate_vendor_provenance(root: Path | str) -> list[str]:
    """Verify the pinned vendor tree is exactly the reviewed inert upstream subset."""
    vendor = Path(root).resolve() / "third_party" / "loop-engineering"
    provenance_path = vendor / "PROVENANCE.yaml"
    issues: list[str] = []
    try:
        provenance = yaml.safe_load(provenance_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"vendor provenance file is missing: {provenance_path}"]
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        return [f"vendor provenance file is invalid: {exc}"]
    if not isinstance(provenance, Mapping):
        return ["vendor PROVENANCE.yaml root must be a mapping"]

    actual_fields = set(provenance)
    if actual_fields != _PROVENANCE_FIELDS:
        issues.append(
            "vendor provenance requires exact fields; "
            f"missing={sorted(_PROVENANCE_FIELDS - actual_fields)}, extra={sorted(actual_fields - _PROVENANCE_FIELDS)}"
        )
    if provenance.get("schema_version") != "1.0":
        issues.append("vendor provenance schema_version must be '1.0'")
    if provenance.get("upstream_repository") != EXPECTED_UPSTREAM_REPOSITORY:
        issues.append(f"upstream_repository must be {EXPECTED_UPSTREAM_REPOSITORY}")
    if provenance.get("upstream_commit") != EXPECTED_UPSTREAM_COMMIT:
        issues.append(f"upstream_commit must be exactly {EXPECTED_UPSTREAM_COMMIT}")
    if provenance.get("license") != "MIT":
        issues.append("vendor license must be exactly MIT")
    if provenance.get("license_blob_sha") != EXPECTED_LICENSE_BLOB:
        issues.append(f"license_blob_sha must be exactly {EXPECTED_LICENSE_BLOB}")
    if provenance.get("excluded_executable_surfaces") != list(EXPECTED_EXCLUDED_EXECUTABLE_SURFACES):
        issues.append("excluded_executable_surfaces must preserve the reviewed executable exclusions")
    if provenance.get("excluded_shadow_state_templates") != list(EXPECTED_EXCLUDED_SHADOW_TEMPLATES):
        issues.append("excluded_shadow_state_templates must preserve the reviewed shadow-state exclusions")

    bindings: dict[str, str] = {}
    raw_files = provenance.get("files")
    if not isinstance(raw_files, list):
        issues.append("vendor provenance files must be an array")
        raw_files = []
    for item in raw_files:
        if not isinstance(item, Mapping):
            issues.append("each vendor provenance file record must be a mapping")
            continue
        if set(item) != {"path", "upstream_blob_sha"}:
            issues.append("each vendor provenance file record requires exactly path and upstream_blob_sha")
            continue
        path = item.get("path")
        blob = item.get("upstream_blob_sha")
        if not isinstance(path, str) or not isinstance(blob, str):
            issues.append("each vendor provenance file record requires string path and upstream_blob_sha")
            continue
        if path in bindings:
            issues.append(f"duplicate vendor provenance path: {path}")
        bindings[path] = blob
    if bindings != EXPECTED_VENDOR_FILES:
        issues.append("vendor provenance files must match the exact reviewed static subset and upstream blob SHAs")

    expected_local_files = set(EXPECTED_VENDOR_FILES) | {"PROVENANCE.yaml"}
    actual_local_files = {path.relative_to(vendor).as_posix() for path in vendor.rglob("*") if path.is_file()}
    if actual_local_files != expected_local_files:
        issues.append(
            "vendored Loop Engineering tree must contain only the reviewed inert subset; "
            f"expected={sorted(expected_local_files)}, actual={sorted(actual_local_files)}"
        )
    symlinks = [path.relative_to(vendor).as_posix() for path in vendor.rglob("*") if path.is_symlink()]
    if symlinks:
        issues.append(f"vendored Loop Engineering tree must not contain symlinks: {sorted(symlinks)}")

    for relative, expected_blob in EXPECTED_VENDOR_FILES.items():
        path = vendor / relative
        try:
            actual_blob = _git_blob_sha(path.read_bytes())
        except (FileNotFoundError, OSError) as exc:
            issues.append(f"vendored file cannot be read: {relative}: {exc}")
            continue
        if bindings.get(relative) != expected_blob:
            issues.append(f"{relative} provenance blob must be {expected_blob}, got {bindings.get(relative)!r}")
        if actual_blob != expected_blob:
            issues.append(f"{relative} Git blob drift: expected {expected_blob}, got {actual_blob}")
    return issues
