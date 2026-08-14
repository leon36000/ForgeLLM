"""Immutable product-neutral resource topology models and validation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from .schema_io import DocumentIssue, load_json_mapping, resolve_input_file, validate_instance


class ComputeKind(StrEnum):
    CPU_GROUP = "cpu_group"
    GPU = "gpu"
    ACCELERATOR = "accelerator"


class MemoryKind(StrEnum):
    L1 = "l1"
    L2 = "l2"
    LLC = "llc"
    NUMA_DRAM = "numa_dram"
    PINNED_HOST = "pinned_host"
    GPU_MEMORY = "gpu_memory"
    STORAGE = "storage"
    REMOTE = "remote"


class LinkKind(StrEnum):
    CACHE_PATH = "cache_path"
    NUMA = "numa"
    PCIE = "pcie"
    PEER = "peer"
    NETWORK = "network"
    STORAGE = "storage"


class TopologyValidationError(ValueError):
    """Raised when a topology document fails schema or semantic validation."""

    def __init__(self, issues: tuple[DocumentIssue, ...]):
        self.issues = tuple(sorted(issues))
        message = "; ".join(issue.render() for issue in self.issues)
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class ComputeDomain:
    id: str
    kind: ComputeKind
    capabilities: frozenset[str]
    rate_ops_per_second: tuple[tuple[str, int], ...]
    attached_memory_ids: tuple[str, ...]

    def rate(self, key: str) -> int:
        for name, value in self.rate_ops_per_second:
            if name == key:
                return value
        raise KeyError(f"unknown rate key for {self.id}: {key}")


@dataclass(frozen=True, slots=True)
class MemoryDomain:
    id: str
    kind: MemoryKind
    capacity_bytes: int
    bandwidth_bytes_per_second: int
    latency_ns: int
    sharing_compute_ids: tuple[str, ...]
    capabilities: frozenset[str]
    line_size_bytes: int | None = None
    associativity: int | None = None
    numa_node_id: int | None = None


@dataclass(frozen=True, slots=True)
class LinkDomain:
    id: str
    kind: LinkKind
    source_id: str
    target_id: str
    bandwidth_bytes_per_second: int
    latency_ns: int
    bidirectional: bool
    capabilities: frozenset[str]


@dataclass(frozen=True, slots=True)
class TopologySnapshot:
    topology_id: str
    source_kind: str
    compute_domains: tuple[ComputeDomain, ...]
    memory_domains: tuple[MemoryDomain, ...]
    links: tuple[LinkDomain, ...]
    telemetry_capabilities: frozenset[str]

    def resource_ids(self) -> frozenset[str]:
        return frozenset(item.id for item in (*self.compute_domains, *self.memory_domains))

    def compute(self, domain_id: str) -> ComputeDomain:
        for domain in self.compute_domains:
            if domain.id == domain_id:
                return domain
        raise KeyError(f"unknown compute domain: {domain_id}")

    def memory(self, domain_id: str) -> MemoryDomain:
        for domain in self.memory_domains:
            if domain.id == domain_id:
                return domain
        raise KeyError(f"unknown memory domain: {domain_id}")

    def direct_link(self, source_id: str, target_id: str) -> LinkDomain | None:
        for link in self.links:
            if link.source_id == source_id and link.target_id == target_id:
                return link
            if link.bidirectional and link.source_id == target_id and link.target_id == source_id:
                return link
        return None


def _issue(source_path: Path, pointer: str, message: str) -> DocumentIssue:
    return DocumentIssue(f"{source_path}{pointer}", message)


def validate_topology_semantics(
    data: Mapping[str, Any],
    source_path: Path,
) -> tuple[DocumentIssue, ...]:
    """Validate references and relationships that JSON Schema cannot express."""

    issues: list[DocumentIssue] = []
    compute_items = data["compute_domains"]
    memory_items = data["memory_domains"]
    link_items = data["links"]

    seen: dict[str, str] = {}
    compute_ids = {str(item["id"]) for item in compute_items}
    memory_ids = {str(item["id"]) for item in memory_items}
    resource_ids = compute_ids | memory_ids

    for collection_name, items in (
        ("compute_domains", compute_items),
        ("memory_domains", memory_items),
        ("links", link_items),
    ):
        for index, item in enumerate(items):
            item_id = str(item["id"])
            if item_id in seen:
                issues.append(
                    _issue(
                        source_path,
                        f"/{collection_name}/{index}/id",
                        f"duplicate domain id {item_id}; first declared at {seen[item_id]}",
                    )
                )
            else:
                seen[item_id] = f"/{collection_name}/{index}/id"

    compute_by_id = {str(item["id"]): item for item in compute_items}
    memory_by_id = {str(item["id"]): item for item in memory_items}

    for c_index, compute in enumerate(compute_items):
        compute_id = str(compute["id"])
        for m_index, memory_id_value in enumerate(compute["attached_memory_ids"]):
            memory_id = str(memory_id_value)
            pointer = f"/compute_domains/{c_index}/attached_memory_ids/{m_index}"
            if memory_id not in memory_ids:
                issues.append(_issue(source_path, pointer, f"unresolved attached memory {memory_id}"))
                continue
            if compute_id not in memory_by_id[memory_id]["sharing_compute_ids"]:
                issues.append(
                    _issue(
                        source_path,
                        pointer,
                        f"compute/memory relationship is not symmetric for {compute_id} and {memory_id}",
                    )
                )

    for m_index, memory in enumerate(memory_items):
        memory_id = str(memory["id"])
        for c_index, compute_id_value in enumerate(memory["sharing_compute_ids"]):
            compute_id = str(compute_id_value)
            pointer = f"/memory_domains/{m_index}/sharing_compute_ids/{c_index}"
            if compute_id not in compute_ids:
                issues.append(_issue(source_path, pointer, f"unresolved sharing compute {compute_id}"))
                continue
            if memory_id not in compute_by_id[compute_id]["attached_memory_ids"]:
                issues.append(
                    _issue(
                        source_path,
                        pointer,
                        f"compute/memory relationship is not symmetric for {compute_id} and {memory_id}",
                    )
                )

    covered_directions: dict[tuple[str, str], str] = {}
    for index, link in enumerate(link_items):
        link_id = str(link["id"])
        source_id = str(link["source_id"])
        target_id = str(link["target_id"])
        if source_id not in resource_ids:
            issues.append(
                _issue(source_path, f"/links/{index}/source_id", f"unresolved link source {source_id}")
            )
        if target_id not in resource_ids:
            issues.append(
                _issue(source_path, f"/links/{index}/target_id", f"unresolved link target {target_id}")
            )
        if source_id == target_id:
            issues.append(_issue(source_path, f"/links/{index}", f"link {link_id} cannot reference itself"))

        directions = [(source_id, target_id)]
        if bool(link["bidirectional"]):
            directions.append((target_id, source_id))
        for direction in directions:
            previous = covered_directions.get(direction)
            if previous is not None:
                issues.append(
                    _issue(
                        source_path,
                        f"/links/{index}",
                        f"ambiguous direct link for {direction[0]} -> {direction[1]}: {previous} and {link_id}",
                    )
                )
            else:
                covered_directions[direction] = link_id

    return tuple(sorted(issues))


def _construct_topology(data: Mapping[str, Any]) -> TopologySnapshot:
    compute_domains = tuple(
        ComputeDomain(
            id=str(item["id"]),
            kind=ComputeKind(item["kind"]),
            capabilities=frozenset(str(value) for value in item["capabilities"]),
            rate_ops_per_second=tuple(
                (str(name), int(value)) for name, value in item["rate_ops_per_second"].items()
            ),
            attached_memory_ids=tuple(str(value) for value in item["attached_memory_ids"]),
        )
        for item in data["compute_domains"]
    )
    memory_domains = tuple(
        MemoryDomain(
            id=str(item["id"]),
            kind=MemoryKind(item["kind"]),
            capacity_bytes=int(item["capacity_bytes"]),
            bandwidth_bytes_per_second=int(item["bandwidth_bytes_per_second"]),
            latency_ns=int(item["latency_ns"]),
            sharing_compute_ids=tuple(str(value) for value in item["sharing_compute_ids"]),
            capabilities=frozenset(str(value) for value in item["capabilities"]),
            line_size_bytes=int(item["line_size_bytes"]) if "line_size_bytes" in item else None,
            associativity=int(item["associativity"]) if "associativity" in item else None,
            numa_node_id=int(item["numa_node_id"]) if "numa_node_id" in item else None,
        )
        for item in data["memory_domains"]
    )
    links = tuple(
        LinkDomain(
            id=str(item["id"]),
            kind=LinkKind(item["kind"]),
            source_id=str(item["source_id"]),
            target_id=str(item["target_id"]),
            bandwidth_bytes_per_second=int(item["bandwidth_bytes_per_second"]),
            latency_ns=int(item["latency_ns"]),
            bidirectional=bool(item["bidirectional"]),
            capabilities=frozenset(str(value) for value in item["capabilities"]),
        )
        for item in data["links"]
    )
    return TopologySnapshot(
        topology_id=str(data["topology_id"]),
        source_kind=str(data["source_kind"]),
        compute_domains=compute_domains,
        memory_domains=memory_domains,
        links=links,
        telemetry_capabilities=frozenset(str(value) for value in data["telemetry_capabilities"]),
    )


def load_topology(path: Path, root: Path) -> TopologySnapshot:
    """Load, schema-validate, semantically validate, and construct a topology."""

    root_resolved = root.resolve(strict=True)
    resolved = resolve_input_file(root_resolved, path)
    display_path = Path(resolved.relative_to(root_resolved))
    data = load_json_mapping(resolved)
    schema_issues = validate_instance(
        data,
        root_resolved / "schemas" / "topology.schema.json",
        display_path,
    )
    if schema_issues:
        raise TopologyValidationError(schema_issues)
    semantic_issues = validate_topology_semantics(data, display_path)
    if semantic_issues:
        raise TopologyValidationError(semantic_issues)
    return _construct_topology(data)
