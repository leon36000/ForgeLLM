# ForgeLLM Handoff

**From state:** S-0003  
**To task:** P0-T03 — GitHub control-plane hardening  
**Generated:** 2026-08-13

## Verified canonical state

- Repository: private GitHub repository `leon36000/ForgeLLM`.
- Default branch: `main`.
- Phase 0 bootstrap PR #1: merged by squash.
- Final PR head: `aa978989a5f6ad3524618eda5cd8b650288c7a67`.
- Merge commit: `20bc5fa061aa039d32c2702d47eeba07dd353363`.
- Merge tree: `c75bc10c17744cba0bf0c5a284cd40f4285a2e10`.
- Final PR CI: run `31676559801`, job `94372299029`, success.
- Post-merge `main` CI: run `31676680397`, job `94372665642`, success.
- Both decoded jobs showed Ruff passing, all Phase 0 validators passing, deterministic five-file mobile hashing, 13 tests passing and the Ubuntu bootstrap dry-run passing.

## P0-T02 disposition

`P0-T02` is complete for its private-bootstrap scope.

Completed outputs:

- canonical private remote;
- merged Phase 0 foundation;
- source-of-truth hierarchy and accepted architecture ADRs;
- five-file mobile context and deterministic hash command;
- solo-project review policy;
- independent fresh-context review report;
- successful PR-head and post-merge CI evidence;
- explicit evidence limits and GPU-runner prohibition while protection is unknown.

## Active task

`tasks/open/P0-T03-repository-hardening.yaml`

P0-T03 must directly inspect and, where authorized and supported, configure:

- branch protection or repository rulesets for `main`;
- stable required check `Validate and test`;
- pull-request, conversation-resolution, force-push and deletion controls;
- GitHub Actions default permissions and selected-action policy;
- CodeQL and Dependency Review support and opt-in variables;
- read-only audit artifacts and rollback instructions.

## Known blocker

The connected GitHub integration returned `403 Resource not accessible by integration` for `repos/leon36000/ForgeLLM/branches/main/protection`. This means the protection state is **unknown**. It is not evidence that protection is absent or present.

Consequences:

- no self-hosted runner may be registered;
- no privileged hardware workflow may be activated;
- P0-T04 remains blocked until protection and runner isolation are directly evidenced.

The next operator may use an authenticated `gh` CLI or owner GitHub settings UI, but must preserve exact redacted output and every administrative write/rollback command.

## Security feature status

- `Phase 0 verification`: active and passing.
- CodeQL: workflow present but skipped by the private-repository feature guard; not claimed active.
- Dependency Review: workflow present but skipped by the private-repository feature guard; not claimed active.
- Dependabot: configured and began dependency update evaluation after the Phase 0 merge; each resulting change requires normal review and CI.
- Active CODEOWNERS: none; do not invent a second owner or team.
- Self-hosted runners: none registered or authorized by this handoff.

## Evidence limits

No inference runtime, kernel, model benchmark, hardware inventory, driver/toolkit installation, distributed deployment, external benchmark reproduction, license decision or public release has occurred.

## Next operator sequence

1. Read S-0003 and the P0-T03 task packet.
2. Run the repository audit read-only before any administrative write.
3. Capture current repository visibility, default branch, Actions permissions, rulesets and branch-protection responses.
4. Apply only owner-authorized, reversible controls supported by the current GitHub plan.
5. Run each optional security workflow successfully before making its check required.
6. Keep all self-hosted runner work blocked.
7. Update state, risks, repository policy and mobile projection.
8. Obtain fresh-context review and exact-head CI before merge.

## Continuity checksum

The next state must preserve decisions D-0001 through D-0007 and unresolved risks R-001, R-002, R-005, R-007 and R-008. A missing reference is a continuity warning, not evidence that an item disappeared.
