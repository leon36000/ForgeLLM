#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path, PurePosixPath
from typing import Any

import yaml

from forgellm_governance.loop_engineering import (
    validate_loop_declaration,
    validate_loop_receipt,
    validate_loop_receipt_template,
    validate_vendor_provenance,
)

TASK_PACKET = Path("tasks/open/P0-T10-bounded-loop-engineering.yaml")
LOOP_DECLARATION = Path("artifacts/governance/loop-engineering/P0-T10-loop.yaml")
RECEIPT_TEMPLATE = Path("artifacts/governance/loop-engineering/receipts/TEMPLATE.yaml")
RECEIPT_INDEX = Path("artifacts/governance/loop-engineering/receipt-index.yaml")
VERIFY_FIREWALL_CASES = Path("artifacts/governance/loop-engineering/verify-firewall-cases.yaml")
DECLARATION_PREFIX = "artifacts/governance/loop-engineering/declarations/"
RECEIPT_PREFIX = "artifacts/governance/loop-engineering/receipts/"
_FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
_INDEX_RECORD_FIELDS = {
    "run_id",
    "declaration_path",
    "declaration_source_commit",
    "declaration_source_blob_sha",
    "receipt_path",
    "receipt_schema_version",
}


def _load_mapping(path: Path) -> tuple[dict[str, Any] | None, list[str]]:
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [f"required Loop Engineering artifact is missing: {path}"]
    except (UnicodeDecodeError, yaml.YAMLError) as exc:
        return None, [f"invalid Loop Engineering YAML at {path}: {exc}"]
    if not isinstance(loaded, dict):
        return None, [f"Loop Engineering artifact root must be a mapping: {path}"]
    return loaded, []


def _firewall_declaration(command: str) -> tuple[dict[str, Any], dict[str, Any]]:
    packet = {
        "task_id": "P0-FIREWALL",
        "allowed_paths": ["tests/test_loop_engineering.py"],
        "verification_commands": [command],
    }
    declaration = {
        "schema_version": "1.0",
        "project": "ForgeLLM",
        "task_id": "P0-FIREWALL",
        "base_commit": "1111111111111111111111111111111111111111",
        "GOAL": "Exercise the verifier privilege firewall oracle.",
        "SCOPE": ["tests/test_loop_engineering.py"],
        "VERIFY": [command],
        "BUDGET": {
            "max_iterations": 1,
            "max_identical_failures": 1,
            "max_wall_minutes": 1,
        },
        "STOP": {
            "on_verify_pass": True,
            "on_budget_exhausted": True,
            "on_identical_failure_limit": True,
            "privileged_operation": "stop_and_escalate",
        },
        "RECEIPT": "artifacts/governance/loop-engineering/receipts/P0-FIREWALL.yaml",
    }
    return declaration, packet


def _validate_firewall_cases(cases: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if cases.get("schema_version") != "1.0":
        issues.append("verifier firewall cases schema_version must be exactly '1.0'")
    allowed = cases.get("allowed")
    rejected = cases.get("rejected")
    if not isinstance(allowed, list) or not all(isinstance(item, str) and item for item in allowed):
        issues.append("verifier firewall allowed cases must be a non-empty string array")
        allowed = []
    if not isinstance(rejected, list) or not all(isinstance(item, str) and item for item in rejected):
        issues.append("verifier firewall rejected cases must be a non-empty string array")
        rejected = []

    for command in allowed:
        declaration, packet = _firewall_declaration(command)
        command_issues = validate_loop_declaration(declaration, packet)
        if command_issues:
            issues.append(f"verifier firewall allowed case rejected: {command!r}: {command_issues}")
    for command in rejected:
        declaration, packet = _firewall_declaration(command)
        command_issues = validate_loop_declaration(declaration, packet)
        if not command_issues:
            issues.append(f"verifier firewall rejected case unexpectedly accepted: {command!r}")
    return issues


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    payload = f"blob {len(data)}\0".encode() + data
    return hashlib.sha1(payload, usedforsecurity=False).hexdigest()


def _catalog_path(value: Any, prefix: str) -> str | None:
    if not isinstance(value, str) or not value.startswith(prefix):
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        return None
    return value


def _validate_index_header(index: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    if index.get("schema_version") != "1.0":
        issues.append("receipt index schema_version must be exactly '1.0'")
    if index.get("project") != "ForgeLLM":
        issues.append("receipt index project must be exactly ForgeLLM")
    if index.get("task_id") != "P0-T10":
        issues.append("receipt index task_id must be exactly P0-T10")
    return issues


def _validate_catalog_record(
    root: Path,
    task_packet: dict[str, Any],
    record: dict[str, Any],
) -> tuple[list[str], str | None, str | None, str | None]:
    issues: list[str] = []
    if set(record) != _INDEX_RECORD_FIELDS:
        issues.append(
            "receipt index run record requires exact fields; "
            f"missing={sorted(_INDEX_RECORD_FIELDS - set(record))}, "
            f"extra={sorted(set(record) - _INDEX_RECORD_FIELDS)}"
        )
        return issues, None, None, None

    run_id = record.get("run_id")
    declaration_path = _catalog_path(record.get("declaration_path"), DECLARATION_PREFIX)
    receipt_path = _catalog_path(record.get("receipt_path"), RECEIPT_PREFIX)
    if not isinstance(run_id, str) or not run_id:
        issues.append("receipt index run_id must be a non-empty string")
    if declaration_path is None or not declaration_path.endswith((".yaml", ".yml")):
        issues.append("receipt index declaration_path must be safe YAML under declarations/")
    if receipt_path is None or not receipt_path.endswith((".yaml", ".yml")):
        issues.append("receipt index receipt_path must be safe YAML under receipts/")
    source_commit = record.get("declaration_source_commit")
    source_blob = record.get("declaration_source_blob_sha")
    if not isinstance(source_commit, str) or _FULL_SHA.fullmatch(source_commit) is None:
        issues.append("receipt index declaration_source_commit must be a full lowercase Git SHA")
    if not isinstance(source_blob, str) or _FULL_SHA.fullmatch(source_blob) is None:
        issues.append("receipt index declaration_source_blob_sha must be a full lowercase Git blob SHA")
    if issues or declaration_path is None or receipt_path is None:
        return issues, run_id if isinstance(run_id, str) else None, declaration_path, receipt_path

    declaration, declaration_issues = _load_mapping(root / declaration_path)
    receipt, receipt_issues = _load_mapping(root / receipt_path)
    issues.extend(declaration_issues)
    issues.extend(receipt_issues)
    if declaration is None or receipt is None:
        return issues, run_id, declaration_path, receipt_path

    if _git_blob_sha(root / declaration_path) != source_blob:
        issues.append(f"{declaration_path} does not match declaration_source_blob_sha {source_blob}")
    issues.extend(validate_loop_declaration(declaration, task_packet))
    expected_schema = record.get("receipt_schema_version")
    if receipt.get("schema_version") != expected_schema:
        issues.append(f"{receipt_path} schema_version must equal indexed value {expected_schema!r}")
    if expected_schema == "1.0":
        issues.extend(validate_loop_receipt(receipt, declaration))
    else:
        issues.append(f"{receipt_path} schema_version {expected_schema!r} is unsupported by repository validation")
    return issues, run_id, declaration_path, receipt_path


def _validate_receipt_catalog(root: Path, task_packet: dict[str, Any]) -> list[str]:
    index, index_issues = _load_mapping(root / RECEIPT_INDEX)
    if index is None:
        return index_issues
    issues = [*index_issues, *_validate_index_header(index)]
    records = index.get("runs")
    if not isinstance(records, list) or not records:
        issues.append("receipt index runs must be a non-empty array")
        return issues

    run_ids: list[str] = []
    declaration_paths: list[str] = []
    receipt_paths: list[str] = []
    for record in records:
        if not isinstance(record, dict):
            issues.append("each receipt index run must be a mapping")
            continue
        record_issues, run_id, declaration_path, receipt_path = _validate_catalog_record(root, task_packet, record)
        issues.extend(record_issues)
        if run_id is not None:
            run_ids.append(run_id)
        if declaration_path is not None:
            declaration_paths.append(declaration_path)
        if receipt_path is not None:
            receipt_paths.append(receipt_path)

    if len(run_ids) != len(set(run_ids)):
        issues.append("receipt index run_id values must be unique")
    if len(declaration_paths) != len(set(declaration_paths)):
        issues.append("receipt index declaration_path values must be unique")
    if len(receipt_paths) != len(set(receipt_paths)):
        issues.append("receipt index receipt_path values must be unique")

    actual_receipts = {
        path.relative_to(root).as_posix()
        for path in (root / RECEIPT_PREFIX).glob("*.yaml")
        if path.name != RECEIPT_TEMPLATE.name
    }
    actual_declarations = {
        path.relative_to(root).as_posix() for path in (root / DECLARATION_PREFIX).glob("*.yaml")
    }
    if set(receipt_paths) != actual_receipts:
        issues.append(
            "receipt index must cover every committed final receipt exactly; "
            f"indexed={sorted(set(receipt_paths))}, actual={sorted(actual_receipts)}"
        )
    if set(declaration_paths) != actual_declarations:
        issues.append(
            "receipt index must cover every immutable declaration snapshot exactly; "
            f"indexed={sorted(set(declaration_paths))}, actual={sorted(actual_declarations)}"
        )
    return issues


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    issues = validate_vendor_provenance(root)

    task_packet, task_issues = _load_mapping(root / TASK_PACKET)
    declaration, declaration_issues = _load_mapping(root / LOOP_DECLARATION)
    receipt, receipt_issues = _load_mapping(root / RECEIPT_TEMPLATE)
    firewall_cases, firewall_issues = _load_mapping(root / VERIFY_FIREWALL_CASES)
    issues.extend(task_issues)
    issues.extend(declaration_issues)
    issues.extend(receipt_issues)
    issues.extend(firewall_issues)

    if task_packet is not None and declaration is not None:
        issues.extend(validate_loop_declaration(declaration, task_packet))
    if declaration is not None and receipt is not None:
        issues.extend(validate_loop_receipt_template(receipt, declaration))
    if firewall_cases is not None:
        issues.extend(_validate_firewall_cases(firewall_cases))
    if task_packet is not None:
        issues.extend(_validate_receipt_catalog(root, task_packet))
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the bounded ForgeLLM Loop Engineering contract.")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()

    issues = validate_repository(args.root)
    for issue in issues:
        print(f"ERROR: {issue}")
    if issues:
        print(f"FAILED: bounded Loop Engineering contract has {len(issues)} issue(s)")
        return 1
    print("OK: bounded Loop Engineering contract is valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
