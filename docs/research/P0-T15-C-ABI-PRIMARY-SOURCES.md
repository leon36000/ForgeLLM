# P0-T15 primary-source review: stable C ABI and runtime lifecycle

- **Task:** P0-T15 / issue #74
- **Review date:** 2026-08-21
- **Canonical ForgeLLM base:** `main@ad079c0bf6f86b044f1d1d819cb105e3afe5a65f`
- **Original proposal base:** `main@901667fe0dc5b20e5b97ef883c6659198202a2ae`
- **Evidence class:** architecture research; no ABI implementation or compatibility measurement
- **Method:** official language/vendor documentation and exact public source revisions only

## 1. Scope and terminology

This record supports a proposed ForgeLLM public C ABI between a Rust-owned runtime core and language bindings or future runtime consumers. It does **not** define the future backend-plugin ABI, model format, tensor serialization, accelerator stream interop or implementation code.

Each source statement below is classified as:

- **observed source fact** — directly supported by the cited official source;
- **ForgeLLM inference** — a project-specific conclusion from one or more source facts;
- **selected rule** — the proposed architectural decision recorded in ADR-0006;
- **not transferred** — a source pattern deliberately excluded from ABI v1.

## 2. Source catalog

### SRC-01 — Rust 1.97.1 Nomicon: FFI and unwinding

- **Official source:** <https://doc.rust-lang.org/1.97.1/nomicon/ffi.html#ffi-and-unwinding>
- **Version:** Rust 1.97.1 documentation, matching ForgeLLM's pinned reference toolchain
- **Accessed:** 2026-08-21
- **Observed source facts:** Rust distinguishes non-unwinding ABIs such as `"C"` from unwind-permitting variants such as `"C-unwind"`; allowing an unwind to cross an ABI that does not permit it is not a valid interoperability contract. Rust also documents `catch_unwind` as a boundary for unwinding panics, not a recovery mechanism for aborting panics or process aborts.
- **ForgeLLM inference:** every exported ABI function needs one no-unwind boundary wrapper. The wrapper can translate an unwinding Rust panic into a stable internal-error status, but cannot promise recovery from `panic=abort`, OOM abort, stack overflow, signal termination or process corruption.
- **Selected rule:** all public exports use the non-unwinding C calling convention and contain unwinding panics before return.
- **Limitation:** this source does not prove that all future implementation code is unwind-safe; executable panic-injection tests remain required.

### SRC-02 — Rust 1.97.1 Reference: type layout and `repr(C)`

- **Official source:** <https://doc.rust-lang.org/1.97.1/reference/type-layout.html>
- **Version:** Rust 1.97.1 documentation
- **Accessed:** 2026-08-21
- **Observed source facts:** Rust's default representation does not provide a stable C ABI layout contract; `repr(C)` follows the target C ABI's layout rules, while primitive widths and alignment remain properties of the declared C-compatible fields and target.
- **ForgeLLM inference:** public ABI declarations must be authored as C11 types first, use fixed-width integer types, and be verified by C/C++ compilation and layout assertions. Rust representations are implementation details generated or checked against that contract.
- **Selected rule:** no Rust enum, Rust `bool`, `usize`, `Vec`, `String`, slice/reference or compiler-dependent aggregate crosses the public boundary.
- **Limitation:** `repr(C)` alone does not prove compatibility across architectures or compilers; per-target ABI evidence is still required.

### SRC-03 — ONNX Runtime C API version table

- **Official repository:** <https://github.com/microsoft/onnxruntime>
- **Exact revision reviewed:** `775526b86ee9112b769e58f99eb41b25f28fcaa5`
- **Primary header:** `include/onnxruntime/core/session/onnxruntime_c_api.h`
- **Header blob:** `ac515abbb54576a703cb61bcacd42f5ed8c3f5e5`
- **Accessed:** 2026-08-21
- **Observed source facts:** ONNX Runtime exposes a small base entry surface that selects a C API table by integer API version and exposes a version string; the C surface uses opaque runtime objects and explicit release operations. Its header also preserves legacy provider-option layouts rather than silently appending incompatible fields.
- **ForgeLLM inference:** selecting one immutable table per ABI version is simpler to test and audit than a growing flat symbol set. A caller must receive either the complete requested table or an unsupported-version result, never a partially compatible table.
- **Selected rule:** ForgeLLM uses one exported version-negotiation entry point and immutable per-version tables. Objects are released through the table version that created them.
- **Not transferred:** ForgeLLM v1 will not expose provider-specific option structs or backend-native streams in the public core ABI.
- **Limitation:** ONNX Runtime's design is evidence of a mature pattern, not proof that its exact ownership/error conventions are optimal for ForgeLLM.

### SRC-04 — LLVM/MLIR C API opaque handles

- **Official repository:** <https://github.com/llvm/llvm-project>
- **Exact revision reviewed:** `d5a1778173374b1597a9f2187217f64cd4d3b9ce`
- **Primary header:** `mlir/include/mlir-c/IR.h`
- **Implementation reference:** `mlir/lib/CAPI/IR/IR.cpp`
- **Accessed:** 2026-08-21
- **Observed source facts:** MLIR's C API represents internal C++ objects through C-compatible opaque handle wrappers and uses explicit create/destroy naming for owned objects. Null-handle checks are explicit rather than inferred from object layout.
- **ForgeLLM inference:** runtime, model, session and request internals must remain opaque. The public contract should specify ownership independently for each constructor/getter instead of relying on naming convention alone.
- **Selected rule:** all stateful objects are incomplete C types accessed only through pointers; every function documents whether a handle is borrowed, retained or consumed.
- **Limitation:** MLIR's object graph and threading model differ from an asynchronous inference runtime; request cancellation and parent-child retention need ForgeLLM-specific rules.

### SRC-05 — CUDA Runtime API version-mixing rules

- **Official source:** <https://docs.nvidia.com/cuda/cuda-runtime-api/version-mixing-rules.html>
- **Documentation version reviewed:** CUDA Runtime API 13.3.1
- **Accessed:** 2026-08-21
- **Observed source facts:** CUDA documents compatibility in terms of API/type versions and warns that resources created through one API version must be used consistently with compatible resource APIs. Some API behavior is tied to versioned types rather than a single timeless binary surface.
- **ForgeLLM inference:** a handle created by one ForgeLLM API-table version must not be consumed through a different table version unless a future explicit cross-version rule is proven. Hidden type-version mixing is a lifecycle defect, not a convenience feature.
- **Selected rule:** every opaque handle records its creating ABI version internally; mismatched table use returns a stable version-mismatch status before touching object state.
- **Not transferred:** the public ForgeLLM core ABI does not expose CUDA runtime handles, stream types or provider structures.
- **Limitation:** CUDA's runtime is not a direct template for ForgeLLM ownership; only the version-consistency lesson is transferred.

### SRC-06 — Vulkan extensible-structure discipline

- **Official repository:** <https://github.com/KhronosGroup/Vulkan-Docs>
- **Exact revision reviewed:** `090f1b190d60ced4a1d198fd3747d071cc271b1c`
- **Primary specification area:** `chapters/fundamentals.adoc` and the registered extensible-structure rules
- **Accessed:** 2026-08-21
- **Observed source facts:** Vulkan structures identify their type explicitly and can be extended through typed chains governed by strict validity rules.
- **ForgeLLM inference:** explicit structure identity and forward-extension rules are valuable, but a general `pNext`-style chain would create unnecessary parsing, lifetime and extension-authority complexity in ForgeLLM ABI v1.
- **Selected rule:** v1 uses `struct_size`, `abi_version` and reserved-zero fields with append-only tail growth; it does not support arbitrary extension chains.
- **Not transferred:** no untyped extension pointer and no vendor-defined extension structure is accepted by the core v1 ABI.
- **Limitation:** size-tagged append-only structures still require executable old-header/new-library and new-header/old-library tests.

### SRC-07 — Wasmtime C API

- **Official source:** <https://docs.wasmtime.dev/c-api/>
- **Pinned source revision:** Wasmtime `v48.0.1`, commit `7bac2c2775808aaec5d4aa5627a5e447b51102cf` (<https://github.com/bytecodealliance/wasmtime/tree/7bac2c2775808aaec5d4aa5627a5e447b51102cf/crates/c-api>)
- **Accessed:** 2026-08-21
- **Observed source facts:** Wasmtime `v48.0.1` exposes C ownership and error/trap results through explicit C API object types and destruction functions rather than leaking Rust implementation types.
- **ForgeLLM inference:** distinct result categories are useful, but ABI v1 should avoid multiple library-allocated diagnostic object families until a concrete need outweighs allocator and lifecycle complexity.
- **Selected rule:** v1 uses stable status codes plus a caller-owned diagnostic buffer; no library-allocated error object is required for ordinary failure reporting.
- **Limitation:** this selection must be re-evaluated if structured nested diagnostics become a real binding requirement.

## 3. Cross-source conclusions

### 3.1 Version negotiation

**Selected rule:** export a minimal stable bootstrap surface conceptually equivalent to:

```text
get_api(requested_version)
```

This is a contract sketch, not a shipped declaration. `get_api` is the one bootstrap entry point and succeeds only when the complete requested immutable table is supported. Version `0` and unknown versions return no callable table; the selected immutable table carries its own version, byte size and build-identification view. There is no second bootstrap version-string entry point.

API-table versions are monotonically increasing positive 32-bit integers. Existing tables are immutable once released. Adding, removing, reordering or changing any function pointer requires a new table version. A table includes its own version and byte size so a caller can validate the result before invocation.

### 3.2 Opaque objects and ownership

Proposed v1 object kinds are limited to:

- runtime;
- model;
- session;
- request.

Each is an opaque incomplete C type. Public callers never inspect or allocate the object. Constructors return a new owned handle on success; release consumes one owned reference. `release(NULL)` is defined as success for cleanup ergonomics. Double release, use after release and fabricated pointers remain caller bugs outside recoverable ABI guarantees.

A child object retains the internal resources it needs from its parent. Releasing the caller's parent handle does not invalidate a live child. This avoids a global `BUSY` destruction protocol and permits language bindings to release wrappers independently. The implementation must prove the retention graph is acyclic or uses explicit weak edges.

All operations validate that a handle was created by the same API-table version used for the call. Cross-version use returns `VERSION_MISMATCH` before state access.

### 3.3 Public scalar and view types

- status: signed 32-bit integer;
- ABI version and flags: unsigned 32-bit integers;
- counts, byte lengths, dimensions and timeouts: unsigned 64-bit integers with checked conversion to host `size_t`/Rust `usize`;
- booleans: unsigned 8-bit values restricted to `0` or `1` only where a flag bit is not clearer;
- strings and bytes: `{const uint8_t *data, uint64_t len}` views;
- mutable buffers: `{uint8_t *data, uint64_t capacity, uint64_t *required}`-style caller-owned descriptors;
- no NUL termination is assumed unless a future API explicitly says so;
- text fields are UTF-8 and reject invalid encoding when text semantics are required.

Null pointer plus zero length is valid for an empty optional view. Null pointer plus non-zero length is invalid. Non-null pointers must remain valid for the documented call duration and satisfy alignment requirements of the declared element type.

### 3.4 Extensible structures

Every ABI-visible options or result structure begins with:

1. `uint32_t struct_size`;
2. `uint32_t abi_version`;
3. structure-specific fields;
4. fixed reserved fields that callers initialize to zero.

Rules:

- the library reads no byte beyond `min(struct_size, supported_size)`;
- in ABI v1, `abi_version` equals the exact API-table version selected by bootstrap; it is not an independent structure revision;
- a structure must include the mandatory `struct_size` and `abi_version` prefix and must match the selected table's `abi_version`, otherwise the call returns `VERSION_MISMATCH` before reading optional fields;
- ABI-visible aggregate structures cross the boundary only through pointers: input descriptors are `const` pointers, output descriptors are mutable pointers, and public aggregate parameters and returns are never passed by value;
- an explicitly supported shorter prefix is a same-table-version compatibility case, not an implicit older-table fallback; `struct_size` never infers a new structure revision;
- fields absent from a smaller valid structure receive documented defaults;
- a larger structure is accepted only when the known prefix is valid and all currently reserved fields in the known prefix are zero;
- fields are appended only; no field is reordered, resized, repurposed or removed within one structure version;
- a semantic reinterpretation requires a new structure identity or ABI-table version;
- outputs report the size/version actually written;
- arbitrary extension chains are excluded from v1.

### 3.5 Status and diagnostics

Status code values are stable and never renumbered. Proposed initial categories are:

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

The design does not assign final numeric values; those belong to the implementation packet's header-first RED gate. Detailed diagnostics use a caller-owned byte buffer descriptor. On insufficient capacity, the function returns the ordinary failure status and reports the required byte count without truncating into an ambiguous success. Diagnostic formatting failure never replaces the original status. Success clears the required length to zero.

No thread-local `last_error` state is selected because it complicates async calls, nested bindings and thread migration. No library-allocated error string is selected because it introduces allocator/lifetime coupling for every failure path.

### 3.6 Memory boundary

- caller-owned input views remain caller-owned and are borrowed only for the documented synchronous call duration;
- asynchronous submission copies or internally retains every required input before returning success; v1 does not borrow caller memory after submission;
- library-owned handles are released only by the creating API table;
- no allocation returned by the library is passed to `free`, `delete` or another runtime allocator;
- v1 has no custom allocator callback;
- large output tensors and zero-copy external buffers require a separate accepted design because their ownership, alignment, device and synchronization contracts are not established here.

### 3.7 Runtime and request state

Proposed lifecycle:

```text
CREATED -> QUEUED -> RUNNING -> {SUCCEEDED | FAILED | CANCELLED}
```

- `cancel` is idempotent and records a request; it does not claim instant device preemption;
- cancellation racing with terminal completion returns the observed terminal state without rewriting success as cancellation;
- `poll` is non-blocking and returns a snapshot state;
- `wait(timeout_ns)` uses an unsigned 64-bit timeout; one reserved maximum value may later represent infinite wait only if the header contract names it explicitly;
- request result access is valid only in `SUCCEEDED`;
- request diagnostics are valid in `FAILED` and may be empty for cancellation;
- releasing a non-terminal request returns `INVALID_STATE`, consumes nothing and never blocks; callers must request cancellation and observe a terminal state before release;
- public v1 has no completion callback, user-data pointer or reentrant invocation path.

Thread-safety proposal:

- the API table is immutable and globally shareable;
- runtime and model handles support concurrent read-only operations documented by the implementation;
- session mutation/configuration completes before request submission; concurrent mutable configuration is invalid;
- request `poll`, `wait` and `cancel` are thread-safe and may race according to the state rules above;
- release requires exclusive ownership of that handle reference; bindings needing shared ownership must implement it above the C ABI or use future explicit retain/release functions.
- after `fork` in a process with a live ForgeLLM runtime, the child makes no ForgeLLM call before `exec`; a fresh runtime is created only after `exec` unless a later accepted fork-safety design proves a stronger rule.

### 3.8 Panic and process-failure boundary

Every exported implementation function is wrapped so an unwinding Rust panic becomes `INTERNAL` after best-effort diagnostic capture. No Rust unwind reaches C. The boundary does not claim recovery from:

- `panic=abort`;
- allocator or explicit process abort;
- stack overflow where the process cannot continue safely;
- signals, access violations or undefined behavior;
- corruption inside native backend code.

Implementation gates must test an injected unwinding panic through the exported boundary and verify that no destructor or lock invariant is violated. This architecture does not authorize using panics for ordinary error handling.

### 3.9 Core ABI versus backend-plugin ABI

The public core ABI version is independent from every backend-plugin ABI version. The public table exposes capabilities and portable lifecycle operations, not CUDA/HIP streams, contexts, graph objects, allocator handles or kernel descriptors.

A future backend ABI requires a separate ADR/task that defines:

- plugin discovery and trust;
- backend table version negotiation;
- device/resource ownership;
- stream and synchronization rules;
- tensor memory domains and zero-copy semantics;
- unload safety;
- backend failure containment;
- conformance against the CPU reference.

A core API version bump does not implicitly authorize or version a backend plugin.

## 4. Rejected alternatives

### Flat exported symbol set

Rejected because feature detection, symbol drift and partial upgrades are harder to reason about than one complete selected table.

### One forever-growing function table

Rejected because an old caller cannot safely infer which tail fields exist without a negotiated version, and function reordering becomes catastrophic.

### Generic `void *user_data` callbacks in v1

Rejected because callback lifetime, reentrancy, thread affinity, panic/exception propagation and unload safety are not yet justified. Poll/wait/cancel is sufficient for the first bounded implementation.

### Thread-local last-error strings

Rejected because request completion may happen on another thread and nested calls can overwrite diagnostics.

### Library-allocated error objects for all failures

Rejected for v1 because they add allocation failure and release obligations to every error path. Caller-owned optional diagnostics preserve the primary status even when no message buffer exists.

### Public backend-native handles

Rejected because they would couple the stable runtime ABI to vendor versions and violate R-009. Future explicit interop can be added only after backend-specific proof.

### General extension chains

Rejected for v1 because arbitrary typed chains expand parser, ownership and extension-authority complexity. Append-only size-tagged structures cover the initial compatibility need.

## 5. Unresolved implementation evidence

This research does not establish:

- final numeric status values;
- final C identifiers or export macro spellings;
- concrete model-loading or tensor-result descriptors;
- platform calling/export attributes;
- object-retention implementation strategy;
- bounded release behavior for a running request;
- ABI compatibility on Windows, macOS, Linux, x86_64, AArch64 or other targets;
- sanitizer/fuzzer behavior;
- C++ exception containment in future native backends;
- zero-copy or external-stream interoperability.

These remain implementation or later-ADR gates. They are not silently filled by analogy to the reviewed projects.
