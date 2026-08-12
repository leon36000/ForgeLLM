# ForgeLLM Deep Research Program

## Purpose

The Phase 0 catalog is a verified discovery snapshot, not a claim that every codebase and paper has already received line-by-line review. This program turns the catalog into bounded tasks that agents can execute and independent reviewers can audit.

## Workstream A — ten primary open-source stacks

Each primary review pins an immutable commit and inspects implementation, tests, CI, benchmark harness, issues affecting ForgeLLM, license and release process. The ten initial stacks are selected for architectural coverage rather than a permanent popularity ranking.

| Order | Source | Decision question | Mandatory implementation areas |
|---:|---|---|---|
| 1 | PyTorch | Which semantics and operator behavior form the initial numerical oracle? | dispatcher, allocator, ATen, compile/custom-op path, CUDA/HIP integration, tests |
| 2 | Transformers | What exact model/config/tokenizer/generation contract must ForgeLLM import first? | model registry, generation loop, cache APIs, safetensors/tokenizers, tests |
| 3 | vLLM | Which scheduler and KV abstractions deserve direct experiments? | scheduler, block manager, attention backends, worker/runtime boundaries, benchmarks |
| 4 | llama.cpp | Which GGUF, CPU, quantization and offload capabilities should be wrapped or independently reimplemented? | GGML graph/tensors, loaders, quantizers, SIMD, backends, tests |
| 5 | SGLang | How should prefix reuse and structured workloads alter ForgeLLM profiles? | radix cache, scheduler, constrained decoding, speculation, distributed path |
| 6 | DeepSpeed | Which distributed/runtime concepts remain relevant without adopting the entire stack? | inference engine, communication, kernels, quantization, build/test strategy |
| 7 | TensorRT-LLM | What is the NVIDIA-specialized comparison ceiling for selected profiles? | engine build/runtime, batching, kernels, quantization, KV/disaggregation |
| 8 | MLC-LLM | Which compiler/runtime boundaries improve portability without hiding hardware-specific tuning? | IR, code generation, runtime, model compilation, target abstraction |
| 9 | CUTLASS/CuTe | Which layout, GEMM and attention abstractions should shape the first NVIDIA backend? | types/layouts, collective builders, architecture specializations, examples/tests |
| 10 | DeepEP | When does specialized MoE communication justify a dedicated component? | dispatch/combine, low-latency/high-throughput modes, buffers, overlap, topology |

## Workstream B — specialist repositories

Dynamo, NIXL, Triton, FlashInfer, KTransformers, mistral.rs, Candle, CubeCL, Burn, TileLang and TGI receive targeted reviews only after a task names the mechanism being evaluated. This prevents broad ecosystem browsing from replacing experiments.

## Workstream C — scientific synthesis

Paper reviews are grouped into decision-relevant families:

1. scheduler and serving: Orca, PagedAttention, SGLang, SARATHI, NanoFlow;
2. prefill/decode disaggregation and cache movement: DistServe, Splitwise, Mooncake;
3. memory hierarchy and paging: vAttention, Jenga, eLLM, SolidAttention, PagedWeight;
4. attention and inference kernels: FlashAttention 1–3 and FlashInfer;
5. quantization: GPTQ, SmoothQuant, AWQ, QServe, SpinQuant and Marlin;
6. speculation: speculative decoding/sampling, Medusa and EAGLE 1–2.

Each synthesis must compare assumptions, baselines, hardware, quality/correctness gates, artifacts, limitations and the smallest discriminating ForgeLLM experiment.

## Mandatory repository-review output

A completed review adds:

- inspected commit, observed date and license verification;
- architecture map and component boundaries;
- relevant data/memory/ownership flows;
- build and dependency graph;
- test and benchmark quality assessment;
- representative issues or failure modes;
- reusable interfaces/components and clean-room concerns;
- claim updates and one bounded experiment or explicit “no action” decision;
- independent reviewer sign-off.

## Mandatory paper-review output

A completed review adds:

- canonical identity, venue/status and artifact links;
- problem boundary, mechanism and assumptions;
- exact model/hardware/software/workload conditions;
- baseline validity and statistical method;
- correctness or quality evaluation;
- ablations and threats to validity;
- claimed result recorded without promotional compression;
- reproduction deviations and experiment task;
- independent reviewer sign-off.

## Adversarial review pass

For every source, agents search official issues, regressions, unsupported paths, numerical discrepancies, memory failures, benchmark caveats and failed reproductions. Absence of found counter-evidence is recorded as a search result, not proof of absence.

## Completion and stopping rules

A review closes only when its decision question is answerable and every material claim has a primary-source pointer. Stop reading when remaining uncertainty is better resolved by experiment. Additional sources enter the queue; they do not silently expand the active task.
