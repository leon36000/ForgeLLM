# ForgeLLM Inference Landscape — 2026-08-12 snapshot

This is a decision-oriented map, not an exhaustive catalog. Version, activity and performance claims must be refreshed before implementation choices.

## 1. Serving engines

### vLLM

**Mechanisms to study:** PagedAttention/block manager, continuous batching, chunked prefill, prefix caching, speculative decoding, graph capture, distributed execution and the evolution of its Rust/C++/CUDA components.

**ForgeLLM use:** principal throughput-serving baseline and source of scheduler/KV design tests.

**Caution:** broad support and rapid change create dependency and version-comparison complexity. Project benchmarks must be reproduced on ForgeLLM hardware.

### SGLang

**Mechanisms to study:** RadixAttention, cache-aware scheduling, structured generation, speculative methods, distributed serving and tight integration with FlashInfer.

**ForgeLLM use:** baseline for prefix-heavy and structured workloads.

**Caution:** application/runtime co-design means comparisons must match workload semantics, not only raw token generation.

### llama.cpp / GGML

**Mechanisms to study:** compact C/C++ runtime, GGUF, broad quantization, CPU SIMD, multiple GPU backends and hybrid offload.

**ForgeLLM use:** local/CPU/quantized baseline, format compatibility reference and fallback adapter candidate.

**Caution:** avoid a line-by-line Rust port; isolate the capabilities actually needed.

### TensorRT-LLM

**Mechanisms to study:** NVIDIA-specialized kernels, engine building, in-flight batching, quantization, speculative decoding and disaggregated serving integrations.

**ForgeLLM use:** NVIDIA performance ceiling and correctness/performance comparison.

**Caution:** vendor-specific scope and rapidly evolving version constraints.

### MLC-LLM

**Mechanisms to study:** compiler-driven deployment, generated kernels and broad targets including GPU, mobile and web ecosystems.

**ForgeLLM use:** portability/compiler architecture reference.

**Caution:** distinguish compiler portability from best-in-class performance on every target.

### LMDeploy and KTransformers

**Mechanisms to study:** persistent batching/quantization and heterogeneous CPU-GPU execution, especially MoE/offload.

**ForgeLLM use:** oversized-model and heterogeneous baseline candidates.

**Caution:** author-reported speedups require exact reproduction and workload matching.

## 2. Runtime and data movement

### NVIDIA Dynamo

Rust-heavy orchestration and disaggregated serving concepts are directly relevant to the control plane. Study router/KV-aware behavior, engine boundaries and operational model without assuming NVIDIA-only architecture should define ForgeLLM semantics.

### NIXL, NCCL, RCCL and UCX

These represent different layers of movement and collectives. ForgeLLM should select transports by operation and topology rather than forcing one library to handle every path. Transfer microbenchmarks precede distributed scheduling decisions.

### DeepEP

Study high-throughput and low-latency expert communication modes, buffer ownership and overlap. Treat it as a specialized MoE component, not a generic transport.

## 3. Kernel stacks

### CUTLASS and CuTe

Primary NVIDIA building blocks for GEMM, attention and architecture-specific specialization. High value for production kernels and as a reference for layout/type systems.

### Triton

High-value kernel research and autotuning environment across NVIDIA and AMD paths. Evaluate compile time, generated code, unsupported features and performance variance by architecture.

### FlashInfer

Inference-focused attention, GEMM and MoE components. Evaluate API boundaries, backend selection, workspace planning and compatibility with ForgeLLM's execution-plan model.

### ROCm libraries and Composable Kernel lineage

Primary AMD path. Track the current canonical ROCm library locations rather than obsolete standalone repositories. Separate RDNA and CDNA assumptions.

### TileLang and TileRT

Emerging tile-level DSL/runtime concepts merit prototypes, especially low-latency and formal/constraint-assisted scheduling ideas. They remain experimental until stability and performance are measured.

## 4. Rust ecosystem

### mistral.rs

Closest direct study for a Rust-native inference runtime with batching, quantization and accelerator support. Inspect ownership boundaries, kernel integration, scheduling and gaps across vendors.

### Candle

Useful lightweight tensor/model framework and reference implementation substrate. Evaluate it for importer/reference paths, not automatically as the production scheduler.

### Burn and CubeCL

CubeCL's one-kernel/multiple-backend model is strategically relevant. Burn demonstrates the surrounding Rust ML ecosystem. Both require version pinning and maturity assessment before production dependence.

### Text Generation Inference

Valuable historical Rust/Python/gRPC serving architecture. Its maintenance direction means it should be studied for lessons and components rather than chosen automatically as the long-term base.

## 5. Research mechanisms to prototype

- fixed-size KV paging and copy-on-write;
- prefix-tree/radix cache indexing;
- chunked prefill and decode-maximal batching;
- prefill/decode disaggregation with topology-aware placement;
- tiered KV/weight storage across VRAM, pinned RAM, DRAM, NVMe and remote memory;
- intra-device overlap and nano-batching;
- attention kernels specialized by phase and hardware;
- per-layer/mixed quantization;
- model-based, feature-based and prompt-lookup speculation;
- MoE expert routing and communication overlap;
- hardware-fingerprinted kernel autotuning.

## 6. Architecture conclusion for Phase 0

No existing project combines all desired properties with proven superiority on the owner's heterogeneous fleet. ForgeLLM should therefore begin as a control plane, conformance framework and backend portfolio that can wrap and measure existing engines, then replace components only where evidence supports it.
