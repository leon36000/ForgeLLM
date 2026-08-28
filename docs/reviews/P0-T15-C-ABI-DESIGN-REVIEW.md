# P0-T15 independent architecture review

## Scope and exact heads

- Task: `P0-T15` — stable versioned C ABI and runtime lifecycle design.
- Canonical protected base: `ad079c0bf6f86b044f1d1d819cb105e3afe5a65f`.
- Initial review head: `3060864f2d3407013ce643b77acdbfd1ec4d57f4`.
- Fix-round review head: `b5fa926e6c609d073ef68774eb912b7e3cc99079`.
- Changed design paths: ADR-0006, the P0-T15 primary-source record, the
  bounded implementation plan, and the P0-T15 task packet. No ABI header,
  exported symbol, FFI/runtime/backend implementation, dependency, or binding
  is part of this task.

## Initial Luna review

- Reviewer: `gpt-5.6-luna`.
- Exact review: `ad079c0bf6f86b044f1d1d819cb105e3afe5a65f..3060864f2d3407013ce643b77acdbfd1ec4d57f4`.
- Implementation-scope verdict: `ACCEPT`.
- Task-quality verdict: `NEEDS FIXES`.
- Findings: lifecycle release semantics conflicted between research and ADR;
  bootstrap entry-point semantics drifted; `abi_version` acceptance was not
  explicit; one verification command named a nonexistent script; and the
  Wasmtime source was not pinned.

## Fix-round disposition

The fix round at `b5fa926e6c609d073ef68774eb912b7e3cc99079`:

- makes non-terminal request release uniformly return `INVALID_STATE`, consume
  nothing and never block;
- makes `get_api(requested_version)` the one bootstrap entry point and places
  version/build information on the selected immutable table;
- defines v1 `abi_version` as the exact selected API-table version, with
  mismatch rejection and explicit same-table-version shorter-prefix rules;
- replaces nonexistent validation commands with the repository's actual
  `validate_task_packet.py` and `validate_project_state.py` commands; and
- pins the Wasmtime C API evidence to v48.0.1 commit
  `7bac2c2775808aaec5d4aa5627a5e447b51102cf`.

## Scoped re-review

- Reviewer: `gpt-5.6-luna`.
- Exact review: `ad079c0bf6f86b044f1d1d819cb105e3afe5a65f..b5fa926e6c609d073ef68774eb912b7e3cc99079`.
- Prior findings: all five `ADDRESSED`.
- New findings: `none`.
- Implementation-scope verdict: `PASS` / `ACCEPT`.
- Task-quality verdict: `CONDITIONAL ACCEPT`, pending fresh `make ci`, hosted
  checks, and the required independent GPT-5.6-Sol architecture/security gate.
- Residual evidence boundary: no ABI behavior, C/C++ compatibility,
  symbol/layout, panic, sanitizer, fuzz, concurrency, hardware, CUDA/ROCm,
  backend, publication, or secret evidence is claimed. P0-T15 is a proposed
  design and does not authorize implementation.

## Sol gate and remediation

- Blind GPT-5.6-Sol reviewed exact head `240be7be298dbffb9b6b2068a7c2f5e02c945258`
  against base `ad079c0bf6f86b044f1d1d819cb105e3afe5a65f` and returned
  `VERDICT=NO-GO` with two `MAJOR` findings: ABI-visible structures were not
  explicitly pointer-only, and the post-`fork` rule incorrectly permitted a
  child to create a runtime before `exec`.
- Remediation commit `428766443cc1c8ad6655e3f1a51572feabb04090` requires
  `const` input pointers and mutable output pointers for all ABI-visible
  aggregate structures, prohibits public by-value aggregate parameters and
  returns, adds C11/C++17 signature-fixture gates, and forbids ForgeLLM calls
  in a child after `fork` and before `exec` when a live runtime was inherited.
- The Sol findings are addressed pending fresh exact-head independent review,
  local/hosted verification and a new blind Sol gate. ADR-0006 remains
  `proposed`; no ABI implementation is authorized.

## Independent re-review of Sol remediation

- Reviewer: `gpt-5.6-luna`.
- Exact remediation review: `240be7be298dbffb9b6b2068a7c2f5e02c945258..35bb8231edd7b59100fb73b431a4e78acca24f01`.
- Prior finding 1, ABI aggregate by-value risk: `ADDRESSED` by the explicit
  pointer-only rule (`const` inputs, mutable outputs), no public aggregate
  by-value parameters or returns, and future C11/C++17 signature fixtures.
- Prior finding 2, unsafe child runtime creation after `fork`: `ADDRESSED` by
  prohibiting ForgeLLM calls in the child before `exec` when a live runtime was
  inherited; fresh runtime creation is post-`exec` only absent a later accepted
  fork-safety design.
- New findings: `none`.
- Implementation verdict: `ACCEPT`.
- Task-quality verdict: `CONDITIONAL ACCEPT`, pending the controller's fresh
  final local evidence, hosted checks and blind GPT-5.6-Sol acceptance.
- Residual boundary: no ABI header/symbol/FFI implementation, binary
  compatibility, runtime/backend, hardware, CUDA/ROCm, publication or secret
  evidence is claimed. ADR-0006 remains `proposed`.
