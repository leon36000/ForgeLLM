# ForgeLLM Benchmark Standard

## 1. Principle

A benchmark is an experiment, not a screenshot. Its result must be reproducible, comparable and scoped. Best-run numbers, undocumented defaults and incomparable baselines are rejected.

## 2. Required identity

Every experiment has:

- experiment ID and related claim ID;
- UTC timestamp;
- baseline and candidate source commits;
- confirmation that measured worktrees were clean;
- environment fingerprint;
- operator and independent reviewer roles;
- result status: valid, invalid, inconclusive or superseded.

## 3. Hardware manifest

Record for every node:

- CPU model, sockets, cores/threads, ISA flags and NUMA layout;
- memory capacity, channels when known, hugepage state;
- accelerator vendor, model, architecture, memory, UUID or redacted stable fingerprint;
- PCIe/NVLink/Infinity Fabric/P2P topology;
- network adapters, negotiated link and transport;
- storage devices/filesystem for offload experiments;
- power mode, clock policy, temperature and throttling indicators when relevant.

Do not infer topology from product names.

## 4. Software manifest

Record OS, kernel, container digest, driver, firmware where accessible, CUDA/ROCm/runtime, compiler, Python/Rust/C++ toolchains, engine and dependency revisions, environment variables that affect execution, and launch commands.

## 5. Model and workload manifest

- canonical model ID and immutable revision/hash;
- architecture and tokenizer revision;
- weight format, dtype, quantization and calibration artifact;
- context/window settings;
- dataset or generated workload with hash;
- prompt and output length distributions;
- batch, concurrency, arrival process and scheduler policy;
- sampling parameters, seeds and structured-output constraints;
- warm-up and measured repetitions;
- cache-cold/warm state;
- prefill/decode or end-to-end phase.

## 6. Correctness gate

Before performance:

- validate model loading and metadata;
- compare deterministic logits/tokens or operation outputs to the oracle;
- record absolute/relative/ULP error as appropriate;
- run selected edge cases;
- record any quality benchmark required by quantization or approximation.

A failed correctness gate invalidates the performance conclusion.

## 7. Measurement method

- Warm up until the selected stability criterion is met.
- Use at least five measured repetitions unless the protocol justifies more or fewer.
- Preserve every sample, including failures; mark exclusions with reasons.
- Interleave baseline/candidate when system drift is material.
- Measure wall-clock at the correct boundary and use synchronized device timing for kernels.
- Avoid timing model download, compilation or cache creation unless that is the declared metric.
- Capture profiler traces for mechanism claims.

## 8. Metrics

At minimum for serving where applicable:

- TTFT median and p95/p99;
- TPOT or inter-token latency median and p95/p99;
- end-to-end latency;
- request goodput under declared SLOs;
- input/output/total tokens per second;
- concurrency and failure rate;
- peak and steady memory;
- cache hit/eviction rates;
- power/energy and thermal state when the objective includes efficiency.

Kernel benchmarks additionally report shapes, layout, dtype, arithmetic intensity assumptions, occupancy/resource data where available, and end-to-end contribution.

## 9. Statistics

Report count, median, mean, standard deviation, min/max and percentile metrics appropriate to the workload. Use confidence intervals or bootstrap intervals for material comparisons. State effect size and variability; do not treat a sub-noise difference as a win.

## 10. Comparability checklist

A comparison is valid only if baseline and candidate match or explicitly control:

- model/revision and output quality;
- precision/quantization;
- prompt/output workload;
- hardware allocation and topology;
- scheduler and cache state;
- software versions and compile flags;
- power/thermal policy;
- metric boundary and repetition method.

## 11. Artifacts

Store:

- machine-readable result JSON;
- raw sample data;
- stdout/stderr logs;
- environment/inventory manifests;
- profiler traces when used;
- model/workload hashes;
- scripts/commands;
- SHA-256 manifest.

Large proprietary model weights are not committed; store immutable references and access instructions consistent with their license.

## 12. Claim language

Use: “On hardware H, software stack S, model M, workload W and protocol P, candidate C changed metric X by Y relative to baseline B.”

Do not use: “ForgeLLM is 2× faster” without a scoped qualifier.
