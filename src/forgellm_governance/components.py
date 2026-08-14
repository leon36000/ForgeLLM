"""Immutable component and implementation profiles for placement simulation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .schema_io import DocumentIssue, load_json_mapping, resolve_input_file, validate_instance
from .topology import ComputeKind, MemoryKind

MAX_GOVERNED_INT = 9_007_199_254_740_991


class ComponentValidationError(ValueError):
    """Raised when a component profile fails schema or semantic validation."""

    def __init__(self, issues: tuple[DocumentIssue, ...]):
        self.issues = tuple(sorted(issues))
        super().__init__("; ".join(issue.render() for issue in self.issues))


@dataclass(frozen=True, slots=True)
class ImplementationProfile:
    id: str
    compute_kind: ComputeKind
    rate_key: str
    operations: int
    bytes_read: int
    bytes_written: int
    required_capabilities: frozenset[str]
    allowed_memory_kinds: frozenset[MemoryKind]
    requires_residency: bool
    is_generic_fallback: bool


@dataclass(frozen=True, slots=True)
class ComponentProfile:
    id: str
    phase: str
    exactness_mode: str
    immutable_bytes: int
    mutable_bytes_per_request: int
    workspace_bytes: int
    input_domain_id: str
    output_domain_id: str
    input_bytes: int
    output_bytes: int
    synchronization_ns: int
    warmup_ns: int
    warmup_amortization_requests: int
    fallback_implementation_id: str
    implementations: tuple[ImplementationProfile, ...]

    @property
    def resident_bytes(self) -> int:
        return self.immutable_bytes + self.mutable_bytes_per_request + self.workspace_bytes

    def implementation(self, implementation_id: str) -> ImplementationProfile:
        for implementation in self.implementations:
            if implementation.id == implementation_id:
                return implementation
        raise KeyError(f"unknown implementation for {self.id}: {implementation_id}")

    def fallback(self) -> ImplementationProfile:
        return self.implementation(self.fallback_implementation_id)


@dataclass(frozen=True, slots=True)
class ComponentProfileDocument:
    profile_id: str
    components: tuple[ComponentProfile, ...]

    def component(self, component_id: str) -> ComponentProfile:
        for component in self.components:
            if component.id == component_id:
                return component
        raise KeyError(f"unknown component: {component_id}")


def _issue(source_path: Path, pointer: str, message: str) -> DocumentIssue:
    return DocumentIssue(f"{source_path}{pointer}", message)


def validate_component_semantics(
    data: Mapping[str, Any],
    source_path: Path,
) -> tuple[DocumentIssue, ...]:
    """Validate uniqueness, fallback, and governed-size invariants."""

    issues: list[DocumentIssue] = []
    seen_components: dict[str, int] = {}

    for component_index, component in enumerate(data["components"]):
        component_id = str(component["id"])
        previous = seen_components.get(component_id)
        if previous is not None:
            issues.append(
                _issue(
                    source_path,
                    f"/components/{component_index}/id",
                    f"duplicate component id {component_id}; first declared at /components/{previous}/id",
                )
            )
        else:
            seen_components[component_id] = component_index

        seen_implementations: dict[str, int] = {}
        generic_ids: list[str] = []
        for implementation_index, implementation in enumerate(component["implementations"]):
            implementation_id = str(implementation["id"])
            previous_impl = seen_implementations.get(implementation_id)
            if previous_impl is not None:
                issues.append(
                    _issue(
                        source_path,
                        f"/components/{component_index}/implementations/{implementation_index}/id",
                        (
                            f"duplicate implementation id {implementation_id}; first declared at "
                            f"/components/{component_index}/implementations/{previous_impl}/id"
                        ),
                    )
                )
            else:
                seen_implementations[implementation_id] = implementation_index
            if bool(implementation["is_generic_fallback"]):
                generic_ids.append(implementation_id)

        if len(generic_ids) != 1:
            issues.append(
                _issue(
                    source_path,
                    f"/components/{component_index}/implementations",
                    f"component {component_id} must declare exactly one generic fallback; found {len(generic_ids)}",
                )
            )

        fallback_id = str(component["fallback_implementation_id"])
        if fallback_id not in seen_implementations:
            issues.append(
                _issue(
                    source_path,
                    f"/components/{component_index}/fallback_implementation_id",
                    f"fallback_implementation_id {fallback_id} does not resolve",
                )
            )
        elif fallback_id not in generic_ids:
            issues.append(
                _issue(
                    source_path,
                    f"/components/{component_index}/fallback_implementation_id",
                    f"fallback_implementation_id {fallback_id} is not the generic fallback",
                )
            )

        resident_bytes = (
            int(component["immutable_bytes"])
            + int(component["mutable_bytes_per_request"])
            + int(component["workspace_bytes"])
        )
        if resident_bytes > MAX_GOVERNED_INT:
            issues.append(
                _issue(
                    source_path,
                    f"/components/{component_index}",
                    f"resident working set exceeds governed integer maximum: {resident_bytes}",
                )
            )

    return tuple(sorted(issues))


def _construct_document(data: Mapping[str, Any]) -> ComponentProfileDocument:
    components = tuple(
        ComponentProfile(
            id=str(component["id"]),
            phase=str(component["phase"]),
            exactness_mode=str(component["exactness_mode"]),
            immutable_bytes=int(component["immutable_bytes"]),
            mutable_bytes_per_request=int(component["mutable_bytes_per_request"]),
            workspace_bytes=int(component["workspace_bytes"]),
            input_domain_id=str(component["input_domain_id"]),
            output_domain_id=str(component["output_domain_id"]),
            input_bytes=int(component["input_bytes"]),
            output_bytes=int(component["output_bytes"]),
            synchronization_ns=int(component["synchronization_ns"]),
            warmup_ns=int(component["warmup_ns"]),
            warmup_amortization_requests=int(component["warmup_amortization_requests"]),
            fallback_implementation_id=str(component["fallback_implementation_id"]),
            implementations=tuple(
                ImplementationProfile(
                    id=str(implementation["id"]),
                    compute_kind=ComputeKind(implementation["compute_kind"]),
                    rate_key=str(implementation["rate_key"]),
                    operations=int(implementation["operations"]),
                    bytes_read=int(implementation["bytes_read"]),
                    bytes_written=int(implementation["bytes_written"]),
                    required_capabilities=frozenset(
                        str(value) for value in implementation["required_capabilities"]
                    ),
                    allowed_memory_kinds=frozenset(
                        MemoryKind(value) for value in implementation["allowed_memory_kinds"]
                    ),
                    requires_residency=bool(implementation["requires_residency"]),
                    is_generic_fallback=bool(implementation["is_generic_fallback"]),
                )
                for implementation in component["implementations"]
            ),
        )
        for component in data["components"]
    )
    return ComponentProfileDocument(profile_id=str(data["profile_id"]), components=components)


def load_component_document(path: Path, root: Path) -> ComponentProfileDocument:
    """Load, validate, and construct one component profile document."""

    root_resolved = root.resolve(strict=True)
    resolved = resolve_input_file(root_resolved, path)
    display_path = Path(resolved.relative_to(root_resolved))
    data = load_json_mapping(resolved)
    schema_issues = validate_instance(
        data,
        root_resolved / "schemas" / "component-profile.schema.json",
        display_path,
    )
    if schema_issues:
        raise ComponentValidationError(schema_issues)
    semantic_issues = validate_component_semantics(data, display_path)
    if semantic_issues:
        raise ComponentValidationError(semantic_issues)
    return _construct_document(data)


def load_component_profile(path: Path, root: Path) -> tuple[ComponentProfile, ...]:
    """Compatibility helper returning only the component tuple."""

    return load_component_document(path, root).components
