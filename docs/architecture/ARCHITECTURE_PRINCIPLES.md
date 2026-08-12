# ForgeLLM Architecture Principles

## 1. Optimize the system, not the syntax

Language choice does not replace memory traffic analysis, kernel quality, scheduling or topology. Rust is selected primarily for lifecycle and concurrency safety, not because it makes GEMM inherently faster.

## 2. Stable narrow boundaries

The plugin ABI exposes coarse operations and execution plans, not one FFI call per tiny tensor operation. Ownership, stream/event lifetime, synchronization, errors and version negotiation are explicit.

## 3. Specialize without fragmenting semantics

A shared operation model defines semantics. Backends may use different layouts, tiling, fusion and precision strategies, but must satisfy common conformance tests and declared numerical budgets.

## 4. Reference before optimization

The CPU reference path favors clarity and deterministic behavior. It is the oracle for GPU and quantized paths. A backend may not redefine semantics to match its bug.

## 5. Separate prefill and decode reasoning

Prefill and decode have different arithmetic intensity, batching, latency and communication characteristics. Plans, kernels and scheduling policies are selected independently and composed deliberately.

## 6. Treat memory as a hierarchy

Weights, activations, workspaces and KV cache have separate lifetimes. VRAM/HBM, pinned memory, DRAM, NVMe and remote memory are explicit tiers with measured transfer costs and eviction policy.

## 7. Measure topology

Do not infer peer-to-peer, NUMA, PCIe, NVLink, Infinity Fabric or network behavior from product names. Probe the actual host and record the topology with every distributed experiment.

## 8. Portfolio plus autotuning

Keep multiple correct implementations for important operations. Select by hardware, dimensions, dtype, layout, batch, context and phase. Autotuning results are cached against immutable environment fingerprints.

## 9. No allocation in steady-state hot loops

After warm-up, decode should use planned arenas, page pools and reusable metadata. Any unavoidable allocation is measured and justified.

## 10. Backpressure and admission control are correctness features

A system that overcommits memory or violates latency contracts under load is not correct at the service level. Scheduling includes quotas, deadlines, cancellation and predictable degradation.

## 11. Failure is part of the interface

GPU errors, worker death, network partition, OOM, invalid model metadata and corrupted artifacts have typed failure paths, cleanup guarantees and observable state transitions.

## 12. Reproducibility is a build output

Every release and benchmark ties source commits, toolchains, containers, model revisions, data, commands and hashes together. Documentation without executable validation is insufficient.
