# P0-T15 execution plan: versioned C ABI and runtime lifecycle

> **Status:** design/review plan only. It does not authorize ABI implementation.

**Task:** P0-T15 / issue #74
**Base:** `main@ad079c0bf6f86b044f1d1d819cb105e3afe5a65f`
**Original proposal base:** `main@901667fe0dc5b20e5b97ef883c6659198202a2ae`
**Deliverable:** proposed ADR-0006, primary-source record and a no-stub future implementation sequence
**Non-goal:** no C header, Rust FFI crate, exported symbol, backend plugin or binding in this task

## 1. Why this plan exists

A public ABI cannot be safely created through incremental placeholder declarations. Once external code compiles against a header or dynamically resolves a symbol, accidental names, layouts and ownership rules become compatibility obligations. P0-T15 therefore ends at a reviewed architecture decision.

The first ABI implementation merge must be one complete, meaningful vertical slice under a later task packet. A header-only shell, empty function table, opaque handles with no real lifecycle or functions returning `UNIMPLEMENTED` are prohibited.

The current ForgeLLM base contains checked reference tensor primitives but no complete decoder-only model path, model loader or request/result data-plane contract. That absence is a dependency fact, not an invitation to invent a placeholder ABI.

## 2. P0-T15 work units

### Work unit A — source-backed compatibility rules

**Files:**

- `docs/research/P0-T15-C-ABI-PRIMARY-SOURCES.md`

**Required evidence:**

- Rust 1.97.1 FFI/unwinding and type-layout rules;
- exact ONNX Runtime source revision and C header;
- exact LLVM/MLIR source revision and opaque-handle C API;
- versioned CUDA resource-mixing documentation;
- exact Vulkan-Docs revision and extensible-structure rules;
- Wasmtime C ownership/error pattern;
- source fact, ForgeLLM inference, transferred rule, rejected rule and limitation kept distinct.

**Stop:** a source pattern is omitted rather than guessed when its official contract cannot be verified.

### Work unit B — proposed ABI/lifecycle ADR

**Files:**

- `docs/architecture/ADR-0006-versioned-c-abi-and-runtime-lifecycle.md`

**Must decide:**

- exact-version API-table handshake;
- calling convention and export surface;
- fixed-width public types;
- size/version-tagged structures;
- opaque ownership and parent-child retention;
- status/error-buffer semantics;
- allocator boundary;
- no-unwind boundary;
- runtime/model/session/request lifecycle;
- finite wait, cancellation, bounded shutdown and terminal-only request release;
- thread/fork/unload rules;
- public core versus backend-plugin version authority;
- rejected callbacks, custom allocators, native handles and extension chains.

**Stop:** if a rule requires fixing the model/tensor data plane or backend ABI, record the boundary and split it rather than silently deciding it.

### Work unit C — future implementation proof plan

**Files:**

- this plan

**Must prevent:**

- a header merged without implementation;
- version negotiation tested only from Rust;
- layout tests on one compiler/target only;
- panic containment inferred from `catch_unwind` without fault injection;
- handles released by a different table version;
- hidden release-time blocking;
- `last_error` thread-local ambiguity;
- public vendor-native resource leakage;
- green tests that never compile an independent C caller;
- an ABI task opened before a real model/request data plane exists.

### Work unit D — blind architecture/security review

**Reviewer:** GPT-5.6 Sol in a fresh context, exact final head only.

**Review inputs:**

- task packet;
- source record;
- ADR;
- this plan;
- Git diff;
- hosted validation results.

**Acceptance:** `VERDICT=ACCEPT`, exact reviewed head, no unresolved `BLOCKER` or `MAJOR`.

Sol must challenge the design rather than merely confirm that all sections exist.

## 3. Next-task selection gate — no premature task-ID reservation

P0-T15 does not reserve P0-T16 or any later identifier for ABI implementation. The next free task ID is assigned only after evaluating the dependency gate below against current canonical Git.

### Gate A — real request/data-plane contract exists

ABI implementation may be proposed only when all of the following are true:

1. ADR-0006 is `accepted`, not merely merged as proposed.
2. A complete CPU-reference operation can be invoked through runtime/model/session/request semantics without canned data or an `UNIMPLEMENTED` path.
3. The canonical repository defines the exact model or operation input descriptor, output/result descriptor, ownership, validation and error behavior needed by that operation.
4. The path does not invent a backend-native handle, proprietary wire format or unreviewed external model format.
5. The packet can own all header, crate, test, build and CI paths it changes.
6. Independent C and C++ compilers are available in hosted CI.
7. A reviewer distinct from the writer is assigned for unsafe/FFI, ownership, panic and concurrency boundaries.

If all seven conditions hold, the next free task ID may be assigned to:

> **Implement and prove the first complete ForgeLLM C ABI vertical slice.**

### Gate B — real request/data-plane contract is absent

If any of conditions 2–4 is absent, the next free task ID is assigned first to a bounded data-plane design or implementation task. That preceding task must establish a real CPU decoder/model/request contract with executable reference semantics. The ABI implementation receives a later free task ID only after that dependency is merged and reviewed.

On the P0-T15 base, Gate B applies: the repository has reference primitives but no complete decoder-only model loader/request path. Therefore the current expected next task is a narrowly named CPU reference data-plane task, not an ABI skeleton.

This selection is re-evaluated from Git at task creation. The plan never hard-codes a future identifier whose prerequisites may not exist.

## 4. Required TDD sequence for the eventual ABI implementation task

The future writer follows these gates in order. Intermediate RED commits may exist on the isolated branch; no incomplete header or implementation is merged.

### Task 1 — independent header consumers RED

Create failing tests before the header exists:

- `tests/abi/c11_header_smoke.c`;
- `tests/abi/cpp17_header_smoke.cc`;
- `tests/abi/layout_assertions.c`;
- `tests/abi/symbol_allowlist.txt`;
- `tests/abi/version_negotiation.c`;
- `tests/abi/malformed_descriptors.c`.

RED must fail because the canonical header/symbols do not exist, not because the compiler or test harness is broken.

### Task 2 — canonical C header

Add the smallest complete header for the authorized vertical slice.

Requirements:

- C11/C++17 clean;
- one bootstrap symbol;
- exact API table prefix;
- fixed-width status and descriptor fields;
- opaque types only for objects that have complete behavior in the slice;
- no dead declaration, reserved future function pointer or `UNIMPLEMENTED` status path;
- documented ownership/nullability/thread rules adjacent to every function;
- ABI version and status numeric assignments frozen by static tests.

### Task 3 — symbol and layout proof

Before Rust behavior:

- compile the header as C11 and C++17 with warnings-as-errors;
- assert widths, offsets, alignment, table size and reserved fields;
- assert that every ABI-visible aggregate descriptor crosses through the required `const` input or mutable output pointer and that no public aggregate parameter or return is by value;
- inspect the dynamic symbol table and reject every unapproved export;
- compile old-size/new-size fixture headers where the accepted table explicitly supports them;
- verify that default compiler packing produces the expected layout without `#pragma pack`.

### Task 4 — Rust FFI boundary

Add a dedicated small crate with:

- `#![deny(unsafe_op_in_unsafe_fn)]`;
- unsafe confined to audited conversion/boundary modules;
- no Rust layout as the source of truth;
- no unwinding export;
- initialized output state before fallible work;
- checked fixed-width to host-size conversions;
- stable status mapping;
- caller-owned diagnostics.

Each unsafe block states the pointer, length, alignment, lifetime and aliasing invariant it relies on.

### Task 5 — exact version negotiation

Tests cover:

- supported exact version returns a complete immutable table;
- zero and unknown versions return null;
- table header size/version match the request;
- repeated calls return the same process-lifetime pointer;
- old and current supported tables remain independently callable when more than one exists;
- handle use through the wrong table returns `VERSION_MISMATCH` without consuming the valid handle.

### Task 6 — ownership and allocation

Tests cover:

- null release;
- successful create/release;
- parent public-handle release while child internals remain valid;
- no cross-allocator free;
- failure leaves output handles null;
- caller diagnostic buffer unchanged on success except zero lengths;
- insufficient diagnostic capacity reports required size and writes no partial message;
- leak and address sanitizers where supported.

Double release and fabricated-pointer behavior are documented caller defects and must not be tested by deliberately invoking undefined memory access in ordinary CI. A debug-handle registry or fuzz harness may detect them only if the design preserves release behavior and does not become a production dependency.

### Task 7 — panic containment

Inject a controlled unwinding panic behind each exported function family and prove:

- C observes `INTERNAL`;
- no unwind reaches the C frame;
- output handles remain null or unchanged according to contract;
- locks and internal ownership remain usable after the call when safe continuation is claimed;
- `panic=abort` is tested only as a subprocess termination boundary and is never described as recovered.

### Task 8 — request state and concurrency

When the real vertical slice includes requests:

- model the allowed state transitions independently from the implementation;
- test poll, finite wait, timeout, idempotent cancel and terminal result access;
- distinguish API-call success from the request's terminal inference outcome;
- race cancel against completion repeatedly under a deterministic scheduler or model checker where feasible;
- verify release of a non-terminal request returns `INVALID_STATE` without blocking or consuming the handle;
- verify release after each terminal state;
- verify bounded shutdown reports timeout without force-freeing active resources;
- verify a child process makes no ForgeLLM call after any `fork` and before a successful `exec`, regardless of parent runtime state;
- run ThreadSanitizer or Loom-style internal concurrency tests where the supported toolchain permits;
- do not add callbacks to make tests convenient.

### Task 9 — malformed-input and fuzz gates

Exercise:

- null/non-zero views;
- invalid UTF-8 text fields;
- count/byte overflows;
- undersized/oversized structures;
- non-zero reserved fields;
- unknown flags and enum values;
- misaligned pointers where the host permits safe subprocess testing;
- call-sequence fuzzing over versioned handles and request states.

The fuzzer never treats a process abort from deliberate caller undefined behavior as a recoverable ABI promise.

### Task 10 — exact-head completion

Required exact-head gates:

- C11 and C++17 compile matrix;
- Rust fmt, Clippy and tests;
- ABI symbol allowlist;
- layout/static assertions;
- sanitizer/concurrency/fuzz receipts appropriate to the slice;
- full `make ci`;
- CodeQL and supply-chain checks relevant to changed dependencies/actions;
- blind Sol review on the exact final head;
- separate fresh-context implementation review for unsafe/FFI code.

A skipped or unavailable platform is recorded as unverified and cannot be used to claim cross-platform compatibility.

## 5. Proposed paths for the eventual ABI implementation task

The later ABI packet may request, but must explicitly own, paths such as:

- `include/forgellm/forgellm.h`;
- `crates/forgellm-ffi/`;
- `tests/abi/`;
- `scripts/verify_abi_symbols.py`;
- a dedicated hosted ABI workflow;
- task, review and state closeout files.

No generated header is edited manually. If generation is selected, the canonical schema/source, generator version and byte-for-byte regeneration test are part of the packet.

## 6. Loop contract for the eventual ABI implementation

- **GOAL:** one complete real ABI vertical slice, not declarations for future functions.
- **SCOPE:** exact header/FFI/test/build paths; no backend implementation.
- **VERIFY:** independent C/C++ callers, symbol/layout gates, Rust tests, fault injection and full CI.
- **BUDGET:** at most two correction cycles for one repeated ABI finding before architectural diagnosis.
- **STOP:** green exact-head gates; repeated identical failure; missing real data-plane contract; unsafe invariant that cannot be stated; Sol or FFI reviewer `REJECT`.
- **RECEIPT:** exact base/head/merge, toolchains/targets, symbols, layouts, tests, sanitizers, reviewer verdicts and unverified platforms.

## 7. No-false-done rule

P0-T15 is complete only when the design is reviewed and truthfully records its evidence boundary. It does not make ForgeLLM ABI-capable.

The eventual ABI implementation task is complete only when independent C/C++ consumers execute one real ForgeLLM vertical slice through the ABI on the tested targets. A compilable header, exported table, opaque allocation or successful version query alone is not a completed inference ABI.
