"""Deterministic synthetic placement simulation and result serialization."""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .components import load_component_document
from .cost_model import CostBreakdown, PlacementCandidate
from .legality import RejectedCandidate
from .planner import ComponentPlan, EvaluatedCandidate, plan_components
from .schema_io import (
    DocumentIssue,
    load_json_mapping,
    resolve_artifact_output,
    resolve_input_file,
    sha256_file,
    validate_instance,
)
from .topology import TopologySnapshot, load_topology

SIMULATOR_VERSION = "0.1.0"
UNSUPPORTED_COST_TERMS = (
    "acceptance_rate_feedback",
    "cache_miss_penalty",
    "energy",
    "interference",
    "multi_hop_routing",
    "overlap",
    "queueing",
)


class SimulationError(ValueError):
    """Raised when a synthetic simulation cannot produce a valid result."""

    def __init__(self, issues: tuple[DocumentIssue, ...]):
        self.issues = tuple(sorted(issues))
        super().__init__("; ".join(issue.render() for issue in self.issues))


def _candidate_document(candidate: PlacementCandidate) -> dict[str, str]:
    return {
        "component_id": candidate.component_id,
        "implementation_id": candidate.implementation_id,
        "compute_domain_id": candidate.compute_domain_id,
        "memory_domain_id": candidate.memory_domain_id,
    }


def _cost_document(cost: CostBreakdown) -> dict[str, int]:
    return {
        "compute_ns": cost.compute_ns,
        "resident_memory_ns": cost.resident_memory_ns,
        "input_transfer_ns": cost.input_transfer_ns,
        "output_transfer_ns": cost.output_transfer_ns,
        "synchronization_ns": cost.synchronization_ns,
        "warmup_amortization_ns": cost.warmup_amortization_ns,
        "total_ns": cost.total_ns,
    }


def _evaluated_document(item: EvaluatedCandidate) -> dict[str, Any]:
    return {
        "candidate": _candidate_document(item.candidate),
        "cost": _cost_document(item.cost),
        "is_generic_fallback": item.is_generic_fallback,
    }


def _rejected_document(item: RejectedCandidate) -> dict[str, Any]:
    return {
        "candidate": _candidate_document(item.candidate),
        "codes": [code.value for code in item.codes],
        "details": list(item.details),
    }


def _plan_document(plan: ComponentPlan) -> dict[str, Any]:
    return {
        "component_id": plan.component_id,
        "selected": _evaluated_document(plan.selected),
        "fallback": _evaluated_document(plan.fallback),
        "legal_candidates": [_evaluated_document(item) for item in plan.legal_candidates],
        "rejected_candidates": [_rejected_document(item) for item in plan.rejected_candidates],
        "selection_reason": plan.selection_reason,
    }


def build_result_document(
    topology_path: Path,
    component_path: Path,
    topology: TopologySnapshot,
    plans: tuple[ComponentPlan, ...],
) -> dict[str, Any]:
    """Build one deterministic synthetic-only placement result document."""

    return {
        "schema_version": "1.0",
        "simulator_version": SIMULATOR_VERSION,
        "evidence_boundary": "synthetic_only",
        "objective": "latency_ns",
        "topology_id": topology.topology_id,
        "profile_id": str(load_json_mapping(component_path)["profile_id"]),
        "inputs": {
            "topology_sha256": sha256_file(topology_path),
            "components_sha256": sha256_file(component_path),
        },
        "unsupported_cost_terms": list(UNSUPPORTED_COST_TERMS),
        "components": [_plan_document(plan) for plan in plans],
    }


def _atomic_write_json(output: Path, document: Mapping[str, Any]) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(document, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output.parent,
            prefix=f".{output.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def run_simulation(
    root: Path,
    topology_path: Path,
    component_path: Path,
    output_path: Path,
) -> Path:
    """Validate, plan, validate the result, then atomically write it under artifacts."""

    root_resolved = root.resolve(strict=True)
    topology_resolved = resolve_input_file(root_resolved, topology_path)
    component_resolved = resolve_input_file(root_resolved, component_path)
    output_resolved = resolve_artifact_output(root_resolved, output_path)
    if output_resolved in {topology_resolved, component_resolved}:
        raise ValueError("output path must differ from input paths")

    initial_hashes = {
        "topology_sha256": sha256_file(topology_resolved),
        "components_sha256": sha256_file(component_resolved),
    }

    topology = load_topology(topology_resolved, root_resolved)
    if topology.source_kind != "synthetic":
        raise SimulationError(
            (DocumentIssue(str(topology_path), "simulator accepts source_kind synthetic only"),)
        )
    profile = load_component_document(component_resolved, root_resolved)
    plans = plan_components(topology, profile.components)
    document = build_result_document(
        topology_resolved,
        component_resolved,
        topology,
        plans,
    )
    if document["inputs"] != initial_hashes or document["profile_id"] != profile.profile_id:
        raise SimulationError(
            (DocumentIssue("inputs", "input changed during simulation"),)
        )

    schema_path = root_resolved / "schemas" / "placement-result.schema.json"
    source_path = Path(output_resolved.relative_to(root_resolved))
    issues = validate_instance(document, schema_path, source_path)
    if issues:
        raise SimulationError(issues)

    _atomic_write_json(output_resolved, document)
    return output_resolved
