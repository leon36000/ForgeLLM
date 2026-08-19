#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from forgellm_governance.loop_engineering import (
    validate_loop_declaration,
    validate_loop_receipt_template,
    validate_vendor_provenance,
)

TASK_PACKET = Path("tasks/open/P0-T10-bounded-loop-engineering.yaml")
LOOP_DECLARATION = Path("artifacts/governance/loop-engineering/P0-T10-loop.yaml")
RECEIPT_TEMPLATE = Path("artifacts/governance/loop-engineering/receipts/TEMPLATE.yaml")
VERIFY_FIREWALL_CASES = Path("artifacts/governance/loop-engineering/verify-firewall-cases.yaml")


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
