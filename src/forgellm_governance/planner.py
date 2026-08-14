"""Deterministic explainable placement selection."""

from __future__ import annotations

from dataclasses import dataclass

from .components import ComponentProfile, ImplementationProfile
from .cost_model import CostBreakdown, CostModelError, PlacementCandidate, estimate_cost
from .legality import PlacementInvariantError, RejectedCandidate, enumerate_candidates
from .topology import TopologySnapshot


class PlacementPlanningError(ValueError):
    """Raised when no valid explainable plan can be produced."""


@dataclass(frozen=True, slots=True)
class EvaluatedCandidate:
    candidate: PlacementCandidate
    cost: CostBreakdown
    is_generic_fallback: bool


@dataclass(frozen=True, slots=True)
class ComponentPlan:
    component_id: str
    selected: EvaluatedCandidate
    legal_candidates: tuple[EvaluatedCandidate, ...]
    rejected_candidates: tuple[RejectedCandidate, ...]
    fallback: EvaluatedCandidate
    selection_reason: str


def _rank_key(item: EvaluatedCandidate) -> tuple[int, str, str, str]:
    candidate = item.candidate
    return (
        item.cost.total_ns,
        candidate.implementation_id,
        candidate.compute_domain_id,
        candidate.memory_domain_id,
    )


def _evaluate_candidate(
    topology: TopologySnapshot,
    component: ComponentProfile,
    implementation: ImplementationProfile,
    candidate: PlacementCandidate,
) -> EvaluatedCandidate:
    try:
        cost = estimate_cost(topology, component, implementation, candidate)
    except CostModelError as exc:
        raise PlacementPlanningError(
            f"legal candidate could not be costed: {candidate.implementation_id}/"
            f"{candidate.compute_domain_id}/{candidate.memory_domain_id}: {exc}"
        ) from exc
    return EvaluatedCandidate(
        candidate=candidate,
        cost=cost,
        is_generic_fallback=implementation.is_generic_fallback,
    )


def plan_component(
    topology: TopologySnapshot,
    component: ComponentProfile,
) -> ComponentPlan:
    """Select the deterministic minimum-cost legal candidate for one component."""

    for direction, memory_id in (
        ("input", component.input_domain_id),
        ("output", component.output_domain_id),
    ):
        try:
            topology.memory(memory_id)
        except KeyError as exc:
            raise PlacementPlanningError(
                f"component {component.id} references unknown {direction} memory domain {memory_id}"
            ) from exc

    try:
        legal_candidates, rejected_candidates = enumerate_candidates(topology, component)
    except PlacementInvariantError as exc:
        raise PlacementPlanningError(str(exc)) from exc

    evaluated = tuple(
        sorted(
            (
                _evaluate_candidate(
                    topology,
                    component,
                    component.implementation(candidate.implementation_id),
                    candidate,
                )
                for candidate in legal_candidates
            ),
            key=_rank_key,
        )
    )
    if not evaluated:
        raise PlacementPlanningError(f"component {component.id} has no legal placement")

    fallback_candidates = tuple(
        item
        for item in evaluated
        if item.candidate.implementation_id == component.fallback_implementation_id
        and item.is_generic_fallback
    )
    if not fallback_candidates:
        raise PlacementPlanningError(
            f"generic fallback {component.fallback_implementation_id} has no evaluated placement "
            f"for component {component.id}"
        )

    selected = evaluated[0]
    fallback = min(fallback_candidates, key=_rank_key)
    minimum_ties = tuple(item for item in evaluated if item.cost.total_ns == selected.cost.total_ns)
    if len(minimum_ties) > 1:
        selection_reason = (
            f"selected deterministic tie at total_ns={selected.cost.total_ns} "
            "using implementation/compute/memory ordering"
        )
    else:
        selection_reason = (
            f"selected minimum total_ns={selected.cost.total_ns}; "
            f"fallback total_ns={fallback.cost.total_ns}; "
            f"estimated delta_ns={fallback.cost.total_ns - selected.cost.total_ns}"
        )

    return ComponentPlan(
        component_id=component.id,
        selected=selected,
        legal_candidates=evaluated,
        rejected_candidates=rejected_candidates,
        fallback=fallback,
        selection_reason=selection_reason,
    )


def plan_components(
    topology: TopologySnapshot,
    components: tuple[ComponentProfile, ...],
) -> tuple[ComponentPlan, ...]:
    """Plan components in stable component-ID order."""

    return tuple(plan_component(topology, component) for component in sorted(components, key=lambda item: item.id))
