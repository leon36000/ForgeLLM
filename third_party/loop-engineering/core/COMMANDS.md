# Loop Engineering — Canonical Command Spec

This is the single source of truth for every command. Adapter files (Claude
Code commands, Codex prompts) are thin: they name the command, pass the
arguments, and defer here. Follow the matching section exactly.

Conventions used by every command:

- **Converse in the user's language; write files in English.** Every file a
  command creates or edits (goals, receipts, ADRs, status, scripts,
  agreements) is written in English, regardless of the conversation language.
- **Trust files over memory.** Project state is reconstructed from
  `docs/GOALS.md`, `docs/plans/`, `docs/receipts/`, `docs/STATUS.md`,
  `docs/adr/` and git history — never from what this session remembers.
- **Templates** live in `templates/` next to this file; the methodology in
  `METHODOLOGY.md`. Read them before generating project files.
- **Goal ids** are `G-<milestone><nn>` (e.g. `G-101`, `G-102`, `G-201`),
  stable, never reused. Milestones are `M1`, `M2`, …
- **Status marks** in `GOALS.md`: `[ ]` pending · `[~]` in progress · `[x]`
  passed · `[!]` stuck · `[$]` budget-exhausted.
- **Active-loop marker.** When a loop starts, write its VERIFY command to
  `.le-active-verify` at the project root (one line: the command; a second
  line: the goal id). Delete the file when the loop closes. The Claude Code
  stop hook reads it; on Codex it is documentation of what is in flight.
  Recommend adding `.le-active-verify` to `.gitignore` during `start`.
- **Plan and evidence.** Before editing a goal, create
  `docs/plans/<goal-id>-<slug>.md` from `templates/PLAN.template.md`. Before
  close, compare changed files since the loop's base revision with SCOPE;
  files outside SCOPE require a named exception in that plan. A passing
  receipt includes the final VERIFY command and output, final revision,
  changed files, plan path and scope-check result.

Adapter capability notes (referenced by the specs below):

- **Claude Code** has stop hooks, `--worktree`, headless mode (`claude -p`),
  and `/le:*` commands with arguments.
- **Codex CLI** has Stop hooks, but no worktree flag or scheduled-task
  manager. Offer its optional Stop hook during `start`. In every command that
  runs a loop, before declaring any goal done, the agent MUST re-run the
  VERIFY command itself in a fresh invocation and paste the final passing
  output into the receipt. `parallel` on Codex CLI emits a sequential plan
  instead of worktree launches.

---

## start [file|url]

Initialize loop engineering in the current project from a functional doc (or
an interview). Four explicit phases; never skip one, never reorder.

**Idempotency check (before Phase 1).** If `docs/GOALS.md` exists and starts
with the `# Goals —` header: the project is already initialized. Say so,
summarize current state (milestones, counts by status), and offer three
options: (a) re-plan via the `plan` command, (b) regenerate a specific
missing artifact, (c) abort. **Never** overwrite `docs/receipts/`,
`docs/adr/`, or goal history. Existing goal ids and their status marks are
preserved by any regeneration.

### Phase 1 — Ingest

- With a file argument: read it. Accept Markdown, plain text, HTML, PDF and
  DOCX (use whatever conversion tooling the environment has — e.g.
  `pdftotext`, `pandoc`, a PDF-capable Read tool). If a format cannot be
  read, say so plainly and ask for an alternative — do not guess at content.
- With a URL argument: fetch it and treat the content as the doc.
- With **no** argument: interview the user using
  `templates/PROJECT_BRIEF.template.md` as the questionnaire (what the
  project is, who it's for, major functional areas, tech stack, how it is
  built and tested today, explicit non-goals, quality constraints). Then
  write the answers into `docs/PROJECT_BRIEF.md`.
- Whichever path: the functional source must end up as a file in the repo.
  If it came from a URL or a file outside the repo, copy/convert it to
  `docs/PROJECT_BRIEF.md` (or reference the in-repo original).

### Phase 2 — Clarify

Process the functional source, inspect the repo (build files, test configs,
CI config, directory layout), and come back with **one batched, numbered
list** of every question needed — not a drip of one-question turns. First
discover repo-native capabilities: installed/project skills, configured MCP
servers, hooks and CI. Record only the ones that affect planning or VERIFY
in `docs/CAPABILITIES.md` from `templates/CAPABILITIES.template.md`; do not
install, enable or name irrelevant tools. Cover at minimum:

1. Proposed milestone boundaries — with a suggested cut, not an open
   question.
2. Verify tooling per functional area: test framework, linters, type
   checkers, and **how to run one module's tests in isolation**. Propose what
   you detected; ask only what you couldn't.
3. Sensible default budgets (propose 10 iterations / 3 identical failures).
4. Appetite for parallel loops (worktrees) vs strictly sequential.
5. Whether CI exists and what it runs.
6. Definition of done — is "compiles" ever acceptable? (Default answer: no.)
7. Anything ambiguous or contradictory in the source doc, quoted.

**Wait for answers before Phase 3.**

### Phase 3 — Generate

Create inside the target project (all in English, from `templates/`):

1. `docs/GOALS.md` — the exhaustive goal map from
   `templates/GOALS.template.md`: **every goal for the entire project**,
   milestone by milestone, each one loop-shaped (six fields). Goals without a
   runnable gate are marked `Verify: human — <manual check>`. Every
   milestone ends with a closing goal that runs the full project-wide gate.
   Every VERIFY command must be runnable exactly as written — execute the
   gate pattern once (against existing code, or expecting a clean failure)
   before recording it; an unrunnable gate fails on invocation, not
   behavior, and wastes the loop's first iterations.
2. `docs/STATUS.md` from `templates/STATUS.template.md`, rows seeded from
   the goal map, everything `not-started` (or reflecting reality if the
   project has existing code — audit before writing).
3. `docs/CAPABILITIES.md` from `templates/CAPABILITIES.template.md`, limited
   to discovered skills, MCPs, hooks and CI that affect planning or VERIFY.
4. `docs/plans/` with `TEMPLATE.md` from `templates/PLAN.template.md`, and
   `docs/receipts/TEMPLATE.md` from `templates/RECEIPT.template.md`.
5. `docs/adr/` with `0001-adopt-loop-engineering.md` (from
   `templates/ADR.template.md`) recording the adoption of this methodology
   and the milestone cut chosen in Phase 2.
6. A **Working Agreement** section appended to `CLAUDE.md` **and**
   `AGENTS.md` from `templates/WORKING_AGREEMENT.template.md`. Create the
   files if absent. If they exist, append inside
   `<!-- loop-engineering:begin -->` / `<!-- loop-engineering:end -->`
   markers — if the markers already exist, replace only what is between
   them. **Never clobber existing content.**
7. `scripts/verify-loop.sh` and `scripts/watch-verify.sh` from `scripts/`
   (next to this file), with their examples adapted to the project's actual
   stack. `watch-verify.sh` is optional bounded observation; do not schedule
   it by default.
8. **Only after asking the user**, offer the Stop hook. For Claude Code, copy
   `scripts/stop-verify.sh` to `.claude/hooks/stop-verify.sh`, make it
   executable, and wire it in `.claude/settings.json`:
   `{"hooks":{"Stop":[{"hooks":[{"type":"command","command":".claude/hooks/stop-verify.sh"}]}]}}`.
   For Codex CLI, copy it to `.codex/hooks/stop-verify.sh`, make it executable,
   and wire it in `.codex/hooks.json`:
   `{"hooks":{"Stop":[{"hooks":[{"type":"command","command":"sh \"$(git rev-parse --show-toplevel)/.codex/hooks/stop-verify.sh\"","timeout":30}]}]}}`.
   Merge existing configuration; never overwrite it. Codex requires the user
   to review and trust non-managed hooks before they run.
9. Suggest adding `.le-active-verify` to `.gitignore`.

### Phase 4 — Handoff

Present: the goal map summary (milestones, goal counts), which goal it would
start with and why, and that goal's **full six-field loop declaration**.
**Do not start executing it without explicit confirmation.** Point the user
at `auto` for when they're ready.

Failure behavior: if the repo is not writable, or `docs/` creation fails,
stop and report — do not scatter files elsewhere.

---

## plan

Re-generate or refine the goal map after scope changes; re-plan without
re-initializing.

Preconditions: `docs/GOALS.md` exists (otherwise: run `start`).

1. Read `docs/GOALS.md`, all receipts, `docs/STATUS.md`, and the functional
   source (`docs/PROJECT_BRIEF.md` or the doc referenced in the GOALS
   header). Ask what changed if the user didn't say.
2. Propose the delta, not a rewrite: goals to add (new ids, never reusing
   old ones), goals to drop (mark `dropped — <reason>` with strikethrough,
   don't delete the line), milestone boundary changes, dependency changes.
3. Goals already `[x]`/`[!]`/`[$]` keep their ids, marks and receipts
   untouched. History is append-only.
4. Wait for confirmation, then apply the edit to `docs/GOALS.md` and record
   a short `## Plan revisions` entry at the bottom (date + one line).
5. If the scope change reverses an architectural decision, propose an ADR.

---

## auto

Resume the project exactly where it was left; pick and run the next eligible
loop. Safe to run at any moment, any number of times.

1. **Reconstruct state, trust files over memory.** Read `docs/GOALS.md`,
   the relevant plans and every receipt in `docs/receipts/`, `docs/STATUS.md`, and the git log
   since the newest receipt. Reconcile inconsistencies explicitly and
   **report what was fixed before proceeding**:
   - goal marked `[~]` whose receipt says `passed` → mark `[x]`;
   - commits touching a scope with no receipt → note the orphan work;
   - stale `.le-active-verify` with no matching in-progress goal → remove.
2. **Select the next eligible goal**: dependencies satisfied (all `Depends
   on` goals are `[x]`), not `[!]` stuck, not `[$]`, respecting milestone
   order. Announce the choice — goal, why it's next, its VERIFY command,
   its budget — before touching code.
3. **Plan, then run the loop**: create or update the goal plan before edits.
   Show scope, intended files, risks and alternatives; wait for confirmation
   only if it introduces a material risk or widens scope. Mark the goal `[~]`,
   record the base revision in the plan, write `.le-active-verify`, then
   implement → run VERIFY → on failure, feed the **raw** failure output into
   the next iteration ("fix the real cause, not the check") → repeat until
   green or a STOP condition fires. Track iteration count and
   identical-failure count honestly — an iteration is one
   implement-then-verify cycle.
   - *Codex check*: before declaring green, re-run VERIFY once more in a
     fresh invocation and use that output as the record.
4. **Close out**: before writing a passing receipt, compare changed files
   since the plan's base revision with SCOPE. Stop on unexplained out-of-scope
   files; add a concrete plan exception or split the work. Write the receipt
   (from `docs/receipts/TEMPLATE.md`) with plan path, base/final revision,
   changed files, exact final VERIFY output and scope-check result; then
   set the goal's mark (`[x]` / `[!]` / `[$]`) in `GOALS.md`; delete
   `.le-active-verify`; update `STATUS.md` if behavior changed; if the run
   surfaced a repeatable lesson, **propose** (don't silently apply) a
   `memory` promotion; then name the next eligible goal and stop.
5. **Nothing eligible?** Say exactly why: list stuck goals awaiting `stuck`
   diagnosis, unmet dependencies, or a milestone whose goals are all `[x]`
   and is ready for `close-milestone`.

---

## goal <id|description>

Run one specific loop.

- With an id (`G-204`): load its six fields from `docs/GOALS.md`. If the
  goal is `[x]`, say so and stop (offer `verify` to re-check). If `[!]`,
  refuse and point at `stuck` — do not re-run a stuck loop unchanged.
- With a description (ad-hoc): construct the six fields interactively —
  propose SCOPE, VERIFY, BUDGET from the project's tooling; the user
  confirms. Then ask whether to append it to `docs/GOALS.md` under the
  current milestone with the next free id (default: yes; a loop without a
  tracked goal leaves no trail).
- Then run steps 3–4 of `auto` (plan, loop, scope check, evidence and
  receipt).
- A `Verify: human` goal: implement, then present the guided manual check
  and **wait for the human result**; record who checked and what they
  observed in the receipt.

---

## verify <scope|goal-id>

Run a verification gate only; report raw pass/fail output. **No fixing.**

- Goal id → run that goal's VERIFY command.
- Scope name → run the scoped gate discovered at `start` for that area (fall
  back to asking if unknown).
- Run it, show the exact output — the failing part verbatim, not summarized
  or softened. Never declare success unless every step of the command
  actually passed.
- Do not edit any file, do not "quickly fix" anything found. If it fails,
  the report *is* the deliverable; suggest `goal <id>` to fix.
- This is the independent judge: run it after any loop reports success —
  the generator never audits itself.

---

## status

Dashboard. Read-only.

1. Reconstruct state as in `auto` step 1 (report inconsistencies, but fix
   nothing without confirmation).
2. Report: per milestone — goals passed / in progress / stuck /
   budget-exhausted / pending; the active loop if `.le-active-verify`
   exists; receipts newer than the last GOALS.md update; receipts missing
   plan/evidence/scope-check fields; goals whose scope was modified after
   their final evidence; and **what's
   eligible next** (same selection rule as `auto` step 2).
3. For every passed goal whose Scope changed after its final revision, propose
   a precise `STATUS.md` entry under `## Revalidation required`. On
   confirmation, add it; never relaunch a loop or mutate the goal status.
   On a later passing revalidation receipt, remove that entry and mark the
   row's Verification `current` in the same update.
4. End with a one-line recommendation: the exact next command to run
   (`auto`, `stuck G-xxx`, or `close-milestone Mx`).

---

## receipt <goal-id>

Write or complete the receipt for a finished/abandoned loop.

1. Locate the goal in `docs/GOALS.md`; derive the receipt path
   (`docs/receipts/<goal-id>-<slug>.md`).
2. If the receipt exists but is incomplete (e.g. written by
   `verify-loop.sh`, which records only the loop-runner fields), fill in the
   narrative and reproducible evidence from the session/git evidence: plan,
   base/final revision, changed files, exact final VERIFY output, scope check,
   what failed along the way, what fixed it, anything worth promoting to memory.
3. If missing, write it fresh from `docs/receipts/TEMPLATE.md`. Ask the
   user for anything not reconstructable from evidence (e.g. the human
   observation on a `Verify: human` goal) — don't invent it.
4. A `passed` receipt without final command/output, revision, changed-files
   list and scope check is incomplete: obtain the evidence or set its result
   honestly to non-passed. Then update the
   goal's mark in `GOALS.md` to match; delete `.le-active-verify` if it
   points at this goal.

---

## stuck <goal-id>

Diagnose a stuck loop. **Never just raises the budget.**

1. Read the goal's receipt and the failure history (last outputs, git log of
   the attempts). If there is no receipt, write one first (`receipt`).
2. Classify the cause using the taxonomy (METHODOLOGY.md, stuck protocol):
   **bad gate** / **missing dependency** / **ambiguous goal** /
   **environment problem** (e.g. a test repo without `user.name` configured
   failing every commit — the code was never the problem).
3. Propose exactly one primary remedy, with the concrete edit:
   - bad gate → the corrected VERIFY command;
   - missing dependency → the goal to run first, and the `Depends on` edit;
   - ambiguous goal → the reformulated GOAL sentence, or a split into two
     smaller goals (new ids);
   - environment problem → the environment fix, which the human may need to
     apply.
   If the diagnosis reveals a decision a loop must not take alone, propose
   an ADR (`templates/ADR.template.md`).
4. On confirmation: apply the edit to `docs/GOALS.md`, reset the goal's mark
   to `[ ]`, append the diagnosis to its receipt (append — keep the failed
   run's record), and offer to relaunch via `goal <id>`.

---

## close-milestone <id>

1. List the milestone's goals from `docs/GOALS.md`. For each, check its
   receipt exists and says `Result: passed` (a `Verify: human` goal's
   receipt must name who checked). **If any is missing or not passed, stop
   and list exactly what's outstanding — do not continue.**
2. Run the full project-wide gate (the milestone's closing goal command).
   Show the output; if red, stop — the milestone does not close.
3. Update `docs/STATUS.md` with the newly landed capabilities.
4. Draft release notes from the commits since the last tag (or since the
   previous milestone close if untagged).
5. Propose the version tag. **Wait for human confirmation before creating
   or pushing any tag.**
6. Mark the milestone closed in `docs/GOALS.md` (date on the milestone
   heading).

---

## memory <lesson>

Promote a correction to the durable memory layer.

1. Restate the lesson as one imperative rule with its trigger context (bad:
   "be careful with encodings"; good: "encoding detection always needs a
   test with BOM present and absent").
2. Decide the layer: a *fact/correction* → append to the project's
   `CLAUDE.md` **and** `AGENTS.md` (inside the loop-engineering markers, so
   both tools see it); a *procedure* (multi-step, reusable) → a project
   skill: `.claude/skills/<name>/SKILL.md` **and** `.agents/skills/<name>/SKILL.md`
   (same content; frontmatter `name` + `description`). A *decision* → this
   is an ADR, not a memory; redirect.
3. Show the exact text and where it will go; apply on confirmation.
4. If the same lesson is already recorded, say so and stop — no duplicates.

---

## parallel

Analyze pending goals and propose what can run concurrently.

1. From `docs/GOALS.md`: eligible goals (as in `auto` step 2) whose SCOPEs
   are disjoint and whose `Parallelizable with` annotations agree. Two goals
   in the same scope never parallelize. Flag any pair with an undeclared
   coupling you can see in the code (shared module, shared config).
2. Before output, write `docs/plans/integration-<YYYY-MM-DD>.md` from
   `templates/INTEGRATION.template.md`: one row per candidate with branch or
   worktree, scope, detected file/config overlap, integration order and
   post-merge VERIFY. Record undeclared coupling or "None detected".
3. Claude Code: emit ready-to-run launch commands, one worktree per goal —
   `claude --worktree <goal-slug>` plus the first message to give each
   session (`/le:goal G-xxx`). Remind: integrate one branch at a time, each
   re-verified with an independent `verify` run before merge.
4. Codex CLI (no worktree flag): emit the sequential fallback plan — the same
   goals in dependency-safe order — and note that manual `git worktree` +
   one Codex session per tree is possible but unmanaged.
5. Execute nothing; this command only plans.

---

## watch <goal-id> [minutes]

Observe a goal's branch for a bounded time; never edit code or start a loop.

1. Load the goal, its VERIFY and its receipt. Refuse a `Verify: human` goal.
   Default to 30 minutes if omitted; require a positive upper bound
   and use `scripts/watch-verify.sh` when available.
2. Record the starting revision. On each new commit touching SCOPE, run VERIFY
   and append the revision, command, raw result and timestamp to the receipt's
   `Watch evidence` section. Do not alter the receipt result or goal status.
3. Stop at the time budget, after three identical failures, or if the user
   interrupts. Report the last result and whether revalidation is required.
   Never run indefinitely, poll a remote service, edit code or relaunch a
   loop. Claude Code and Codex follow exactly the same local behavior.

---

## review <goal-id>

Read-only review packet for a completed or in-progress goal.

1. Read its plan, receipt, `git diff <base>...<final>` (or working diff), and
   final VERIFY evidence. Do not run a new gate or edit files.
2. Show compactly: goal/scope, intended versus changed files, risks and
   rejected alternatives, scope exceptions, final verification evidence and
   unresolved questions. Flag missing evidence, missing plan or scope drift.
3. Do not create a pull request, branch, tag or external review. The output is
   the local review-ready handoff for both Claude Code and Codex.

---

## help

1. Summarize the method in a few sentences (loop anatomy, the gate decides,
   memory layers) and list the commands with one line each.
2. Then look at the actual project state (is there a `docs/GOALS.md`? stuck
   goals? milestone complete?) and end with **"what you should run right
   now"** — one concrete recommendation, e.g. "no goal map yet → run
   `start <your-spec>`", or "G-204 is stuck → run `stuck G-204`".
