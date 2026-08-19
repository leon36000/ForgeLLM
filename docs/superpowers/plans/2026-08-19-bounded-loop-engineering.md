# Bounded Loop Engineering Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Install and operationalize a pinned Loop Engineering methodology through a ForgeLLM-specific, bounded, machine-validated bridge without creating a second source of truth or privilege path.

**Architecture:** Vendor only reviewed static upstream methodology/templates at one immutable commit, then layer a small ForgeLLM contract on top. The contract binds each loop declaration to an existing task packet and Git base revision, mechanically constrains SCOPE and VERIFY, requires finite BUDGET/STOP semantics, and records RECEIPT evidence. Agent adapters are thin project-local instructions; they never run upstream `install.sh`, an eval runner, or Stop hook.

**Tech Stack:** Python 3.11, PyYAML 6.0.3, pytest 9.0.2, Ruff 0.16.2, Make, GitHub Actions, project-local Claude/Codex skill Markdown, vendored MIT-licensed Markdown templates.

**Spec:** `docs/architecture/ADR-0005-bounded-loop-engineering.md`

## Global Constraints

- Canonical base for P0-T10 is `8594ef5abb19ca7a870fe6d71ae7aad8e15f4602`; issue is #36; branch is `p0-t10-bounded-loop-engineering`.
- Upstream source is exactly `lcajigasm/loop-engineering@ae2d610985064bb30c5013261988c813013c09e3`.
- Do not run upstream `install.sh`, `start`, `auto`, the eval-based headless runner, or any Stop hook.
- Do not create `docs/GOALS.md`, `docs/STATUS.md`, `docs/PROJECT_BRIEF.md`, or a second ADR hierarchy.
- ForgeLLM task packet `allowed_paths` and `verification_commands` are the maximum loop authority; loop declarations may only narrow them.
- Every modifying loop uses one isolated branch/worktree and one writer.
- Every loop has finite iteration and repeated-identical-failure limits; no daemon or unbounded watcher.
- Loops have no authority over secrets, accounts, billing, GitHub/Sonar administration, Tailscale, privileged hosts, runners, or P0-T09 external activation.
- P0-T09 files modified by PR #35 are out of P0-T10 scope; avoid `src/forgellm_governance/validation.py` and `tests/test_validation.py` to keep branches independent.
- No direct push to `main`; exact-head Phase 0, CodeQL, GitGuardian, Sonar and independent architecture/security review are required before merge.

---

### Task 1: Governance foundation

**Files:**
- Create: `tasks/open/P0-T10-bounded-loop-engineering.yaml`
- Create: `docs/architecture/ADR-0005-bounded-loop-engineering.md`
- Create: `docs/superpowers/plans/2026-08-19-bounded-loop-engineering.md`

**Interfaces:**
- Consumes: owner approval, charter, ADR-0002, upstream supply-chain review.
- Produces: authorized path boundary, proposed architecture decision, implementation plan.

- [ ] **Step 1: Create the task packet with exact authority and non-goals.**

Use schema `schemas/task-packet.schema.json`; status is `in_progress`; `allowed_paths` excludes every P0-T09 implementation file except shared state files explicitly needed only at closeout.

- [ ] **Step 2: Write ADR-0005 as `proposed`.**

The decision must explicitly select the vendored bridge, reject upstream installation unchanged, forbid shadow GOALS/STATUS, forbid the eval runner and Stop hook, and retain task-packet authority.

- [ ] **Step 3: Validate the packet.**

Run:
```bash
python scripts/validate_task_packet.py tasks/open/P0-T10-bounded-loop-engineering.yaml --root .
```
Expected: `OK: tasks/open/P0-T10-bounded-loop-engineering.yaml`.

- [ ] **Step 4: Commit the governance foundation.**

```bash
git add tasks/open/P0-T10-bounded-loop-engineering.yaml \
  docs/architecture/ADR-0005-bounded-loop-engineering.md \
  docs/superpowers/plans/2026-08-19-bounded-loop-engineering.md
git commit -m "docs(governance): authorize bounded loop engineering"
```

### Task 2: Vendor the reviewed static upstream subset

**Files:**
- Create: `third_party/loop-engineering/PROVENANCE.yaml`
- Create: `third_party/loop-engineering/LICENSE`
- Create: `third_party/loop-engineering/core/METHODOLOGY.md`
- Create: `third_party/loop-engineering/core/COMMANDS.md`
- Create: `third_party/loop-engineering/core/templates/PLAN.template.md`
- Create: `third_party/loop-engineering/core/templates/RECEIPT.template.md`
- Create: `third_party/loop-engineering/core/templates/INTEGRATION.template.md`
- Create: `third_party/loop-engineering/core/templates/CAPABILITIES.template.md`

**Interfaces:**
- Consumes: exact upstream commit and Git blob SHAs.
- Produces: inert, reproducible reference material for adapters and provenance validation.

- [ ] **Step 1: Copy only the approved upstream files byte-for-byte.**

Required upstream blob bindings:

```yaml
LICENSE: 84524f23b209fccb02a8f239165f0444bfd70f3f
core/METHODOLOGY.md: c7094ca40c2257d653c4d48f6b87c40cb82b209b
core/COMMANDS.md: 4de9e981ad89c04f28d94ea4ad5b97e1b513b578
core/templates/PLAN.template.md: 3477e664b738a46b36e4b015b1b2ef502b5c6dd4
core/templates/RECEIPT.template.md: 2f5da7d5736067c965b4fed2604982e00a79b024
core/templates/INTEGRATION.template.md: 2f740b4dbc1f7ee63688abe570c179bd28fc4508
core/templates/CAPABILITIES.template.md: da89bdb92b2f61558babc7c699cd2c350904f07a
```

Do **not** vendor `install.sh`, `core/scripts/`, GOALS/STATUS/PROJECT_BRIEF templates, Claude plugin installers, or Codex/Claude upstream adapters.

- [ ] **Step 2: Create `PROVENANCE.yaml`.**

Exact structure:

```yaml
schema_version: '1.0'
upstream_repository: https://github.com/lcajigasm/loop-engineering
upstream_commit: ae2d610985064bb30c5013261988c813013c09e3
license: MIT
license_blob_sha: 84524f23b209fccb02a8f239165f0444bfd70f3f
files:
  - path: LICENSE
    upstream_blob_sha: 84524f23b209fccb02a8f239165f0444bfd70f3f
  - path: core/METHODOLOGY.md
    upstream_blob_sha: c7094ca40c2257d653c4d48f6b87c40cb82b209b
  - path: core/COMMANDS.md
    upstream_blob_sha: 4de9e981ad89c04f28d94ea4ad5b97e1b513b578
  - path: core/templates/PLAN.template.md
    upstream_blob_sha: 3477e664b738a46b36e4b015b1b2ef502b5c6dd4
  - path: core/templates/RECEIPT.template.md
    upstream_blob_sha: 2f5da7d5736067c965b4fed2604982e00a79b024
  - path: core/templates/INTEGRATION.template.md
    upstream_blob_sha: 2f740b4dbc1f7ee63688abe570c179bd28fc4508
  - path: core/templates/CAPABILITIES.template.md
    upstream_blob_sha: da89bdb92b2f61558babc7c699cd2c350904f07a
excluded_executable_surfaces:
  - install.sh
  - core/scripts/
  - claude-code/
  - codex/
```

- [ ] **Step 3: Confirm no executable upstream shell surface was copied.**

Run:
```bash
find third_party/loop-engineering -type f -name '*.sh' -print
```
Expected: no output.

- [ ] **Step 4: Commit the vendor snapshot.**

```bash
git add third_party/loop-engineering
git commit -m "chore(vendor): pin loop engineering methodology"
```

### Task 3: Specify the ForgeLLM loop contract with failing tests

**Files:**
- Create: `tests/test_loop_engineering.py`

**Interfaces:**
- Consumes: task packet schema and future `validate_loop_declaration()`/`validate_loop_receipt()` APIs.
- Produces: RED contract for all safety invariants before implementation.

- [ ] **Step 1: Write the positive declaration fixture.**

Use a temporary task packet containing `allowed_paths: [src/example.py, tests/test_example.py]` and `verification_commands: [python -m pytest -q tests/test_example.py]`. Its loop declaration must contain:

```yaml
schema_version: '1.0'
project: ForgeLLM
task_id: P0-T99
base_commit: 0123456789abcdef0123456789abcdef01234567
GOAL: Make the bounded example pass its authorized focused test.
SCOPE:
  - src/example.py
  - tests/test_example.py
VERIFY:
  - python -m pytest -q tests/test_example.py
BUDGET:
  max_iterations: 10
  max_identical_failures: 3
STOP:
  on_verify_pass: true
  on_budget_exhausted: true
  on_identical_failure_limit: true
  privileged_operation: stop_and_escalate
RECEIPT: artifacts/governance/loop-engineering/receipts/P0-T99.yaml
```

- [ ] **Step 2: Write one failing test per rejection class.**

Tests must assert explicit failures for:

```python
@pytest.mark.parametrize("bad_scope", [["src/not-authorized.py"], ["."]])
def test_loop_scope_cannot_widen_task_packet(...): ...

def test_loop_verify_must_be_authorized_by_task_packet(...): ...

def test_loop_budget_requires_positive_max_iterations(...): ...

def test_loop_budget_requires_identical_failure_limit(...): ...

def test_loop_stop_requires_all_fail_closed_conditions(...): ...

def test_loop_privileged_operation_must_stop_and_escalate(...): ...

def test_loop_receipt_must_stay_under_governance_receipts(...): ...

def test_loop_rejects_shadow_state_paths(...): ...

def test_vendor_provenance_requires_exact_upstream_commit(...): ...

def test_receipt_requires_base_final_commits_and_scope_result(...): ...
```

- [ ] **Step 3: Run focused tests and capture RED.**

Run:
```bash
python -m pytest -q tests/test_loop_engineering.py
```
Expected: collection/import failure because `forgellm_governance.loop_engineering` does not exist yet, or equivalent failures only for the new contract.

- [ ] **Step 4: Commit RED tests only.**

```bash
git add tests/test_loop_engineering.py
git commit -m "test(governance): specify bounded loop contract"
```

### Task 4: Implement the bounded validator to GREEN

**Files:**
- Create: `src/forgellm_governance/loop_engineering.py`
- Create: `scripts/validate_loop_engineering.py`
- Create: `artifacts/governance/loop-engineering/P0-T10-loop.yaml`
- Create: `artifacts/governance/loop-engineering/receipts/TEMPLATE.yaml`

**Interfaces:**
- Produces:
  - `validate_loop_declaration(declaration: Mapping[str, Any], task_packet: Mapping[str, Any]) -> list[str]`
  - `validate_loop_receipt(receipt: Mapping[str, Any], declaration: Mapping[str, Any]) -> list[str]`
  - `validate_vendor_provenance(root: Path) -> list[str]`
  - CLI exit 0 only when provenance, active declaration, and receipt template validate.

- [ ] **Step 1: Implement fail-closed constants and helpers.**

Use exact constants:

```python
REQUIRED_LOOP_FIELDS = {"GOAL", "SCOPE", "VERIFY", "BUDGET", "STOP", "RECEIPT"}
SHADOW_STATE_PATHS = {
    "docs/GOALS.md",
    "docs/STATUS.md",
    "docs/PROJECT_BRIEF.md",
}
PRIVILEGED_OPERATION_POLICY = "stop_and_escalate"
EXPECTED_UPSTREAM_COMMIT = "ae2d610985064bb30c5013261988c813013c09e3"
```

- [ ] **Step 2: Implement declaration validation.**

Required checks:

```python
if set(loop_fields) != REQUIRED_LOOP_FIELDS: ...
if not set(declaration["SCOPE"]).issubset(set(task_packet["allowed_paths"])): ...
if not set(declaration["VERIFY"]).issubset(set(task_packet["verification_commands"])): ...
if budget["max_iterations"] <= 0: ...
if budget["max_identical_failures"] <= 0: ...
if stop.get("privileged_operation") != PRIVILEGED_OPERATION_POLICY: ...
if receipt_path.startswith("artifacts/governance/loop-engineering/receipts/") is False: ...
```

Reject a SCOPE containing any shadow-state path even if a future task packet mistakenly lists one.

- [ ] **Step 3: Implement receipt validation.**

Require exact keys:

```python
{
    "schema_version", "project", "task_id", "plan", "base_commit", "final_commit",
    "iterations", "identical_failures_at_stop", "stop_reason", "changed_paths",
    "scope_check", "verify_commands", "verify_evidence", "reviewer"
}
```

`scope_check` must be `pass`; changed paths must be a subset of declaration SCOPE; `verify_commands` must equal declaration VERIFY; commits must be 40 lowercase hex characters.

- [ ] **Step 4: Implement provenance validation.**

Read `third_party/loop-engineering/PROVENANCE.yaml`, require exact upstream commit/license blob and exact seven vendored paths. Recompute local Git-compatible blob SHA-1 as `sha1(b"blob " + len(content) + b"\0" + content)` and compare to recorded upstream blob SHA for each file.

- [ ] **Step 5: Create the active P0-T10 declaration.**

Use:

```yaml
schema_version: '1.0'
project: ForgeLLM
task_id: P0-T10
base_commit: 8594ef5abb19ca7a870fe6d71ae7aad8e15f4602
GOAL: Install a bounded and independently verifiable Loop Engineering bridge without widening ForgeLLM authority.
SCOPE:
  - third_party/loop-engineering/
  - src/forgellm_governance/loop_engineering.py
  - scripts/validate_loop_engineering.py
  - tests/test_loop_engineering.py
  - .agents/skills/forgellm-loop-engineering/
  - .claude/skills/forgellm-loop-engineering/
  - AGENTS.md
  - CLAUDE.md
  - Makefile
  - docs/quality/P0-T10-LOOP-ENGINEERING.md
  - artifacts/governance/loop-engineering/
  - tasks/open/P0-T10-bounded-loop-engineering.yaml
  - docs/architecture/ADR-0005-bounded-loop-engineering.md
  - docs/superpowers/plans/2026-08-19-bounded-loop-engineering.md
VERIFY:
  - python scripts/validate_loop_engineering.py --root .
  - python -m pytest -q tests/test_loop_engineering.py
  - make ci
BUDGET:
  max_iterations: 10
  max_identical_failures: 3
STOP:
  on_verify_pass: true
  on_budget_exhausted: true
  on_identical_failure_limit: true
  privileged_operation: stop_and_escalate
RECEIPT: artifacts/governance/loop-engineering/receipts/P0-T10.yaml
```

If SCOPE needs a path not authorized by the task packet, update the task packet through reviewed governance first; never silently widen the declaration.

- [ ] **Step 6: Run focused tests to GREEN.**

```bash
python -m pytest -q tests/test_loop_engineering.py
python scripts/validate_loop_engineering.py --root .
```
Expected: all focused tests pass and validator prints `OK: bounded Loop Engineering contract is valid`.

- [ ] **Step 7: Commit implementation.**

```bash
git add src/forgellm_governance/loop_engineering.py scripts/validate_loop_engineering.py \
  artifacts/governance/loop-engineering tests/test_loop_engineering.py
git commit -m "feat(governance): enforce bounded loop contracts"
```

### Task 5: Install thin project-local Claude/Codex bridge skills

**Files:**
- Create: `.agents/skills/forgellm-loop-engineering/SKILL.md`
- Create: `.claude/skills/forgellm-loop-engineering/SKILL.md`
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: ADR-0005, active task packet, validated loop declaration, vendored methodology.
- Produces: discoverable agent instructions with no executable hooks.

- [ ] **Step 1: Create identical adapter semantics for both agents.**

Each `SKILL.md` must require, in order:

1. read `AGENTS.md`, accepted ADRs, current state, active task packet, then the loop declaration;
2. reject any loop scope or verifier wider than the task packet;
3. announce GOAL/SCOPE/VERIFY/BUDGET/STOP/RECEIPT before edits;
4. use one isolated writer branch/worktree;
5. after each iteration run only the declared verifier(s), feed raw failure evidence to the next iteration, increment iteration/identical-failure counters, and stop at limits;
6. on verifier pass, rerun VERIFY independently before writing a passing receipt;
7. stop-and-escalate for secrets, accounts, GitHub/Sonar administration, Tailscale, privileged hosts/runners, or any path/authority conflict;
8. never create upstream GOALS/STATUS/project brief or execute vendored scripts;
9. keep receipts subordinate to Git task/ADR authority.

The skill may link to `third_party/loop-engineering/core/METHODOLOGY.md` and `core/COMMANDS.md` as reference only.

- [ ] **Step 2: Append a short Working Agreement paragraph without clobbering existing agent instructions.**

Use explicit markers:

```markdown
<!-- forgellm-loop-engineering:begin -->
For authorized bounded loops, use the project-local ForgeLLM Loop Engineering bridge. Git task packets and accepted ADRs remain authoritative; loop declarations may narrow but never widen SCOPE/VERIFY/privilege. No upstream installer, eval runner, Stop hook, shadow GOALS/STATUS state, or privileged operation is permitted by a loop.
<!-- forgellm-loop-engineering:end -->
```

- [ ] **Step 3: Extend focused tests to assert both adapters contain the authority, budget, external verifier, and privilege-firewall markers and contain no Stop-hook installation instruction.**

Run:
```bash
python -m pytest -q tests/test_loop_engineering.py
```
Expected: PASS.

- [ ] **Step 4: Commit adapters.**

```bash
git add .agents/skills/forgellm-loop-engineering .claude/skills/forgellm-loop-engineering AGENTS.md CLAUDE.md tests/test_loop_engineering.py
git commit -m "docs(agents): install ForgeLLM loop bridge"
```

### Task 6: Wire repository gates and document operational evidence

**Files:**
- Modify: `Makefile`
- Create: `docs/quality/P0-T10-LOOP-ENGINEERING.md`
- Modify: `tests/test_loop_engineering.py`

**Interfaces:**
- Produces: `make validate` and `make ci` enforce P0-T10 packet and loop contract on every PR.

- [ ] **Step 1: Update Makefile without weakening existing commands.**

Add `validate-loop` to `.PHONY` and:

```make
validate-loop:
	$(PYTHON) scripts/validate_task_packet.py tasks/open/P0-T10-bounded-loop-engineering.yaml --root .
	$(PYTHON) scripts/validate_loop_engineering.py --root .
```

Make `validate` depend on or invoke these two commands in addition to all existing P0-T09 and Phase 0 validation. Add new loop Python/test files to a `LOOP_FORMAT_FILES` variable and include it in Ruff format checking.

- [ ] **Step 2: Add a Makefile regression test.**

Test reads `Makefile` and asserts both exact commands occur and all existing P0-T09 validation markers remain present.

- [ ] **Step 3: Write operational evidence doc.**

`docs/quality/P0-T10-LOOP-ENGINEERING.md` records:

- exact upstream SHA/blob inventory and exclusions;
- owner approval and ADR status;
- RED/GREEN focused test commits;
- no installer/eval runner/Stop hook;
- six-field contract and default P0-T10 budget `10 iterations / 3 identical failures`;
- privilege firewall;
- exact final CI/review IDs when available;
- explicit non-claims: Loop Engineering does not authorize P0-T09 activation, hardware, runtime, performance, or external administration.

- [ ] **Step 4: Run complete local/repository verification.**

```bash
python scripts/validate_task_packet.py tasks/open/P0-T10-bounded-loop-engineering.yaml --root .
python scripts/validate_loop_engineering.py --root .
python -m pytest -q tests/test_loop_engineering.py
make ci
git diff --check
git status --short
```
Expected: all gates pass; status is clean after commit.

- [ ] **Step 5: Commit repository gates/evidence.**

```bash
git add Makefile tests/test_loop_engineering.py docs/quality/P0-T10-LOOP-ENGINEERING.md
git commit -m "quality: gate bounded loop engineering"
```

### Task 7: Independent architecture/security review and ADR acceptance

**Files:**
- Modify: `docs/architecture/ADR-0005-bounded-loop-engineering.md`
- Modify when needed: files inside P0-T10 allowed paths only.

**Interfaces:**
- Consumes: exact final PR diff and all machine evidence.
- Produces: independent ACCEPT or concrete BLOCKER/MAJOR findings.

- [ ] **Step 1: Freeze an exact review SHA and request independent review.**

Review prompt must specifically challenge:

- competing source-of-truth paths;
- command injection/eval surfaces;
- scope widening and path-prefix mistakes;
- verifier self-certification;
- unbounded retry/daemon behavior;
- privilege escalation through task/loop text;
- third-party provenance drift;
- agent-instruction conflicts;
- concurrency/worktree assumptions.

- [ ] **Step 2: Resolve every BLOCKER/MAJOR through code/test changes, then rerun all exact-head gates.**

Do not dismiss findings solely because CI is green.

- [ ] **Step 3: Change ADR status from `proposed` to `accepted` only after independent review ACCEPT.**

Record reviewer/model, review SHA, and evidence references in the ADR or quality evidence document.

- [ ] **Step 4: Re-run exact-head gates after the ADR-status commit.**

Require Phase 0, CodeQL, GitGuardian and Sonar success on that exact SHA. Report Dependency Review by actual conclusion.

### Task 8: Merge and prove protected-main integration

**Files:**
- No new implementation files before merge.
- Closeout changes happen in a separate reviewed PR after main evidence.

**Interfaces:**
- Consumes: accepted ADR, exact-head machine gates, independent review ACCEPT.
- Produces: merged bounded Loop Engineering integration with protected-main proof.

- [ ] **Step 1: Re-read PR head, `main`, checks, and reviews immediately before merge.**

Abort if the head moved, main changed incompatibly, any required check is not success, or independent review is absent.

- [ ] **Step 2: Squash-merge using `expected_head_sha`.**

No direct push to main.

- [ ] **Step 3: Require resulting main Phase 0, CodeQL, GitGuardian/Sonar evidence as applicable and confirm Loop validation runs from `make ci`.**

- [ ] **Step 4: Create a separate closeout PR.**

Move `tasks/open/P0-T10-bounded-loop-engineering.yaml` to `tasks/closed/`, write final receipt `artifacts/governance/loop-engineering/receipts/P0-T10.yaml`, update CURRENT_STATE/HANDOFF/PHASE0_TASKS only from exact merged-main evidence, and preserve P0-T09 independently.

## Self-review

- Spec coverage: every ADR-0005 invariant maps to Tasks 2–7; privilege and shadow-state controls have explicit negative tests.
- Placeholder scan: no TBD/TODO implementation steps remain.
- Type consistency: public validator functions and declaration/receipt keys are defined once in Task 4 and used consistently afterward.
- Scope consistency: implementation avoids P0-T09 `validation.py` and `test_validation.py`, so #35 and P0-T10 can proceed independently until merge ordering is resolved by Git.
