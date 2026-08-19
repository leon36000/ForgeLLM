#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

from forgellm_governance.loop_engineering import (
    validate_loop_declaration,
    validate_loop_receipt,
    validate_vendor_provenance,
)

TASK_PACKET = Path("tasks/open/P0-T10-bounded-loop-engineering.yaml")
LOOP_DECLARATION = Path("artifacts/governance/loop-engineering/P0-T10-loop.yaml")
RECEIPT_TEMPLATE = Path("artifacts/governance/loop-engineering/receipts/TEMPLATE.yaml")


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


def validate_repository(root: Path) -> list[str]:
    root = root.resolve()
    issues = validate_vendor_provenance(root)

    task_packet, task_issues = _load_mapping(root / TASK_PACKET)
    declaration, declaration_issues = _load_mapping(root / LOOP_DECLARATION)
    receipt, receipt_issues = _load_mapping(root / RECEIPT_TEMPLATE)
    issues.extend(task_issues)
    issues.extend(declaration_issues)
    issues.extend(receipt_issues)

    if task_packet is not None and declaration is not None:
        issues.extend(validate_loop_declaration(declaration, task_packet))
    if declaration is not None and receipt is not None:
        issues.extend(validate_loop_receipt(receipt, declaration))
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
