# ForgeLLM Cache-Aware Placement Simulator

## Scope

The simulator validates a product-neutral resource topology and component profile, enumerates legal implementation/compute/memory placements, estimates a deterministic analytical latency cost, and emits the selected plan together with the legal fallback and every rejection reason.

It is a **synthetic-only** design tool. It does not probe hardware, run an LLM, execute a kernel, measure cache behavior, or predict production performance.

## Governed inputs

- `schemas/topology.schema.json` describes compute, memory, and direct-link domains.
- `schemas/component-profile.schema.json` describes component working sets, exactness mode, implementations, and a mandatory generic fallback.
- `schemas/placement-result.schema.json` governs the deterministic output.

The canonical example files are:

```text
examples/simulations/synthetic-cache-draft-topology.json
examples/simulations/synthetic-cache-draft-components.json
```

All values in those examples are hypothetical. Commercial product names cannot affect simulator behavior.

## Run

```bash
make simulate-cache-draft
```

Equivalent command:

```bash
python scripts/simulate_placement.py \
  --root . \
  --topology examples/simulations/synthetic-cache-draft-topology.json \
  --components examples/simulations/synthetic-cache-draft-components.json \
  --output artifacts/simulations/synthetic-cache-draft-result.json
```

The CLI writes atomically and only beneath `artifacts/`. Traversal and symlink escapes fail closed.

## Cost accounting

The first version uses integer bytes, rates, and nanoseconds only. Each legal candidate reports compute time, selected-memory access time, input and output transfer time, explicit synchronization time, amortized warmup time, and total time.

All division rounds upward. A missing direct transfer link is an error or a legality rejection; the simulator never assumes a free transfer or hidden multi-hop route.

## Determinism and explainability

Candidates are ranked by:

```text
total_ns, implementation_id, compute_domain_id, memory_domain_id
```

The result retains the selected candidate, every legal candidate and full cost breakdown, the best legal generic fallback, every rejected candidate with stable reason codes, SHA-256 hashes of both inputs, and `evidence_boundary: synthetic_only`.

The same validated inputs produce byte-identical JSON output regardless of input array ordering or the requested artifact filename.

## Unsupported terms

The result explicitly lists cost terms that are not modeled yet: queueing, interference, energy, cache-miss penalties, CPU/GPU overlap, speculative acceptance-rate feedback, and multi-hop routing. A zero is not silently substituted for these terms.

## Interpretation

Predicted nanoseconds are outputs of the declared synthetic model, not measured latency. A cache-local winner means only that the supplied hypothetical rates, capacities, and links make it win under the supported terms. It does not establish performance on any processor or accelerator.

P0-T04 remains the observation-only hardware inventory gate. P0-T05 still defines model, workload, and SLO profiles before performance claims or hardware calibration.
