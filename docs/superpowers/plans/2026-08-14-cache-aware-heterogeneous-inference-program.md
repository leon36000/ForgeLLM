# ForgeLLM Cache-Aware Heterogeneous Inference Program Plan

**Date:** 2026-08-14  
**Status:** program decomposition derived from the owner-approved specification  
**Canonical specification:** `docs/superpowers/specs/2026-08-13-cache-aware-heterogeneous-inference-design.md`  
**Current canonical state:** S-0005  
**Current execution gate:** P0-T04 remains blocked on owner designation of one inventory host

## Purpose

This document decomposes the approved cache-aware heterogeneous inference design into independently reviewable work packages. It prevents the broad design from becoming one unbounded implementation task and preserves the existing inventory and workload gates.

No work package may infer hardware facts from product names, promote an external benchmark to ForgeLLM evidence, or remove the generic correctness fallback.

## Program invariants

1. Portable semantics precede specialization.
2. Exactness gates precede performance gates.
3. Synthetic simulation may proceed before P0-T04; hardware calibration may not.
4. Hardware-dependent constants remain inputs until measured on an authorized host.
5. Every promoted plan records an immutable environment fingerprint.
6. Cache residency is best-effort locality, never a correctness assumption.
7. Transition Atlas remains experimental until it wins a scoped exactness-and-performance comparison.
8. Runtime or kernel implementation requires a separate authorized task packet.

## Work-package graph

```text
CA-01  Synthetic topology + component descriptors
   │
   ▼
CA-02  Deterministic cost model + placement simulator
   │                         ┌──────────── P0-T04 inventory extension
   │                         │
   ├──────────────┐          ▼
   ▼              ▼       CA-05  Hardware calibration microbenchmarks
CA-03          CA-04          │
Exact draft    Transition     ▼
semantics      Atlas       CA-06  Empirical autotuning + plan database
   │              │          │
   └──────┬───────┘          │
          ▼                  ▼
       CA-07  ForgeCacheDraft runtime integration plan
          │
          ▼
       CA-08  Production promotion and multi-profile validation
```

CA-01 and CA-02 are combined in the first executable implementation plan because they share schemas, deterministic units and synthetic fixtures. All later packages remain separate.

## CA-01 — Synthetic topology and component descriptors

### Goal

Define machine-readable, product-neutral schemas and immutable Python models for compute, memory and link domains plus component working-set/exactness descriptors.

### Outputs

- JSON Schemas with `additionalProperties: false`;
- semantic validation of cross-references and capacities;
- deterministic topology and component fingerprints;
- synthetic fixtures only;
- no host probing.

### Exit gate

Valid synthetic examples parse into immutable models; malformed references, duplicate IDs, impossible capacities, unknown capabilities and path escapes fail closed.

## CA-02 — Deterministic cost model and placement simulator

### Goal

Generate legal implementation/placement candidates, compute deterministic integer-nanosecond cost breakdowns and emit an explainable selected plan.

### Outputs

- lower-bound transfer and compute estimates;
- legality rejection reasons;
- stable candidate ordering and plan serialization;
- CLI for synthetic scenarios;
- no claim of predictive accuracy on real hardware.

### Exit gate

Property/adversarial tests prove monotonicity, deterministic ranking, fallback preservation and rejection of unsupported placements. A synthetic cache-draft example produces the same result across repeated runs.

## CA-03 — Exact speculative-decoding reference semantics

### Goal

Specify and test proposal probabilities, accept/reject correction, KV/state commit boundaries, cancellation and rollback independently of CPU/GPU placement.

### Dependencies

CA-01/CA-02 models; selected target/draft reference models from later workload-profile work.

### Exit gate

Greedy and sampled exact-mode outputs match the non-speculative target within declared numerical/tie budgets. Quantized draft errors may alter acceptance only.

## CA-04 — Transition Atlas research prototype

### Goal

Compare a full low-rank head, top-M transition table, top-M plus residual and dynamic vocabulary truncation in a synthetic/reference environment.

### Dependencies

CA-02 simulator and CA-03 exactness oracle.

### Exit gate

The work produces acceptance/latency/memory tradeoff curves and a clear adopt/reject/continue decision. No runtime integration occurs in this package.

## P0-T04 extension — observed cache/NUMA capability inventory

### Goal

Extend the observation-only inventory to capture cache IDs, sharing CPU sets, NUMA relations, ISA flags, huge-page state, `resctrl` capabilities and available counter tooling without running performance tests.

### Dependency

Owner-designated host and P0-T04 authorization.

### Exit gate

One publication-safe observed topology validates against the same topology semantics used by CA-01, with unknown fields preserved rather than guessed.

## CA-05 — Hardware calibration microbenchmarks

### Goal

Measure primitive rates needed by the cost model: local/cross-domain memory access, low-rank kernels, top-M lookup, transfer latency/bandwidth, synchronization, cache pressure and interference.

### Dependencies

P0-T04 reviewed inventory and P0-T05 workload/SLO definition.

### Exit gate

Raw samples, telemetry, environment manifests and statistical summaries pass the benchmark schema and independent replay.

## CA-06 — Empirical autotuning and plan database

### Goal

Combine analytical screening with bounded measurements and persist plans keyed by immutable environment fingerprints.

### Dependencies

CA-02 and CA-05.

### Exit gate

Records invalidate correctly after relevant environment changes, replay raw samples, retain rejected alternatives and never remove the generic fallback.

## CA-07 — ForgeCacheDraft runtime integration plan

### Goal

Design the Rust control-plane interfaces, C ABI/backend boundary, asynchronous buffers, state machine, cancellation and telemetry required to run the exact cache-domain sidecar with a GPU target.

### Dependencies

CA-03 exactness, CA-05 calibration and CA-06 plan selection.

### Exit gate

A separately approved implementation plan defines crates, ABI structs, ownership, state transitions, failure handling, tests and benchmark gates. No implementation is authorized by this program plan alone.

## CA-08 — Production promotion and multi-profile validation

### Goal

Validate cache-aware paths under concurrency, interference, thermal variation, multiple models, precisions and hardware families.

### Dependencies

P0-T05 profiles, Phase 1 baselines and CA-07 implementation.

### Exit gate

A promoted path has reproduced exactness, statistically meaningful scoped gain, bounded resource growth, a generic fallback and an independent verifier verdict.

## First executable plan

The first executable plan is:

`docs/superpowers/plans/2026-08-14-cache-aware-topology-placement-simulator.md`

It implements CA-01 and CA-02 only. It uses synthetic data, Python 3.11, JSON Schema Draft 2020-12 and existing project dependencies. It does not probe hardware, execute models, change drivers, register runners or implement the ForgeLLM runtime.

## Program stopping rules

Pause the program and open an ADR/task revision when:

- a proposed optimization changes target-model semantics;
- a new dependency or public interchange format is introduced;
- a product-specific condition leaks into public APIs;
- the simulator requires hardware facts not available from P0-T04;
- the analytical model cannot be distinguished from alternatives by a bounded experiment;
- any work would bypass P0-T05 workload/SLO definition;
- an optimization cannot retain a correct generic fallback.
