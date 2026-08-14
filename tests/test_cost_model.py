from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path

import pytest

from forgellm_governance.components import load_component_document
from forgellm_governance.cost_model import (
    CostModelError,
    PlacementCandidate,
    ceil_div,
    estimate_cost,
    rate_time_ns,
)
from forgellm_governance.topology import load_topology

ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = ROOT / "tests" / "fixtures" / "topology" / "valid-synthetic.json"
COMPONENTS = ROOT / "tests" / "fixtures" / "components" / "valid-cache-draft.json"


def _inputs():
    topology = load_topology(TOPOLOGY, ROOT)
    component = load_component_document(COMPONENTS, ROOT).component("confidence-head")
    implementation = component.implementation("cpu-llc")
    candidate = PlacementCandidate(
        component_id=component.id,
        implementation_id=implementation.id,
        compute_domain_id="cpu-cache-group-0",
        memory_domain_id="llc-0",
    )
    return topology, component, implementation, candidate


def test_ceil_div_and_rate_time_round_up() -> None:
    assert ceil_div(0, 3) == 0
    assert ceil_div(1, 3) == 1
    assert ceil_div(4, 3) == 2
    assert rate_time_ns(0, 1) == 0
    assert rate_time_ns(1, 3) == 333_333_334
    with pytest.raises(ValueError, match="numerator must be non-negative"):
        ceil_div(-1, 1)
    with pytest.raises(ValueError, match="denominator must be positive"):
        ceil_div(1, 0)


def test_estimate_cost_returns_integer_breakdown() -> None:
    topology, component, implementation, candidate = _inputs()
    cost = estimate_cost(topology, component, implementation, candidate)
    assert cost.compute_ns > 0
    assert cost.resident_memory_ns > 0
    assert cost.input_transfer_ns > 0
    assert cost.output_transfer_ns > 0
    assert cost.synchronization_ns == component.synchronization_ns
    assert cost.warmup_amortization_ns == 1_000
    assert cost.total_ns == sum(
        getattr(cost, field.name) for field in fields(cost) if field.name != "total_ns"
    )
    assert all(isinstance(getattr(cost, field.name), int) for field in fields(cost))
    assert estimate_cost(topology, component, implementation, candidate) == cost


def test_compute_and_transfer_costs_are_monotonic() -> None:
    topology, component, implementation, candidate = _inputs()
    base = estimate_cost(topology, component, implementation, candidate)

    slower_compute = replace(implementation, operations=implementation.operations * 2)
    assert estimate_cost(topology, component, slower_compute, candidate).compute_ns >= base.compute_ns * 2

    original_link = topology.direct_link("gpu-memory-0", "llc-0")
    slower_link = replace(original_link, bandwidth_bytes_per_second=original_link.bandwidth_bytes_per_second // 2)
    slower_topology = replace(
        topology,
        links=tuple(slower_link if link.id == original_link.id else link for link in topology.links),
    )
    slower = estimate_cost(slower_topology, component, implementation, candidate)
    assert slower.input_transfer_ns >= base.input_transfer_ns
    assert slower.output_transfer_ns >= base.output_transfer_ns

    slower_memory = replace(topology.memory("llc-0"), latency_ns=topology.memory("llc-0").latency_ns + 100)
    latency_topology = replace(
        topology,
        memory_domains=tuple(
            slower_memory if memory.id == slower_memory.id else memory for memory in topology.memory_domains
        ),
    )
    assert estimate_cost(latency_topology, component, implementation, candidate).total_ns > base.total_ns


def test_missing_direct_transfer_link_fails_closed() -> None:
    topology, component, implementation, candidate = _inputs()
    topology = replace(topology, links=tuple())
    with pytest.raises(CostModelError, match="missing direct input link"):
        estimate_cost(topology, component, implementation, candidate)


def test_required_residency_larger_than_capacity_fails_closed() -> None:
    topology, component, implementation, candidate = _inputs()
    tiny = replace(topology.memory("llc-0"), capacity_bytes=component.resident_bytes - 1)
    topology = replace(
        topology,
        memory_domains=tuple(tiny if memory.id == tiny.id else memory for memory in topology.memory_domains),
    )
    with pytest.raises(CostModelError, match="resident working set"):
        estimate_cost(topology, component, implementation, candidate)


def test_candidate_identity_mismatch_is_rejected() -> None:
    topology, component, implementation, candidate = _inputs()
    with pytest.raises(CostModelError, match="candidate component mismatch"):
        estimate_cost(topology, component, implementation, replace(candidate, component_id="other"))
    with pytest.raises(CostModelError, match="candidate implementation mismatch"):
        estimate_cost(topology, component, implementation, replace(candidate, implementation_id="other"))


def test_zero_byte_transfers_cost_zero_but_memory_ids_must_resolve() -> None:
    topology, component, implementation, candidate = _inputs()
    component = replace(component, input_bytes=0, output_bytes=0)
    topology_without_links = replace(topology, links=tuple())

    cost = estimate_cost(topology_without_links, component, implementation, candidate)
    assert cost.input_transfer_ns == 0
    assert cost.output_transfer_ns == 0

    missing = replace(component, input_domain_id="missing-memory", output_domain_id="missing-memory")
    with pytest.raises(CostModelError, match="unknown input transfer memory domain"):
        estimate_cost(topology_without_links, missing, implementation, candidate)


def test_zero_resident_memory_access_costs_zero() -> None:
    topology, component, implementation, candidate = _inputs()
    implementation = replace(implementation, bytes_read=0, bytes_written=0)
    cost = estimate_cost(topology, component, implementation, candidate)
    assert cost.resident_memory_ns == 0
