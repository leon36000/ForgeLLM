from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from forgellm_governance.components import load_component_document
from forgellm_governance.legality import RejectionCode, enumerate_candidates
from forgellm_governance.planner import plan_components
from forgellm_governance.topology import load_topology

ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = ROOT / "examples" / "simulations" / "synthetic-cache-draft-topology.json"
COMPONENTS = ROOT / "examples" / "simulations" / "synthetic-cache-draft-components.json"


def test_canonical_synthetic_cache_draft_example_is_valid_and_explainable() -> None:
    topology = load_topology(TOPOLOGY, ROOT)
    profile = load_component_document(COMPONENTS, ROOT)
    plans = {plan.component_id: plan for plan in plan_components(topology, profile.components)}

    confidence = plans["confidence-head"]
    assert confidence.selected.candidate.implementation_id == "cpu-llc"
    assert confidence.selected.candidate.memory_domain_id == "llc-0"
    assert confidence.fallback.candidate.implementation_id == "cpu-generic"

    markov = plans["markov-head"]
    assert markov.selected.candidate.implementation_id == "gpu"
    assert markov.fallback.candidate.implementation_id == "cpu-generic"

    repeated = {plan.component_id: plan for plan in plan_components(topology, profile.components)}
    assert json.dumps(asdict(confidence), sort_keys=True) == json.dumps(
        asdict(repeated["confidence-head"]), sort_keys=True
    )


def test_reducing_llc_capacity_rejects_residency_candidate(tmp_path: Path) -> None:
    topology_data = json.loads(TOPOLOGY.read_text(encoding="utf-8"))
    llc = next(item for item in topology_data["memory_domains"] if item["id"] == "llc-0")
    llc["capacity_bytes"] = 1024
    topology_path = tmp_path / "small-llc.json"
    topology_path.write_text(json.dumps(topology_data), encoding="utf-8")

    profile_data = json.loads(COMPONENTS.read_text(encoding="utf-8"))
    component_path = tmp_path / "components.json"
    component_path.write_text(json.dumps(profile_data), encoding="utf-8")
    (tmp_path / "schemas").mkdir()
    for name in ("topology.schema.json", "component-profile.schema.json"):
        (tmp_path / "schemas" / name).write_bytes((ROOT / "schemas" / name).read_bytes())

    topology = load_topology(topology_path, tmp_path)
    profile = load_component_document(component_path, tmp_path)
    confidence = profile.component("confidence-head")
    legal, rejected = enumerate_candidates(topology, confidence)

    assert not any(candidate.implementation_id == "cpu-llc" for candidate in legal)
    assert any(RejectionCode.MEMORY_CAPACITY_EXCEEDED in item.codes for item in rejected)


def test_behavior_fields_are_product_neutral() -> None:
    forbidden = ("9950", "xeon", "nvidia", "amd")
    for path in (TOPOLOGY, COMPONENTS):
        data = json.loads(path.read_text(encoding="utf-8"))
        behavior_text = json.dumps(data, sort_keys=True).lower()
        for word in forbidden:
            assert word not in behavior_text
        assert "hostname" not in behavior_text
        assert "uuid" not in behavior_text
