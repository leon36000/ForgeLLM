# ForgeLLM Project Charter

**Charter version:** 0.1.0  
**Accepted on:** 2026-08-12  
**Current lifecycle:** Phase 0 bootstrap

## 1. Purpose

ForgeLLM exists to design and implement a heterogeneous LLM inference engine whose correctness, performance, safety, portability and reproducibility can be independently verified.

The project is not defined by a single language, vendor or existing engine. It is defined by measurable outcomes on declared workloads and by disciplined engineering boundaries.

## 2. Product profiles

ForgeLLM will eventually support several profiles. They are optimized separately because one configuration cannot maximize all objectives.

1. **Interactive local:** low time-to-first-token and low time-per-output-token at low concurrency.
2. **Throughput server:** high goodput under explicit latency service-level objectives.
3. **Long context:** bounded memory growth, prefix reuse and controlled TTFT.
4. **Oversized model:** capacity through quantization and hierarchical offload.
5. **Heterogeneous cluster:** topology-aware work placement across CPU, NVIDIA, AMD, memory and storage.

Phase 1 must define concrete workloads and success functions for each profile before ForgeLLM claims superiority.

## 3. In-scope capabilities

- model import and immutable model revision tracking;
- reference CPU execution path;
- intermediate representation and execution planning;
- versioned plugin ABI;
- NVIDIA, AMD, CPU and portable experimental backends;
- quantized and mixed-precision execution;
- paged and hierarchical KV-cache management;
- continuous batching, chunked prefill, prefix reuse and scheduling;
- speculative decoding and structured output when validated;
- tensor, pipeline, expert and request-level parallelism;
- prefill/decode disaggregation when topology makes it beneficial;
- observability, profiling, reproducible benchmarks and fault recovery;
- compatibility layers for selected existing model and serving formats.

## 4. Out of scope until explicitly promoted

- training a foundation model;
- inventing a new accelerator ISA;
- supporting every architecture or model family in the first release;
- guaranteeing identical performance across vendors;
- replacing mature external libraries without a measured reason;
- using an agent conversation as the only project record;
- accepting unverifiable benchmark claims;
- driver or firmware automation across arbitrary production machines.

## 5. Architectural commitments

- Rust is the default control-plane and runtime language.
- C ABI is the stable cross-language plugin boundary.
- GPU kernels use target-native technologies where they win.
- Python is a first-class research and tooling language but is excluded from the token hot path by default.
- Unsafe code is isolated and reviewed against explicit invariants.
- The first executable engine path is a correctness reference, not a performance showcase.
- Existing engines are baselines and potential adapters, not enemies to rewrite blindly.

These commitments may change only through an accepted ADR supported by new evidence.

## 6. Definition of evidence

A statement is stored as one of:

- **fact:** directly supported by a cited primary source;
- **inference:** reasoned conclusion from cited facts;
- **hypothesis:** falsifiable proposition awaiting experiment;
- **decision:** chosen course with alternatives and consequences;
- **measurement:** observation from a declared protocol and environment.

External performance results are not ForgeLLM measurements.

## 7. Success criteria

ForgeLLM succeeds when it can demonstrate, for declared profiles:

- correct model outputs within documented numerical budgets;
- no unbounded resource or lifecycle defects under stress;
- competitive or superior performance against named baselines;
- reproducibility on clean machines using pinned sources and manifests;
- explainable scheduling and placement decisions;
- bounded unsafe/FFI surface with contract tests;
- recovery behavior under GPU, network and process faults;
- maintainability by human and agent contributors using small verified changes.

## 8. Governance

The owner approves charter changes, security-sensitive operations, repository visibility, licensing and release policy. Agents may propose but cannot silently enact those choices.

Architecture changes require ADRs. Performance claims require experiment records. Work starts from an issue or task packet and ends with state and handoff updates.

## 9. Phase gates

### Phase 0 exit

- source-of-truth files exist and validate;
- agent instructions are loaded by target tools;
- research and claim catalogs are machine-readable;
- benchmark schema and examples validate;
- CI validates repository state;
- private repository and protected workflow plan are documented.

### Phase 1 exit

- hardware inventory captured;
- workload profiles frozen for the first benchmark cycle;
- at least three external engines benchmarked under one harness;
- correctness oracle and model revisions pinned;
- raw results reviewed independently.

Later phase gates are refined only after the preceding phase supplies evidence.
