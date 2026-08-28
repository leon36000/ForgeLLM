# P0-T16 — Rust Reference-Core CI Gate Evidence

- Task: P0-T16 — wire the Rust reference-core suite into the required repository gate
- Canonical base: `ad079c0bf6f86b044f1d1d819cb105e3afe5a65f` (protected `main`, includes merged PR #77 provenance repair and PR #78-line P0-T13 hardening)
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
  - `cargo test --workspace --all-targets --locked`: **46/46 passed** (2 unit in `allocation_tests.rs`, 3 `numerical_contract.rs`, 17 `decoder_primitives.rs`, 24 `reference_ops.rs`) — matches the count already documented in `docs/roadmap/PHASE0_TASKS.md`.
  - Python side unchanged and still green: 487 full `pytest` tests, 230 focused speculative-decoding tests, cache-placement simulation hash checks all pass.
- Before this change: `git stash` the Makefile edit and re-run `make ci` — completes with **zero** `cargo` invocations anywhere in the output (confirmed by `grep -c cargo` on the captured log: 0 before, 3 after).
- `git diff --check`: clean. `git status --short`: only this task's files.

**Correction:** an earlier version of this document and the original PR description stated 471 pytest tests. That count was captured in this same clone before it was rebased onto the current base (`ad079c0…`, which includes PR #78's P0-T13 test additions) and was never re-verified after the rebase before being written down — a process lapse, not a fabricated number. An independent reviewer flagged the discrepancy against the real hosted CI log; re-running `python3 -m pytest -q` fresh (new venv, this exact head) confirms **487** is the correct, reproducible count on both this PR's base and head. Corrected here and in the PR description.

## Non-claims

This task does not make `reference-core` a required GitHub branch-protection status check — that is a repository-settings change reserved for the owner (`AGENTS.md §9`: destructive/administrative changes require explicit owner authorization; the tool operating this session does not perform GitHub settings mutations under any authorization). It is recorded here as a direct recommendation: add `reference-core` to `tools/repository-policy.yaml`'s `required_checks` and to the branch ruleset once this PR is merged, so a future PR cannot silently skip Rust verification the way every PR could before this change.

## Related finding, not fixed by this task

While preparing this task, a separate root cause was found for why `make validate`'s `validate-loop` step can pass in hosted CI on a stale `declaration_source_commit` reference that a normal `git clone` cannot see: `scripts/validate_loop_engineering.py`'s `_ensure_revision` only attempts an exact-SHA `git fetch origin <sha>` fallback when `.git/shallow` is present locally — i.e., only on a shallow checkout (as GitHub Actions' default `fetch-depth: 1` produces), never on a full clone, even though the same fetch-by-exact-SHA would succeed there too. PR #77 (merged, `6c38e39098`) already replaced the specific stale reference this task started from with a genuine ancestor commit (`87a1ddeb76d2bca45fe75853b4c3b4c9f19c78b0`, independently verified against a fresh clone), so this is not currently causing a failure — but the underlying shallow-only fetch gate remains a latent gap for any future stale reference. Not fixed here: this task's `allowed_paths` deliberately excludes `scripts/validate_loop_engineering.py` and `artifacts/governance/loop-engineering/` (see the P0-T16 task packet's `forbidden_actions`), since that validator is hard-pinned to `task_id == "P0-T10"` and deserves its own scoped decision.
