# P0-T16 bounded dense decoder reference review

- **Task:** P0-T16
- **Authorization source:** approved convergence plan Task 5 and the live free task ID
- **Base:** `55d08c76b7fcdc3b6c256d35a4d74b275652964c`
- **Packet RED commit:** `a81b7daa663265aa17c7b02a84272170bcc77c1b`
- **Implementation head:** `7ad8efdf53c60178ea83f3883a88178169583062`
- **Test-hardening head:** `a43a0fa32650524ad4759cf0f0676d4bab690363`
- **State/projection synchronization:** `c80fcdd53ca579b35b332dd751c4baae127c652c`
- **Evidence boundary:** in-memory Rust CPU reference semantics only
- **Status:** candidate complete; exact hosted checks on the test-hardening head are green; final receipt/Sol gate and protected merge pending

## Scope

P0-T16 adds one public Rust composition for a single dense decoder token:
`embedding_gather -> RMSNorm -> projection -> softmax -> greedy argmax`. Inputs are checked,
contiguous in-memory tensors and scalar/vector parameters. The slice does not load models or
tokenizers and does not implement attention, KV cache, scheduling, runtime, ABI, FFI, backend,
GPU, CUDA, HIP or performance behavior.

## Test-driven evidence

The packet and independent oracle tests were committed before production code. The first RED
run was:

```text
cargo test --test dense_decoder
error[E0432]: unresolved import `forgellm_reference::dense_decode_single_token`
```

The implementation was then added as `dense_decode_single_token` in `lib.rs`. It composes the
existing checked operations without changing their contracts. The integration oracle computes
RMS normalization and projection directly over synthetic buffers and compares the returned
token; it does not call the composed operation's internal stages.

## Independent review

GPT-5.6 Luna reviewed implementation head `7ad8efdf53c60178ea83f3883a88178169583062` and
returned `VERDICT=CHANGES_REQUESTED` only for governance synchronization: one unquoted YAML
value, a stale README status block, and stale `TREE.txt`. It found no Rust correctness,
scope, dependency, unsafe-code, runtime, ABI, backend, GPU, model or performance issue.
The packet value was quoted, README/TREE/state/mobile/manifest projections were synchronized,
and the packet was moved to `tasks/closed` with `status: complete`.

## Local candidate evidence

- The test-hardening head `a43a0fa32650524ad4759cf0f0676d4bab690363` was checked locally after `git rev-parse HEAD` returned that exact hash.
- `cargo test --test dense_decoder`: **7 passed**;
- `cargo test --workspace --all-targets --locked`: **53 passed**;
- `cargo fmt --all --check`: passed;
- `cargo clippy --workspace --all-targets --locked -- -D warnings`: passed;
- prohibited implementation scan: no TODO/stub/unimplemented path; the only `unsafe` match is
  the crate-level `#![forbid(unsafe_code)]` declaration;
- `make validate`, exact P0-T16 packet validation, lifecycle/project-state validators and
  `git diff --check`: passed;
- full `make ci` on that exact head: **503 Python tests passed**, **230 reference tests passed**, with Ruff,
  validators, deterministic simulation and SHA-256 evidence passed;
- state S-0016 and canonical source `55d08c76b7fcdc3b6c256d35a4d74b275652964c` are bound to
  the protected baseline and all derived projections match.

## Exact hosted checks on the test-hardening head

PR #82 has base `55d08c76b7fcdc3b6c256d35a4d74b275652964c`, head
`a43a0fa32650524ad4759cf0f0676d4bab690363`, and merge state `CLEAN`. The exact head passed
Validate and test (`98754113702`), analyze-python (`98754113669`), reference-core
(`98754113745`), CodeQL (`98754217984`), SonarCloud (`98754145177`, zero annotations), and
GitGuardian (`98754099320`). Dependency Review (`98754114917`) was skipped by the existing
workflow policy. SonarCloud reported a passing Quality Gate, 0 new issues, 0 accepted issues
and 0 security hotspots. The documentation receipt below is intentionally revalidated on its
own exact head before the final Sol decision.

## Boundaries and residual limitations

No secret was read or written. No GitHub/Sonar setting or issue was mutated. No hardware probe,
model inference, model download, runtime/backend/ABI/FFI/kernel, CUDA or ROCm operation was
performed. This is not real-model conformance, tokenization, model-format support, attention,
KV-cache, scheduling, production-decoder, P1/P2 or performance evidence. ADR-0005 and ADR-0006
remain `proposed`; P0-T10 remains `review` and P0-T15 remains design-only `in_progress`.

**Final verdict:** the implementation/test-hardening head is independently reviewed and hosted-green; the final documentation receipt, exact-head Sol gate and protected merge remain pending.
