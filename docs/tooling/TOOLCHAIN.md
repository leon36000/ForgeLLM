# ForgeLLM Toolchain

Versions are pinned in lockfiles or environment manifests when a phase begins. Do not blindly install “latest” into a shared lab machine. GPU drivers and firmware are lab-operator decisions.

## Tier 0 — source control and reproducible environments

| Tool | Purpose | Required in P0 |
|---|---|---:|
| Git | source history, worktrees, bisect | yes |
| Git LFS | large pointer-managed artifacts when approved | yes |
| GitHub CLI `gh` | issues, PRs, Actions, releases, attestations | GitHub path |
| GitLab CLI `glab` | issues, MRs, pipelines, releases | GitLab path |
| Docker or Podman | isolated build/benchmark environments | recommended |
| Dev Containers | repeatable agent environment | recommended |
| `jq`, `yq` | manifest processing | yes |
| `direnv` | local environment isolation without committed secrets | optional |
| `pre-commit` | deterministic local gates | yes |

## Tier 1 — languages and builds

### Rust

- `rustup`, stable toolchain and a committed `rust-toolchain.toml` when engine code begins;
- `rustfmt`, Clippy;
- `cargo-nextest` for test execution;
- `cargo-llvm-cov` for coverage;
- `cargo-audit` and `cargo-deny` for advisory/license/source policy;
- `cargo-fuzz`, Miri and Loom for unsafe/concurrent components;
- Criterion and `iai-callgrind` for microbenchmarks;
- Kani or Verus selectively for safety-critical invariants.

### C/C++ and native builds

- LLVM/Clang, LLD and a supported GCC toolchain;
- CMake and Ninja with presets;
- `ccache` or `sccache`;
- clang-format, clang-tidy;
- Address, Undefined, Thread and Leak sanitizers where supported;
- Valgrind, `perf`, heaptrack and LLVM coverage;
- GoogleTest or Catch2 for native contract tests.

### Python

- Python 3.11+ and `uv` or isolated virtual environments;
- Ruff, Pyright or mypy;
- pytest, Hypothesis and nox;
- `pip-audit` or OSV-Scanner;
- `build` and `twine` only for package release tasks.

## Tier 2 — accelerator development

### NVIDIA

Install only a driver/toolkit combination supported by the target GPU and selected libraries. Candidate tools:

- CUDA Toolkit and NVRTC;
- Nsight Systems and Nsight Compute;
- Compute Sanitizer;
- CUPTI;
- DCGM and `nvidia-smi`;
- NCCL and `nccl-tests`;
- CUTLASS/CuTe;
- TensorRT-LLM and FlashInfer as baselines/components;
- Triton and TileLang for research kernels.

### AMD

Install only from the official compatibility matrix for the target GPU/OS. Candidate tools:

- ROCm/HIP toolchain;
- rocprofiler-SDK and AMD Compute Profiler;
- `rocminfo` and AMD SMI;
- RCCL and RCCL tests;
- hipBLASLt and current ROCm library packages;
- Triton/TileLang/CubeCL paths when supported.

### CPU and system

- `lscpu`, `numactl`, hwloc, `dmidecode` where authorized;
- `perf`, `likwid` where supported, `bpftrace`;
- hugepage and NUMA inspection tools;
- ISA-specific compiler flags only after runtime capability detection;
- fio for storage and iperf3 for network baselines.

## Tier 3 — correctness and security

- differential tests against PyTorch and selected external engines;
- property/metamorphic tests;
- Z3 for schedule/layout constraint experiments;
- CBMC/Kani/Verus for scoped verification;
- CodeQL;
- Gitleaks and platform secret scanning/push protection;
- Trivy, Syft, Grype and Cosign;
- Dependabot or Renovate;
- `actionlint` and `zizmor` for GitHub Actions;
- SBOM generation and artifact provenance.

## Tier 4 — benchmarking and observability

- ForgeLLM JSON schemas and raw artifact store;
- Criterion, `hyperfine`, pytest-benchmark;
- vendor profilers and system traces;
- GenAI-Perf/AIPerf or engine-native clients after compatibility review;
- Prometheus, Grafana and OpenTelemetry;
- power/temperature telemetry from vendor tools;
- flame graphs and trace correlation IDs.

## Tier 5 — research management

- Zotero with Better BibTeX or another exportable reference manager;
- arXiv API, DBLP, Crossref, OpenAlex and Semantic Scholar for discovery/metadata;
- GitHub and GitLab APIs for dated repository snapshots;
- a local paper/artifact index whose records link back to `research/claims.yaml`.

## Installation strategy

1. Bootstrap only Tier 0 and P0 Python dependencies.
2. Inventory the machine.
3. Select a tested OS/driver/toolkit matrix.
4. Use containers for user-space libraries where practical.
5. Pin exact commits, package hashes and container digests.
6. Install one accelerator stack at a time and run smoke tests.
7. Record every environment change before benchmarking.
