from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from forgellm_governance.components import load_component_document
from forgellm_governance.cost_model import PlacementCandidate
from forgellm_governance.legality import (
    PlacementInvariantError,
    RejectionCode,
    enumerate_candidates,
)
from forgellm_governance.topology import MemoryDomain, MemoryKind, load_topology

ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = ROOT / "tests" / "fixtures" / "topology" / "valid-synthetic.json"
COMPONENTS = ROOT / "tests" / "fixtures" / "components" / "valid-cache-draft.json"


def _inputs(component_id: str = "confidence-head"):
    topology = load_topology(TOPOLOGY, ROOT)
    component = load_component_document(COMPONENTS, ROOT).component(component_id)
    return topology, component


def _key(candidate: PlacementCandidate) -> tuple[str, str, str, str]:
    return (
        candidate.implementation_id,
        candidate.compute_domain_id,
        candidate.memory_domain_id,
        candidate.component_id,
    )


def test_enumerate_candidates_is_deterministic_and_complete() -> None:
    topology, component = _inputs()
    legal, rejected = enumerate_candidates(topology, component)

    expected_count = len(component.implementations) * len(topology.compute_domains) * len(topology.memory_domains)
    assert len(legal) + len(rejected) == expected_count
    assert legal == tuple(sorted(legal, key=_key))
    assert tuple(item.candidate for item in rejected) == tuple(
        sorted((item.candidate for item in rejected), key=_key)
    )
    assert any(candidate.implementation_id == component.fallback_implementation_id for candidate in legal)


def test_rejection_codes_cover_mismatch_attachment_and_capacity() -> None:
    topology, component = _inputs()
    tiny_llc = replace(topology.memory("llc-0"), capacity_bytes=component.resident_bytes - 1)
    topology = replace(
        topology,
        memory_domains=tuple(tiny_llc if memory.id == tiny_llc.id else memory for memory in topology.memory_domains),
    )
    _, rejected = enumerate_candidates(topology, component)
    all_codes = {code for item in rejected for code in item.codes}
    assert RejectionCode.COMPUTE_KIND_MISMATCH in all_codes
    assert RejectionCode.MEMORY_KIND_MISMATCH in all_codes
    assert RejectionCode.MEMORY_NOT_ATTACHED in all_codes
    assert RejectionCode.MEMORY_CAPACITY_EXCEEDED in all_codes


def test_missing_capability_and_rate_are_explicit() -> None:
    topology, component = _inputs()
    gpu = replace(topology.compute("gpu-0"), capabilities=frozenset(), rate_ops_per_second=(("tensor_ops", 1),))
    topology = replace(
        topology,
        compute_domains=tuple(gpu if compute.id == gpu.id else compute for compute in topology.compute_domains),
    )
    _, rejected = enumerate_candidates(topology, component)
    gpu_rejections = [item for item in rejected if item.candidate.implementation_id == "gpu"]
    assert any(RejectionCode.MISSING_CAPABILITY in item.codes for item in gpu_rejections)
    assert any(RejectionCode.MISSING_RATE in item.codes for item in gpu_rejections)


def test_missing_direct_links_are_explicit_and_reason_order_is_stable() -> None:
    topology, component = _inputs()
    topology = replace(topology, links=tuple(link for link in topology.links if link.id != "pcie-gpu-numa"))
    _, rejected = enumerate_candidates(topology, component)
    candidate = next(
        item
        for item in rejected
        if item.candidate
        == PlacementCandidate(
            component_id="confidence-head",
            implementation_id="cpu-generic",
            compute_domain_id="cpu-cache-group-0",
            memory_domain_id="numa-dram-0",
        )
    )
    assert RejectionCode.INPUT_LINK_MISSING in candidate.codes
    assert RejectionCode.OUTPUT_LINK_MISSING in candidate.codes
    assert candidate.codes == tuple(sorted(candidate.codes, key=lambda item: item.value))
    assert all("0x" not in detail for detail in candidate.details)


def test_fallback_without_any_legal_placement_fails_closed() -> None:
    topology, component = _inputs()
    cpu = replace(topology.compute("cpu-cache-group-0"), capabilities=frozenset())
    topology = replace(
        topology,
        compute_domains=tuple(cpu if compute.id == cpu.id else compute for compute in topology.compute_domains),
    )
    with pytest.raises(PlacementInvariantError, match="generic fallback cpu-generic has no legal placement"):
        enumerate_candidates(topology, component)


def test_unknown_capability_is_not_optimistically_accepted() -> None:
    topology, component = _inputs()
    implementation = replace(
        component.implementation("gpu"),
        id="gpu-future",
        required_capabilities=frozenset({"future_unknown_capability"}),
    )
    component = replace(component, implementations=component.implementations + (implementation,))
    _, rejected = enumerate_candidates(topology, component)
    future = [item for item in rejected if item.candidate.implementation_id == "gpu-future"]
    assert future
    assert all(RejectionCode.MISSING_CAPABILITY in item.codes for item in future)


def test_unattached_matching_memory_is_rejected() -> None:
    topology, component = _inputs()
    extra = MemoryDomain(
        id="llc-unattached",
        kind=MemoryKind.LLC,
        capacity_bytes=component.resident_bytes * 2,
        bandwidth_bytes_per_second=1_000_000_000_000,
        latency_ns=10,
        sharing_compute_ids=("gpu-0",),
        capabilities=frozenset(),
    )
    topology = replace(topology, memory_domains=topology.memory_domains + (extra,))
    _, rejected = enumerate_candidates(topology, component)
    match = next(
        item
        for item in rejected
        if item.candidate.implementation_id == "cpu-llc"
        and item.candidate.compute_domain_id == "cpu-cache-group-0"
        and item.candidate.memory_domain_id == "llc-unattached"
    )
    assert RejectionCode.MEMORY_NOT_ATTACHED in match.codes


def test_zero_byte_transfers_do_not_require_direct_links() -> None:
    topology, component = _inputs()
    component = replace(component, input_bytes=0, output_bytes=0)
    topology = replace(topology, links=tuple())

    legal, rejected = enumerate_candidates(topology, component)
    fallback_candidate = PlacementCandidate(
        component_id=component.id,
        implementation_id="cpu-generic",
        compute_domain_id="cpu-cache-group-0",
        memory_domain_id="numa-dram-0",
    )
    assert fallback_candidate in legal
    matching_rejections = [item for item in rejected if item.candidate == fallback_candidate]
    assert matching_rejections == []
