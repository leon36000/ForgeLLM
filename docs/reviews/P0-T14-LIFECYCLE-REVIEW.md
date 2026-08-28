# P0-T14 Lifecycle and Derived-State Verification Review

- **Task:** P0-T14
- **Authorization source:** owner-approved issue #73 and the bounded execution plan
- **Base:** `9932a5a496df53e812d9f47c6bb95ae94b3a4a2f`
- **Implementation head:** `51aa42cbff06d3a79df9a485ad6045b74148f522`
- **Lifecycle packet head:** `29560d4e7ac9592e151f3fea75a4721d2cf845a1`
- **Candidate head reviewed in round 2:** `b8706238aff8cffbbf66e9ee9aec8bcb6a30ebf2`
- **Evidence boundary:** repository governance and deterministic projections only
- **Status:** remediation in progress after Sol gate NO-GO

## Scope

This review covers task-directory lifecycle semantics, ADR dependency metadata, canonical state freshness, the rebuildable mobile manifest, the README current-state block, and the exact tracked-path tree. It does not authorize or assess inference, models, hardware, CUDA/ROCm, runtime, ABI, backend, kernel, serving, benchmarks, secrets or external settings.

## Test-driven evidence

The first focused RED checkpoint was committed as `ed82788f9db86cc5dc05f7ea5b2b5bd9cd48aa51`. Before implementation, the following command failed during collection because the lifecycle APIs did not yet exist:

```text
PYTHONPATH=src python3 -m pytest -q tests/test_lifecycle.py
ImportError: cannot import name 'build_mobile_manifest' from forgellm_governance.validation
```

The implementation and validator integration were committed as `51aa42cbff06d3a79df9a485ad6045b74148f522`. The task packet authorization and closeout state were recorded in `c93fecf48de64e1160ad3694644e336b3dac945b` and `29560d4e7ac9592e151f3fea75a4721d2cf845a1`.

## Local verification on the candidate

- `PYTHONPATH=src python3 -m pytest -q tests/test_lifecycle.py tests/test_validation.py`: **28 passed**;
- `make validate`: all project, research, benchmark, task, topology, mobile and shell gates passed;
- `make ci`: Ruff check passed, the configured format gate passed, **501 tests passed**, **230 reference tests passed**, and the canonical synthetic simulation plus SHA-256 evidence passed;
- `python3 -m ruff check src scripts tests`: passed;
- `git diff --check`: passed before report remediation;
- `TREE.txt` equals the sorted `git ls-files` output and the derived manifest equals the generator output;
- the lifecycle validator reports `OK: ForgeLLM lifecycle state is semantically valid`.

## Hosted PR failure and systematic remediation

PR #80 exposed a portability defect not visible in the full local clone. On head `9283ad106bc9ee30080daa1cadfbab3d116935ae`, hosted job `98741174915` failed in `make ci` at `validate_lifecycle` because the workflow checkout did not contain the older canonical source commit `29560d4e7ac9592e151f3fea75a4721d2cf845a1`. The independent hosted checks `CodeQL 98741309269`, `SonarCloud`, `analyze-python` and GitGuardian passed; dependency review was skipped by the existing workflow policy.

The failure was reduced to the smallest reproducer: a depth-one clone of the projection fixture cannot prove ancestry for an older source commit. The regression test was committed as `aa6a3e9` after reproducing the failure with `1 failed, 13 deselected`; the fix is `b7ee96e`. In a shallow repository, the validator now retains structural full-hash and manifest checks and skips only the impossible object-presence/ancestor assertion; in a repository with the object available, both presence and ancestry checks remain enforced. No workflow, external setting or security gate was weakened.

The initial hosted SonarCloud run reported a passing Quality Gate but still created 11 new annotations on the changed validator: five quality findings for duplicated literals and cognitive complexity, plus six concise-regex warnings. None were accepted as harmless by default. The literal findings were removed with shared path/pattern constants; the complexity findings were reduced by splitting decision and packet/lifecycle collection helpers; and the numeric regexes now use `\d` with `re.ASCII` so the original ASCII identifier semantics remain explicit.

The shallow-checkout fix was committed as `b7ee96e`; the Sonar remediation refactor is `3a75f78`. The fresh local `make ci` on `13dce624da6f0cf27962ad06796696953b6e3bd2` passed with **501** full tests and **230** reference tests. The matching hosted checks are: Validate and test `98742841471`, analyze-python `98742841262`, CodeQL `98742957759`, SonarCloud `98742924616` with **0 annotations**, and GitGuardian `98742840150`; dependency review `98742863210` was skipped by the existing workflow policy. The hosted remediation head is therefore green and requires only the final critical Sol gate before merge.

The final GPT-5.6 Luna review on `bf95b16b8fd4ca7a7131b9a51875375f4630d46e` returned `VERDICT=ACCEPT`. Its only LOW observation was that the packet's standalone `validate_task_packet.py` command relied on the Makefile's exported `PYTHONPATH`; the command is now explicitly prefixed with `PYTHONPATH=src` in the packet. No functional scope or gate was changed.

The status inventory is deterministic: P0-T03, P0-T07, P0-T08, P0-T11, P0-T12, P0-T13 and P0-T14 are closed/complete; P0-T04 is open/blocked; P0-T09 is open/in_progress; P0-T10 is open/review; and P0-T15 is open/in_progress. ADR-0005 and ADR-0006 remain proposed.

## Independent review round 1

GPT-5.6 Luna reviewed candidate `4ed80f473e107b149c69a7b76496c5791a8ff781` in a separate read-only context and returned `VERDICT=CHANGES_REQUESTED` for:

1. missing versioned closeout evidence at `docs/reviews/P0-T14-LIFECYCLE-REVIEW.md` despite the packet requiring RED, base, implementation, review and merge evidence;
2. the deletion of the stale open P0-T03 packet not being explicitly listed in the packet's `allowed_paths`.

Both findings are addressed by this report and by adding the deleted open P0-T03 path to the P0-T14 allowed-path declaration. A new exact-head independent review is required before publication.

## Independent review round 2

GPT-5.6 Luna reviewed the corrected candidate `b8706238aff8cffbbf66e9ee9aec8bcb6a30ebf2` in a separate read-only context. It reran the RED replay, focused tests, packet/lifecycle/project validators, `make ci` in a temporary clone, manifest/tree comparison and the allowed-path audit. It found no Critical, High or Medium issue; the two round-1 findings were confirmed resolved. The review recorded **500 passing Python tests**, **230 passing reference tests**, successful Ruff/validation/simulation/hash gates, a clean worktree and no external mutation.

**Round-2 verdict:** `ACCEPT` for the reviewed candidate. The final exact-head receipt review below confirms the report and all lifecycle evidence before publication.

## Pre-remediation exact-head receipt review

GPT-5.6 Luna reviewed the exact receipt candidate `59a912a89136ee9ae7860deb118e1bb755d178f7` in a separate read-only context. It found no issue and confirmed the diff, allowed-path scope, `TREE.txt`, derived manifest, lifecycle validators and the fresh `make ci` result (**500** full tests and **230** reference tests, with validation and simulation/hash gates successful). No secret, external setting, issue, hardware, model, runtime, backend, ABI, CUDA or ROCm operation was involved.

**Pre-remediation exact-head receipt verdict:** `ACCEPT`; superseded as the final publication head by the hosted-check and Sonar remediation above.

## Sol gate round 1

GPT-5.6 Sol reviewed the exact PR head `44b94b49b3a2251faf5c2cb7c080af810576aafd` with all hosted checks green and returned `VERDICT=NO-GO` for two factual/test-coverage gaps:

1. the roadmap row stated **13 lifecycle tests**, while the shallow-checkout regression had already increased the suite to 14;
2. the lifecycle test module lacked a negative regression proving that a stale `TREE.txt` is rejected.

The first gap is corrected to **15 lifecycle tests** after adding the tree regression. The second is covered by `test_tree_projection_rejects_stale_listing`, which exercises the existing validator against a committed stale tree. No runtime, security, external-setting or evidence-boundary change is involved. A fresh exact-head Sol gate is required after the remediation.

## Safety and evidence boundaries

No secret was read or written. No GitHub/Sonar setting or issue was mutated. No hardware probe, model inference, runtime/backend/ABI/kernel/CUDA/ROCm operation or benchmark was run. Historical implementation merges do not accept ADR-0005 or ADR-0006; P0-T10 remains `review` and P0-T15 remains design-only `in_progress`.

**Final verdict:** pending post-remediation critical Sol gate and hosted checks.
