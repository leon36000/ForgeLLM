# ForgeLLM Agent Contract

These rules apply to every AI or human contributor in this repository unless a more specific nested `AGENTS.md` overrides them.

## 1. Mission

Build ForgeLLM as a rigorously verified, heterogeneous LLM inference engine. Optimize only after correctness, measurement quality, and reproducibility are established.

## 2. Mandatory startup sequence

Before proposing or changing anything:

1. Read `docs/architecture/PROJECT_CHARTER.md`.
2. Read `docs/architecture/ARCHITECTURE_PRINCIPLES.md`.
3. Read `docs/state/CURRENT_STATE.md`.
4. Read `docs/state/DECISIONS.md`, `RISKS.md`, `OPEN_QUESTIONS.md`, and `HANDOFF.md`.
5. Read the active task packet or linked issue.
6. Run `make validate` before editing when the checkout is expected to be healthy.
7. State the task identifier, intended deliverable, non-goals, and verification plan in your work log.

Do not rely on conversation memory for facts that should be in the repository.

## 3. Anti-drift gate

Every task must map to at least one charter goal and must not silently expand scope.

Stop and open a decision record when any of these occur:

- the requested change conflicts with an accepted ADR;
- a new dependency, wire format, model format, backend ABI, or public API is introduced;
- an optimization changes numerical behavior;
- benchmark methodology changes;
- the task would weaken a security or reproducibility gate;
- the work cannot satisfy its acceptance criteria with available evidence.

A useful discovery outside scope goes to `docs/state/OPEN_QUESTIONS.md` or a new issue; it is not implemented opportunistically.

## 4. Evidence rules

- Prefer peer-reviewed papers, official preprints, official repositories, official documentation, and vendor specifications.
- Record source URL, access date, version or commit, claim, limitations, and reproduction status.
- Treat author-reported performance as `external_unreproduced` until ForgeLLM reproduces it.
- Never compare throughput without matching model, revision, precision, quantization, workload, scheduler policy, output length, hardware, software stack, warm-up, and concurrency.
- Preserve raw artifacts and SHA-256 hashes.
- Clearly separate fact, inference, hypothesis, decision, and measurement.

## 5. Engineering workflow

- One issue or task packet per branch and worktree.
- Never push directly to `main`.
- Keep pull requests small enough for an independent reviewer to reason about.
- Write the failing test or executable oracle before implementation where feasible.
- Implement the smallest change that passes the test.
- Run relevant unit, integration, sanitizer, differential, and benchmark checks.
- Commit intentionally; do not mix refactors with behavior changes.
- Update state, ADRs, risks, research records, and handoff material in the same pull request when they changed.

## 6. Correctness hierarchy

1. Reference semantics against a trusted implementation.
2. Deterministic unit tests and property tests.
3. Differential tests across backends and precisions.
4. Numerical error budgets documented per operation and model path.
5. Sanitizers, race detectors, fuzzing, and fault injection.
6. Performance measurements only after the above pass.

A faster incorrect kernel is a regression.

## 7. Performance claims

A performance claim is mergeable only when it includes:

- baseline commit and candidate commit;
- clean worktree confirmation;
- exact hardware inventory and topology;
- driver, firmware, runtime, compiler, library and container versions;
- model identifier and immutable revision;
- workload manifest and random seeds;
- warm-up and measured run counts;
- raw samples, summary statistics and variability;
- power and thermal notes when relevant;
- correctness comparison;
- machine-readable result conforming to `schemas/benchmark-result.schema.json`.

Use median and tail metrics. Do not report only a best run.

## 8. Language boundaries

- Rust owns orchestration, lifecycle, scheduling, safe resource abstractions, service logic and observability.
- Native GPU kernels remain in the ecosystem best suited to the target hardware.
- Unsafe Rust and FFI are confined to small reviewed crates with explicit safety invariants.
- C ABI boundaries use opaque handles, explicit ownership, versioned structs and error codes.
- Python stays outside the per-token hot path unless measurement proves otherwise.
- Portable kernels are valuable, but do not replace specialized kernels without evidence.

## 9. Security and supply chain

- Never commit credentials, model access tokens, private datasets, machine identifiers or secrets.
- Pin third-party CI actions to full commit SHAs.
- Review dependency and license changes.
- Generate SBOM and provenance for release artifacts.
- GPU runners must be private, restricted, ephemeral where possible, and unable to run unreviewed fork code.
- Destructive commands, force pushes, repository deletion and credential changes require explicit owner authorization.

## 10. Required completion report

End every task with:

1. task identifier and result;
2. files changed;
3. tests and commands run with outcomes;
4. evidence added;
5. known limitations and residual risks;
6. state or decision records updated;
7. exact next recommended task.

Do not claim completion when required checks were not run. State what was not verified and why.
