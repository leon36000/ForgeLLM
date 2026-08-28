"""Console entry point for ForgeLLM Phase 0 governance tools."""

from __future__ import annotations

import argparse
from pathlib import Path

from .components import ComponentValidationError, load_component_document
from .hardware import write_public_hardware_inventory
from .planner import PlacementPlanningError
from .simulation import SimulationError, run_simulation
from .snapshot import create_session_snapshot
from .topology import TopologyValidationError, load_topology
from .validation import validate_benchmark_file, validate_project, validate_research_catalogs, validate_task_packet_file


def _print_issues(issues: list) -> int:
    if not issues:
        print("OK")
        return 0
    for issue in issues:
        print(issue.render())
    print(f"FAILED: {len(issues)} issue(s)")
    return 1


def _print_exception(exc: Exception) -> int:
    issues = getattr(exc, "issues", None)
    if issues:
        for issue in issues:
            print(f"ERROR: {issue.render()}")
    else:
        print(f"ERROR: {exc}")
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

    topology = sub.add_parser("validate-topology")
    topology.add_argument("path", type=Path)
    topology.add_argument("--root", type=Path, default=Path.cwd())

    components = sub.add_parser("validate-components")
    components.add_argument("path", type=Path)
    components.add_argument("--root", type=Path, default=Path.cwd())

    simulation = sub.add_parser("simulate-placement")
    simulation.add_argument("--root", type=Path, default=Path.cwd())
    simulation.add_argument("--topology", type=Path, required=True)
    simulation.add_argument("--components", type=Path, required=True)
    simulation.add_argument("--output", type=Path, required=True)

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
    if args.command == "validate-topology":
        try:
            path = load_topology(args.path, args.root)
        except (TopologyValidationError, ValueError) as exc:
            return _print_exception(exc)
        print(f"OK: {path.topology_id}")
        return 0
    if args.command == "validate-components":
        try:
            document = load_component_document(args.path, args.root)
        except (ComponentValidationError, ValueError) as exc:
            return _print_exception(exc)
        print(f"OK: {document.profile_id}")
        return 0
    if args.command == "simulate-placement":
        try:
            output = run_simulation(args.root, args.topology, args.components, args.output)
        except (
            ComponentValidationError,
            PlacementPlanningError,
            SimulationError,
            TopologyValidationError,
            ValueError,
        ) as exc:
            return _print_exception(exc)
        print(output)
        return 0
    if args.command == "inventory":
        print(write_public_hardware_inventory(Path.cwd(), args.output))
        return 0
    if args.command == "snapshot":
        print(create_session_snapshot(args.root, args.output))
        return 0
    raise AssertionError("unreachable")


if __name__ == "__main__":
    raise SystemExit(main())
