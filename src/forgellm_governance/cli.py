"""Console entry point for ForgeLLM Phase 0 governance tools."""

from __future__ import annotations

import argparse
from pathlib import Path

from .hardware import write_hardware_inventory
from .snapshot import create_session_snapshot
from .validation import validate_benchmark_file, validate_project, validate_research_catalogs, validate_task_packet_file


def _print_issues(issues: list) -> int:
    if not issues:
        print("OK")
        return 0
    for issue in issues:
        print(issue.render())
    print(f"FAILED: {len(issues)} issue(s)")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(prog="forgellm-governance")
    sub = parser.add_subparsers(dest="command", required=True)

    project = sub.add_parser("validate-project")
    project.add_argument("--root", type=Path, default=Path.cwd())

    research = sub.add_parser("validate-research")
    research.add_argument("--root", type=Path, default=Path.cwd())

    benchmark = sub.add_parser("validate-benchmark")
    benchmark.add_argument("path", type=Path)
    benchmark.add_argument("--root", type=Path, default=Path.cwd())

    task = sub.add_parser("validate-task")
    task.add_argument("path", type=Path)
    task.add_argument("--root", type=Path, default=Path.cwd())

    inventory = sub.add_parser("inventory")
    inventory.add_argument("--output", type=Path, default=Path("artifacts/hardware-local.json"))

    snapshot = sub.add_parser("snapshot")
    snapshot.add_argument("--root", type=Path, default=Path.cwd())
    snapshot.add_argument("--output", type=Path, default=Path("artifacts/session-snapshot.md"))

    args = parser.parse_args()
    if args.command == "validate-project":
        return _print_issues(validate_project(args.root))
    if args.command == "validate-research":
        return _print_issues(validate_research_catalogs(args.root))
    if args.command == "validate-benchmark":
        return _print_issues(validate_benchmark_file(args.path, root=args.root))
    if args.command == "validate-task":
        return _print_issues(validate_task_packet_file(args.path, root=args.root))
    if args.command == "inventory":
        print(write_hardware_inventory(args.output))
        return 0
    if args.command == "snapshot":
        print(create_session_snapshot(args.root, args.output))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
