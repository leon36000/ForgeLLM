# ADR-0006: Stable versioned C ABI and runtime lifecycle

- **Status:** proposed
- **Date:** 2026-08-21
- **Owners:** ForgeLLM project owner / architecture authority; independent ABI, FFI and security reviewer required
- **Related tasks/risks:** P0-T15, issue #74, ADR-0001, R-003, R-006, R-009

## Context

ForgeLLM's charter places runtime orchestration, lifecycle, scheduling and safe resource abstractions in Rust while permitting CUDA, HIP and portable native backends only behind explicit boundaries. ADR-0001 requires a stable versioned C ABI with opaque handles, explicit ownership and error codes. P0-T11 and P0-T12 now provide a bounded CPU reference nucleus, so the next architecture risk is not another isolated primitive: it is defining the binary boundary before backend and language-binding implementation hardens accidental layouts into compatibility obligations.

A C ABI is necessary but not sufficient. A technically C-compatible function can still be unsafe or unstable when:

- Rust or C++ exceptions unwind across the boundary;
- a public struct is extended without size/version rules;
- one allocator creates memory that another allocator frees;
- opaque handles outlive parents or are used through a different API version;
- cancellation races with completion or destruction;
- thread-local error state is overwritten by async work;
- public declarations expose backend-native streams or vendor structures;
- a flat exported symbol set grows without a complete compatibility handshake.

The P0-T15 source review compares official Rust 1.97.1 FFI/layout rules, ONNX Runtime's selected C API table, MLIR opaque-handle conventions, CUDA resource-version consistency, Vulkan extensible structures and Wasmtime C ownership. Those projects are evidence sources, not authority over ForgeLLM. The selected rules below are ForgeLLM decisions and remain unproven until executable cross-language tests pass.

## Decision

ForgeLLM will define its public runtime boundary as a **C11-compatible, exact-version-negotiated function-table ABI**. ABI v1 is intentionally narrow. It establishes compatibility, ownership, errors and asynchronous request lifecycle without exposing backend-native resources or introducing callbacks.

### 1. Authority and scope

The canonical C header created by a future implementation task will be the public ABI source of truth. Rust FFI declarations, C++ wrappers and generated language bindings must conform to that header and its executable layout/symbol tests; they may not redefine the contract independently.

This ADR defines the public core runtime ABI. A backend-plugin ABI is a separate future authority with its own version negotiation, security model and conformance packet. A core ABI version never implicitly versions or authorizes a backend ABI.

No header, exported symbol or FFI implementation is authorized by this design task. Implementation begins only under a separate packet after this ADR is accepted.

### 2. Bootstrap and API-table versioning

The public dynamic-library bootstrap surface contains one required exported entry point conceptually equivalent to:

```text
const api_header *get_api(uint32_t requested_version)
```

This notation describes behavior only; final C identifiers and numeric values belong to the header-first implementation task.

Rules:

1. ABI versions are monotonically increasing positive `uint32_t` values. Version zero is invalid.
2. The entry point returns a pointer to one immutable, process-lifetime API table for the exact requested version, or null when that complete version is unsupported.
3. There is no nearest-version fallback, partial table, feature-probing mutation or caller-writable table.
4. Every table begins with `uint32_t struct_size` and `uint32_t abi_version`.
5. The caller validates both fields before reading a version-specific table tail.
6. Once released, a version's function order, signatures, status values and type contracts are immutable.
7. Adding, removing, reordering or changing a function, public enum domain or public structure contract requires a new API-table version.
8. A library may support multiple historical tables concurrently. Removing a previously shipped table is a documented compatibility break and requires an explicit support-policy decision.
9. Build/product information is obtained through a function in the selected table; it is informational and never substitutes for ABI negotiation.
10. Function pointers and handles become invalid if the dynamic library is unloaded. The caller must release every handle and cease every call before unloading; v1 provides no safe hot-unload protocol.

### 3. Calling convention, symbols and language surface

The future public header must:

- compile as C11 and C++17;
- use `extern "C"` in C++;
- define one explicit export/import macro;
- select the C calling convention explicitly on platforms where multiple conventions exist; the initial Windows rule is `__cdecl`;
- use no C bitfields, packed structures, flexible array members or compiler-specific anonymous layout in the stable surface;
- use only standard fixed-width integer types and opaque incomplete types;
- keep all non-bootstrap implementation symbols hidden by default and verify the exported symbol list.

Public ABI fields do not use:

- Rust or C++ standard-library types;
- Rust references, slices, `Vec`, `String`, `Option`, trait objects or enums;
- C++ classes, exceptions, templates or RTTI;
- C `bool` or layout-dependent enum storage;
- public `size_t`, `long` or pointer-sized integer semantics;
- backend-native CUDA/HIP/driver/DSL structures.

Flags and enum-like domains use fixed-width unsigned integers with named constants. Input values with unknown mandatory bits or unknown enum values return `INVALID_ARGUMENT`. Reserved bits must be zero.

### 4. Opaque object model

ABI v1 recognizes four public stateful object kinds:

- runtime;
- model;
- session;
- request.

They are incomplete C types accessed only through pointers. Callers do not allocate, copy, inspect or embed their representation.

Ownership rules:

1. A successful constructor returns exactly one owned handle reference through a caller-provided output pointer.
2. Before work that can fail, constructors initialize the output handle to null after validating that the output pointer itself is writable.
3. A release function consumes one owned handle reference on success.
4. `release(NULL)` succeeds and has no effect.
5. Release functions return a status; destruction failure is never hidden in a `void` function.
6. Double release, fabricated pointers, use after release and concurrent release of the same owned reference are caller defects outside recoverable guarantees.
7. Every internal handle records its creating ABI-table version. A function from another table returns `VERSION_MISMATCH` before accessing object state.
8. A child retains the internal resources it needs from its parent. Releasing the caller's runtime, model or session handle does not invalidate an already-created child.
9. The implementation must keep the internal retention graph acyclic or explicitly prove every weak edge. Public ownership does not expose internal reference counts.
10. The caller must not unload the library while any handle or API-table pointer remains live.

The initial lifetime graph is:

```text
runtime -> model -> session -> request
```

This graph describes retained dependencies, not exclusive ownership. Multiple models may share one runtime, multiple sessions may retain one model and multiple requests may retain one session.

### 5. Public scalar, string and byte views

ABI-visible values use:

- `int32_t` for status codes;
- `uint32_t` for ABI versions, structure versions, flags and enum domains;
- `uint64_t` for byte lengths, element counts, dimensions and finite timeout values;
- `uint8_t` restricted to `0` or `1` only when a dedicated flag bit is not appropriate.

Every `uint64_t` count is checked before conversion to platform `size_t` or Rust `usize`. Overflow returns `INVALID_ARGUMENT` or `RESOURCE_EXHAUSTED` according to whether the requested representation is impossible or merely unavailable; the implementation packet must freeze this mapping in tests.

Immutable strings and bytes use pointer-plus-length views. Text fields explicitly require UTF-8. No view assumes NUL termination. Null plus zero length is a valid empty optional view; null plus non-zero length is invalid. Non-null data must remain readable and correctly aligned for the documented synchronous call duration.

ABI v1 does not retain caller input memory after an asynchronous submission returns success. The implementation must either copy or internally own every byte required by a live request before returning. Zero-copy external buffers, mapped model weights and device memory require a separate accepted ownership/synchronization design.

### 6. Extensible structures

Every public options, input-descriptor or output-descriptor structure begins with:

1. `uint32_t struct_size`;
2. `uint32_t abi_version`;
3. structure-specific fields;
4. documented reserved fields initialized to zero by callers.

Compatibility rules:

- the API table version fixes the semantic contract for every structure it accepts;
- a released structure never changes within one table version;
- a newer table may deliberately accept an older structure prefix, but that compatibility is explicit in the newer table's tests and documentation;
- the library reads no byte beyond `min(struct_size, size_known_by_that_table)`;
- `struct_size` smaller than the mandatory prefix is invalid;
- missing optional tail fields receive documented defaults only when that table explicitly accepts the older size;
- a larger structure is accepted only when its known prefix is valid and every reserved field in the known prefix is zero;
- fields are append-only between compatible structure revisions; no field is reordered, resized, removed or repurposed;
- outputs report the structure size and ABI version actually written;
- unknown extension pointers and general `pNext`-style chains are rejected in v1.

### 7. Status codes and diagnostics

Every fallible table function returns a stable `int32_t` status. `OK` is zero; every failure is non-zero. Once assigned in the implementation header, numeric values are never renumbered or reused.

The initial required semantic categories are:

- `OK`;
- `INVALID_ARGUMENT`;
- `UNSUPPORTED_VERSION`;
- `VERSION_MISMATCH`;
- `INVALID_STATE`;
- `NOT_FOUND`;
- `RESOURCE_EXHAUSTED`;
- `CANCELLED`;
- `TIMEOUT`;
- `BACKEND_UNAVAILABLE`;
- `NUMERICAL_ERROR`;
- `INTERNAL`.

Final names and values are frozen by the future header-first RED tests, not by illustrative code in this ADR.

Detailed diagnostics use an optional caller-owned buffer descriptor containing data pointer, capacity, written length and required length, all with fixed-width fields and a size/version prefix where applicable.

Diagnostic rules:

1. A null diagnostic descriptor means no detailed message is requested.
2. Null data with non-zero capacity is invalid and is detected before a mutating operation begins.
3. On failure, `required` reports the complete UTF-8 byte count when the descriptor is valid.
4. If capacity is sufficient, the exact non-NUL-terminated UTF-8 message is written and `written == required`.
5. If capacity is insufficient, no partial message is written and `written == 0`.
6. Diagnostic formatting failure never replaces the operation's primary status.
7. Success clears `written` and `required` to zero.
8. No thread-local `last_error` and no library-allocated ordinary error string/object is part of v1.

### 8. Allocation boundary

The allocator that creates memory also releases it.

- caller-owned input and diagnostic buffers remain caller-owned;
- library-owned opaque handles are released only through their creating API table;
- the caller never invokes `free`, `delete` or a language allocator on library-owned storage;
- the library never releases caller-owned storage;
- v1 exposes no custom allocator callback;
- ordinary output metadata is copied into caller-provided size-tagged descriptors;
- ownership for large output tensors is deferred to the first data-plane implementation packet and must not be inferred from this ADR.

### 9. No-unwind and process-failure boundary

Every exported function uses a non-unwinding C ABI and contains Rust unwinding panics before returning to the caller. An injected unwinding panic maps to `INTERNAL` after best-effort diagnostic capture. Locks, ownership transfers and output initialization must remain valid when this path is exercised.

No ordinary invalid input is handled by panic. No Rust or C++ exception may cross the boundary.

The ABI does not claim typed recovery from:

- `panic=abort`;
- allocator/process abort or unrecoverable OOM;
- stack overflow where safe continuation is unavailable;
- signals, access violations or undefined behavior;
- memory corruption or abort inside future native backend code.

Those limits must appear in user-facing binding documentation and fault-injection receipts.

### 10. Request state machine

A request follows this monotonic state machine:

```text
CREATED -> QUEUED -> RUNNING -> SUCCEEDED
                              -> FAILED
                              -> CANCELLED
```

A future implementation may transition directly from `CREATED` or `QUEUED` to a terminal failure/cancellation when validation or scheduling ends the request, but no terminal state transitions to another state.

Rules:

- submission returns a request only after all retained input has been copied or internally owned;
- `poll` is non-blocking and returns one snapshot state;
- `wait` accepts only a finite `uint64_t timeout_ns`; timeout zero is a non-blocking observation and `UINT64_MAX` is rejected in v1 rather than serving as a hidden infinite wait;
- wait timeout returns `TIMEOUT` without changing request state;
- `cancel` is thread-safe and idempotent; it records a cancellation request but does not promise instantaneous accelerator preemption;
- cancellation racing with terminal completion preserves the first terminal state actually committed;
- a successful completion is never rewritten to cancellation after the result becomes terminal;
- result access is valid only in `SUCCEEDED`;
- failure diagnostics are valid in `FAILED` and may be empty in `CANCELLED`;
- release of a non-terminal request returns `INVALID_STATE`, consumes nothing and never blocks;
- callers must cancel if desired and observe a terminal state before release;
- no callback, user-data pointer, reentrant completion call or hidden release-time wait exists in v1.

### 11. Thread-safety contract

The API table is immutable and globally shareable.

Object rules:

- runtime: concurrent documented operations are permitted; creation-time configuration is immutable after successful construction;
- model: immutable after load and safe for concurrent session creation/read-only queries;
- session: immutable after successful construction and safe for concurrent request submission unless a later function is explicitly documented otherwise;
- request: `poll`, finite `wait` and `cancel` are thread-safe and may race according to the state machine;
- release: the caller provides exclusive ownership of the released handle reference and must not race release against another operation on that same reference.

Language bindings that need shared public-handle ownership implement that policy above the C ABI or use a future explicit retain/release addition under a new ABI version. V1 does not expose generic retain.

Fork behavior is not guaranteed after a runtime exists. A process that forks must create a new runtime in the child before using ForgeLLM there; inherited live handles are invalid in the child.

### 12. Core/backend separation

The public core ABI exposes portable capability, object and request semantics only. It does not expose:

- CUDA or HIP contexts, streams, events or graph objects;
- vendor allocator handles;
- CuTe/CUTLASS descriptors;
- portable-DSL compiler/runtime objects;
- backend plugin function tables;
- device pointers or external memory handles;
- backend-specific status enums.

A future backend-plugin ADR must separately define discovery, trust, version negotiation, unload safety, device/resource ownership, synchronization, tensor memory domains, error containment and CPU-reference conformance. Backend ABI versions and core ABI versions evolve independently.

## Required implementation sequence

After this ADR is accepted, one separate implementation packet may begin with tests and declarations only in this order:

1. canonical C11 header tests that intentionally fail because no header exists;
2. C11 and C++17 compile tests on every supported target/compiler;
3. static assertions for scalar widths, table prefix, structure offsets, alignment and reserved fields;
4. exported-symbol allowlist proving only the bootstrap symbol is globally visible initially;
5. exact version-negotiation tests: supported, zero, unknown, old table and complete-table validation;
6. old-header/new-library and new-header/old-library size/version fixtures;
7. null, length, alignment, overflow, unknown-flag and malformed-structure negatives;
8. ownership and parent-release tests with leak, address and thread sanitizers where supported;
9. wrong-table-version handle tests;
10. injected Rust unwinding-panic containment tests;
11. request-state, finite-wait, cancellation and release-race model tests;
12. C ABI fuzzing over bootstrap, descriptors and invalid call sequences;
13. only then the smallest Rust implementation that makes those gates pass.

Tensor/model data-plane descriptors, output-buffer ownership and backend plugin loading are split into later reviewed increments if the first implementation packet cannot define them without widening scope.

## Alternatives considered

### A. Flat exported function set

Rejected. It makes complete version negotiation, symbol compatibility and old/new library behavior harder to prove.

### B. One forever-growing table

Rejected. Tail discovery alone cannot make changed signatures, reordered functions or type semantics safe.

### C. C++ ABI between Rust and backends

Rejected. Name mangling, exception, standard-library and compiler ABI variation create a larger compatibility surface than a C11 contract.

### D. General callback-based async API in v1

Rejected. Callback lifetime, thread affinity, reentrancy, user-data ownership, panic/exception containment and library unload are not yet proven. Poll/wait/cancel is sufficient for the initial bounded interface.

### E. Thread-local last-error state

Rejected. Async completion, nested calls and thread migration can overwrite or misassociate diagnostics.

### F. Library-allocated error objects for ordinary failures

Rejected for v1. They add allocator failure and release obligations to every failure path. Stable status plus optional caller-owned diagnostics preserves the primary error without cross-allocator ownership.

### G. General extension chains

Rejected for v1. Size/version-tagged structures provide bounded forward compatibility without arbitrary parser and extension-authority complexity.

### H. Public vendor-native interoperability handles in v1

Rejected. They would couple the stable core ABI to backend versions and violate the vendor-independence mitigation for R-009.

## Consequences

Positive:

- binary compatibility has one exact handshake and a testable table surface;
- Rust/native ownership and cancellation races are explicit before implementation;
- language bindings can be thin without inheriting Rust layouts;
- vendor details remain behind a separately governed backend boundary;
- no callback or custom-allocator complexity is introduced prematurely;
- old ABI versions can remain available without mutating their tables.

Costs:

- maintaining multiple immutable API tables requires adapters inside the Rust core;
- caller-provided diagnostics are less convenient than allocated error objects;
- terminal-only request release requires callers to model cancellation and completion honestly;
- exclusion of zero-copy/native handles may require copies in early implementations;
- header, layout, cross-compiler, sanitizer and fuzz gates add implementation work before backend progress.

## Evidence boundary

This ADR does not prove:

- that any C header or symbol exists;
- binary compatibility on any operating system or architecture;
- panic containment in compiled code;
- data-plane tensor ownership;
- dynamic backend loading or unload safety;
- language binding correctness;
- native backend exception containment;
- performance or production readiness.

Those remain executable gates. Merging this proposed ADR authorizes review of the design only; accepting it authorizes creation of a separate implementation task, not automatic implementation or merge.

## Reversal or supersession conditions

Reconsider this decision if executable evidence shows that:

- immutable per-version tables create unmanageable adapter debt;
- caller-owned diagnostics cannot express required structured failures;
- terminal-only request release prevents bounded shutdown under real workloads;
- callback-free operation cannot support required service-runtime integration;
- a different boundary materially improves safety/portability without exposing vendor internals;
- cross-platform layout or calling-convention evidence cannot satisfy the compatibility contract;
- the core/backend separation cannot prevent version or resource ownership leakage.
