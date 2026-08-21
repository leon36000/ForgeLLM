# P0-T15 execution plan: versioned C ABI and runtime lifecycle

> **Status:** design/review plan only. It does not authorize ABI implementation.

**Task:** P0-T15 / issue #74  
**Base:** `main@901667fe0dc5b20e5b97ef883c6659198202a2ae`  
**Deliverable:** proposed ADR-0006, primary-source record and a no-stub future implementation sequence  
**Non-goal:** no C header, Rust FFI crate, exported symbol, backend plugin or binding in this task

## 1. Why this plan exists

A public ABI cannot be safely created through incremental placeholder declarations. Once external code compiles against a header or dynamically resolves a symbol, accidental names, layouts and ownership rules become compatibility obligations. P0-T15 therefore ends at a reviewed architecture decision.

The first implementation merge must be a complete, meaningful vertical slice under a new task packet. A header-only shell, empty function table, opaque handles with no real lifecycle or functions returning `UNIMPLEMENTED` are prohibited.

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
- finite wait, cancellation and terminal-only request release;
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
- green tests that never compile an independent C caller.

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

## 3. Reserved next task: P0-T16

The next implementation packet is reserved as:

> **P0-T16 — implement and prove the first complete ForgeLLM C ABI vertical slice**

P0-T16 is not automatically authorized by merging P0-T15. It may be opened only after ADR-0006 is accepted and after a real CPU request/data-plane contract exists that can cross the ABI without a placeholder model or tensor format.

### Mandatory P0-T16 entry conditions

1. ADR-0006 is `accepted`, not merely merged as proposed.
2. The exact first vertical slice performs a real ForgeLLM operation with the CPU reference; it does not return canned data or `UNIMPLEMENTED`.
3. Input and output data ownership can be specified without exposing a vendor-native handle or inventing an unreviewed model format.
4. The packet owns all header, crate, test, build and CI paths it changes.
5. Independent C and C++ compilers are available in hosted CI.
6. A reviewer distinct from the writer is assigned for FFI, ownership and panic boundaries.

If entry condition 2 or 3 is absent, the next task is a narrowly named data-plane design task, not a fake ABI implementation.

## 4. P0-T16 required TDD sequence

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
- handle use through the wrong table returns `VERSION_MISMATCH`.

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
- race cancel against completion repeatedly under a deterministic scheduler or model checker where feasible;
- verify release of a non-terminal request returns `INVALID_STATE` without blocking or consuming the handle;
- verify release after each terminal state;
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

## 5. Proposed future paths

P0-T16 may request, but must explicitly own, paths such as:

- `include/forgellm/forgellm.h`;
- `crates/forgellm-ffi/`;
- `tests/abi/`;
- `scripts/verify_abi_symbols.py`;
- a dedicated hosted ABI workflow;
- task, review and state closeout files.

No generated header is edited manually. If generation is selected, the canonical schema/source, generator version and byte-for-byte regeneration test are part of the packet.

## 6. Loop contract

- **GOAL:** one complete real ABI vertical slice, not declarations for future functions.
- **SCOPE:** exact header/FFI/test/build paths; no backend implementation.
- **VERIFY:** independent C/C++ callers, symbol/layout gates, Rust tests, fault injection and full CI.
- **BUDGET:** at most two correction cycles for one repeated ABI finding before architectural diagnosis.
- **STOP:** green exact-head gates; repeated identical failure; missing real data-plane contract; unsafe invariant that cannot be stated; Sol or FFI reviewer `REJECT`.
- **RECEIPT:** exact base/head/merge, toolchains/targets, symbols, layouts, tests, sanitizers, reviewer verdicts and unverified platforms.

## 7. No-false-done rule

P0-T15 is complete only when the design is reviewed and truthfully records its evidence boundary. It does not make ForgeLLM ABI-capable.

P0-T16 is complete only when independent C/C++ consumers execute a real ForgeLLM vertical slice through the ABI on the tested targets. A compilable header, exported table, opaque allocation or successful `get_version` call alone is not a completed inference ABI.
