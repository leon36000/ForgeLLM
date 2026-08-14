"""Deterministic integer-only analytical placement cost accounting."""

from __future__ import annotations

from dataclasses import dataclass, fields

from .components import MAX_GOVERNED_INT, ComponentProfile, ImplementationProfile
from .topology import TopologySnapshot

NANOSECONDS_PER_SECOND = 1_000_000_000


class CostModelError(ValueError):
    """Raised when a candidate cannot be costed without an unsupported assumption."""


@dataclass(frozen=True, slots=True)
class PlacementCandidate:
    component_id: str
    implementation_id: str
    compute_domain_id: str
    memory_domain_id: str


@dataclass(frozen=True, slots=True)
class CostBreakdown:
    compute_ns: int
    resident_memory_ns: int
    input_transfer_ns: int
    output_transfer_ns: int
    synchronization_ns: int
    warmup_amortization_ns: int

    def __post_init__(self) -> None:
        for field in fields(self):
            value = getattr(self, field.name)
            if not isinstance(value, int) or isinstance(value, bool):
                raise TypeError(f"{field.name} must be an integer")
            if value < 0:
                raise ValueError(f"{field.name} must be non-negative")
            if value > MAX_GOVERNED_INT:
                raise ValueError(f"{field.name} exceeds governed integer maximum")
        if sum(getattr(self, field.name) for field in fields(self)) > MAX_GOVERNED_INT:
            raise ValueError("total cost exceeds governed integer maximum")

    @property
    def total_ns(self) -> int:
        return sum(getattr(self, field.name) for field in fields(self))


def ceil_div(numerator: int, denominator: int) -> int:
    """Return integer ceiling division with explicit domain checks."""

    if numerator < 0:
        raise ValueError("numerator must be non-negative")
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return (numerator + denominator - 1) // denominator


def rate_time_ns(work: int, units_per_second: int) -> int:
    """Convert integer work/rate into integer nanoseconds, rounding upward."""

    if work < 0:
        raise ValueError("work must be non-negative")
    if units_per_second <= 0:
        raise ValueError("rate must be positive")
    result = ceil_div(work * NANOSECONDS_PER_SECOND, units_per_second)
    if result > MAX_GOVERNED_INT:
        raise ValueError("rate-derived time exceeds governed integer maximum")
    return result


def _transfer_time_ns(
    topology: TopologySnapshot,
    source_memory_id: str,
    target_memory_id: str,
    byte_count: int,
    *,
    direction_name: str,
) -> int:
    try:
        topology.memory(source_memory_id)
        topology.memory(target_memory_id)
    except KeyError as exc:
        raise CostModelError(f"unknown {direction_name} transfer memory domain: {exc.args[0]}") from exc
    if byte_count == 0 or source_memory_id == target_memory_id:
        return 0
    link = topology.direct_link(source_memory_id, target_memory_id)
    if link is None:
        raise CostModelError(
            f"missing direct {direction_name} link: {source_memory_id} -> {target_memory_id}"
        )
    return link.latency_ns + rate_time_ns(byte_count, link.bandwidth_bytes_per_second)


def estimate_cost(
    topology: TopologySnapshot,
    component: ComponentProfile,
    implementation: ImplementationProfile,
    candidate: PlacementCandidate,
) -> CostBreakdown:
    """Estimate one already-legal candidate without floats or hidden routes."""

    if candidate.component_id != component.id:
        raise CostModelError(
            f"candidate component mismatch: {candidate.component_id} != {component.id}"
        )
    if candidate.implementation_id != implementation.id:
        raise CostModelError(
            f"candidate implementation mismatch: {candidate.implementation_id} != {implementation.id}"
        )

    try:
        compute = topology.compute(candidate.compute_domain_id)
        memory = topology.memory(candidate.memory_domain_id)
    except KeyError as exc:
        raise CostModelError(exc.args[0]) from exc

    if implementation.requires_residency and component.resident_bytes > memory.capacity_bytes:
        raise CostModelError(
            "resident working set exceeds selected memory capacity: "
            f"{component.resident_bytes} > {memory.capacity_bytes}"
        )

    try:
        compute_rate = compute.rate(implementation.rate_key)
    except KeyError as exc:
        raise CostModelError(exc.args[0]) from exc

    compute_ns = rate_time_ns(implementation.operations, compute_rate)
    resident_bytes_accessed = implementation.bytes_read + implementation.bytes_written
    resident_memory_ns = (
        0
        if resident_bytes_accessed == 0
        else memory.latency_ns
        + rate_time_ns(
            resident_bytes_accessed,
            memory.bandwidth_bytes_per_second,
        )
    )
    input_transfer_ns = _transfer_time_ns(
        topology,
        component.input_domain_id,
        candidate.memory_domain_id,
        component.input_bytes,
        direction_name="input",
    )
    output_transfer_ns = _transfer_time_ns(
        topology,
        candidate.memory_domain_id,
        component.output_domain_id,
        component.output_bytes,
        direction_name="output",
    )
    warmup_amortization_ns = ceil_div(
        component.warmup_ns,
        component.warmup_amortization_requests,
    )

    try:
        return CostBreakdown(
            compute_ns=compute_ns,
            resident_memory_ns=resident_memory_ns,
            input_transfer_ns=input_transfer_ns,
            output_transfer_ns=output_transfer_ns,
            synchronization_ns=component.synchronization_ns,
            warmup_amortization_ns=warmup_amortization_ns,
        )
    except (TypeError, ValueError) as exc:
        raise CostModelError(str(exc)) from exc
