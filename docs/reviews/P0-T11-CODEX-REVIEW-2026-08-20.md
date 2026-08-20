# P0-T11 independent review — 2026-08-20

## Verdict

`ACCEPT` for the exact publication head:

```text
head       dfd6849cfc3c48e801f1e495239f2ec1ad810569
base       aff9897e1c9e3aaebd67889eb9ff6d65a1710694
merge      04342c859f790948fa784b72df940ac441ed5ed3
toolchain  rustc/cargo 1.97.1, x86_64-unknown-linux-gnu
```

The fresh independent Codex review found no concrete findings. A first review identified and
blocked two out-of-allowlist documentation changes; those files were removed before publication,
and a second review accepted the corrected head.

## Evidence

- `cargo test --workspace --all-targets --locked`: **28/28** Rust tests passed (1 allocation,
  3 numerical, 24 reference).
- `cargo fmt --all --check`: passed.
- `cargo clippy --workspace --all-targets --locked -- -D warnings`: passed.
- `PYTHONDONTWRITEBYTECODE=1 make validate`: passed.
- `PYTHONDONTWRITEBYTECODE=1 make ci`: passed with **371** Python tests, **230** focused
  speculative tests, and the deterministic simulation hash check.
- `git diff --check`: passed; generated Cargo and simulation outputs were removed.
- Hosted PR #48 checks passed: Validate and test, reference-core, CodeQL, SonarCloud and
  GitGuardian. Dependency Review was `SKIPPED` by the existing workflow configuration.

The exact PR head merged to protected `main` as `04342c859f790948fa784b72df940ac441ed5ed3`.

## Boundaries

P0-T11 is a bounded CPU reference experiment. It does not establish real-model conformance,
PyTorch numerical agreement, GPU behavior, ABI compatibility, scheduling, performance, service
runtime behavior, P1/P2 promotion, or production readiness.
