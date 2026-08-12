# ForgeLLM Roadmap and Phase Gates

## P0 — Project operating system

**Goal:** make project state, research, agent work and evidence durable and auditable.

**Deliverables:** charter, ADRs, state registries, mobile context, agent prompts, catalogs, schemas, validators, CI and repository-security plan.

**Exit gate:** `make ci` passes; private repository initialized; mobile context installed; no unresolved structural validation errors.

## P1 — Reproducibility laboratory and baselines

**Goal:** define what “powerful” and “optimized” mean on the owner's real workloads.

**Tasks:**

1. immutable hardware/topology inventory;
2. OS/driver/toolchain compatibility matrix;
3. model and dataset/license inventory;
4. workload profiles and objective functions;
5. common correctness oracle;
6. baseline harness adapters for at least vLLM, llama.cpp and one of SGLang/TensorRT-LLM;
7. raw baseline results with independent review;
8. microbenchmarks for memory bandwidth, PCIe/P2P, network, collectives, storage and CPU SIMD.

**Exit gate:** one benchmark report can be reproduced from a clean environment with matching hashes and no unresolved correctness discrepancy.

## P2 — Reference core and minimal IR

**Goal:** execute a small supported decoder-only model correctly on CPU with explicit semantics.

**Tasks:**

- immutable model manifest and tokenizer path;
- tensor/layout/dtype model;
- minimal operation IR;
- deterministic CPU reference kernels;
- weight loading and validation;
- autoregressive decode and sampling reference;
- property/differential tests against PyTorch;
- memory-plan trace and error model.

**Exit gate:** selected model logits/tokens match the reference within declared budgets across deterministic test vectors; sanitizers/fuzz targets pass.

## P3 — Plugin ABI and first NVIDIA backend

**Goal:** prove the Rust/native boundary and execute the P2 model on the first NVIDIA target.

**Tasks:** versioned C ABI, safe Rust wrapper, device/stream/event lifecycle, coarse execution plans, initial CUDA/CUTLASS kernels or library adapters, conformance suite, profiler traces and FFI-overhead study.

**Exit gate:** GPU path is correct, leak/race checks pass, and end-to-end performance is measured against P1 baselines without claiming universal superiority.

## P4 — First AMD backend and portable experiment

**Goal:** validate shared semantics across vendors and one portable DSL path.

**Tasks:** HIP/ROCm backend, RDNA/CDNA assumptions, RCCL where needed, portable CubeCL/Triton/TileLang prototype, cross-backend differential tests and build matrix.

**Exit gate:** the same model/IR passes on NVIDIA, AMD and CPU; unsupported differences are explicit; portable-path performance is measured.

## P5 — KV cache and service scheduler

**Goal:** add production-relevant request concurrency.

**Tasks:** page pool, copy-on-write, prefix index, continuous batching, chunked prefill, cancellation, priorities, admission control, structured output hooks and observability.

**Exit gate:** deterministic scheduler simulations, stress tests and matched serving benchmarks meet declared profile constraints.

## P6 — Distributed and heterogeneous execution

**Goal:** scale beyond one device while respecting topology.

**Tasks:** tensor/pipeline/expert/request parallelism, transport abstraction, NIXL/UCX/NCCL/RCCL experiments, prefill/decode disaggregation, hierarchical KV/weight storage, fault injection and recovery.

**Exit gate:** distributed correctness, failure recovery and net goodput gains are demonstrated on the actual topology; transfer costs are included.

## P7 — Advanced optimization and production hardening

**Goal:** build the measured kernel portfolio and operational system.

**Tasks:** autotuning database, mixed/per-layer quantization, speculative decoding, graph capture, fusion, power/thermal tuning, multi-tenant isolation, release provenance, security audit and long-duration soak tests.

**Exit gate:** profile-specific release criteria are met, artifacts are reproducible and signed, and claims are independently reviewed.

## Gate rule

A later phase may run a small disposable experiment to reduce risk, but its production implementation cannot bypass the preceding phase’s correctness and evidence gate.
