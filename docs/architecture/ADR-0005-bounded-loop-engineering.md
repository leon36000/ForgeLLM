# ADR-0005: Adopt bounded Loop Engineering through a ForgeLLM bridge

- **Status:** proposed
- **Date:** 2026-08-19
- **Owners:** ForgeLLM project owner / chief architect delegate; independent architecture and security reviewer required
- **Related tasks/claims:** P0-T10, issue #36, R-006, R-007, R-014, R-015

## Context

ForgeLLM needs long-running and repetitive engineering work to remain bounded, observable, interruptible, reproducible, and externally verifiable. The project charter requires small verified changes, Git-backed project records, issue/task-packet authorization, and ADRs for architecture changes. ADR-0002 already establishes Git as the source of truth, so an orchestration method may accelerate work but may not introduce an equal or higher competing state system.

The reviewed upstream candidate is `lcajigasm/loop-engineering` at exact commit `ae2d610985064bb30c5013261988c813013c09e3`. Its useful contract centers on six loop fields: GOAL, SCOPE, VERIFY, BUDGET, STOP, and RECEIPT. It also provides bounded failure/retry conventions, receipts, scope checking, and separate verification concepts.

The upstream project is MIT licensed at blob `84524f23b209fccb02a8f239165f0444bfd70f3f`. The reviewed core files are `core/COMMANDS.md` blob `4de9e981ad89c04f28d94ea4ad5b97e1b513b578` and `core/METHODOLOGY.md` blob `c7094ca40c2257d653c4d48f6b87c40cb82b209b`.

The upstream package cannot be adopted unchanged. Its initialization model can create `docs/GOALS.md`, `docs/STATUS.md`, a project brief, a separate ADR hierarchy, and managed Working Agreement sections. That would duplicate ForgeLLM's existing canonical state/task/ADR system. Its installer writes Claude/Codex adapters, and its headless loop runner interprets a VERIFY command through shell evaluation. Optional Stop hooks can also run verification automatically. Those behaviors are broader than P0-T10 needs and would create unnecessary command-execution and authority surfaces.

On 2026-08-19 the owner approved the bounded vendored-and-bridged design (design B): pin upstream, preserve provenance/license, keep ForgeLLM Git authority, use isolated writers and external VERIFY gates, persist receipts, and deny loops authority over secrets or privileged systems.

## Decision

ForgeLLM will adopt the **Loop Engineering methodology only through a ForgeLLM-specific bounded bridge**.

1. **Authority remains unchanged.** Accepted charter/ADRs and the active ForgeLLM task packet outrank every loop declaration, plan, receipt, skill, prompt, or upstream document. Loop artifacts cannot authorize work, widen paths, change external privileges, or supersede canonical state.
2. **Upstream is pinned and vendored as static evidence/reference.** P0-T10 may vendor only a reviewed subset from exact commit `ae2d610985064bb30c5013261988c813013c09e3`, with the MIT license, upstream path/blob SHA, and local content hash recorded. No floating branch or runtime fetch is allowed.
3. **The upstream installer is not used.** `install.sh` will not run against ForgeLLM, the user home directory, or global agent directories. ForgeLLM creates its own thin adapters under project-local `.agents/skills/forgellm-loop-engineering/` and `.claude/skills/forgellm-loop-engineering/`.
4. **No shadow project state.** P0-T10 will not create upstream `docs/GOALS.md`, `docs/STATUS.md`, `docs/PROJECT_BRIEF.md`, or an upstream ADR numbering system. A ForgeLLM loop declaration is subordinate execution metadata bound to one existing task packet and one Git base revision.
5. **Six-field contract.** Every runnable ForgeLLM loop must declare GOAL, SCOPE, VERIFY, BUDGET, STOP, and RECEIPT. SCOPE must be a subset of the task packet `allowed_paths`; VERIFY must be one or more commands explicitly present in the task packet `verification_commands`; BUDGET must be finite and positive; STOP must include verifier-pass, budget-exhaustion, and repeated-identical-failure conditions; RECEIPT must identify the evidence destination.
6. **No eval-based headless runner.** The upstream runner is not vendored as an executable integration and is not invoked. Loop iterations are orchestrated by the active agent/controller using normal tool calls subject to ForgeLLM authorization. The external VERIFY gate is rerun independently before a passing receipt is accepted.
7. **No Stop hooks in P0-T10.** Claude Code or Codex Stop hooks are not installed or enabled. A future hook requires a separate task/review because it changes automatic command execution semantics.
8. **Privilege firewall.** A loop has no authority over secrets, credentials, accounts, billing, GitHub/Sonar administration, Tailscale, privileged hosts, runners, or other external state. Such actions remain separate explicitly authorized operations with before/after verification and cannot be obtained from a loop declaration.
9. **Isolation and review.** Each modifying loop uses one isolated branch/worktree and one writer. Architecture, security, unsafe/FFI, concurrency, distributed, performance, or migration work retains independent verification/review requirements. Parallel loops are allowed only when their write scopes are disjoint.
10. **Receipts are evidence, not authority.** Receipts bind task id, plan, base/final commit, changed paths, iteration counts, stop reason, verifier command/output or evidence reference, and scope check. A receipt cannot make an unauthorized change canonical.

## Alternatives considered

### A. Run the upstream installation and initialization unchanged

**Benefit:** fastest path to the upstream command set and automatic workflow.

**Rejected because:** it would write a competing GOALS/STATUS/ADR project record, modify agent instructions through upstream conventions, expose an eval-based runner, and optionally add Stop hooks. These conflict with ForgeLLM's existing authority hierarchy and least-privilege requirements.

### B. Vendored ForgeLLM bridge with bounded semantics

**Selected.** It preserves the useful six-field loop discipline, budgets, receipts, scope checking, and external verification while keeping the existing ForgeLLM governance model authoritative. The cost is maintaining a small adapter and provenance validator.

### C. Use only the ideas informally without installing/versioning anything

**Benefit:** smallest supply-chain surface.

**Rejected because:** informal use is difficult to reproduce, audit, or independently review and does not satisfy the requirement to install and operationalize Loop Engineering. A pinned static subset plus bridge provides a reconstructible boundary.

### D. Build an unrelated ForgeLLM loop framework from scratch

**Benefit:** full control.

**Rejected because:** it would duplicate a usable external methodology without evidence that a rewrite is necessary. ForgeLLM should adapt mature external work when a small boundary suffices.

## Consequences

Positive consequences:

- long agent work gets an explicit finite budget and stop policy;
- verification is structurally separated from the writer's claim of completion;
- scope drift and repeated identical failures become reviewable evidence;
- loop adoption is reproducible from pinned Git content rather than chat memory;
- Claude/Codex can share one ForgeLLM-specific orchestration contract.

Negative consequences and costs:

- ForgeLLM must maintain a compatibility bridge when upstream changes;
- upstream commands cannot be copied blindly; useful upstream changes require re-review and repinning;
- loops do not become autonomous privileged operators, so some administrative workflows remain manually/controller gated;
- no initial Stop hook means loop completion remains explicitly orchestrated rather than automatically intercepted at agent stop.

Operationally, P0-T10 adds one focused validation surface and receipts but does not authorize runtime, hardware, Sonar activation, or benchmark work.

## Safety and correctness invariants

- Git ForgeLLM is authoritative; loop artifacts are subordinate.
- One modifying task/loop has one writer and one isolated branch/worktree.
- A loop may narrow but never widen its task packet's path scope or verification authority.
- VERIFY is an external gate capable of failing; writer self-report is insufficient.
- BUDGET is always finite; repeated identical failure stops the loop for diagnosis instead of blind retry.
- No loop may obtain a secret or privileged external capability by declaring it in GOAL, SCOPE, VERIFY, or STOP.
- Vendored upstream content is inert unless a ForgeLLM adapter explicitly permits its use.
- Upstream provenance is immutable at the accepted SHA; updates require new evidence and review.
- A green loop result never overrides an accepted ADR, task non-goal, failed correctness oracle, or security gate.
- P0-T09 and P0-T04/P0-T05 boundaries remain unchanged by this ADR.

## Evidence required for review

Before acceptance:

1. validate the P0-T10 task packet and this ADR against current Git state;
2. record exact upstream commit, license, source blob SHAs, and local vendored hashes;
3. TDD proof that the ForgeLLM validator rejects scope widening, verifier widening, missing/invalid budgets, privileged capability requests, shadow-state authority, provenance mismatch, and incomplete receipts;
4. demonstrate a positive bounded declaration and receipt without invoking `install.sh`, an eval runner, or Stop hook;
5. run focused tests and the complete `make ci` gate on the exact PR head;
6. require CodeQL, GitGuardian, Sonar, and Phase 0 exact-head evidence;
7. obtain an independent architecture/security review of the final diff with no unresolved BLOCKER or MAJOR finding.

## Reversal condition

Reconsider or supersede this ADR if any of the following becomes true:

- the bridge cannot prevent loop state from diverging materially from the authoritative task packet;
- a loop or adapter can execute privileged/secret-bearing operations without a separate explicit authorization gate;
- external VERIFY cannot be made independent/reproducible;
- upstream changes remove the risky behaviors and provide a directly compatible authority model with materially lower maintenance cost;
- the bridge causes repeated task friction or failures that exceed its productivity benefit;
- a security review identifies a command-injection, scope-escape, or persistence path that cannot be fixed without abandoning the design.
