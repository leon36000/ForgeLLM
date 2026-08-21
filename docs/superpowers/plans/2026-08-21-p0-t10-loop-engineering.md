# P0-T10 Bounded Loop Engineering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a pinned, fail-closed Loop Engineering bridge whose declarations and receipts remain subordinate to ForgeLLM task packets and accepted ADRs.

**Architecture:** Keep the upstream project as an inert, exact-commit static reference subset. Implement all authority, command-firewall, declaration, provenance, and receipt validation in ForgeLLM Python code and a repository validator. Integrate only deterministic validation into `make ci`; do not ship an autonomous runner, shell evaluator, hook, or privileged operation.

**Tech Stack:** Python 3, PyYAML, pytest, Ruff, Make, Git worktrees, GitHub-hosted Phase 0/CodeQL/GitGuardian/Sonar checks.

**Spec:** `docs/superpowers/specs/2026-08-21-p0-t10-loop-engineering-design.md`

## Global Constraints

- ForgeLLM task packets and accepted ADRs remain the source of truth.
- Upstream reference is `https://github.com/lcajigasm/loop-engineering` at commit `ae2d610985064bb30c5013261988c813013c09e3`.
- Never execute or vendor upstream `install.sh`, shell/eval runners, Stop hooks, or agent adapters.
- The verifier rejects shell composition/redirection, wrappers, Git/GitHub mutations, privileged reads, secrets, infrastructure clients, and unbounded verification.
- P0-T09 files and Sonar/GitHub settings are out of scope; no token, scan, or activation is allowed.
- No direct push to `main`; final integration requires exact-head CI and GPT-5.6-Sol review.

---

### Task 1: Establish the firewall RED suite

**Files:**
- Create: `tests/test_loop_engineering.py`
- Test only: `src/forgellm_governance/loop_engineering.py` is intentionally absent at the start of this task.

**Interfaces:**
- The tests will import `validate_loop_verify_command(command) -> list[str]` from `forgellm_governance.loop_engineering`.
- A safe single command returns `[]`; every rejected command returns at least one message containing `stop_and_escalate`.

- [ ] **Step 1: Write the failing tests**

```python
import pytest

from forgellm_governance.loop_engineering import validate_loop_verify_command


@pytest.mark.parametrize("command", [
    "make ci && git push origin main",
    "make ci; gh pr merge 37",
    "make ci > /tmp/result.log",
    "env git push origin main",
    "command git status",
    "git add README.md",
    "git branch -D review-head",
    "gh workflow run release.yml",
    "kubectl get secret sonar-token",
])
def test_firewall_rejects_composition_wrappers_mutations_and_privileged_reads(command):
    messages = validate_loop_verify_command(command)
    assert messages
    assert "stop_and_escalate" in messages[0]


@pytest.mark.parametrize("command", [
    "git status --short",
    "git diff --check",
    "gh pr view 37 --json state",
])
def test_firewall_allows_explicit_read_only_commands(command):
    assert validate_loop_verify_command(command) == []
```

- [ ] **Step 2: Run the RED check**

Run: `python -m pytest -q tests/test_loop_engineering.py`

Expected: collection fails because the new module/API does not exist. This proves the tests target the missing firewall behavior, not a pre-existing implementation.

- [ ] **Step 3: Commit the RED tests**

```bash
git add tests/test_loop_engineering.py
git commit -m "test(p0-t10): expose loop verifier firewall bypasses"
```

### Task 2: Implement the minimal command firewall GREEN

**Files:**
- Create: `src/forgellm_governance/loop_engineering.py`
- Modify: `tests/test_loop_engineering.py`

**Interfaces:**
- `validate_loop_verify_command(command: object) -> list[str]` tokenizes with `shlex` punctuation, rejects composition/redirection and wrappers before classification, and classifies the complete command.
- The allowlist includes read-only Git inspection and `gh pr view`; it does not include mutation commands or secret/infrastructure clients.

- [ ] **Step 1: Implement only the parser and firewall constants required by Task 1**

Implement `_split_verify_tokens`, `_verify_shell_structure_issue`, `_verify_wrapper_issue`, `_verify_tool_authority_issue`, and `validate_loop_verify_command`. Do not add receipt or repository code in this task.

- [ ] **Step 2: Run the focused GREEN check**

Run: `python -m pytest -q tests/test_loop_engineering.py`

Expected: all Task 1 tests pass with no warnings.

- [ ] **Step 3: Add edge-case tests for inline code, command substitution, install commands, curl/wget mutation flags, and environment assignments; run them RED then GREEN**

Run: `python -m pytest -q tests/test_loop_engineering.py`

Expected: each new test first fails for the missing rule and then passes after the smallest rule is added.

- [ ] **Step 4: Commit the firewall slice**

```bash
git add src/forgellm_governance/loop_engineering.py tests/test_loop_engineering.py
git commit -m "feat(p0-t10): enforce fail-closed verifier firewall"
```

### Task 3: Add declaration authority and receipt unit tests

**Files:**
- Modify: `tests/test_loop_engineering.py`
- Modify: `src/forgellm_governance/loop_engineering.py`

**Interfaces:**
- `validate_loop_declaration(declaration: Mapping[str, Any], task_packet: Mapping[str, Any]) -> list[str]`.
- `validate_loop_receipt(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]`.
- `validate_loop_receipt_template(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]`.

- [ ] **Step 1: Write RED tests for authority invariants**

Cover exactly-six semantic fields (`GOAL`, `SCOPE`, `VERIFY`, `BUDGET`, `STOP`, `RECEIPT`), task/project binding, prefix-confusion scope escapes, unauthorized verification commands, positive finite budgets, `stop_and_escalate`, shadow-state paths, and receipt destination containment.

- [ ] **Step 2: Run the authority RED check**

Run: `python -m pytest -q tests/test_loop_engineering.py -k 'declaration or scope or verify or budget or stop or shadow'`

Expected: new tests fail because the declaration/receipt validators are not implemented.

- [ ] **Step 3: Implement the smallest pure validators**

Add normalized POSIX path containment, task-packet binding, exact field checks, authorized VERIFY membership, finite budget/stop checks, and receipt destination checks. Do not read repository files or call subprocesses from this module.

- [ ] **Step 4: Run the authority GREEN check and the prior firewall suite**

Run: `python -m pytest -q tests/test_loop_engineering.py`

Expected: all focused tests pass.

- [ ] **Step 5: Add RED/GREEN receipt tests**

Test lowercase non-zero full SHAs, base-commit equality, iteration/failure ceilings, changed-path scope, exact VERIFY equality, non-empty evidence, independent reviewer identity, final stop reasons, and template rejection as final evidence.

- [ ] **Step 6: Commit the declaration/receipt slice**

```bash
git add src/forgellm_governance/loop_engineering.py tests/test_loop_engineering.py
git commit -m "feat(p0-t10): bind declarations and receipts to task authority"
```

### Task 4: Bind every repository receipt to immutable declarations

**Files:**
- Modify: `scripts/validate_loop_engineering.py`
- Modify: `tests/test_loop_engineering.py`
- Create: `artifacts/governance/loop-engineering/receipt-index.yaml`
- Create: `artifacts/governance/loop-engineering/declarations/P0-T10-run-01.yaml`
- Create: `artifacts/governance/loop-engineering/receipts/P0-T10-run-01.yaml`
- Create: `artifacts/governance/loop-engineering/receipts/TEMPLATE.yaml`

**Interfaces:**
- `validate_repository(root: Path) -> list[str]` is the repository-level gate.
- The receipt index records exact declaration/receipt paths, declaration source commit/blob SHA, and schema version for every final run.

- [ ] **Step 1: Write RED catalog tests**

Use `tmp_path` to mutate a declaration blob, add an unindexed receipt, duplicate a run ID, point a record outside the fixed prefix, mismatch the declaration base commit, and make `stop_reason` disagree with verification disposition. Assert `validate_repository` returns a precise failure.

- [ ] **Step 2: Run the catalog RED check**

Run: `python -m pytest -q tests/test_loop_engineering.py -k 'catalog or index or immutable or declaration_source or disposition'`

Expected: failures demonstrate that real committed artifacts are not yet validated.

- [ ] **Step 3: Implement catalog validation**

Load mappings safely, validate the index header and exact record keys, hash declaration files with Git blob SHA-1, validate every indexed declaration/receipt pair, reject duplicate IDs/paths, and require the index to cover every committed final receipt and immutable declaration exactly.

- [ ] **Step 4: Run GREEN and inspect all raw failure messages**

Run: `python -m pytest -q tests/test_loop_engineering.py`

Expected: all unit and repository-catalog tests pass; each mutation fixture fails for the intended reason.

- [ ] **Step 5: Commit the immutable declaration and final receipt before indexing**

Commit the declaration and final receipt first so the declaration has a real containing commit. The index is intentionally absent for this intermediate commit; the next step records that commit and its Git blob SHA instead of creating a circular self-reference.

```bash
git add scripts/validate_loop_engineering.py tests/test_loop_engineering.py artifacts/governance/loop-engineering/declarations/P0-T10-run-01.yaml artifacts/governance/loop-engineering/receipts/P0-T10-run-01.yaml artifacts/governance/loop-engineering/receipts/TEMPLATE.yaml
git commit -m "feat(p0-t10): add immutable loop declaration and receipt"
```

- [ ] **Step 6: Write the receipt index from the committed declaration**

Run `git rev-parse HEAD` and `git hash-object artifacts/governance/loop-engineering/declarations/P0-T10-run-01.yaml`; write those exact values into `receipt-index.yaml`, run the catalog tests and repository validator, then commit the index.

```bash
git add artifacts/governance/loop-engineering/receipt-index.yaml
git commit -m "test(p0-t10): index immutable loop evidence"
```

- [ ] **Step 7: Commit the receipt-integrity slice**

```bash
git add scripts/validate_loop_engineering.py tests/test_loop_engineering.py artifacts/governance/loop-engineering
git commit -m "feat(p0-t10): validate immutable loop receipt catalog"
```

### Task 5: Add pinned static provenance, task packet, bridge docs, and gates

**Files:**
- Create: `tasks/open/P0-T10-bounded-loop-engineering.yaml`
- Create: `third_party/loop-engineering/LICENSE`
- Create: `third_party/loop-engineering/PROVENANCE.yaml`
- Create: `third_party/loop-engineering/core/METHODOLOGY.md`
- Create: `third_party/loop-engineering/core/COMMANDS.md`
- Create: `third_party/loop-engineering/core/templates/{PLAN,RECEIPT,INTEGRATION,CAPABILITIES}.template.md`
- Create: `.agents/skills/forgellm-loop-engineering/SKILL.md`
- Create: `.claude/skills/forgellm-loop-engineering/SKILL.md`
- Create: `docs/architecture/ADR-0005-bounded-loop-engineering.md`
- Create: `docs/quality/P0-T10-LOOP-ENGINEERING.md`
- Modify: `AGENTS.md`, `CLAUDE.md`, `Makefile`, `docs/roadmap/PHASE0_TASKS.md`, `docs/state/CURRENT_STATE.md`, `docs/state/HANDOFF.md`, `docs/state/RISKS.md`

- [ ] **Step 1: Add static vendor files only from the exact upstream commit**

Record the upstream repository, commit, license blob, and every selected source blob in `PROVENANCE.yaml`. Include no installer, executable script, adapter, shadow-state template, or hook.

- [ ] **Step 2: Add the task packet and proposed ADR**

Bind P0-T10 to the current canonical base `f8364f12402c3c58796dbc1b56f8c65d378e88de`, preserve all forbidden P0-T09 and privilege actions, and mark ADR-0005 `proposed` until independent review.

- [ ] **Step 3: Add the two byte-identical local bridge skills and working-agreement markers**

The skills may explain the bounded contract and point to the static reference, but must not install hooks, execute vendor scripts, create shadow state, or override task packets/ADRs.

- [ ] **Step 4: Wire `validate-loop` into `make validate` and `make ci` without removing existing gates**

Add task-packet validation, repository-loop validation, and Ruff formatting for the new Python surface. Preserve all P0-T09 validation and simulation/hash gates.

- [ ] **Step 5: Run the repository validator and full suite**

Run: `make validate-loop`, `make validate`, `python -m pytest -q tests/test_loop_engineering.py`, `make ci`, and `git diff --check`.

Expected: all commands exit 0; the validator confirms exact vendor provenance and complete receipt coverage.

- [ ] **Step 6: Commit the static integration slice**

```bash
git add tasks/open/P0-T10-bounded-loop-engineering.yaml third_party .agents .claude docs/architecture/ADR-0005-bounded-loop-engineering.md docs/quality/P0-T10-LOOP-ENGINEERING.md AGENTS.md CLAUDE.md Makefile docs/roadmap/PHASE0_TASKS.md docs/state/CURRENT_STATE.md docs/state/HANDOFF.md docs/state/RISKS.md
git commit -m "feat(p0-t10): add bounded loop engineering bridge"
```

### Task 6: Exact-head review, acceptance, and publication

**Files:**
- Modify: `docs/architecture/ADR-0005-bounded-loop-engineering.md`
- Modify: `tasks/open/P0-T10-bounded-loop-engineering.yaml`
- Modify: `docs/state/CURRENT_STATE.md`
- Modify: `docs/state/HANDOFF.md`
- Create: `docs/reviews/P0-T10-LOOP-ENGINEERING-REVIEW-2026-08-21.md`

- [ ] **Step 1: Review the complete diff and task boundary**

Run: `git diff --stat origin/main...HEAD`, `git diff --name-only origin/main...HEAD`, `git diff --check`, and `git status --short`. Confirm no P0-T09 implementation file, secret, setting, hook, runner, or external mutation is present.

- [ ] **Step 2: Obtain independent Luna architecture/security reviews**

Give each reviewer the exact head and raw evidence, with distinct questions: one reviews authority/firewall correctness; the other reviews supply-chain/provenance/receipt integrity. Resolve every BLOCKER/MAJOR before acceptance.

- [ ] **Step 3: Obtain GPT-5.6-Sol decision on ADR acceptance**

Request a read-only exact-head gate. If it returns `ACCEPT`, update ADR-0005 to `accepted`, record the review evidence, and update task/state/handoff without changing code. If it returns `NO-GO`, fix only the cited finding through a new RED/GREEN slice.

- [ ] **Step 4: Re-run every exact-head check after the acceptance commit**

Run: `make ci`, `gh pr checks <number> --watch`, and inspect Phase 0, CodeQL, GitGuardian, Sonar, and Dependency Review conclusions individually. Do not call skipped Dependency Review a pass.

- [ ] **Step 5: Obtain the GPT-5.6-Sol merge gate and merge**

Merge only the exact reviewed head with `gh pr merge --squash --delete-branch`. Confirm the PR state is `MERGED` and record the merge SHA; never direct-push `main`.

- [ ] **Step 6: Perform post-merge readback and close agents**

Fetch `origin/main`, list workflows by merge SHA, inspect all job conclusions, run a fresh local validation, update the state/handoff receipt with exact evidence, close completed agents, and leave P0-T09/P0-T04 unchanged.
