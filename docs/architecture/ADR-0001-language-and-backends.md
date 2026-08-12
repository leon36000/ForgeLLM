# ADR-0001: Rust control plane with native accelerator backends

- **Status:** accepted
- **Date:** 2026-08-12
- **Owners:** ForgeLLM project owner; architecture reviewer role
- **Related claims:** CLM-001, CLM-002, CLM-003

## Context

ForgeLLM must coordinate asynchronous requests, long-lived resource ownership, KV pages, streams, events, multiple devices and network transfers while also using vendor-native kernels. A single-language rewrite would either abandon mature accelerator ecosystems or put the entire service runtime in a less memory-safe language.

## Decision

Use Rust for the control plane, scheduler, lifecycle, service layer, topology model, memory metadata and safe abstractions. Use a versioned C ABI for coarse plugin operations. Implement or integrate target-native kernels in CUDA C++/CuTe/CUTLASS for NVIDIA, HIP C++/ROCm libraries for AMD, CPU SIMD for reference and selected hot paths, and portable DSLs as measured experimental backends. Keep Python outside steady-state per-token execution unless a benchmark proves a specific exception.

## Alternatives considered

### All C++

Strong accelerator ecosystem and fewer FFI boundaries, but a larger unsafe lifecycle/concurrency surface in the service runtime.

### All Rust

Excellent ownership model, but accelerator coverage and the maturity of specialized kernels are not uniformly sufficient. It would encourage avoidable reimplementation.

### Python-first runtime

Excellent experimentation velocity and ecosystem compatibility, but additional interpreter/runtime overhead and weaker ownership control in the core serving loop.

### C-only engine

Stable ABI and portability, but poor fit for template-heavy GPU libraries and a high manual memory-management burden.

## Consequences

- The ABI and plugin lifecycle become critical design artifacts.
- FFI crossings must be coarse and amortized.
- Rust `unsafe` wrappers need explicit safety contracts and fuzz/contract tests.
- Build tooling spans Rust, C/C++, CUDA/HIP and Python.
- Portable kernels are not assumed equivalent to native kernels.
- Existing engines may be wrapped as baselines during gradual replacement.

## Safety and correctness invariants

- Opaque handles have one documented owner and destructor.
- No host object is freed while referenced by an in-flight device operation.
- Stream/event synchronization is explicit in the ABI.
- Structs include size and ABI version fields.
- Error codes are stable and never represented by undefined behavior.
- Backend-specific numerical behavior is tested against common semantics.

## Evidence required for review

Phase 2 and Phase 3 must measure FFI overhead, lifecycle defect rate, build complexity and end-to-end latency against a comparable C++-hosted prototype. The decision remains architectural until those measurements exist.

## Reversal condition

Reconsider if the ABI demonstrably blocks required optimization, if a Rust-native accelerator stack reaches equal coverage and performance with lower complexity, or if measured control-plane overhead violates the declared profile budgets.
