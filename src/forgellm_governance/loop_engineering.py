"""Fail-closed validation for ForgeLLM bounded Loop Engineering artifacts."""

from __future__ import annotations

import hashlib
import re
import shlex
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

REQUIRED_LOOP_FIELDS = {"GOAL", "SCOPE", "VERIFY", "BUDGET", "STOP", "RECEIPT"}
_LOOP_METADATA_FIELDS = {"schema_version", "project", "task_id", "base_commit"}
SHADOW_STATE_PATHS = {
    "docs/GOALS.md",
    "docs/STATUS.md",
    "docs/PROJECT_BRIEF.md",
}
PRIVILEGED_OPERATION_POLICY = "stop_and_escalate"
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
EXPECTED_EXCLUDED_EXECUTABLE_SURFACES = {"install.sh", "core/scripts/", "claude-code/", "codex/"}
EXPECTED_EXCLUDED_SHADOW_TEMPLATES = {
    "core/templates/GOALS.template.md",
    "core/templates/STATUS.template.md",
    "core/templates/PROJECT_BRIEF.template.md",
    "core/templates/ADR.template.md",
}
_RECEIPT_PREFIX = "artifacts/governance/loop-engineering/receipts/"
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_ZERO_SHA = "0" * 40
_TEMPLATE_FINAL_COMMIT = "REPLACE_WITH_FINAL_COMMIT"
_TEMPLATE_STOP_REASON = "template"
_TEMPLATE_PREFIX = "TEMPLATE:"
_VALID_FINAL_STOP_REASONS = {
    "verify_pass",
    "budget_exhausted",
    "identical_failure_limit",
    "privileged_operation",
    "manual_stop",
}
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
    "verify_evidence",
    "reviewer",
}
_SECRET_VERIFY_MARKERS = (
    "SONAR_TOKEN",
    "GITHUB_TOKEN",
    "AWS_SECRET_ACCESS_KEY",
    "${{ secrets.",
    "secrets.",
)
_FORBIDDEN_VERIFY_TOKENS = {
    "sudo",
    "ssh",
    "scp",
    "tailscale",
    "sonar-scanner",
    "sonar-scanner-cli",
    "systemctl",
    "nohup",
    "watch",
}
_FORBIDDEN_VERIFY_WRAPPERS = {
    "busybox",
    "chrt",
    "command",
    "env",
    "exec",
    "ionice",
    "nice",
    "parallel",
    "setsid",
    "stdbuf",
    "timeout",
    "xargs",
}
_ALLOWED_GIT_SUBCOMMANDS = {
    "cat-file",
    "describe",
    "diff",
    "log",
    "ls-files",
    "ls-tree",
    "rev-parse",
    "show",
    "status",
}
_ALLOWED_GH_OPERATIONS = {("pr", "view")}
_FORBIDDEN_INFRASTRUCTURE_CLIENTS = {
    "ansible",
    "aws",
    "az",
    "docker",
    "gcloud",
    "helm",
    "kubectl",
    "nomad",
    "podman",
    "terraform",
    "vault",
}
_SHELL_PUNCTUATION = ";&|<>"
_ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
_CURL_MUTATION_FLAGS = {
    "-d",
    "--data",
    "--data-ascii",
    "--data-binary",
    "--data-raw",
    "--data-urlencode",
    "-F",
    "--form",
    "-T",
    "--upload-file",
}


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, (str, bytes))


def _positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_nonzero_full_sha(value: Any) -> bool:
    return isinstance(value, str) and value != _ZERO_SHA and _FULL_SHA.fullmatch(value) is not None


def _normalize_repo_path(value: Any) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip().replace("\\", "/")
    if raw in {".", ".."} or raw.startswith("/"):
        return None
    path = PurePosixPath(raw)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return None
    normalized = str(path)
    return normalized if normalized not in {"", "."} else None


def _path_is_within(entry: Any, scope: Any) -> bool:
    entry_path = _normalize_repo_path(entry)
    scope_path = _normalize_repo_path(scope)
    if entry_path is None or scope_path is None:
        return False
    if entry_path == scope_path:
        return True
    return isinstance(scope, str) and scope.rstrip().endswith("/") and entry_path.startswith(scope_path + "/")


def _scope_entry_authorized(entry: Any, allowed_paths: Sequence[Any]) -> bool:
    return any(_path_is_within(entry, allowed) for allowed in allowed_paths)


def _validate_loop_fields(declaration: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    semantic_fields = set(declaration) - _LOOP_METADATA_FIELDS
    if semantic_fields != REQUIRED_LOOP_FIELDS:
        missing = sorted(REQUIRED_LOOP_FIELDS - semantic_fields)
        extra = sorted(semantic_fields - REQUIRED_LOOP_FIELDS)
        issues.append(
            "loop must declare exactly the six semantic fields GOAL, SCOPE, VERIFY, BUDGET, STOP, RECEIPT; "
            f"missing={missing}, extra={extra}"
        )
    if declaration.get("schema_version") != "1.0":
        issues.append("schema_version must be exactly '1.0'")
    if declaration.get("project") != "ForgeLLM":
        issues.append("project must be exactly ForgeLLM")
    if not isinstance(declaration.get("GOAL"), str) or not declaration["GOAL"].strip():
        issues.append("GOAL must be a non-empty sentence")
    if not _is_nonzero_full_sha(declaration.get("base_commit")):
        issues.append("base_commit must be a non-zero 40-character lowercase Git SHA")
    return issues


def _validate_scope(declaration: Mapping[str, Any], task_packet: Mapping[str, Any]) -> list[str]:
    scope = declaration.get("SCOPE")
    allowed_paths = task_packet.get("allowed_paths")
    if not _is_sequence(scope) or not scope:
        return ["SCOPE must be a non-empty array constrained by task packet allowed_paths"]
    if not _is_sequence(allowed_paths):
        return ["task packet allowed_paths must be an array before validating SCOPE"]

    issues: list[str] = []
    for entry in scope:
        normalized = _normalize_repo_path(entry)
        if normalized is None or not _scope_entry_authorized(entry, allowed_paths):
            issues.append(f"SCOPE entry {entry!r} is outside task packet allowed_paths")
            continue
        if normalized in SHADOW_STATE_PATHS:
            issues.append(f"SCOPE entry {normalized} is forbidden shadow project state")
    return issues


def _first_subcommand(tokens: Sequence[str], executable: str) -> str | None:
    if not tokens or Path(tokens[0]).name != executable:
        return None
    for token in tokens[1:]:
        if token == "--":
            continue
        if token.startswith("-"):
            continue
        return token
    return None


def _curl_mutates(tokens: Sequence[str]) -> bool:
    for index, token in enumerate(tokens):
        if token in _CURL_MUTATION_FLAGS:
            return True
        if (
            token in {"-X", "--request"}
            and index + 1 < len(tokens)
            and tokens[index + 1].upper() in {"POST", "PUT", "PATCH", "DELETE"}
        ):
            return True
        if token.startswith("--request=") and token.split("=", 1)[1].upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            return True
    return False


def _wget_mutates(tokens: Sequence[str]) -> bool:
    for token in tokens:
        lowered = token.lower()
        if lowered.startswith(("--post-data", "--post-file")):
            return True
        if lowered.startswith("--method=") and lowered.split("=", 1)[1].upper() in {"POST", "PUT", "PATCH", "DELETE"}:
            return True
    return False


def _verify_preparse_issue(command: Any) -> str | None:
    if not isinstance(command, str) or not command.strip():
        return "VERIFY command must be a non-empty string"
    if "\n" in command or "\r" in command:
        return "VERIFY command must be one physical command line"
    if "$(" in command or "`" in command:
        return "VERIFY command uses shell command substitution and must stop_and_escalate"
    if any(marker in command for marker in _SECRET_VERIFY_MARKERS):
        return "VERIFY command references a secret-bearing environment and must stop_and_escalate"
    return None


def _split_verify_tokens(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=_SHELL_PUNCTUATION)
    lexer.whitespace_split = True
    lexer.commenters = ""
    return list(lexer)


def _verify_shell_structure_issue(tokens: Sequence[str]) -> str | None:
    for token in tokens:
        if token and set(token) <= set(_SHELL_PUNCTUATION):
            return "VERIFY command uses shell control or redirection syntax and must stop_and_escalate"
    if tokens and _ENV_ASSIGNMENT.match(tokens[0]):
        return "VERIFY command starts with an environment assignment and must stop_and_escalate"
    return None


def _verify_token_issue(tokens: Sequence[str]) -> str | None:
    token_names = {Path(token).name for token in tokens}
    forbidden = sorted(token_names & _FORBIDDEN_VERIFY_TOKENS)
    if forbidden:
        return f"VERIFY command uses privileged/external token {forbidden[0]!r} and must stop_and_escalate"
    return None


def _verify_wrapper_issue(tokens: Sequence[str]) -> str | None:
    executable = Path(tokens[0]).name
    if executable in _FORBIDDEN_VERIFY_WRAPPERS:
        return f"VERIFY command uses wrapper {executable!r} and must stop_and_escalate"
    return None


def _verify_tool_authority_issue(tokens: Sequence[str]) -> str | None:
    executable = Path(tokens[0]).name
    if executable in _FORBIDDEN_INFRASTRUCTURE_CLIENTS:
        return f"VERIFY command uses infrastructure client {executable!r} and must stop_and_escalate"
    if executable == "git":
        if len(tokens) < 2 or tokens[1] not in _ALLOWED_GIT_SUBCOMMANDS:
            return "VERIFY command uses a Git operation outside the read-only allowlist and must stop_and_escalate"
    if executable == "gh":
        operation = tuple(tokens[1:3]) if len(tokens) >= 3 else ()
        if operation not in _ALLOWED_GH_OPERATIONS:
            return "VERIFY command uses a GitHub operation outside the read-only allowlist and must stop_and_escalate"
    if executable == "curl" and _curl_mutates(tokens):
        return "VERIFY command performs an HTTP mutation and must stop_and_escalate"
    if executable == "wget" and _wget_mutates(tokens):
        return "VERIFY command performs an HTTP mutation and must stop_and_escalate"
    return None


def _verify_inline_issue(tokens: Sequence[str]) -> str | None:
    executable = Path(tokens[0]).name
    if executable in {"bash", "dash", "ksh", "sh", "zsh"} and "-c" in tokens[1:]:
        return "VERIFY command executes inline shell code and must stop_and_escalate"
    if executable in {"python", "python3", "pypy", "pypy3"} and "-c" in tokens[1:]:
        return "VERIFY command executes inline Python code and must stop_and_escalate"
    if executable == "node" and any(token in {"-e", "--eval"} for token in tokens[1:]):
        return "VERIFY command executes inline Node code and must stop_and_escalate"
    return None


def _verify_install_issue(tokens: Sequence[str]) -> str | None:
    executable = Path(tokens[0]).name
    if executable in {"pip", "pip3"} and _first_subcommand(tokens, executable) == "install":
        return "VERIFY command installs Python packages and must stop_and_escalate"
    if executable in {"python", "python3"} and len(tokens) >= 4 and tokens[1:4] == ["-m", "pip", "install"]:
        return "VERIFY command installs Python packages and must stop_and_escalate"
    if executable == "cargo" and _first_subcommand(tokens, "cargo") == "install":
        return "VERIFY command installs Cargo tools and must stop_and_escalate"
    return None


def validate_loop_verify_command(command: Any) -> list[str]:
    """Reject verifier commands that cross the loop privilege or mutation firewall."""

    preparse_issue = _verify_preparse_issue(command)
    if preparse_issue is not None:
        return [preparse_issue]
    assert isinstance(command, str)
    try:
        tokens = _split_verify_tokens(command)
    except ValueError as exc:
        return [f"VERIFY command cannot be parsed safely: {exc}"]
    if not tokens:
        return ["VERIFY command must be non-empty after parsing"]
    checks = (
        _verify_shell_structure_issue,
        _verify_token_issue,
        _verify_wrapper_issue,
        _verify_tool_authority_issue,
        _verify_inline_issue,
        _verify_install_issue,
    )
    for check in checks:
        issue = check(tokens)
        if issue is not None:
            return [issue]
    return []


def _validate_verify(declaration: Mapping[str, Any], task_packet: Mapping[str, Any]) -> list[str]:
    verify = declaration.get("VERIFY")
    authorized = task_packet.get("verification_commands")
    if not _is_sequence(verify) or not verify:
        return ["VERIFY must be a non-empty array of task packet verification_commands"]
    if not _is_sequence(authorized):
        return ["task packet verification_commands must be an array before validating VERIFY"]

    issues: list[str] = []
    for command in verify:
        if not isinstance(command, str) or command not in authorized:
            issues.append(f"VERIFY command {command!r} is not present in task packet verification_commands")
            continue
        issues.extend(validate_loop_verify_command(command))
    return issues


def _validate_budget_and_stop(declaration: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    budget = declaration.get("BUDGET")
    if not isinstance(budget, Mapping):
        return ["BUDGET must be a mapping with finite positive ceilings"]
    for field in ("max_iterations", "max_identical_failures", "max_wall_minutes"):
        if not _positive_int(budget.get(field)):
            issues.append(f"BUDGET.{field} must be a positive integer")

    stop = declaration.get("STOP")
    if not isinstance(stop, Mapping):
        issues.append("STOP must be a fail-closed mapping")
        return issues
    for field in ("on_verify_pass", "on_budget_exhausted", "on_identical_failure_limit"):
        if stop.get(field) is not True:
            issues.append(f"STOP.{field} must be true")
    if stop.get("privileged_operation") != PRIVILEGED_OPERATION_POLICY:
        issues.append("STOP.privileged_operation must be exactly stop_and_escalate")
    return issues


def _validate_receipt_destination(declaration: Mapping[str, Any]) -> list[str]:
    destination = declaration.get("RECEIPT")
    normalized = _normalize_repo_path(destination)
    if (
        normalized is None
        or not isinstance(destination, str)
        or not destination.startswith(_RECEIPT_PREFIX)
        or not normalized.startswith(_RECEIPT_PREFIX.rstrip("/") + "/")
        or not normalized.endswith((".yaml", ".yml"))
    ):
        return [f"RECEIPT must be a YAML path under {_RECEIPT_PREFIX}"]
    return []


def validate_loop_declaration(declaration: Mapping[str, Any], task_packet: Mapping[str, Any]) -> list[str]:
    """Validate one loop declaration against the maximum authority of its task packet."""

    if not isinstance(declaration, Mapping):
        return ["loop declaration must be a mapping"]
    if not isinstance(task_packet, Mapping):
        return ["task packet must be a mapping"]

    issues = _validate_loop_fields(declaration)
    packet_task_id = task_packet.get("task_id")
    if not isinstance(declaration.get("task_id"), str) or declaration.get("task_id") != packet_task_id:
        issues.append(f"task_id must match the task packet task_id {packet_task_id!r}")
    issues.extend(_validate_scope(declaration, task_packet))
    issues.extend(_validate_verify(declaration, task_packet))
    issues.extend(_validate_budget_and_stop(declaration))
    issues.extend(_validate_receipt_destination(declaration))
    return issues


def _git_blob_sha(data: bytes) -> str:
    payload = f"blob {len(data)}\0".encode() + data
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


def _load_provenance(path: Path) -> tuple[Mapping[str, Any] | None, list[str]]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"vendor provenance file is missing: {path}"]
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        return None, [f"vendor provenance file is invalid: {exc}"]
    if not isinstance(loaded, Mapping):
        return None, ["vendor PROVENANCE.yaml root must be a mapping"]
    return loaded, []


def _validate_provenance_header(provenance: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if provenance.get("upstream_repository") != EXPECTED_UPSTREAM_REPOSITORY:
        issues.append(f"upstream_repository must be {EXPECTED_UPSTREAM_REPOSITORY}")
    if provenance.get("upstream_commit") != EXPECTED_UPSTREAM_COMMIT:
        issues.append(f"upstream_commit must be exactly {EXPECTED_UPSTREAM_COMMIT}")
    if provenance.get("license") != "MIT":
        issues.append("vendor license must be exactly MIT")
    if provenance.get("license_blob_sha") != EXPECTED_LICENSE_BLOB:
        issues.append(f"license_blob_sha must be exactly {EXPECTED_LICENSE_BLOB}")
    if set(provenance.get("excluded_executable_surfaces", [])) != EXPECTED_EXCLUDED_EXECUTABLE_SURFACES:
        issues.append("excluded_executable_surfaces must preserve the reviewed installer/script/adapter exclusions")
    if set(provenance.get("excluded_shadow_state_templates", [])) != EXPECTED_EXCLUDED_SHADOW_TEMPLATES:
        issues.append("excluded_shadow_state_templates must preserve the reviewed shadow-state exclusions")
    return issues


def _provenance_file_bindings(provenance: Mapping[str, Any]) -> tuple[dict[str, str], list[str]]:
    raw_files = provenance.get("files")
    if not _is_sequence(raw_files):
        return {}, ["vendor provenance files must be an array"]
    bindings: dict[str, str] = {}
    issues: list[str] = []
    for item in raw_files:
        if not isinstance(item, Mapping):
            issues.append("each vendor provenance file record must be a mapping")
            continue
        path = item.get("path")
        blob = item.get("upstream_blob_sha")
        if not isinstance(path, str) or not isinstance(blob, str):
            issues.append("each vendor provenance file record requires path and upstream_blob_sha")
            continue
        if path in bindings:
            issues.append(f"duplicate vendor provenance path: {path}")
        bindings[path] = blob
    if bindings != EXPECTED_VENDOR_FILES:
        issues.append("vendor provenance files must match the exact reviewed static subset and upstream blob SHAs")
    return bindings, issues


def validate_vendor_provenance(root: Path | str) -> list[str]:
    """Verify the vendored static subset is pinned, inert, and byte-identical to reviewed Git blobs."""

    root = Path(root).resolve()
    vendor = root / "third_party" / "loop-engineering"
    provenance, issues = _load_provenance(vendor / "PROVENANCE.yaml")
    if provenance is None:
        return issues
    issues.extend(_validate_provenance_header(provenance))
    bindings, binding_issues = _provenance_file_bindings(provenance)
    issues.extend(binding_issues)

    expected_local_files = set(EXPECTED_VENDOR_FILES) | {"PROVENANCE.yaml"}
    actual_local_files = {path.relative_to(vendor).as_posix() for path in vendor.rglob("*") if path.is_file()}
    if actual_local_files != expected_local_files:
        issues.append(
            "vendored Loop Engineering tree must contain only the reviewed inert subset; "
            f"expected={sorted(expected_local_files)}, actual={sorted(actual_local_files)}"
        )

    for relative, expected_blob in EXPECTED_VENDOR_FILES.items():
        path = vendor / relative
        try:
            actual_blob = _git_blob_sha(path.read_bytes())
        except FileNotFoundError:
            issues.append(f"vendored file is missing: {relative}")
            continue
        recorded_blob = bindings.get(relative)
        if recorded_blob != expected_blob:
            issues.append(f"{relative} provenance blob must be {expected_blob}, got {recorded_blob!r}")
        if actual_blob != expected_blob:
            issues.append(f"{relative} Git blob drift: expected {expected_blob}, got {actual_blob}")
    return issues


def _receipt_keys(receipt: Mapping[str, Any]) -> list[str]:
    keys = set(receipt)
    missing = sorted(_REQUIRED_RECEIPT_FIELDS - keys)
    extra = sorted(keys - _REQUIRED_RECEIPT_FIELDS)
    if not missing and not extra:
        return []
    return [f"receipt requires exact evidence fields; missing={missing}, extra={extra}"]


def _validate_receipt_binding(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if receipt.get("schema_version") != "1.0":
        issues.append("receipt schema_version must be exactly '1.0'")
    if receipt.get("project") != declaration.get("project") or receipt.get("project") != "ForgeLLM":
        issues.append("receipt project must match ForgeLLM loop declaration")
    if receipt.get("task_id") != declaration.get("task_id"):
        issues.append("receipt task_id must match loop declaration task_id")
    return issues


def _validate_receipt_commits(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    for field in ("base_commit", "final_commit"):
        if not _is_nonzero_full_sha(receipt.get(field)):
            issues.append(f"receipt {field} must be a non-zero 40-character lowercase Git SHA")
    if receipt.get("base_commit") != declaration.get("base_commit"):
        issues.append("receipt base_commit must equal the loop declaration base_commit")
    return issues


def _validate_receipt_counts(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    iterations = receipt.get("iterations")
    budget = declaration.get("BUDGET") if isinstance(declaration.get("BUDGET"), Mapping) else {}
    max_iterations = budget.get("max_iterations")
    if not _non_negative_int(iterations):
        issues.append("receipt iterations must be a non-negative integer")
    elif _positive_int(max_iterations) and iterations > max_iterations:
        issues.append(f"receipt iterations {iterations} exceeds BUDGET.max_iterations {max_iterations}")

    identical = receipt.get("identical_failures_at_stop")
    max_identical = budget.get("max_identical_failures")
    if not _non_negative_int(identical):
        issues.append("receipt identical_failures_at_stop must be a non-negative integer")
    elif _positive_int(max_identical) and identical > max_identical:
        issues.append("receipt identical_failures_at_stop exceeds BUDGET.max_identical_failures")
    return issues


def _validate_receipt_scope(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    changed_paths = receipt.get("changed_paths")
    scope = declaration.get("SCOPE")
    if not _is_sequence(changed_paths):
        return ["receipt changed_paths must be an array constrained by loop SCOPE"]
    if not _is_sequence(scope):
        return ["loop SCOPE must be an array before validating receipt changed_paths"]
    issues = [
        f"receipt changed_paths entry {path!r} is outside loop SCOPE"
        for path in changed_paths
        if not any(_path_is_within(path, scope_entry) for scope_entry in scope)
    ]
    if receipt.get("scope_check") != "pass":
        issues.append("receipt scope_check must be exactly pass")
    return issues


def _validate_receipt_evidence(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if receipt.get("verify_commands") != declaration.get("VERIFY"):
        issues.append("receipt verify_commands must exactly equal declared VERIFY")
    evidence = receipt.get("verify_evidence")
    if not _is_sequence(evidence) or not evidence or not all(isinstance(item, str) and item for item in evidence):
        issues.append("receipt verify_evidence must be a non-empty array of evidence strings")
    reviewer = receipt.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.strip() or reviewer.startswith(_TEMPLATE_PREFIX):
        issues.append("receipt reviewer must identify the independent verifier and cannot be a template marker")
    plan = receipt.get("plan")
    if not isinstance(plan, str) or not plan.strip():
        issues.append("receipt plan must identify the controlling plan")
    stop_reason = receipt.get("stop_reason")
    if stop_reason not in _VALID_FINAL_STOP_REASONS:
        issues.append(f"receipt stop_reason must be one of {sorted(_VALID_FINAL_STOP_REASONS)}")
    return issues


def validate_loop_receipt(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    """Validate final reproducible evidence; templates are intentionally rejected."""

    if not isinstance(receipt, Mapping):
        return ["receipt must be a mapping"]
    if not isinstance(declaration, Mapping):
        return ["loop declaration must be a mapping before validating its receipt"]

    issues = _receipt_keys(receipt)
    issues.extend(_validate_receipt_binding(receipt, declaration))
    issues.extend(_validate_receipt_commits(receipt, declaration))
    issues.extend(_validate_receipt_counts(receipt, declaration))
    issues.extend(_validate_receipt_scope(receipt, declaration))
    issues.extend(_validate_receipt_evidence(receipt, declaration))
    return issues


def _validate_template_identity(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    issues = _validate_receipt_binding(receipt, declaration)
    if not _is_nonzero_full_sha(receipt.get("base_commit")):
        issues.append("receipt template base_commit must be a non-zero full Git SHA")
    if receipt.get("base_commit") != declaration.get("base_commit"):
        issues.append("receipt template base_commit must equal the loop declaration base_commit")
    if receipt.get("final_commit") != _TEMPLATE_FINAL_COMMIT:
        issues.append(f"receipt template final_commit must be exactly {_TEMPLATE_FINAL_COMMIT}")
    plan = receipt.get("plan")
    if not isinstance(plan, str) or not plan.strip():
        issues.append("receipt template plan must identify the controlling plan")
    return issues


def _validate_template_state(receipt: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    expected = {
        "iterations": 0,
        "identical_failures_at_stop": 0,
        "stop_reason": _TEMPLATE_STOP_REASON,
        "changed_paths": [],
        "scope_check": "pass",
    }
    for field, value in expected.items():
        if receipt.get(field) != value:
            issues.append(f"receipt template {field} must be {value!r}")
    return issues


def _validate_template_verification(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    if receipt.get("verify_commands") != declaration.get("VERIFY"):
        issues.append("receipt template verify_commands must exactly equal declared VERIFY")

    evidence = receipt.get("verify_evidence")
    evidence_valid = _is_sequence(evidence) and bool(evidence)
    if evidence_valid:
        evidence_valid = all(isinstance(item, str) and item.startswith(_TEMPLATE_PREFIX) for item in evidence)
    if not evidence_valid:
        issues.append("receipt template verify_evidence entries must be non-empty and start with TEMPLATE:")

    reviewer = receipt.get("reviewer")
    if not isinstance(reviewer, str) or not reviewer.startswith(_TEMPLATE_PREFIX):
        issues.append("receipt template reviewer must start with TEMPLATE:")
    return issues


def validate_loop_receipt_template(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]:
    """Validate the inert receipt template without promoting it to final evidence."""

    if not isinstance(receipt, Mapping):
        return ["receipt template must be a mapping"]
    if not isinstance(declaration, Mapping):
        return ["loop declaration must be a mapping before validating its receipt template"]

    issues = _receipt_keys(receipt)
    issues.extend(_validate_template_identity(receipt, declaration))
    issues.extend(_validate_template_state(receipt))
    issues.extend(_validate_template_verification(receipt, declaration))
    return issues
