# P0-T10 — Bounded Loop Engineering Evidence

- Task: P0-T10 — bounded Loop Engineering static integration
- Canonical base: f8364f12402c3c58796dbc1b56f8c65d378e88de
- ADR: ADR-0005-bounded-loop-engineering.md, proposed and not yet accepted
- Evidence boundary: governance/reference validation only; no runtime, inference, hardware, backend, benchmark, or Sonar activation claim

## Selected boundary

ForgeLLM uses a project-local bridge around an inert, pinned upstream reference. Git task packets and accepted ADRs remain authoritative. A loop declaration may narrow task-packet authority but cannot widen paths, verification commands, decisions, or privilege.

The bridge validates the six semantic fields GOAL, SCOPE, VERIFY, BUDGET, STOP, and RECEIPT. It has no autonomous runner, shell evaluator, Stop hook, installer, adapter, credential capability, or external mutation path.

The repository gate also supports GitHub's shallow checkout safely: when a fixed, full SHA required by an indexed declaration or receipt is absent locally, it fetches only that exact ForgeLLM revision from the configured `origin`, then verifies the commit/blob or diff. It never fetches a floating branch or interprets an untrusted shell command.

The validator keeps the subprocess boundary explicit (`shell=False`), rejects control characters before invoking Git, and uses only fixed subcommands plus validated revision/path tokens. It also requires receipt `base_commit` and `final_commit` to be real Git commits with an ancestor relationship. The receipt's `final_commit` identifies the reviewed implementation head; later catalog-only receipt binding does not change that implementation evidence. The hosted quality gate's complexity findings are addressed by keeping declaration, index, and reviewer checks in small single-purpose helpers.

## Upstream provenance

The reviewed source is https://github.com/lcajigasm/loop-engineering at commit ae2d610985064bb30c5013261988c813013c09e3, licensed under MIT. The license Git blob is 84524f23b209fccb02a8f239165f0444bfd70f3f.

The exact selected upstream blob bindings are recorded in third_party/loop-engineering/PROVENANCE.yaml and checked by validate_vendor_provenance. The local tree is required to contain only LICENSE, PROVENANCE.yaml, core/METHODOLOGY.md, core/COMMANDS.md, and the four selected core templates. install.sh, scripts, hooks, adapters, and shadow-state templates are excluded.

## Verification evidence

- Controller RED tests initially failed at collection because validate_vendor_provenance was absent.
- The focused controller suite is the required regression gate for the firewall, authority, receipt, provenance, skill, marker, and Makefile contracts.
- make validate-loop validates the P0-T10 packet and the repository catalog/provenance gate.
- make validate retains all existing project and P0-T09 validation commands through a dependency on validate-loop.
- ADR-0005 remains proposed pending independent architecture/security review.

## Public closeout record

- Public merge: PR #65, `main@87a1ddeb76d2bca45fe75853b4c3b4c9f19c78b0`.
- Receipt binding: `base_commit=f8364f12402c3c58796dbc1b56f8c65d378e88de`, `final_commit=87a1ddeb76d2bca45fe75853b4c3b4c9f19c78b0`; the 29 recorded paths equal `git diff --name-only f8364f1..87a1dde`.
- Independent gate record: GPT-5.6-Terra/Kepler accepted the implementation head; GPT-5.6-Terra/Chandrasekhar accepted the catalog-only binding. The final public-head correction was required because the first receipt named a private pre-merge commit; no source or scope change was introduced by that correction.
- Post-merge local evidence: `make ci` passed with 464 complete tests and 230 focused speculative tests; the focused P0-T10 suite passed 86 tests, and task-packet, catalog/provenance, lint, format, and diff checks passed.
- Hosted PR evidence: Phase 0, CodeQL, GitGuardian and SonarCloud succeeded; Dependency Review was `SKIPPED` under the existing workflow configuration.
- Scope boundary: no P0-T09 activation, token, hardware probe, runtime, backend, CUDA/ROCm, or model execution was performed. ADR-0005 remains proposed pending explicit architectural acceptance.

## Terra gate remediation

The first exact-head review rejected the candidate for process-substitution parsing, synthetic declaration-source commits, receipt path omissions, and unbound reviewer evidence. The bridge now rejects `>(...)`/`<(...)`, verifies that the indexed declaration commit exists and contains the exact non-executable blob, compares receipt `changed_paths` with the Git base-to-final commit range, and binds an independent review record to the final commit and `ACCEPT` disposition. These controls remain local governance validation; they do not authorize runtime, privileged, or external administrative operations.

## Limitations and non-goals

This increment does not authorize or validate P0-T09 implementation/settings/tokens, GitHub or Sonar administration, hardware probing, model execution, runtime/backend/kernel work, Cargo/Rust changes, chatgpt/mobile-core changes, or closed task packets.
