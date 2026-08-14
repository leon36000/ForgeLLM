# Cache-Aware Topology and Placement Simulator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Use `superpowers:test-driven-development` for every behavior change and `superpowers:verification-before-completion` before any completion claim.

**Goal:** Build a deterministic, synthetic-only simulator that validates product-neutral resource topologies and component profiles, generates legal placements, estimates integer-nanosecond costs and emits an explainable selected plan without probing hardware or implementing the inference runtime.

**Architecture:** JSON Schema governs external documents. Immutable Python dataclasses represent compute, memory and link domains plus component/implementation profiles. A legality layer rejects unsupported candidates. A unit-safe analytical model produces a complete cost breakdown. A deterministic planner ranks candidates and serializes selected and rejected alternatives. The CLI consumes explicit synthetic JSON files and writes only beneath `artifacts/`.

**Tech Stack:** Python 3.11 standard library, `jsonschema==4.26.0`, PyYAML only where already used by project governance, pytest 9, Ruff 0.16.2, JSON Schema Draft 2020-12, GitHub Actions.

**Canonical specification:** `docs/superpowers/specs/2026-08-13-cache-aware-heterogeneous-inference-design.md`

## Global constraints

- No hardware probing, performance counters, affinity changes, huge-page changes or `resctrl` writes.
- No model download, model execution, CUDA, ROCm, kernel or runtime implementation.
- No external speedup may be recorded as a ForgeLLM result.
- No new third-party dependency is authorized by this plan.
- All time values are integer nanoseconds; all sizes are integer bytes; all rates are integer units per second.
- All public documents use `additionalProperties: false` at governed boundaries.
- Product names may appear in fixture descriptions only; they cannot affect behavior.
- Unknown capability is not equivalent to absent capability.
- Every selected specialized candidate must have a legal generic fallback in the same result.
- Output paths are confined beneath `artifacts/`; traversal and symlink escape fail closed.
- The active hardware task P0-T04 remains unchanged and blocked on host designation.

---

### Task 1: Create the bounded task packet and public schemas

**Files:**
- Create: `tasks/open/P0-T07-cache-aware-placement-simulator.yaml`
- Create: `schemas/topology.schema.json`
- Create: `schemas/component-profile.schema.json`
- Create: `schemas/placement-result.schema.json`
- Create: `tests/test_cache_aware_schemas.py`

**Interfaces:**
- Produces governed external formats with `schema_version: "1.0"`.
- Does not yet parse documents into runtime models.

- [ ] **Step 1: Write the failing schema-presence and schema-validity tests.**

```python
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def test_cache_aware_schemas_are_valid_draft_2020_12() -> None:
    for name in (
        "topology.schema.json",
        "component-profile.schema.json",
        "placement-result.schema.json",
    ):
        schema = json.loads((ROOT / "schemas" / name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
        assert schema["additionalProperties"] is False
```

- [ ] **Step 2: Run the test and confirm the expected failure.**

```bash
python -m pytest -q tests/test_cache_aware_schemas.py
```

Expected: failure because the three schema files do not exist.

- [ ] **Step 3: Create `topology.schema.json` with exact governed fields.**

Required top-level fields:

```json
{
  "schema_version": "1.0",
  "topology_id": "synthetic-cache-draft-v1",
  "source_kind": "synthetic",
  "compute_domains": [],
  "memory_domains": [],
  "links": [],
  "telemetry_capabilities": []
}
```

The schema must define:

- `source_kind`: `synthetic` or `observed`;
- compute kinds: `cpu_group`, `gpu`, `accelerator`;
- memory kinds: `l1`, `l2`, `llc`, `numa_dram`, `pinned_host`, `gpu_memory`, `storage`, `remote`;
- link kinds: `cache_path`, `numa`, `pcie`, `peer`, `network`, `storage`;
- positive `capacity_bytes`, `bandwidth_bytes_per_second`, `latency_ns >= 0`;
- IDs matching `^[a-z0-9][a-z0-9._-]{0,63}$`;
- arrays with unique scalar entries where JSON Schema can enforce uniqueness;
- no product-name field used by policy. Optional human description is allowed.

- [ ] **Step 4: Create `component-profile.schema.json`.**

Required document shape:

```json
{
  "schema_version": "1.0",
  "profile_id": "cache-draft-components-v1",
  "components": [
    {
      "id": "confidence-head",
      "phase": "draft",
      "exactness_mode": "exact",
      "immutable_bytes": 8388608,
      "mutable_bytes_per_request": 4096,
      "workspace_bytes": 1048576,
      "input_domain_id": "gpu-hbm-0",
      "output_domain_id": "gpu-hbm-0",
      "input_bytes": 8192,
      "output_bytes": 4096,
      "fallback_implementation_id": "cpu-generic",
      "implementations": []
    }
  ]
}
```

Implementation fields:

- `id`;
- `compute_kind`;
- `rate_key`;
- `operations`;
- `bytes_read`;
- `bytes_written`;
- `required_capabilities`;
- `allowed_memory_kinds`;
- `requires_residency`;
- `is_generic_fallback`.

- [ ] **Step 5: Create `placement-result.schema.json`.**

The result must include:

- input file SHA-256 values;
- objective `latency_ns`;
- selected candidate;
- all legal candidate cost breakdowns;
- all rejected candidates with stable reason codes;
- deterministic tie-break fields;
- evidence boundary text stating `synthetic_only`;
- simulator version.

Candidate cost breakdown fields are integer nanoseconds:

```json
{
  "compute_ns": 0,
  "resident_memory_ns": 0,
  "input_transfer_ns": 0,
  "output_transfer_ns": 0,
  "synchronization_ns": 0,
  "warmup_amortization_ns": 0,
  "total_ns": 0
}
```

- [ ] **Step 6: Create the draft task packet.**

`tasks/open/P0-T07-cache-aware-placement-simulator.yaml` must remain `status: draft` until owner authorization to execute the plan. It must explicitly forbid host probes, benchmarks, model execution and runtime implementation.

- [ ] **Step 7: Run schema and task-packet validation.**

```bash
python -m pytest -q tests/test_cache_aware_schemas.py
python scripts/validate_task_packet.py tasks/open/P0-T07-cache-aware-placement-simulator.yaml --root .
```

Expected: both pass.

- [ ] **Step 8: Commit.**

```bash
git add schemas/topology.schema.json schemas/component-profile.schema.json \
  schemas/placement-result.schema.json tests/test_cache_aware_schemas.py \
  tasks/open/P0-T07-cache-aware-placement-simulator.yaml
git commit -m "feat(simulation): define topology and placement schemas"
```

---

### Task 2: Add confined schema I/O and deterministic hashing

**Files:**
- Create: `src/forgellm_governance/schema_io.py`
- Create: `tests/test_schema_io.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class DocumentIssue:
    path: str
    message: str


def load_json_mapping(path: Path) -> Mapping[str, Any]: ...
def validate_instance(instance: Mapping[str, Any], schema_path: Path, source_path: Path) -> tuple[DocumentIssue, ...]: ...
def sha256_file(path: Path) -> str: ...
def resolve_input_file(root: Path, path: Path) -> Path: ...
def resolve_artifact_output(root: Path, path: Path) -> Path: ...
```

- [ ] **Step 1: Write failing tests for parse errors, traversal and symlink escape.**

Required cases:

- valid JSON object loads;
- JSON array is rejected where a mapping is required;
- malformed JSON reports line and column;
- `../outside.json` is rejected;
- an input symlink resolving outside the repository is rejected;
- an output path outside `artifacts/` is rejected;
- an output symlink escape is rejected;
- SHA-256 matches a known byte sequence.

- [ ] **Step 2: Run tests and confirm import failure.**

```bash
python -m pytest -q tests/test_schema_io.py
```

Expected: failure because `forgellm_governance.schema_io` does not exist.

- [ ] **Step 3: Implement path confinement before any file access.**

Use resolved paths and `Path.relative_to()`; do not use prefix-string comparison.

```python
def _require_within(path: Path, parent: Path) -> Path:
    resolved = path.resolve(strict=False)
    parent_resolved = parent.resolve(strict=True)
    try:
        resolved.relative_to(parent_resolved)
    except ValueError as exc:
        raise ValueError(f"path escapes {parent_resolved}: {path}") from exc
    return resolved
```

For output, reject an existing symlink at the output path and ensure the resolved parent remains under `root / "artifacts"`.

- [ ] **Step 4: Implement schema validation with deterministic issue ordering.**

Sort validation errors by absolute JSON path, then message. Do not emit raw Python reprs containing machine-specific paths beyond the governed relative source path.

- [ ] **Step 5: Run focused tests.**

```bash
python -m pytest -q tests/test_schema_io.py
```

Expected: pass.

- [ ] **Step 6: Run security/lint checks.**

```bash
python -m ruff check src/forgellm_governance/schema_io.py tests/test_schema_io.py
python -m ruff format --check src/forgellm_governance/schema_io.py tests/test_schema_io.py
```

- [ ] **Step 7: Commit.**

```bash
git add src/forgellm_governance/schema_io.py tests/test_schema_io.py
git commit -m "feat(simulation): add confined schema IO"
```

---

### Task 3: Implement immutable topology models and semantic validation

**Files:**
- Create: `src/forgellm_governance/topology.py`
- Create: `tests/test_topology.py`
- Create: `tests/fixtures/topology/valid-synthetic.json`
- Create: `tests/fixtures/topology/duplicate-id.json`
- Create: `tests/fixtures/topology/unresolved-link.json`
- Create: `tests/fixtures/topology/contradictory-sharing.json`

**Interfaces:**

```python
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


@dataclass(frozen=True, slots=True)
class ComputeDomain:
    id: str
    kind: ComputeKind
    capabilities: frozenset[str]
    rate_ops_per_second: tuple[tuple[str, int], ...]
    attached_memory_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MemoryDomain:
    id: str
    kind: MemoryKind
    capacity_bytes: int
    bandwidth_bytes_per_second: int
    latency_ns: int
    sharing_compute_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LinkDomain:
    id: str
    kind: str
    source_id: str
    target_id: str
    bandwidth_bytes_per_second: int
    latency_ns: int
    bidirectional: bool


@dataclass(frozen=True, slots=True)
class TopologySnapshot:
    topology_id: str
    source_kind: str
    compute_domains: tuple[ComputeDomain, ...]
    memory_domains: tuple[MemoryDomain, ...]
    links: tuple[LinkDomain, ...]
    telemetry_capabilities: frozenset[str]

    def resource_ids(self) -> frozenset[str]: ...
    def compute(self, domain_id: str) -> ComputeDomain: ...
    def memory(self, domain_id: str) -> MemoryDomain: ...
    def direct_link(self, source_id: str, target_id: str) -> LinkDomain | None: ...


def load_topology(path: Path, root: Path) -> TopologySnapshot: ...
def validate_topology_semantics(data: Mapping[str, Any], source_path: Path) -> tuple[DocumentIssue, ...]: ...
```

- [ ] **Step 1: Write failing tests for valid parsing and semantic failures.**

Required semantic rules:

- IDs are unique across compute, memory and link domains;
- every attached-memory and sharing-compute reference resolves;
- every link endpoint resolves;
- a compute domain and memory domain relationship is symmetric where declared attached/shared;
- no link references itself;
- every rate is positive;
- observed/synthetic source kind is preserved;
- lookup methods fail with a stable `KeyError` message;
- tuple ordering follows source order but lookup and serialization remain deterministic.

- [ ] **Step 2: Run tests and confirm module absence.**

```bash
python -m pytest -q tests/test_topology.py
```

- [ ] **Step 3: Implement schema-first loading.**

The loader order is mandatory:

1. confine input path;
2. parse JSON mapping;
3. validate against `schemas/topology.schema.json`;
4. run semantic validation;
5. construct immutable dataclasses.

Do not construct a partial model after an issue.

- [ ] **Step 4: Implement direct-link lookup.**

For bidirectional links, lookup must match either endpoint order while preserving the declared link ID. Multi-hop routing is explicitly out of scope and returns `None`.

- [ ] **Step 5: Run focused tests and mutation checks.**

```bash
python -m pytest -q tests/test_topology.py
python - <<'PY'
from pathlib import Path
from forgellm_governance.topology import load_topology

t = load_topology(Path('tests/fixtures/topology/valid-synthetic.json'), Path.cwd())
try:
    t.compute_domains += ()
except Exception as exc:
    print(type(exc).__name__)
else:
    raise SystemExit('topology unexpectedly mutable')
PY
```

Expected: tests pass; mutation attempt prints `FrozenInstanceError`.

- [ ] **Step 6: Commit.**

```bash
git add src/forgellm_governance/topology.py tests/test_topology.py tests/fixtures/topology
git commit -m "feat(simulation): model immutable resource topology"
```

---

### Task 4: Implement component and implementation profiles

**Files:**
- Create: `src/forgellm_governance/components.py`
- Create: `tests/test_components.py`
- Create: `tests/fixtures/components/valid-cache-draft.json`
- Create: `tests/fixtures/components/missing-fallback.json`
- Create: `tests/fixtures/components/duplicate-implementation.json`

**Interfaces:**

```python
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
    def resident_bytes(self) -> int: ...


def load_component_profile(path: Path, root: Path) -> tuple[ComponentProfile, ...]: ...
```

- [ ] **Step 1: Write failing schema and semantic tests.**

Required rules:

- component IDs unique;
- implementation IDs unique within each component;
- exactly one `is_generic_fallback` implementation per component;
- `fallback_implementation_id` resolves to that implementation;
- exact-mode component implementations cannot declare an approximate-only flag;
- `resident_bytes = immutable + mutable + workspace` with overflow-safe non-negative integers;
- input/output memory IDs are checked later against the topology, not guessed here.

- [ ] **Step 2: Confirm tests fail before implementation.**

```bash
python -m pytest -q tests/test_components.py
```

- [ ] **Step 3: Implement schema-first immutable loading.**

Use the same issue ordering and path confinement as topology loading.

- [ ] **Step 4: Add the valid cache-draft fixture.**

The fixture contains two components:

1. `confidence-head`, small enough for the synthetic LLC;
2. `markov-head`, with CPU-local, CPU-generic and GPU implementations.

All byte/rate values must be explicitly labeled synthetic in the fixture description.

- [ ] **Step 5: Run tests and lint.**

```bash
python -m pytest -q tests/test_components.py
python -m ruff check src/forgellm_governance/components.py tests/test_components.py
```

- [ ] **Step 6: Commit.**

```bash
git add src/forgellm_governance/components.py tests/test_components.py tests/fixtures/components
git commit -m "feat(simulation): model component placement profiles"
```

---

### Task 5: Implement deterministic integer cost accounting

**Files:**
- Create: `src/forgellm_governance/cost_model.py`
- Create: `tests/test_cost_model.py`

**Interfaces:**

```python
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

    @property
    def total_ns(self) -> int: ...


def ceil_div(numerator: int, denominator: int) -> int: ...
def rate_time_ns(work: int, units_per_second: int) -> int: ...
def estimate_cost(
    topology: TopologySnapshot,
    component: ComponentProfile,
    implementation: ImplementationProfile,
    candidate: PlacementCandidate,
) -> CostBreakdown: ...
```

- [ ] **Step 1: Write failing unit and monotonicity tests.**

Required cases:

- zero work costs zero;
- positive work rounds upward, never down;
- doubling operations cannot reduce `compute_ns`;
- reducing bandwidth cannot reduce transfer time;
- increasing latency cannot reduce total time;
- warmup amortization uses ceiling division;
- integer results are identical across repeated runs;
- no float appears in serialized dataclass fields;
- missing direct transfer link raises a stable `CostModelError`, never assumes zero transfer;
- a resident working set larger than memory capacity raises a stable error when residency is required.

- [ ] **Step 2: Run tests and confirm expected failures.**

```bash
python -m pytest -q tests/test_cost_model.py
```

- [ ] **Step 3: Implement integer-only rate conversion.**

```python
NANOSECONDS_PER_SECOND = 1_000_000_000


def rate_time_ns(work: int, units_per_second: int) -> int:
    if work < 0 or units_per_second <= 0:
        raise ValueError("work must be non-negative and rate must be positive")
    return ceil_div(work * NANOSECONDS_PER_SECOND, units_per_second)
```

- [ ] **Step 4: Implement cost terms.**

- `compute_ns`: implementation operations against the compute-domain `rate_key`;
- `resident_memory_ns`: memory latency plus read/write bytes at the memory-domain bandwidth;
- transfer terms: direct link latency plus bytes at link bandwidth; zero only when source/target is the selected memory domain;
- `synchronization_ns`: explicit component value;
- `warmup_amortization_ns`: `ceil_div(warmup_ns, warmup_amortization_requests)`.

Do not add uncalibrated cache-miss, energy or queueing constants in this first implementation. The result schema must label these future terms as unsupported rather than silently zero if they are exposed.

- [ ] **Step 5: Run focused and adversarial tests.**

```bash
python -m pytest -q tests/test_cost_model.py
```

- [ ] **Step 6: Commit.**

```bash
git add src/forgellm_governance/cost_model.py tests/test_cost_model.py
git commit -m "feat(simulation): add deterministic placement cost model"
```

---

### Task 6: Generate legal candidates with stable rejection reasons

**Files:**
- Create: `src/forgellm_governance/legality.py`
- Create: `tests/test_legality.py`

**Interfaces:**

```python
class RejectionCode(StrEnum):
    COMPUTE_KIND_MISMATCH = "compute_kind_mismatch"
    MISSING_CAPABILITY = "missing_capability"
    MISSING_RATE = "missing_rate"
    MEMORY_KIND_MISMATCH = "memory_kind_mismatch"
    MEMORY_CAPACITY_EXCEEDED = "memory_capacity_exceeded"
    MEMORY_NOT_ATTACHED = "memory_not_attached"
    INPUT_LINK_MISSING = "input_link_missing"
    OUTPUT_LINK_MISSING = "output_link_missing"
    FALLBACK_NOT_LEGAL = "fallback_not_legal"


@dataclass(frozen=True, slots=True)
class RejectedCandidate:
    candidate: PlacementCandidate
    codes: tuple[RejectionCode, ...]
    details: tuple[str, ...]


def enumerate_candidates(
    topology: TopologySnapshot,
    component: ComponentProfile,
) -> tuple[tuple[PlacementCandidate, ...], tuple[RejectedCandidate, ...]]: ...
```

- [ ] **Step 1: Write failing legality tests.**

Cover every rejection code plus:

- all compute × memory × implementation combinations are considered deterministically;
- reason codes are sorted by enum value;
- details do not contain memory addresses or platform-specific reprs;
- a candidate requiring residency is rejected when `resident_bytes > capacity_bytes`;
- generic fallback must be legal on at least one domain;
- unknown capability causes rejection rather than optimistic acceptance;
- direct input/output links are mandatory unless source/target already equals selected memory.

- [ ] **Step 2: Run tests and confirm failure.**

```bash
python -m pytest -q tests/test_legality.py
```

- [ ] **Step 3: Implement deterministic enumeration.**

Sort iteration inputs by IDs before constructing candidates. Return tuples, not sets or dictionaries whose iteration order could leak into output.

- [ ] **Step 4: Add fallback invariant.**

If the component's declared generic fallback has no legal placement, raise `PlacementInvariantError` before ranking any specialized candidate.

- [ ] **Step 5: Run tests.**

```bash
python -m pytest -q tests/test_legality.py
```

- [ ] **Step 6: Commit.**

```bash
git add src/forgellm_governance/legality.py tests/test_legality.py
git commit -m "feat(simulation): enumerate legal placement candidates"
```

---

### Task 7: Implement deterministic selection and explainability

**Files:**
- Create: `src/forgellm_governance/planner.py`
- Create: `tests/test_planner.py`

**Interfaces:**

```python
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


def plan_component(topology: TopologySnapshot, component: ComponentProfile) -> ComponentPlan: ...
def plan_components(topology: TopologySnapshot, components: tuple[ComponentProfile, ...]) -> tuple[ComponentPlan, ...]: ...
```

- [ ] **Step 1: Write failing planner tests.**

Required behavior:

- minimum `total_ns` wins;
- ties break by `(implementation_id, compute_domain_id, memory_domain_id)`;
- candidate and rejection lists have stable order;
- selected/fallback entries are members of legal candidates;
- generic fallback remains present when a specialized candidate wins;
- specialized candidate is not selected when its cost is equal to fallback unless tie-break order explicitly wins and the result explains the tie;
- repeated planning and JSON serialization are byte-identical;
- changing an unrelated description field does not alter selection;
- missing legal fallback fails closed.

- [ ] **Step 2: Run tests and confirm module absence.**

```bash
python -m pytest -q tests/test_planner.py
```

- [ ] **Step 3: Implement ranking.**

```python
def _rank_key(item: EvaluatedCandidate) -> tuple[int, str, str, str]:
    c = item.candidate
    return (item.cost.total_ns, c.implementation_id, c.compute_domain_id, c.memory_domain_id)
```

- [ ] **Step 4: Implement stable explanation strings.**

Allowed forms:

```text
selected minimum total_ns=12345; fallback total_ns=23456; estimated delta_ns=11111
selected deterministic tie at total_ns=12345 using implementation/compute/memory ordering
```

Do not use free-form model-generated text.

- [ ] **Step 5: Run focused tests.**

```bash
python -m pytest -q tests/test_planner.py
```

- [ ] **Step 6: Commit.**

```bash
git add src/forgellm_governance/planner.py tests/test_planner.py
git commit -m "feat(simulation): select and explain deterministic plans"
```

---

### Task 8: Serialize results and add a fail-closed CLI

**Files:**
- Create: `src/forgellm_governance/simulation.py`
- Create: `scripts/simulate_placement.py`
- Create: `tests/test_simulation_cli.py`

**Interfaces:**

```python
def build_result_document(
    topology_path: Path,
    component_path: Path,
    topology: TopologySnapshot,
    plans: tuple[ComponentPlan, ...],
) -> dict[str, Any]: ...


def run_simulation(
    root: Path,
    topology_path: Path,
    component_path: Path,
    output_path: Path,
) -> Path: ...
```

CLI:

```text
python scripts/simulate_placement.py \
  --root . \
  --topology examples/simulations/synthetic-cache-draft-topology.json \
  --components examples/simulations/synthetic-cache-draft-components.json \
  --output artifacts/simulations/synthetic-cache-draft-result.json
```

- [ ] **Step 1: Write failing CLI tests.**

Required cases:

- successful invocation returns 0 and writes valid result JSON;
- output is deterministic across two temporary artifact paths after normalizing only the output path itself;
- malformed topology returns non-zero and writes no partial output;
- output traversal and symlink escape return non-zero;
- unknown argument returns argparse exit 2;
- existing output is replaced atomically only after complete validation;
- result validates against `placement-result.schema.json`;
- result input hashes match source files;
- evidence boundary equals `synthetic_only`.

- [ ] **Step 2: Run tests and confirm failure.**

```bash
python -m pytest -q tests/test_simulation_cli.py
```

- [ ] **Step 3: Implement atomic output.**

Write to a sibling temporary file under the already-confined artifact directory, `flush()`, `os.fsync()`, then `os.replace()`. Remove the temporary file after any exception.

- [ ] **Step 4: Implement deterministic JSON.**

Use:

```python
json.dumps(document, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"
```

Do not include wall-clock timestamps, hostnames, absolute paths or random IDs in a synthetic result.

- [ ] **Step 5: Implement concise diagnostics.**

The script prints one `ERROR:` line per structured issue to stderr, never a traceback for expected validation failures. Unexpected exceptions remain visible in tests and CI.

- [ ] **Step 6: Run focused tests and lint.**

```bash
python -m pytest -q tests/test_simulation_cli.py
python -m ruff check src/forgellm_governance/simulation.py scripts/simulate_placement.py tests/test_simulation_cli.py
```

- [ ] **Step 7: Commit.**

```bash
git add src/forgellm_governance/simulation.py scripts/simulate_placement.py tests/test_simulation_cli.py
git commit -m "feat(simulation): add synthetic placement CLI"
```

---

### Task 9: Add the canonical synthetic cache-draft example

**Files:**
- Create: `examples/simulations/synthetic-cache-draft-topology.json`
- Create: `examples/simulations/synthetic-cache-draft-components.json`
- Create: `docs/simulations/CACHE_AWARE_SIMULATOR.md`
- Create: `tests/test_cache_draft_example.py`

**Interfaces:**
- Provides a documented synthetic example, not a hardware profile.

- [ ] **Step 1: Write the failing example test.**

The test must assert:

- both example files validate;
- the planner selects the synthetic LLC-local confidence head;
- the result retains a generic CPU fallback;
- the synthetic Markov head winner is determined by the explicitly chosen fixture values;
- changing LLC capacity below the resident working set rejects the residency-required candidate;
- no file contains `9950`, `Xeon`, `NVIDIA`, `AMD`, a hostname or a device UUID in behavior-defining fields.

- [ ] **Step 2: Confirm failure because example files are missing.**

```bash
python -m pytest -q tests/test_cache_draft_example.py
```

- [ ] **Step 3: Create the topology fixture with declared synthetic values.**

Use generic IDs:

```text
cpu-cache-group-0
llc-0
numa-dram-0
gpu-0
gpu-memory-0
pcie-0
```

The description states that capacities/rates are hypothetical and cannot support a performance claim.

- [ ] **Step 4: Create the component fixture.**

Include a small confidence head and a larger Markov head with explicit generic fallback implementations.

- [ ] **Step 5: Document how to interpret the result.**

`CACHE_AWARE_SIMULATOR.md` must include:

- schema overview;
- exact command;
- deterministic output explanation;
- what the simulator does not model yet: contention, queueing, energy, cache misses, multi-hop routing, overlap and acceptance-rate feedback;
- explicit warning that predicted nanoseconds are not measured performance.

- [ ] **Step 6: Run example tests and CLI twice.**

```bash
python -m pytest -q tests/test_cache_draft_example.py
python scripts/simulate_placement.py --root . \
  --topology examples/simulations/synthetic-cache-draft-topology.json \
  --components examples/simulations/synthetic-cache-draft-components.json \
  --output artifacts/simulations/cache-draft-a.json
python scripts/simulate_placement.py --root . \
  --topology examples/simulations/synthetic-cache-draft-topology.json \
  --components examples/simulations/synthetic-cache-draft-components.json \
  --output artifacts/simulations/cache-draft-b.json
cmp artifacts/simulations/cache-draft-a.json artifacts/simulations/cache-draft-b.json
```

Expected: all pass and `cmp` exits 0.

- [ ] **Step 7: Commit.**

```bash
git add examples/simulations docs/simulations/CACHE_AWARE_SIMULATOR.md tests/test_cache_draft_example.py
git commit -m "docs(simulation): add synthetic cache-draft scenario"
```

---

### Task 10: Integrate validation, CLI and repository gates

**Files:**
- Modify: `src/forgellm_governance/cli.py`
- Modify: `src/forgellm_governance/__init__.py`
- Modify: `Makefile`
- Modify: `tests/test_validation.py`
- Create: `scripts/validate_topology.py`
- Create: `scripts/validate_component_profile.py`

**Interfaces:**

New console commands:

```text
forgellm-governance validate-topology PATH --root .
forgellm-governance validate-components PATH --root .
forgellm-governance simulate-placement --topology PATH --components PATH --output PATH --root .
```

- [ ] **Step 1: Write failing CLI dispatch tests.**

Use direct `main()` calls with patched `sys.argv`; verify exit codes and concise output.

- [ ] **Step 2: Confirm dispatch tests fail.**

```bash
python -m pytest -q tests/test_validation.py -k 'topology or components or simulate'
```

- [ ] **Step 3: Add CLI subcommands without changing existing command semantics.**

Export only stable public functions from `__init__.py`; internal dataclasses need not all become public.

- [ ] **Step 4: Update `Makefile`.**

Add:

```make
validate:
	$(PYTHON) scripts/validate_topology.py examples/simulations/synthetic-cache-draft-topology.json --root .
	$(PYTHON) scripts/validate_component_profile.py examples/simulations/synthetic-cache-draft-components.json --root .
	$(PYTHON) scripts/validate_task_packet.py tasks/open/P0-T07-cache-aware-placement-simulator.yaml --root .

simulate-cache-draft:
	$(PYTHON) scripts/simulate_placement.py --root . \
	  --topology examples/simulations/synthetic-cache-draft-topology.json \
	  --components examples/simulations/synthetic-cache-draft-components.json \
	  --output artifacts/simulations/synthetic-cache-draft-result.json
```

Do not remove the active P0-T04 task validation when the repository gate is updated. Remove only genuinely stale task checks through a separate state-consistent change if needed.

- [ ] **Step 5: Run targeted and complete verification.**

```bash
python -m pytest -q tests/test_validation.py
make ci
make simulate-cache-draft
```

- [ ] **Step 6: Commit.**

```bash
git add src/forgellm_governance/cli.py src/forgellm_governance/__init__.py \
  Makefile tests/test_validation.py scripts/validate_topology.py \
  scripts/validate_component_profile.py
git commit -m "ci(simulation): enforce cache-aware simulator gates"
```

---

### Task 11: Adversarial validation and evidence closeout

**Files:**
- Create: `tests/test_cache_aware_adversarial.py`
- Create: `docs/reviews/P0-T07-CACHE-AWARE-SIMULATOR-REVIEW.md`
- Modify: `tasks/open/P0-T07-cache-aware-placement-simulator.yaml`
- Modify only if task is authorized and completed: state, roadmap, handoff and mobile state files listed by the active closeout task.

**Interfaces:**
- Produces independent verification evidence, not new simulator behavior unless a finding requires a fix.

- [ ] **Step 1: Add adversarial tests before review.**

Required attacks/failures:

- duplicate resource IDs across domain kinds;
- unresolved attached memory;
- bidirectional link ambiguity;
- zero or negative rates;
- integer values beyond permitted schema maximum;
- output traversal and symlink escape;
- missing fallback;
- fallback with unavailable capability;
- candidate requiring absent direct link;
- topology description containing product names must not affect selection;
- reordered input arrays produce byte-identical selected plan after canonical sorting;
- unrelated telemetry capability cannot change ranking;
- unsupported future schema version fails closed;
- malformed Unicode/JSON fails without partial output.

- [ ] **Step 2: Run adversarial tests and fix every valid finding using TDD.**

```bash
python -m pytest -q tests/test_cache_aware_adversarial.py
```

Expected: pass after any required fixes.

- [ ] **Step 3: Run complete local verification from a clean environment.**

```bash
python3 -m venv .venv-plan-verify
.venv-plan-verify/bin/python -m pip install -e '.[dev]'
make PYTHON=.venv-plan-verify/bin/python ci
make PYTHON=.venv-plan-verify/bin/python simulate-cache-draft
git diff --check
git status --short
```

Expected:

- all commands exit 0;
- only intentionally untracked local verification artifacts are ignored;
- worktree is clean after generated artifacts are removed or ignored.

- [ ] **Step 4: Request a fresh-context review.**

The reviewer receives:

- canonical spec path;
- this implementation plan;
- base and head SHAs;
- exact task packet;
- test/CI commands and outputs;
- generated synthetic result and source hashes;
- explicit evidence boundary.

Review checklist:

- no hardware inference or product-name branching;
- integer/unit correctness;
- deterministic output;
- fallback invariant;
- path confinement;
- schema strictness;
- no unsupported performance claim;
- P0-T04/P0-T05 gates preserved.

- [ ] **Step 5: Resolve all BLOCKER/MAJOR findings and rerun complete verification.**

- [ ] **Step 6: Update the task packet only after evidence exists.**

Change `status` from `draft` to `complete` only when owner authorization, exact-head CI, fresh review and all acceptance criteria are present. Otherwise leave it `draft`, `ready`, `in_progress` or `review` as truth requires.

- [ ] **Step 7: Commit the review and closeout evidence.**

```bash
git add tests/test_cache_aware_adversarial.py \
  docs/reviews/P0-T07-CACHE-AWARE-SIMULATOR-REVIEW.md \
  tasks/open/P0-T07-cache-aware-placement-simulator.yaml
git commit -m "docs(review): verify cache-aware placement simulator"
```

- [ ] **Step 8: Verify hosted exact-head gates before merge.**

Required hosted evidence:

- `Validate and test`: success;
- CodeQL: execution/upload success, with alert details characterized honestly;
- Dependency Review: success or explicitly skipped/non-required according to repository policy;
- no unresolved review threads;
- changed-file list matches the task packet.

## Completion report format

The implementing agent reports:

1. task identifier and owner authorization;
2. base/head/merge SHAs;
3. files changed;
4. exact test and CI commands with outcomes;
5. synthetic example input hashes and result hash;
6. selected/fallback plan and evidence boundary;
7. known unsupported cost terms;
8. residual risks and blocked hardware work;
9. state/task records updated;
10. next recommended work package.

## Planned next package after successful completion

The next package is CA-03: exact speculative-decoding reference semantics. It must not begin automatically. It requires its own specification check, task packet and owner authorization, and it may need P0-T05 model/workload choices before finalizing reference vectors.
