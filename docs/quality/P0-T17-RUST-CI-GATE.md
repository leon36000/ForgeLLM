# P0-T17 — Rust Reference-Core CI Gate Evidence

- Task: P0-T17 — wire the Rust reference-core suite into the required repository gate (renamed from P0-T16, which PR #82 claimed for an unrelated dense-decoder feature merged concurrently)
- Canonical base (rebased once, after main advanced during review): `0458f765ee91f482ce64d9c72fe357335129343e` (protected `main`, includes merged PR #77 provenance repair, PR #78-line P0-T13 hardening, #80 P0-T14 lifecycle enforcement, #81 state-anchor repair, #82 dense-decoder reference, and a corrected/re-reviewed C-ABI merge)
- Evidence boundary: build/CI tooling only; no change to `crates/forgellm-reference/src/lib.rs` or any numerical behavior.

## Change

`Makefile`'s `ci` target previously invoked zero `cargo` commands — a required, protected-`main` branch check (`Validate and test` → `make ci`) could pass while `crates/forgellm-reference` was untested, unformatted, or lint-failing. The only Rust check, `.github/workflows/rust-reference.yml`, is path-filtered to `crates/**`/`Cargo.*` and is not a required status check (verified via `gh api repos/leon36000/ForgeLLM/rulesets/20820530`: `required_status_checks` names only `Validate and test`).

The fix appends a guarded recipe block to the existing `ci:` target (no existing line modified):

```makefile
ci: lint verify verify-speculative simulate-cache-draft
	if [ -f Cargo.toml ]; then \
	  cargo fmt --all --check && \
	  cargo clippy --workspace --all-targets --locked -- -D warnings && \
	  cargo test --workspace --all-targets --locked; \
	fi
```

The `[ -f Cargo.toml ]` guard keeps `make ci` usable in a hypothetical future checkout that doesn't include the Rust workspace; on the current repository it is always true.

## Verification (this exact head, this exact commit)

- Toolchain: `rustc 1.97.1 (8bab26f4f 2026-07-14)`, installed via `rustup toolchain install 1.97.1 --profile minimal --component rustfmt,clippy` — matches `rust-toolchain.toml`/`rust-reference.yml` exactly.
- `make ci` (full target, Python + Rust): **exit 0**.
  - `cargo fmt --all --check`: pass (no diff).
  - `cargo clippy --workspace --all-targets --locked -- -D warnings`: pass (0 warnings).
  - `cargo test --workspace --all-targets --locked`: **53/53 passed** (2 unit, 17 `decoder_primitives`, 7 `dense_decoder` [new in #82, merged during this task's review], 3 `numerical_contract`, 24 `reference_ops`).
  - Python side unchanged in behavior (this task touches no Python source) and still green: 503 full `pytest` tests (up from 487 at this task's original base, due to #80's lifecycle test additions), 230 focused speculative-decoding tests, cache-placement simulation hash checks, and the new `validate-lifecycle` check (README.md/TREE.txt projections, regenerated for this task's own new files) all pass.
- Before this change: `git stash` the Makefile edit and re-run `make ci` — completes with **zero** `cargo` invocations anywhere in the output (confirmed by `grep -c cargo` on the captured log: 0 before, 3 after).
- `git diff --check`: clean. `git status --short`: only this task's files.

**Corrections, in order:** (1) an earlier version of this document stated 471 pytest tests, captured before a rebase and never re-verified — corrected to 487 after an independent reviewer flagged the discrepancy against the real hosted CI log. (2) After that correction, `main` advanced again (PR #82 claimed task ID P0-T16 for an unrelated dense-decoder feature; PR #80 added a new lifecycle validator requiring README.md/TREE.txt to stay in sync with tracked files/task statuses). This task was renamed P0-T16→P0-T17, rebased onto the new base, and README.md/TREE.txt regenerated using the validator's own functions (`forgellm_governance.validation._task_status_map`, `_extract_state_metadata`) rather than hand-edited, to guarantee an exact match. All counts in this document are from that final rebased state, re-verified fresh.

## Non-claims

This task does not make `reference-core` a required GitHub branch-protection status check — that is a repository-settings change reserved for the owner (`AGENTS.md §9`: destructive/administrative changes require explicit owner authorization; the tool operating this session does not perform GitHub settings mutations under any authorization). It is recorded here as a direct recommendation: add `reference-core` to `tools/repository-policy.yaml`'s `required_checks` and to the branch ruleset once this PR is merged, so a future PR cannot silently skip Rust verification the way every PR could before this change.

## Related finding, not fixed by this task

While preparing this task, a separate root cause was found for why `make validate`'s `validate-loop` step can pass in hosted CI on a stale `declaration_source_commit` reference that a normal `git clone` cannot see: `scripts/validate_loop_engineering.py`'s `_ensure_revision` only attempts an exact-SHA `git fetch origin <sha>` fallback when `.git/shallow` is present locally — i.e., only on a shallow checkout (as GitHub Actions' default `fetch-depth: 1` produces), never on a full clone, even though the same fetch-by-exact-SHA would succeed there too. PR #77 (merged, `6c38e39098`) already replaced the specific stale reference this task started from with a genuine ancestor commit (`87a1ddeb76d2bca45fe75853b4c3b4c9f19c78b0`, independently verified against a fresh clone), so this is not currently causing a failure — but the underlying shallow-only fetch gate remains a latent gap for any future stale reference. Not fixed here: this task's `allowed_paths` deliberately excludes `scripts/validate_loop_engineering.py` and `artifacts/governance/loop-engineering/` (see the P0-T17 task packet's `forbidden_actions`), since that validator is hard-pinned to `task_id == "P0-T10"` and deserves its own scoped decision.
