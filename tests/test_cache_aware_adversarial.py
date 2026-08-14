from __future__ import annotations

import json
import shutil
from dataclasses import asdict
from pathlib import Path

import pytest

from forgellm_governance.components import load_component_document
from forgellm_governance.legality import RejectionCode, enumerate_candidates
from forgellm_governance.planner import PlacementPlanningError, plan_components
from forgellm_governance.simulation import run_simulation
from forgellm_governance.topology import TopologyValidationError, load_topology

ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY_NAME = "synthetic-cache-draft-topology.json"
COMPONENT_NAME = "synthetic-cache-draft-components.json"


def _root(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "repo"
    (root / "schemas").mkdir(parents=True)
    (root / "examples" / "simulations").mkdir(parents=True)
    (root / "artifacts" / "simulations").mkdir(parents=True)
    for name in ("topology.schema.json", "component-profile.schema.json", "placement-result.schema.json"):
        shutil.copy2(ROOT / "schemas" / name, root / "schemas" / name)
    topology = root / "examples" / "simulations" / TOPOLOGY_NAME
    components = root / "examples" / "simulations" / COMPONENT_NAME
    shutil.copy2(ROOT / "examples" / "simulations" / TOPOLOGY_NAME, topology)
    shutil.copy2(ROOT / "examples" / "simulations" / COMPONENT_NAME, components)
    return root, topology, components


def _write(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _plans(root: Path, topology: Path, components: Path) -> str:
    snapshot = load_topology(topology, root)
    profile = load_component_document(components, root)
    return json.dumps([asdict(item) for item in plan_components(snapshot, profile.components)], sort_keys=True)


def test_duplicate_id_across_domain_kinds_fails_closed(tmp_path: Path) -> None:
    root, topology, _ = _root(tmp_path)
    data = json.loads(topology.read_text())
    data["memory_domains"][0]["id"] = data["compute_domains"][0]["id"]
    _write(topology, data)
    with pytest.raises(TopologyValidationError, match="duplicate domain id"):
        load_topology(topology, root)


def test_unresolved_attachment_and_ambiguous_bidirectional_link_fail(tmp_path: Path) -> None:
    root, topology, _ = _root(tmp_path)
    data = json.loads(topology.read_text())
    data["compute_domains"][0]["attached_memory_ids"].append("missing-memory")
    duplicate = dict(data["links"][0])
    duplicate["id"] = "pcie-gpu-llc-duplicate"
    data["links"].append(duplicate)
    _write(topology, data)
    with pytest.raises(TopologyValidationError) as raised:
        load_topology(topology, root)
    message = str(raised.value)
    assert "unresolved attached memory" in message
    assert "ambiguous direct link" in message


@pytest.mark.parametrize("rate", [0, -1, 9_007_199_254_740_992])
def test_invalid_or_unrepresentable_rate_is_schema_rejected(tmp_path: Path, rate: int) -> None:
    root, topology, _ = _root(tmp_path)
    data = json.loads(topology.read_text())
    data["compute_domains"][0]["rate_ops_per_second"]["int8_ops"] = rate
    _write(topology, data)
    with pytest.raises(TopologyValidationError):
        load_topology(topology, root)


def test_missing_or_incapable_fallback_fails_before_selection(tmp_path: Path) -> None:
    root, topology, components = _root(tmp_path)
    data = json.loads(components.read_text())
    confidence = next(item for item in data["components"] if item["id"] == "confidence-head")
    fallback = next(item for item in confidence["implementations"] if item["id"] == "cpu-generic")
    fallback["required_capabilities"].append("unknown-capability")
    _write(components, data)
    snapshot = load_topology(topology, root)
    profile = load_component_document(components, root)
    with pytest.raises(PlacementPlanningError, match="generic fallback"):
        plan_components(snapshot, profile.components)


def test_missing_direct_link_is_a_stable_rejection(tmp_path: Path) -> None:
    root, topology, components = _root(tmp_path)
    topology_data = json.loads(topology.read_text())
    topology_data["links"] = [
        item for item in topology_data["links"] if item["target_id"] != "llc-0"
    ]
    _write(topology, topology_data)
    snapshot = load_topology(topology, root)
    profile = load_component_document(components, root)
    confidence = profile.component("confidence-head")
    _, rejected = enumerate_candidates(snapshot, confidence)
    llc_candidate = next(
        item
        for item in rejected
        if item.candidate.implementation_id == "cpu-llc"
        and item.candidate.memory_domain_id == "llc-0"
        and item.candidate.compute_domain_id == "cpu-cache-group-0"
    )
    assert RejectionCode.INPUT_LINK_MISSING in llc_candidate.codes
    assert RejectionCode.OUTPUT_LINK_MISSING in llc_candidate.codes


def test_descriptions_and_unrelated_telemetry_do_not_change_plan(tmp_path: Path) -> None:
    root, topology, components = _root(tmp_path)
    baseline = _plans(root, topology, components)
    topology_data = json.loads(topology.read_text())
    topology_data["description"] = "Arbitrary product description with no policy meaning."
    topology_data["telemetry_capabilities"].append("unrelated_counter")
    for item in topology_data["compute_domains"] + topology_data["memory_domains"]:
        item["description"] = f"Changed description for {item['id']}"
    _write(topology, topology_data)
    component_data = json.loads(components.read_text())
    component_data["description"] = "Changed prose only."
    _write(components, component_data)
    assert _plans(root, topology, components) == baseline


def test_reordered_arrays_produce_the_same_selected_plan(tmp_path: Path) -> None:
    root, topology, components = _root(tmp_path)
    baseline = _plans(root, topology, components)
    topology_data = json.loads(topology.read_text())
    for key in ("compute_domains", "memory_domains", "links", "telemetry_capabilities"):
        topology_data[key] = list(reversed(topology_data[key]))
    _write(topology, topology_data)
    component_data = json.loads(components.read_text())
    component_data["components"] = list(reversed(component_data["components"]))
    for component in component_data["components"]:
        component["implementations"] = list(reversed(component["implementations"]))
    _write(components, component_data)
    assert _plans(root, topology, components) == baseline


def test_future_schema_version_fails_closed(tmp_path: Path) -> None:
    root, topology, _ = _root(tmp_path)
    data = json.loads(topology.read_text())
    data["schema_version"] = "2.0"
    _write(topology, data)
    with pytest.raises(TopologyValidationError):
        load_topology(topology, root)


def test_malformed_utf8_writes_no_partial_output(tmp_path: Path) -> None:
    root, topology, components = _root(tmp_path)
    topology.write_bytes(b"{\xff}")
    output = root / "artifacts" / "simulations" / "result.json"
    with pytest.raises(ValueError, match="not valid UTF-8"):
        run_simulation(root, topology, components, output)
    assert not output.exists()


def test_output_traversal_and_symlink_escape_fail_closed(tmp_path: Path) -> None:
    root, topology, components = _root(tmp_path)
    with pytest.raises(ValueError, match="beneath artifacts"):
        run_simulation(root, topology, components, root / "escape.json")

    outside = tmp_path / "outside.json"
    link = root / "artifacts" / "simulations" / "link.json"
    link.symlink_to(outside)
    with pytest.raises(ValueError, match="cannot be a symlink"):
        run_simulation(root, topology, components, link)
    assert not outside.exists()
