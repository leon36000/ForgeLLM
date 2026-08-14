"""Deterministic legality filtering for component placement candidates."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .components import ComponentProfile, ImplementationProfile
from .cost_model import PlacementCandidate
from .topology import ComputeDomain, MemoryDomain, TopologySnapshot


class RejectionCode(StrEnum):
    COMPUTE_KIND_MISMATCH = "compute_kind_mismatch"
    FALLBACK_NOT_LEGAL = "fallback_not_legal"
    INPUT_LINK_MISSING = "input_link_missing"
    MEMORY_CAPACITY_EXCEEDED = "memory_capacity_exceeded"
    MEMORY_KIND_MISMATCH = "memory_kind_mismatch"
    MEMORY_NOT_ATTACHED = "memory_not_attached"
    MISSING_CAPABILITY = "missing_capability"
    MISSING_RATE = "missing_rate"
    OUTPUT_LINK_MISSING = "output_link_missing"


class PlacementInvariantError(ValueError):
    """Raised when the component cannot retain a legal generic fallback."""


@dataclass(frozen=True, slots=True)
class RejectedCandidate:
    candidate: PlacementCandidate
    codes: tuple[RejectionCode, ...]
    details: tuple[str, ...]


def _candidate_key(candidate: PlacementCandidate) -> tuple[str, str, str, str]:
    return (
        candidate.implementation_id,
        candidate.compute_domain_id,
        candidate.memory_domain_id,
        candidate.component_id,
    )


def _rate_keys(compute: ComputeDomain) -> frozenset[str]:
    return frozenset(name for name, _ in compute.rate_ops_per_second)


def _rejection_details(
    topology: TopologySnapshot,
    component: ComponentProfile,
    implementation: ImplementationProfile,
    compute: ComputeDomain,
    memory: MemoryDomain,
) -> dict[RejectionCode, str]:
    reasons: dict[RejectionCode, str] = {}

    if compute.kind is not implementation.compute_kind:
        reasons[RejectionCode.COMPUTE_KIND_MISMATCH] = (
            f"implementation requires compute kind {implementation.compute_kind.value}; "
            f"domain {compute.id} is {compute.kind.value}"
        )

    missing_capabilities = sorted(implementation.required_capabilities - compute.capabilities)
    if missing_capabilities:
        reasons[RejectionCode.MISSING_CAPABILITY] = (
            f"domain {compute.id} lacks required capabilities: {','.join(missing_capabilities)}"
        )

    if implementation.rate_key not in _rate_keys(compute):
        reasons[RejectionCode.MISSING_RATE] = (
            f"domain {compute.id} has no rate for {implementation.rate_key}"
        )

    if memory.kind not in implementation.allowed_memory_kinds:
        allowed = ",".join(sorted(kind.value for kind in implementation.allowed_memory_kinds))
        reasons[RejectionCode.MEMORY_KIND_MISMATCH] = (
            f"implementation allows memory kinds {allowed}; domain {memory.id} is {memory.kind.value}"
        )

    if (
        memory.id not in compute.attached_memory_ids
        or compute.id not in memory.sharing_compute_ids
    ):
        reasons[RejectionCode.MEMORY_NOT_ATTACHED] = (
            f"memory domain {memory.id} is not attached symmetrically to compute domain {compute.id}"
        )

    if implementation.requires_residency and component.resident_bytes > memory.capacity_bytes:
        reasons[RejectionCode.MEMORY_CAPACITY_EXCEEDED] = (
            f"resident working set {component.resident_bytes} exceeds {memory.id} capacity {memory.capacity_bytes}"
        )

    if (
        component.input_bytes > 0
        and component.input_domain_id != memory.id
        and topology.direct_link(component.input_domain_id, memory.id) is None
    ):
        reasons[RejectionCode.INPUT_LINK_MISSING] = (
            f"no direct input link {component.input_domain_id} -> {memory.id}"
        )

    if (
        component.output_bytes > 0
        and component.output_domain_id != memory.id
        and topology.direct_link(memory.id, component.output_domain_id) is None
    ):
        reasons[RejectionCode.OUTPUT_LINK_MISSING] = (
            f"no direct output link {memory.id} -> {component.output_domain_id}"
        )

    return reasons


def enumerate_candidates(
    topology: TopologySnapshot,
    component: ComponentProfile,
) -> tuple[tuple[PlacementCandidate, ...], tuple[RejectedCandidate, ...]]:
    """Enumerate every implementation × compute × memory candidate deterministically."""

    try:
        fallback = component.fallback()
    except KeyError as exc:
        raise PlacementInvariantError(
            f"generic fallback {component.fallback_implementation_id} does not resolve for component {component.id}"
        ) from exc
    if not fallback.is_generic_fallback:
        raise PlacementInvariantError(
            f"generic fallback {component.fallback_implementation_id} is not marked generic "
            f"for component {component.id}"
        )

    legal: list[PlacementCandidate] = []
    rejected: list[RejectedCandidate] = []

    for implementation in sorted(component.implementations, key=lambda item: item.id):
        for compute in sorted(topology.compute_domains, key=lambda item: item.id):
            for memory in sorted(topology.memory_domains, key=lambda item: item.id):
                candidate = PlacementCandidate(
                    component_id=component.id,
                    implementation_id=implementation.id,
                    compute_domain_id=compute.id,
                    memory_domain_id=memory.id,
                )
                reasons = _rejection_details(
                    topology,
                    component,
                    implementation,
                    compute,
                    memory,
                )
                if not reasons:
                    legal.append(candidate)
                    continue
                ordered = tuple(sorted(reasons, key=lambda code: code.value))
                rejected.append(
                    RejectedCandidate(
                        candidate=candidate,
                        codes=ordered,
                        details=tuple(reasons[code] for code in ordered),
                    )
                )

    legal_tuple = tuple(sorted(legal, key=_candidate_key))
    rejected_tuple = tuple(sorted(rejected, key=lambda item: _candidate_key(item.candidate)))

    if not any(
        candidate.implementation_id == component.fallback_implementation_id
        for candidate in legal_tuple
    ):
        raise PlacementInvariantError(
            f"generic fallback {component.fallback_implementation_id} has no legal placement "
            f"for component {component.id}"
        )

    return legal_tuple, rejected_tuple
