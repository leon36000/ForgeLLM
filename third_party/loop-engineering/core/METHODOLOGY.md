# Loop Engineering — Methodology

This file is the operational core loaded by both adapters (Claude Code and
Codex). It is dense on purpose: rules and mechanisms, not essays. When this
file and an adapter file disagree, this file wins.

## Definition

Loop engineering: stop writing individual prompts and construct **verified
loops** instead — *goal → action → feedback → stopping condition*. The loop
only advances when an external verification gate passes.

Origin: Boris Cherny's workflow ("I don't prompt Claude anymore. I have loops
that are running… My job is to write loops"), labeled "loop engineering" by
third parties (guide: https://cocodedk.github.io/loop-engineering/). The label
is marketing; the mechanics are real.

## Loop anatomy

Every loop declares these six fields **before** it starts:

```
GOAL     — one sentence, a verifiable condition. Never a task list.
SCOPE    — the bounded unit (module / package / crate / service / directory).
           Gates never run project-wide except at milestone close.
VERIFY   — the exact command that decides pass/fail. It must be able to fail,
           and it must EXECUTE the behavior, not merely compile or lint it.
BUDGET   — iteration ceiling (default 8–10); optionally time/cost ceilings.
STOP     — green gate (success), or N identical consecutive failures
           (stuck, default 3), or budget exhausted.
RECEIPT  — the file path where this run is recorded
           (docs/receipts/<goal-id>-<slug>.md).
```

A loop with a missing field is not a loop; it is an open-ended conversation.
Refuse to start it until all six are declared.

Before implementation, create a small plan at
`docs/plans/<goal-id>-<slug>.md`: intended files, phases, risks,
alternatives and any expected files outside SCOPE. It is a change-control
artifact, not a second backlog: update it only when scope or risk changes.

## Verification principles

1. **The generator is never the judge.** The session that writes the code does
   not decide the gate passed — the VERIFY command does. After a loop reports
   success, an *independent* run of the gate (fresh invocation, not the loop's
   own memory of it) is the confirmation.
2. **Design the verify before the code.** The TDD instinct applied as the
   loop's stopping condition: if you cannot write the VERIFY command, the goal
   is not ready to loop.
3. **The gate must execute behavior.** A gate that can't fail, or that only
   checks compilation, lets a loop converge on something that *looks* done.
   "It compiles" is never the definition of done.
4. **Cheap check before expensive gate.** Run the fast static filter first so
   you don't pay for the full suite when the code doesn't even typecheck:

   | Stack      | Cheap filter                  | Real gate (scoped)               |
   |------------|-------------------------------|----------------------------------|
   | Rust       | `cargo check -p <crate>`      | `cargo test -p <crate> <filter>` |
   | TypeScript | `tsc --noEmit`                | `vitest run <path>` / `jest <path>` |
   | Python     | `ruff check` + `mypy <pkg>`   | `pytest <path>`                  |
   | Go         | `go vet ./pkg/...`            | `go test ./pkg/...`              |
   | Anything   | linter / typechecker on scope | the scoped test/behavior command |

   The pattern is what matters, not the tools: *static filter && scoped
   behavioral test*, discovered per-project during `start` Phase 2.
5. **Scoped, not global.** Project-wide gates run only at milestone close.
   A per-goal gate scoped to the whole project makes every iteration pay for
   the whole world and hides which change broke what.
6. **Feed back raw output.** When the gate fails, the next iteration receives
   the exact failure output — not a summary — with the instruction: *fix the
   real cause, not the check*. Weakening a test or skipping an assertion to
   go green is a method violation, not a fix.
7. **Evidence is reproducible.** A passing receipt records the final command
   and output, revision, changed files, plan, and scope-check result. A green
   claim without this evidence is incomplete.
8. **Scope is enforced at close.** Compare the changed files with SCOPE before
   closing. Files outside it need a written exception in the plan or belong in
   another goal; never hide scope expansion behind a passing gate.

## Human-verified goals

Some goals cannot have a runnable gate (visual design, IME behavior, screen
readers, wording). Mark them `Verify: human — <description of the manual
check>` in the goal map. The loop for such a goal ends with a guided manual
check, and the receipt records **who checked it and what they observed**.
Never silently downgrade a human gate to "looks right to me".

## The project record

| Layer | What it stores | Write trigger |
|---|---|---|
| Agent memory file (`CLAUDE.md` / `AGENTS.md`) | Durable corrections and working rules that would otherwise repeat ("never run the global suite in a goal gate", "encoding detection always needs a BOM test"). | Whenever a loop fails **twice for the same avoidable reason**. |
| `docs/adr/NNNN-*.md` | Architecture decisions: context, alternatives considered, decision, consequences (including downsides accepted). | On any significant technical decision or reversal. Superseded by a new ADR, never rewritten. |
| `docs/STATUS.md` | What actually exists, per area/platform: `implemented` / `partial` / `not-started`. | In the same change that alters behavior. |
| `docs/plans/<goal-id>-<slug>.md` | Intent before edits: scope, phases, risks, alternatives and scope exceptions. | Before starting a goal; revise only when scope/risk changes. |
| `docs/receipts/<goal-id>-<slug>.md` | The log and reproducible evidence of one loop run: iterations, failures, final command/output, revision, changed files and result. | On closing (or abandoning) each loop. |

An ADR explains a decision that survives forever; a plan controls a change;
a receipt proves its result. These files let the **next session resume
without the human re-explaining anything** — read the relevant plan and
receipt before writing new code.

## Budgets and the stuck protocol

Always set all three ceilings:

- **Iterations** — default 8–10. Raise only if loops consistently converge
  near the ceiling.
- **Identical consecutive failures** — default 3. The same error repeating
  means the loop is not learning from feedback; it is retrying.
- **Time/cost** — mandatory for unattended runs; recommended when a single
  iteration is expensive (heavy compilation, long suites).

When a loop gets stuck, the correct response is **never "raise the ceiling
and relaunch"**. It is:

1. Read the receipt.
2. Classify the cause:
   - **Bad gate** — the VERIFY was wrong, ambiguous, or asked for something
     impossible.
   - **Missing dependency** — the goal needed something another goal hasn't
     delivered yet.
   - **Ambiguous goal** — the GOAL sentence admitted multiple readings.
   - **Environment problem** — the failure is in the test environment, not
     the code (classic example: a temp git repo with no `user.name`
     configured failing every commit).
3. Then: reformulate the goal, split it into smaller loops, or escalate to a
   human decision recorded as an ADR.

## Orchestration

- **Sequential by default.** One loop at a time is the mode that stays
  debuggable.
- **Parallel only for disjoint scopes.** Two goals may run concurrently only
  if they touch different scopes and neither depends on an API the other has
  not stabilized. In Claude Code, use git worktrees (`claude --worktree
  <name>`); Codex CLI has no worktree flag — run sequentially or manage
  `git worktree` by hand.
- **Chained for milestones.** A milestone is a chain of loops ending in a
  closing goal that runs the full project-wide gate.
- **Integrate one branch at a time.** Each parallel branch is re-verified
  with an independent gate run before merge — never merge all at once.
- **Plan integration, too.** `parallel` writes the branch/worktree, overlap
  check, merge order and post-merge gate to `docs/plans/integration-*.md`.
  It does not launch agents or create worktrees.
- **Watch is bounded observation, not automation.** A watcher may re-run a
  goal gate after new commits, but it has a time budget and stops after three
  identical failures. It records results; it never edits, restarts loops or
  runs forever.

## When NOT to loop

Say so instead of forcing the pattern:

- **Exploratory or design work** — there is no gate to converge on; the
  output is understanding, an ADR, or a plan.
- **One-shot trivial edits** — the loop overhead exceeds the work.
- **Inherently human verification** — visual design, wording, feel. Use a
  `Verify: human` goal if it must be tracked, or just do the work.

## Non-negotiable rules (the working agreement)

These are the rules `start` writes into every project's working agreement:

1. **Nothing simulated.** A capability is fully implemented or it does not
   exist. No stubs that return plausible data, no UI for unimplemented
   features. A stub that looks right is worse than a visible failure.
2. **The gate decides, not the generator.** No goal is done until its VERIFY
   command passes in an independent run.
3. **Scoped verifies.** Goal gates run on the goal's SCOPE; project-wide
   gates only at milestone close.
4. **Budgets always.** Every loop declares iteration, identical-failure and
   (when unattended) time/cost ceilings before starting.
5. **Stuck → diagnose, don't relaunch.** Follow the stuck protocol; never
   just raise the budget.
6. **Memory discipline.** Repeated corrections go to the agent memory file;
   decisions to ADRs; reality to STATUS.md; every run to a receipt.
7. **When a target is unreachable, stop and report.** Write up the finding
   and propose alternatives. Explicitly preferred over shipping something
   that looks like it works.
8. **Plans and evidence stay honest.** Plan before editing; record final
   evidence and explain every scope exception before closing a goal.
