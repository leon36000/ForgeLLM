# ForgeLLM Current State

- **State ID:** S-0006
- **Updated:** 2026-08-14
- **Phase:** P0
- **Milestone:** P0-M5 — synthetic cache-aware placement simulator verified
- **Overall status:** P0-T07 is complete with synthetic-only evidence; P0-T04 remains blocked on designation of one owner-authorized host; CA-03 exact speculative-decoding semantics is owner-authorized for subagent-driven execution but has not yet begun implementation
- **Authorized next work:** CA-03 specification, implementation plan and bounded task packet; P0-T04 may proceed independently after host designation
- **State anchor:** the Git commit containing this file

## Objective

Define and verify exact speculative-decoding reference semantics independently of hardware placement while preserving P0-T04 and P0-T05 as the gates for observed hardware and workload-dependent claims.

## Canonical repository and protection

- Repository: `leon36000/ForgeLLM`.
- Visibility: public under ADR-0003.
- Default branch: `main`.
- `main` is protected by active ruleset `FLLM`.
- P0-T07 implementation merge: `b0f3f241537b50de0dd3c0cb7bc2e6bf274a7034`.
- Pull request: #20.
- No self-hosted runner, hardware probe, model execution or accelerator kernel was introduced by P0-T07.

## P0-T07 completion

P0-T07 delivered a deterministic synthetic-only topology and placement simulator.

### Delivered capabilities

- strict Draft 2020-12 schemas for topology, component profiles and placement results;
- immutable product-neutral compute, memory, link, component and implementation models;
- duplicate-key rejection and repository/artifact path confinement;
- deterministic integer-only byte/rate/nanosecond cost accounting;
- exhaustive legal candidate generation with stable rejection codes;
- deterministic selection retaining a legal generic fallback;
- atomic JSON output under `artifacts/`;
- a canonical product-neutral cache-draft example;
- focused, adversarial and CLI tests;
- hosted execution of the canonical synthetic scenario.

### Final pull-request evidence

Final reviewed head: `99c1c1488f622a6d4290e21a17ff313a1c3568c6`.

- Phase 0 run `31784275654`, job `94716606110`: success.
- Complete suite: **102 passed**.
- Canonical `make simulate-cache-draft`: success.
- CodeQL run `31784275655`, job `94716597658`: success.
- Dependency Review run `31784275656`: skipped by policy and not treated as executed evidence.
- Fresh-context review verdict: `ACCEPT`.

### Post-merge evidence

On `main` commit `b0f3f241537b50de0dd3c0cb7bc2e6bf274a7034`:

- Phase 0 run `31784610893`, job `94717633943`: success.
- CodeQL run `31784610881`, job `94717633957`: success.

A successful CodeQL workflow proves execution and upload, not zero alerts; alert details are not asserted here.

### Synthetic evidence hashes

```text
6738d9596a2a9b9224a68e071a94463cdcbe7cff10a7cd30c4de29cd3381aa2f  examples/simulations/synthetic-cache-draft-topology.json
3aa6dcb2504aebee7c3db236abdd59867efe25296420bdc7e9ba1883061f4cb5  examples/simulations/synthetic-cache-draft-components.json
e5eb661bb48eca62b778714670000f963922ca459cb8590b3717150993a921ae  artifacts/simulations/synthetic-cache-draft-result.json
```

## Evidence boundary

P0-T07 evidence is `synthetic_only`. Its predicted nanoseconds are analytical fixture outputs, not measurements. P0-T07 does not establish:

- inference correctness;
- model or tokenizer support;
- hardware performance or energy efficiency;
- CPU cache residency on any real processor;
- GPU compatibility;
- runtime, ABI, scheduler or kernel readiness;
- production suitability.

Unsupported cost terms remain explicit: acceptance-rate feedback, cache-miss penalties, energy, interference, multi-hop routing, overlap and queueing.

## Owner authorization: CA-03

On 2026-08-14 the owner authorized `CA-03 / subagent-driven`.

CA-03 is limited to exact speculative-decoding reference semantics:

- target and proposal distributions;
- acceptance/rejection correction;
- greedy reference behavior;
- exact probability-law verification on finite synthetic models;
- KV and auxiliary-state commit/rollback boundaries;
- cancellation, EOS and token-budget behavior;
- deterministic test traces.

CA-03 must not introduce model downloads, real inference, hardware-dependent placement, runtime or accelerator code. A schema-valid task packet and reviewed implementation plan precede code.

## P0-T04 remains active and blocked

Task packet: `tasks/open/P0-T04-first-hardware-inventory.yaml`.

P0-T04 remains observation-only and blocked on one owner input: a project-safe host label and execution mode. CA-03 may proceed without bypassing P0-T04 because it uses finite synthetic reference models only.

## Forbidden next steps

- no hardware calibration or benchmark before P0-T04 and P0-T05;
- no model download or production inference;
- no Rust runtime, C ABI, GPU backend or kernel under CA-03;
- no claim that exact distributional semantics imply performance;
- no Transition Atlas implementation before CA-03 provides an exact oracle;
- no approximate quality-changing policy under the exact-mode task.
