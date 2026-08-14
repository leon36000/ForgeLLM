from __future__ import annotations

import json
from dataclasses import asdict, replace
from pathlib import Path

import pytest

from forgellm_governance.components import load_component_document
from forgellm_governance.planner import PlacementPlanningError, plan_component, plan_components
from forgellm_governance.topology import load_topology

ROOT = Path(__file__).resolve().parents[1]
TOPOLOGY = ROOT / "tests" / "fixtures" / "topology" / "valid-synthetic.json"
COMPONENTS = ROOT / "tests" / "fixtures" / "components" / "valid-cache-draft.json"


def _inputs():
    topology = load_topology(TOPOLOGY, ROOT)
    document = load_component_document(COMPONENTS, ROOT)
    return topology, document


def _serialized(value: object) -> bytes:
    return (json.dumps(asdict(value), sort_keys=True, separators=(",", ":")) + "\n").encode()


def test_minimum_total_cost_wins_and_fallback_is_retained() -> None:
    topology, document = _inputs()
    plan = plan_component(topology, document.component("confidence-head"))
    totals = [candidate.cost.total_ns for candidate in plan.legal_candidates]
    assert plan.selected.cost.total_ns == min(totals)
    assert plan.selected in plan.legal_candidates
    assert plan.fallback in plan.legal_candidates
    assert plan.fallback.is_generic_fallback is True
    assert plan.fallback.candidate.implementation_id == "cpu-generic"
    assert "fallback total_ns=" in plan.selection_reason


def test_legal_candidates_are_ranked_deterministically() -> None:
    topology, document = _inputs()
    plan = plan_component(topology, document.component("markov-head"))
    keys = [
        (
            item.cost.total_ns,
            item.candidate.implementation_id,
            item.candidate.compute_domain_id,
            item.candidate.memory_domain_id,
        )
        for item in plan.legal_candidates
    ]
    assert keys == sorted(keys)


def test_equal_cost_uses_stable_tie_break_and_explains_it() -> None:
    topology, document = _inputs()
    base_component = document.component("confidence-head")
    gpu = base_component.implementation("gpu")
    specialized = replace(gpu, id="a-specialized", is_generic_fallback=False)
    fallback = replace(gpu, id="z-fallback", is_generic_fallback=True)
    component = replace(
        base_component,
        fallback_implementation_id="z-fallback",
        implementations=(fallback, specialized),
    )
    plan = plan_component(topology, component)
    assert plan.selected.candidate.implementation_id == "a-specialized"
    assert plan.fallback.candidate.implementation_id == "z-fallback"
    assert plan.selected.cost.total_ns == plan.fallback.cost.total_ns
    assert "selected deterministic tie" in plan.selection_reason


def test_reordered_inputs_produce_byte_identical_plan() -> None:
    topology, document = _inputs()
    component = document.component("confidence-head")
    first = plan_component(topology, component)
    reordered_topology = replace(
        topology,
        compute_domains=tuple(reversed(topology.compute_domains)),
        memory_domains=tuple(reversed(topology.memory_domains)),
        links=tuple(reversed(topology.links)),
    )
    reordered_component = replace(component, implementations=tuple(reversed(component.implementations)))
    second = plan_component(reordered_topology, reordered_component)
    assert _serialized(first) == _serialized(second)


def test_repeated_planning_and_multi_component_order_are_deterministic() -> None:
    topology, document = _inputs()
    first = plan_components(topology, document.components)
    second = plan_components(topology, tuple(reversed(document.components)))
    assert tuple(plan.component_id for plan in first) == ("confidence-head", "markov-head")
    assert json.dumps([asdict(item) for item in first], sort_keys=True) == json.dumps(
        [asdict(item) for item in second], sort_keys=True
    )


def test_description_changes_cannot_change_selection() -> None:
    topology, document = _inputs()
    # Descriptions are intentionally excluded from executable dataclasses.
    plan = plan_component(topology, document.component("confidence-head"))
    reloaded = load_component_document(COMPONENTS, ROOT).component("confidence-head")
    assert plan.selected == plan_component(topology, reloaded).selected


def test_missing_or_non_generic_fallback_fails_closed() -> None:
    topology, document = _inputs()
    component = document.component("confidence-head")
    invalid = replace(component, fallback_implementation_id="missing")
    with pytest.raises(PlacementPlanningError, match="generic fallback missing does not resolve"):
        plan_component(topology, invalid)


def test_component_memory_references_must_resolve_even_for_zero_byte_transfers() -> None:
    topology, document = _inputs()
    component = replace(
        document.component("confidence-head"),
        input_domain_id="missing-input",
        output_domain_id="missing-output",
        input_bytes=0,
        output_bytes=0,
    )
    with pytest.raises(PlacementPlanningError, match="unknown input memory domain missing-input"):
        plan_component(topology, component)
