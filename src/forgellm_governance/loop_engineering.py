"""ForgeLLM bounded Loop Engineering public validation surface."""

from __future__ import annotations

from collections.abc import Mapping
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

validate_loop_verify_command = _legacy.validate_loop_verify_command
validate_loop_declaration = _legacy.validate_loop_declaration
validate_vendor_provenance = _legacy.validate_vendor_provenance

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
        issues.append("receipt verification.verifier must identify the execution verifier and cannot be a template marker")

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
