from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from forgellm_governance.topology import (
    ComputeKind,
    MemoryKind,
    TopologyValidationError,
    load_topology,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "topology"


def test_load_topology_constructs_immutable_product_neutral_model() -> None:
    topology = load_topology(FIXTURES / "valid-synthetic.json", ROOT)

    assert topology.topology_id == "synthetic-cache-draft-v1"
    assert topology.source_kind == "synthetic"
    assert topology.compute("cpu-cache-group-0").kind is ComputeKind.CPU_GROUP
    assert topology.memory("llc-0").kind is MemoryKind.LLC
    assert topology.compute("cpu-cache-group-0").rate("int8_ops") == 2_000_000_000_000
    assert topology.resource_ids() == frozenset(
        {
            "cpu-cache-group-0",
            "gpu-0",
            "llc-0",
            "numa-dram-0",
            "pinned-host-0",
            "gpu-memory-0",
        }
    )
    assert topology.direct_link("gpu-memory-0", "llc-0").id == "pcie-gpu-llc"
    assert topology.direct_link("llc-0", "gpu-memory-0").id == "pcie-gpu-llc"
    assert topology.direct_link("llc-0", "pinned-host-0") is None

    with pytest.raises(FrozenInstanceError):
        topology.topology_id = "changed"  # type: ignore[misc]


def test_lookup_failures_have_stable_messages() -> None:
    topology = load_topology(FIXTURES / "valid-synthetic.json", ROOT)
    with pytest.raises(KeyError, match="unknown compute domain: missing"):
        topology.compute("missing")
    with pytest.raises(KeyError, match="unknown memory domain: missing"):
        topology.memory("missing")


def test_duplicate_ids_across_domain_kinds_are_rejected() -> None:
    with pytest.raises(TopologyValidationError) as caught:
        load_topology(FIXTURES / "duplicate-id.json", ROOT)
    assert any("duplicate domain id" in issue.message for issue in caught.value.issues)


def test_unresolved_link_endpoint_is_rejected() -> None:
    with pytest.raises(TopologyValidationError) as caught:
        load_topology(FIXTURES / "unresolved-link.json", ROOT)
    assert any("unresolved link target" in issue.message for issue in caught.value.issues)


def test_compute_memory_relationship_must_be_symmetric() -> None:
    with pytest.raises(TopologyValidationError) as caught:
        load_topology(FIXTURES / "contradictory-sharing.json", ROOT)
    assert any("relationship is not symmetric" in issue.message for issue in caught.value.issues)


def test_direct_link_ambiguity_is_rejected(tmp_path: Path) -> None:
    source = (FIXTURES / "valid-synthetic.json").read_text(encoding="utf-8")

    data = json.loads(source)
    duplicate = dict(data["links"][0])
    duplicate["id"] = "another-pcie-link"
    data["links"].append(duplicate)
    (tmp_path / "schemas").mkdir()
    (tmp_path / "schemas" / "topology.schema.json").write_text(
        (ROOT / "schemas" / "topology.schema.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    path = tmp_path / "ambiguous.json"
    path.write_text(json.dumps(data), encoding="utf-8")

    with pytest.raises(TopologyValidationError) as caught:
        load_topology(path, tmp_path)
    assert any("ambiguous direct link" in issue.message for issue in caught.value.issues)


def test_tuple_order_follows_source_order() -> None:
    topology = load_topology(FIXTURES / "valid-synthetic.json", ROOT)
    assert tuple(item.id for item in topology.compute_domains) == ("cpu-cache-group-0", "gpu-0")
    assert tuple(item.id for item in topology.links) == (
        "pcie-gpu-llc",
        "pcie-gpu-numa",
        "pcie-gpu-pinned",
    )
