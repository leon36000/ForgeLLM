# ForgeLLM — Cache-Aware Heterogeneous Inference Design

**Status:** owner-approved design; written specification pending final owner review  
**Date:** 2026-08-13  
**Proposed task:** P0-T07  
**Canonical state at drafting:** S-0005 / P0-T04 blocked on first-host designation  
**Implementation status:** none  
**Hardware measurements:** none  
**ForgeLLM performance claims:** none

## 1. Durable decision

ForgeLLM will use a two-layer architecture:

1. a portable semantic execution graph that defines correctness independently of hardware;
2. a microarchitecture-aware placement and specialization plane that maps graph components onto CPU cache domains, NUMA nodes, GPUs, memory tiers, storage and links using observed capabilities and an empirical cost model.

The first bounded case study is **ForgeCacheDraft**: a speculative-decoding sidecar in which compact, sequential and high-reuse components may execute in a dedicated CPU cache domain while the target model and parallel verification remain on the GPU.

The architecture does not expose product-name conditionals such as `9950X3D`, `9950X3D2`, a particular Xeon SKU, or one GPU family in public semantics. Product-specific knowledge is translated into observed capabilities and immutable environment fingerprints.

## 2. Motivation

LLM inference is often constrained by data movement, memory hierarchy and synchronization rather than arithmetic alone. Large CPU last-level caches, heterogeneous CPU/GPU speculative decoding, low-rank draft heads and cache-resident execution make some non-GPU placements plausible when three conditions hold:

- the component working set is sufficiently small;
- the component is reused frequently enough to benefit from locality;
- transfer and synchronization costs do not exceed the GPU work avoided.

The design must avoid two opposite failure modes:

- **per-processor bespoke engine:** high short-term specialization, but unmaintainable fragmentation and semantic drift;
- **fully generic scheduler:** clean portability, but insufficient representation of cache domains, cross-CCD penalties, transfer granularity and dynamic contention.

ForgeLLM therefore selects a **capability graph plus empirical specialization** approach: shared semantics, multiple legal implementations, analytical screening, measurement and bounded autotuning.

## 3. Goals

- Represent CPU cores, cache domains, NUMA nodes, GPUs, memory tiers, links and storage as explicit resources.
- Describe every inference component by working-set size, lifetime, access pattern, parallelism, precision, exactness requirements and transfer dependencies.
- Generate legal placement candidates and choose among them using measured latency, bandwidth, contention, energy and acceptance-rate data.
- Support cache-aware CPU sidecars without making cache residency a correctness assumption.
- Preserve target-model semantics in the default speculative mode.
- Permit component-level specialization without fragmenting model/runtime semantics.
- Make every selected and rejected placement explainable and reproducible.
- Retain a correct generic fallback for every promoted specialized path.

## 4. Non-goals

- Keeping an entire large MTP module in a desktop LLC.
- Assuming that a large cache automatically improves response quality.
- Hard-coding commercial product names into scheduling policy or public APIs.
- Implementing kernels or runtime code during this design task.
- Running performance benchmarks before inventory and workload-profile gates.
- Treating external speedups as ForgeLLM measurements.
- Requiring Linux `resctrl`; it is an optional discovered capability.
- Bypassing P0-T04 or P0-T05.

## 5. Selected architecture

### 5.1 Portable semantic graph

The semantic graph defines:

- model and operator semantics;
- tensor layouts and precision contracts;
- KV, sampling, grammar and recurrent state;
- accepted numerical error budgets;
- rollback, cancellation and commit boundaries;
- dependencies between prefill, decode, draft and verification components.

The semantic graph cannot depend on one processor topology. It is the reference against which specialized plans are verified.

### 5.2 ForgeTopology

`ForgeTopology` is an immutable snapshot for one run. It models:

- CPU packages, cores, SMT siblings and ISA capabilities;
- cache IDs and sharing CPU sets for L1, L2 and LLC;
- NUMA nodes and memory capacity;
- GPU devices, local memory, copy engines and peer links;
- observed PCIe, NVLink, Infinity-Fabric-like or network paths;
- pinned and pageable host-memory capabilities;
- storage and remote-memory tiers;
- optional `resctrl`, RDT or QoS capabilities;
- timer, counter, energy and thermal telemetry availability.

Commercial product names are retained only as descriptive metadata. Scheduling uses the observed resource graph.

### 5.3 Resource-domain model

```text
ComputeDomain
  CPU core group
  GPU execution partition
  accelerator/plugin domain

MemoryDomain
  L1/L2/LLC cache ID
  NUMA DRAM
  pinned host memory
  GPU HBM/VRAM
  storage
  remote memory

LinkDomain
  CPU/cache relation
  NUMA interconnect
  PCIe
  GPU peer link
  network transport
```

A cache domain is represented by its cache ID, capacity, line size, sharing CPU set and optional control/monitoring capabilities. ForgeLLM must not infer one uniform LLC solely from total advertised cache.

### 5.4 Component descriptor

Each graph component declares:

- immutable bytes by precision;
- mutable bytes per request;
- temporary workspace;
- read/write ratio;
- access sequence and reuse distance;
- arithmetic intensity;
- vectorization and parallelism;
- batching behavior;
- phase: prefill, decode, draft, verification, sampling or transfer;
- exactness and numerical budget;
- legal implementations;
- input/output transfer size;
- cancellation and rollback behavior;
- warm and cold initialization cost.

Representative components include target layers, attention, KV metadata, a draft backbone, a Markov or low-rank head, a confidence head, tokenizer, grammar automata, sampler, MoE router and expert-prefetch metadata.

### 5.5 Placement planner

The planner works in four stages:

1. **Legality:** remove placements unsupported by ISA, precision, memory capacity, synchronization or exactness.
2. **Analytical screen:** reject candidates whose lower-bound transfer or compute cost cannot beat the reference.
3. **Profiled model:** predict latency, bandwidth, occupancy, energy, queueing and interference.
4. **Bounded autotune:** measure the remaining candidates and cache the result under an immutable environment fingerprint.

The planner returns both the selected plan and rejected alternatives with reasons.

## 6. Cost model

For component `c` placed on domain `d`:

```text
cost(c, d) =
    compute_time
  + input_transfer
  + output_transfer
  + synchronization
  + cache_miss_penalty
  + queueing
  + interference
  + warmup_amortization
  + energy_penalty
  + SLO_violation_penalty
```

For speculative decoding:

```text
net_gain =
    target_steps_avoided
  - draft_compute
  - transfer
  - verification_expansion
  - rollback
  - scheduler_overhead
```

The sidecar is enabled only when a conservative lower-confidence estimate of `net_gain` is positive. A plan may be parked dynamically when measured transfer, queueing, cache pressure or acceptance falls outside its valid envelope.

## 7. ForgeCacheService

`ForgeCacheService` exposes best-effort locality rather than guaranteed cache locking.

Capabilities:

- discover cache IDs and sharing CPU sets;
- pin threads to one cache and NUMA domain;
- allocate memory from the corresponding NUMA node;
- align and pack hot read-only data;
- warm selected working sets;
- use huge pages only when measured beneficial;
- expose prefetch strategies;
- monitor LLC misses, occupancy, memory bandwidth, migrations, clocks and thermal state;
- optionally use CAT, CQM or MBM through `resctrl`;
- fall back automatically when counters or control are unavailable.

Cache pseudo-locking remains experimental because it may reduce average access latency but does not create an absolute residency guarantee.

## 8. ForgeCacheDraft

### 8.1 Exact default pipeline

```text
GPU target hidden state or compact features
                 │
                 ▼
asynchronous compact transfer or shared host buffer
                 │
                 ▼
CPU cache-domain sidecar
  - low-rank or Markov draft head
  - confidence head
  - adaptive draft budget
  - sampler and grammar state
                 │
                 ▼
candidate block plus proposal probabilities
                 │
                 ▼
GPU target verification
                 │
                 ▼
exact accept/reject correction and KV commit/rollback
```

CPU and GPU work overlap through double buffering. The CPU sidecar must not enter the critical path unless measured overlap and acceptance justify it.

### 8.2 Cache-resident candidate order

1. confidence head and draft-budget controller;
2. compact Markov or low-rank LM head;
3. sampling and grammar automata;
4. top-M transition tables;
5. prefix/radix metadata;
6. MoE routing and expert-prefetch metadata;
7. quantization scales and codebooks;
8. selected tiny experts or adapters only if the complete hot working set fits.

A large MTP module containing billions of parameters is not a cache-resident candidate. Its compact subcomponents may be.

### 8.3 Transition Atlas — experimental

A token-indexed representation stores top-M candidate transitions and quantized scores, optionally with a low-rank residual.

Variants to compare:

- full low-rank head;
- top-M table;
- top-M table plus residual;
- dynamic vocabulary truncation;
- conventional GPU draft head.

The target verifier remains authoritative in exact mode. The experiment must measure draft latency, LLC miss rate, acceptance length, target verification expansion, TPOT, memory footprint and exactness.

### 8.4 Adaptive control

ForgeCacheDraft may:

- change draft length;
- change branching width;
- switch head implementation;
- park speculation and use autoregressive decode;
- relocate one component between CPU and GPU;
- reduce concurrency to protect an SLO.

Adaptation uses only causal request state and previously measured behavior. Future target outcomes cannot retroactively bias a sampling decision.

## 9. Exactness and quality modes

### Exact mode — default

- The target model defines the final distribution.
- Draft probabilities required by the correction algorithm are preserved.
- Quantized draft error may reduce acceptance but cannot silently change target semantics.
- Greedy mode must match the non-speculative target subject only to documented floating-point tie behavior.
- KV, recurrent, grammar and sampling state are committed only to the accepted prefix.
- Any exactness mismatch disables the candidate path.

### Approximate mode — separate research profile

A verifier regret budget, reranker, critic, ensemble or quality-changing policy is a different product profile with independent quality and safety evaluation. Cache placement itself is never presented as improving alignment.

## 10. Falsifiable hypotheses

### H1 — compact draft heads

A quantized Markov or low-rank head whose hot working set fits one LLC domain has lower and more stable latency than a DRAM-streamed CPU implementation.

### H2 — overlap

CPU drafting reduces end-to-end decode latency only when transfer and synchronization are hidden behind useful GPU work.

### H3 — cache-domain pinning

Pinning the sidecar and allocating its data in the matching NUMA/cache domain outperforms unconstrained scheduling on multi-CCD or multi-socket systems.

### H4 — Transition Atlas

A compact top-M transition representation reduces draft latency enough to offset any acceptance decrease.

### H5 — cache-aware MoE prefetch

Draft or routing information can prefetch likely experts or metadata, but bandwidth contention may erase the gain.

### H6 — large-LLC portability

The same abstractions scale from desktop X3D cache domains to server CPUs with hundreds of megabytes or larger LLCs without changing public semantics.

## 11. Experiment ladder

### Stage 0 — simulation

Inputs:

- component working sets;
- measured or hypothetical cache, DRAM and GPU bandwidth;
- link latency and bandwidth;
- draft acceptance curves;
- concurrency and context length;
- thermal and queueing envelopes.

Outputs:

- candidate placements;
- predicted TTFT and TPOT;
- sensitivity analysis;
- break-even thresholds.

### Stage 1 — synthetic microbenchmarks

- cache warm/cold latency;
- local versus cross-cache-domain execution;
- vectorized low-rank projection;
- top-M lookup;
- pinned versus pageable transfer;
- single and double buffering;
- interference workloads;
- cache occupancy and memory-bandwidth telemetry.

### Stage 2 — component conformance

- draft logits/probabilities against a reference;
- quantization error;
- sampler identity;
- grammar state;
- rollback and cancellation;
- deterministic seeds.

### Stage 3 — exact end-to-end decode

Compare:

- autoregressive target;
- GPU-only MTP;
- GPU-only DSpark-like drafter;
- CPU draft / GPU target;
- ForgeCacheDraft cache-local;
- no pinning;
- cross-domain placement;
- speculation parked.

### Stage 4 — load and interference

Sweep concurrency, prompt/output lengths, cache pressure, background CPU traffic, thermal state and GPU load. Report p50, p95, p99, goodput, energy, acceptance, failure rate and migrations.

## 12. Required P0-T04 inventory extensions

P0-T04 remains observation-only. The future inventory must capture, where available:

- cache level, type, size, line size, associativity, ID and shared CPU list;
- package/core/thread topology;
- NUMA node CPU and memory maps;
- ISA flags including AVX2 and AVX-512 variants;
- `resctrl` capability flags and mounted-state metadata;
- huge-page capability and current state;
- PCIe topology without stable identifiers;
- available performance-counter tooling;
- installed GPU driver/runtime versions without changing them.

No benchmark is added to P0-T04.

## 13. Error handling and fail-closed behavior

- Missing topology data becomes `unknown`, never an inferred capability.
- Counter unavailability disables the dependent optimization path.
- Cross-domain migrations invalidate a measurement sample.
- Thermal or frequency instability may mark a result inconclusive.
- Any exactness mismatch disables the candidate implementation.
- Transfer or queueing overruns park speculation.
- Cache-control failure falls back to ordinary affinity and local allocation.
- An autotune record becomes invalid after any relevant environment-fingerprint change.
- A specialized path never removes the generic correctness fallback.

## 14. Testing strategy

- schema tests for topology and component descriptors;
- property tests for legal placement generation;
- adversarial tests for missing or contradictory topology;
- cost-model monotonicity and dimensional checks;
- deterministic plan serialization;
- differential exactness tests;
- cache-domain migration fault injection;
- transfer timeout and cancellation tests;
- replay of raw autotune samples;
- independent review of every promoted optimization.

## 15. Future implementation acceptance criteria

A cache-aware path may be promoted only if:

1. exactness tests pass;
2. the gain exceeds variability and a predefined minimum meaningful effect;
3. the result persists across repeated warm, cold and interference conditions;
4. no unbounded memory or queue growth appears;
5. the plan records its full environment fingerprint;
6. the generic fallback remains correct;
7. a fresh verifier reproduces the result;
8. the claim is scoped to measured hardware, model, precision, workload and SLO.

## 16. Research basis and evidence boundary

The design is motivated by:

- large LLC capacities in current desktop and server processors;
- Linux cache-domain discovery and optional `resctrl` control/monitoring;
- CPU-draft/GPU-target and inverse heterogeneous speculative-decoding research;
- DSpark-like parallel plus sequential draft structures;
- low-rank draft LM-head research;
- recent cache-resident LLM architecture research;
- reported integration risks under batching, disaggregation and quantized targets.

All reported external performance remains `external_unreproduced`. This specification contains no ForgeLLM benchmark result and does not select a winning implementation.

## 17. Phase and task relationship

- P0-T04 remains blocked pending one owner-authorized host and performs observation only.
- P0-T07 may proceed in parallel as design and research only.
- Hardware-dependent thresholds remain simulation variables, not accepted constants.
- P0-T05 still defines workload profiles before any benchmark claim.
- Implementation planning begins only after written-spec review and a separate reviewed implementation plan.

## 18. Spec self-review

- No implementation code is authorized.
- No product-specific conditional is part of the public architecture.
- No external speedup is treated as a ForgeLLM measurement.
- Exact and approximate modes are separated.
- P0-T04 is not bypassed.
- Hardware-dependent decisions remain falsifiable.
- Transition Atlas is explicitly experimental.
- The design is decomposable into independent future tasks.
- No `TODO`, `TBD`, placeholder or unresolved design contradiction remains.

## 19. Written-spec review gate

The durable decision is:

> ForgeLLM will use a capability graph plus empirical placement/autotuning as its general microarchitecture-aware optimization plane, and ForgeCacheDraft will be the first bounded cache-aware CPU/GPU case study. Transition Atlas remains an experimental representation whose value must be established by simulation, conformance and end-to-end measurement.

After the owner reviews this committed specification, the next action is to create a detailed implementation/research plan. No runtime implementation begins at that point without its own task authorization and review gates.
