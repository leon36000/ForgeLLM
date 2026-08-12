# ForgeLLM Phase 0 Operating System Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a verified, Git-backed memory, research, agent-governance and benchmark foundation for ForgeLLM before inference-engine code begins.

**Architecture:** The repository is canonical; a five-file mobile bundle is a compact projection. Markdown and YAML hold human-reviewed state, JSON Schema plus Python provide machine enforcement, and GitHub/GitLab automation runs the same local gates.

**Tech Stack:** Markdown, YAML 1.2-compatible data, JSON Schema Draft 2020-12, Python 3.11+, pytest, jsonschema, PyYAML, Git, GitHub Actions and GitLab CI.

## Global Constraints

- No inference-engine implementation is part of Phase 0.
- No external performance claim may be marked reproduced without a reviewed ForgeLLM experiment.
- No GPU driver installation is automated.
- No self-hosted GPU runner may execute unreviewed fork code.
- No project license is assumed before an accepted licensing ADR.
- CI actions are pinned to full commit SHAs.
- Repository state, not conversation memory, is canonical.

---

### Task 1: Establish the project charter and authority model

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `CLAUDE.md`
- Create: `docs/architecture/PROJECT_CHARTER.md`
- Create: `docs/architecture/ARCHITECTURE_PRINCIPLES.md`
- Create: `docs/architecture/ADR-0001-language-and-backends.md`
- Create: `docs/architecture/ADR-0002-source-of-truth.md`

**Interfaces:**
- Consumes: owner acceptance of the ForgeLLM name and hybrid Rust/native direction.
- Produces: authority order, architectural invariants and agent startup contract used by every later task.

- [ ] **Step 1: Write the charter with measurable phase boundaries and explicit non-goals.**
- [ ] **Step 2: Write ADR-0001 selecting Rust control plane, narrow C ABI and specialized native backends.**
- [ ] **Step 3: Write ADR-0002 making Git-tracked artifacts canonical over implicit chat memory.**
- [ ] **Step 4: Add root instructions that require reading charter, state and active task before edits.**
- [ ] **Step 5: Run `python scripts/validate_project_state.py --root .` and confirm exit code 0.**
- [ ] **Step 6: Commit with `git commit -m "docs: establish ForgeLLM charter and authority model"`.**

### Task 2: Build the five-file mobile continuity bundle

**Files:**
- Create: `chatgpt/PROJECT_INSTRUCTIONS.txt`
- Create: `chatgpt/SESSION_BOOTSTRAP_PROMPT.md`
- Create: `chatgpt/SESSION_CLOSEOUT_PROMPT.md`
- Create: `chatgpt/mobile-core/00_FORGELLM_CORE_CONTEXT.md`
- Create: `chatgpt/mobile-core/01_FORGELLM_AGENT_OPERATING_SYSTEM.md`
- Create: `chatgpt/mobile-core/02_FORGELLM_RESEARCH_AND_EVIDENCE.md`
- Create: `chatgpt/mobile-core/03_FORGELLM_STATE_AND_DECISIONS.md`
- Create: `chatgpt/mobile-core/04_FORGELLM_PROMPTS_AND_WORKFLOWS.md`

**Interfaces:**
- Consumes: authority and architecture from Task 1.
- Produces: exact mobile startup and closeout protocol, plus five uploadable context files.

- [ ] **Step 1: Encode mission, accepted architecture and forbidden assumptions in file 00.**
- [ ] **Step 2: Encode task lifecycle, role separation and completion report in file 01.**
- [ ] **Step 3: Encode evidence levels, claim states and reproduction rules in file 02.**
- [ ] **Step 4: Project the accepted decisions, current phase, risks and next task into file 03.**
- [ ] **Step 5: Add bootstrap, research, task-packet, review and closeout prompts to file 04.**
- [ ] **Step 6: Run `python scripts/validate_project_state.py --root .` and verify all five files exist and are non-empty.**
- [ ] **Step 7: Commit with `git commit -m "docs: add ForgeLLM mobile continuity bundle"`.**

### Task 3: Create the claim-centered research registry

**Files:**
- Create: `research/repos.yaml`
- Create: `research/papers.yaml`
- Create: `research/claims.yaml`
- Create: `research/queries.yaml`
- Create: `docs/research/EVIDENCE_POLICY.md`
- Create: `docs/research/RESEARCH_PROTOCOL.md`
- Create: `docs/research/LANDSCAPE_2026-08-12.md`
- Create: `docs/research/SOURCE_CATALOG.md`
- Test: `tests/test_validation.py`

**Interfaces:**
- Consumes: architectural questions from Task 1.
- Produces: unique repository, paper and claim IDs with resolvable cross-references.

- [ ] **Step 1: Record ten primary open-source reference stacks and specialized candidates with canonical URLs and licenses.**
- [ ] **Step 2: Record foundational and recent papers by immutable arXiv ID or conference page.**
- [ ] **Step 3: Translate architectural assertions into claim records with class, status, sources and required experiments.**
- [ ] **Step 4: Define recurring arXiv, GitHub and GitLab discovery queries.**
- [ ] **Step 5: Write a failing test for duplicate IDs and unresolved claim/source references.**
- [ ] **Step 6: Implement validation until `pytest tests/test_validation.py -q` passes.**
- [ ] **Step 7: Commit with `git commit -m "research: add claim-centered source registry"`.**

### Task 4: Enforce benchmark evidence with schemas and validators

**Files:**
- Create: `schemas/benchmark-result.schema.json`
- Create: `schemas/task-packet.schema.json`
- Create: `schemas/source-record.schema.json`
- Create: `schemas/claim-record.schema.json`
- Create: `examples/benchmarks/valid-example.json`
- Create: `examples/tasks/P0-T02.yaml`
- Create: `src/forgellm_governance/validation.py`
- Create: `scripts/validate_benchmark.py`
- Test: `tests/test_validation.py`

**Interfaces:**
- Consumes: benchmark standard and task packet contract.
- Produces: `validate_benchmark(path)` and `validate_project(root)` functions plus command-line gates.

- [ ] **Step 1: Write a benchmark example containing commits, inventory, workload, correctness, samples, statistics and artifacts.**
- [ ] **Step 2: Write a test asserting the example fails before the schema exists.**
- [ ] **Step 3: Define Draft 2020-12 schemas with `additionalProperties: false` at governed boundaries.**
- [ ] **Step 4: Implement schema loading and formatted validation errors in `validation.py`.**
- [ ] **Step 5: Add semantic checks for clean worktrees, sample count, correctness pass and artifact hashes.**
- [ ] **Step 6: Run `pytest tests/test_validation.py -q` and confirm valid examples pass while invalid fixtures fail.**
- [ ] **Step 7: Commit with `git commit -m "feat(governance): validate tasks and benchmark evidence"`.**

### Task 5: Add reproducible inventory and continuity snapshots

**Files:**
- Create: `src/forgellm_governance/hardware.py`
- Create: `src/forgellm_governance/snapshot.py`
- Create: `scripts/hardware_inventory.py`
- Create: `scripts/new_session_snapshot.py`
- Test: `tests/test_hardware.py`

**Interfaces:**
- Consumes: operating-system commands available without privilege.
- Produces: redacted JSON inventory and Markdown continuity snapshot under `artifacts/`.

- [ ] **Step 1: Write tests using injected command results for missing NVIDIA/AMD tools and malformed output.**
- [ ] **Step 2: Implement timeout-limited probes for OS, CPU, memory, PCI, NVIDIA, AMD, network and storage.**
- [ ] **Step 3: Hash or omit stable device identifiers by default.**
- [ ] **Step 4: Implement a snapshot that records Git revision, dirty state, current phase, open risks and next task.**
- [ ] **Step 5: Run `pytest tests/test_hardware.py -q`.**
- [ ] **Step 6: Run `python scripts/hardware_inventory.py --output artifacts/hardware-local.json` on a non-GPU host and confirm graceful completion.**
- [ ] **Step 7: Commit with `git commit -m "feat(governance): add hardware and session snapshots"`.**

### Task 6: Configure local and hosted verification

**Files:**
- Create: `pyproject.toml`
- Create: `Makefile`
- Create: `.pre-commit-config.yaml`
- Create: `.github/workflows/phase0.yml`
- Create: `.github/workflows/codeql.yml`
- Create: `.github/workflows/gpu-inventory.yml`
- Create: `.gitlab-ci.yml`
- Create: `.github/dependabot.yml`

**Interfaces:**
- Consumes: validators and tests from Tasks 3–5.
- Produces: `make validate`, `make test`, `make lint`, `make verify`, `make ci`, hosted CI and a manual trusted GPU inventory job.

- [ ] **Step 1: Declare Python 3.11+, runtime dependencies and test tooling in `pyproject.toml`.**
- [ ] **Step 2: Add Make targets that call the same scripts locally and in CI.**
- [ ] **Step 3: Add SHA-pinned GitHub Actions for pull requests, pushes and merge queues.**
- [ ] **Step 4: Add CodeQL and dependency automation without granting write permissions to untrusted jobs.**
- [ ] **Step 5: Add a manual-only self-hosted GPU workflow with private-repository and trusted-ref guards.**
- [ ] **Step 6: Add equivalent GitLab validation stages without privileged GPU execution.**
- [ ] **Step 7: Run `make ci`.**
- [ ] **Step 8: Commit with `git commit -m "ci: enforce ForgeLLM Phase 0 gates"`.**

### Task 7: Add collaboration and security templates

**Files:**
- Create: `.github/ISSUE_TEMPLATE/research.yml`
- Create: `.github/ISSUE_TEMPLATE/experiment.yml`
- Create: `.github/ISSUE_TEMPLATE/engineering-task.yml`
- Create: `.github/ISSUE_TEMPLATE/bug.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `.gitlab/issue_templates/Research.md`
- Create: `.gitlab/merge_request_templates/Default.md`
- Create: `docs/governance/SECURITY_POLICY.md`
- Create: `docs/governance/LICENSING_DECISION.md`

**Interfaces:**
- Consumes: task, evidence and security requirements.
- Produces: structured intake and review fields that map work to claims and acceptance criteria.

- [ ] **Step 1: Require task/claim IDs, scope, non-goals, evidence and acceptance tests in issue forms.**
- [ ] **Step 2: Require correctness, benchmark comparability, security and documentation checklists in pull requests.**
- [ ] **Step 3: Document private reporting and runner isolation.**
- [ ] **Step 4: Document the no-license-yet gate and dependency intake record.**
- [ ] **Step 5: Run `python scripts/validate_project_state.py --root .`.**
- [ ] **Step 6: Commit with `git commit -m "chore: add ForgeLLM collaboration and security controls"`.**

### Task 8: Package and independently verify the bootstrap

**Files:**
- Create: `MANIFEST.sha256`
- Create: `TREE.txt`
- Create: `artifacts/verification-report.json`
- Create: `ForgeLLM-Phase0.zip` outside the repository tree
- Create: `ForgeLLM-Mobile-Core.zip` outside the repository tree

**Interfaces:**
- Consumes: all previous tasks.
- Produces: hash-verifiable full and mobile distributions plus a machine-readable verification report.

- [ ] **Step 1: Run `make ci` from a clean virtual environment.**
- [ ] **Step 2: Scan tracked content for high-confidence secret patterns and unresolved placeholders.**
- [ ] **Step 3: Generate `TREE.txt` with sorted relative paths.**
- [ ] **Step 4: Generate SHA-256 hashes for every packaged file except the manifest itself.**
- [ ] **Step 5: Create both archives with deterministic path ordering.**
- [ ] **Step 6: Extract each archive into a temporary directory and verify hashes and `make ci`.**
- [ ] **Step 7: Record commands, outcomes and limitations in `artifacts/verification-report.json`.**
- [ ] **Step 8: Commit the manifest and report with `git commit -m "chore: package verified ForgeLLM Phase 0 bootstrap"`.**
