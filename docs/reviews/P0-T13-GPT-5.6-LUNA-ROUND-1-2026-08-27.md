# P0-T13 independent blind review — round 1

## Review identity and exact heads

- Task: `P0-T13` — public artifact privacy hardening.
- Initial reviewer model: `gpt-5.6-luna`.
- Review package generation base: `37b6f4878d4aa96588f5ea307e37e0152ed7b27`.
- Exact pre-fix implementation head reviewed: `db957eaeebedc36d467815ffcdd47aeaaeb85275`.
- Review scope: the P0-T13 implementation delta from the scoped base above; this is distinct from the full reconstruction base `6c38e39098dca500f3b5e46af6685b08d5961014`.

## Round-1 verdict

- Implementation verdict: `ACCEPT`.
- Task-quality verdict: `Needs fixes`.
- Reason: the implementation was accepted, but the task evidence needed two Minor test-coverage additions and the task report needed to distinguish the full reconstruction base from the scoped implementation-review base.

## Findings

1. `Minor` — Add a nested forbidden network-field regression, such as an address-like field nested under an otherwise dropped structured value, to demonstrate that the public network boundary does not retain nested forbidden data.
2. `Minor` — Parameterize the unexpected nested storage-value regression so it covers both mapping and list shapes, not only a mapping value.

## Fix-round disposition

The fix round adds the requested real regressions in `tests/test_hardware.py`: nested `address` data under a dropped network structure is asserted absent, and the storage unexpected value is parameterized for both mapping and list values. The amended focused suite passes at the pre-fix implementation head, so no production change is required by these findings. The task report is being corrected to identify the full reconstruction base, scoped review base, pre-fix head, fix-round final head, and exact path scopes.

These findings are addressed pending scoped re-review. This record does not claim a post-fix `ACCEPT`; the controller must obtain and record the scoped re-review against the fix-round final head before merge.

## Sol round-2 NO-GO and resolution

- Gate outcome: `NO-GO` from the Sol round-2 review.
- Exact pre-fix head: `28640bf4864a251cdb40ef9697e32861d85e930d`.
- Blocking finding: `_sanitize_storage_data` accepted mapping-shaped values for the root `blockdevices` field and a device `children` field, recursed into those mappings as if they were device records, and left the storage probe `status` as `ok`. This violated the P0-T13 requirement that malformed structured storage output fail closed.

### Test-first resolution

Two real regressions were added in `tests/test_hardware.py` and committed first as `3776204` (`test(security): reject mapping-shaped storage containers`): root `data.blockdevices` as a mapping and a device `children` value as a mapping. The focused suite was run before production edits and produced the expected RED result: `2 failed, 32 passed in 1.25s`, with both failures asserting that status incorrectly remained `ok`.

The minimal production fix was committed as `bd37b16` (`fix(security): reject mapping-shaped storage containers`): `blockdevices` and `children` must be lists before recursive sanitization. Focused GREEN then passed with `34 passed in 1.08s`, preserving valid list fixtures, recursive mountpoint omission, unknown-field rejection, and existing behavior.

The round-2 blocking finding is resolved in code pending a new exact-head independent review. The post-fix review target is implementation head `bd37b16` (with the subsequent receipt-only commit recorded separately); this receipt does not claim final acceptance.

## Final scoped re-review — Sol round 2 resolution

- Reviewer model: `gpt-5.6-luna`.
- Review package base: `28640bf4864a251cdb40ef9697e32861d85e930d`.
- Exact reviewed head: `f481200b38ed1a093806433ba02e3050effe0907`.
- Prior Sol round-2 `NO-GO` finding: `_sanitize_storage_data` accepted mapping-shaped values for root `blockdevices` and device `children`, recursed into them as device records, and left malformed storage output with status `ok`.
- Resolution reviewed: `3776204` added real RED regressions for both mapping shapes, `bd37b16` added the minimal list guards before recursion, and `f481200` recorded the round-2 receipt; valid list fixtures, mountpoint omission, unknown-field rejection, and existing behavior remained intact.
- Re-review verdict: `ADDRESSED`.
- New findings: `none`.
- Spec Compliance: `Approved`.
- Task quality: `Approved`.
- Final independent review disposition: `ACCEPT` for the scoped re-review. This binds the final independent acceptance without changing production or test files in this documentation-only step. The controller must still revalidate exact head `f481200b38ed1a093806433ba02e3050effe0907`; no additional post-controller acceptance is claimed here.

## Fix-round 3 — Sonar S3776 refactor

- Finding source: live Sonar annotations on PR `#78`, exact annotated head `1f0e2ca2afd5e9b41310afa0ed4812fc023fff1b`.
- Findings: `_sanitize_storage_data` at `src/forgellm_governance/hardware.py:160` had cognitive complexity `28` with `15` allowed; `sanitize_inventory` at `src/forgellm_governance/hardware.py:208` had cognitive complexity `20` with `15` allowed.
- Behavior-preserving resolution: production commit `446d46c66f875c3d3c40e1bc9b3460e8a43a587d` split storage dispatch/list/record/field validation and probe metadata/network/storage collection into small helpers. The refactor retains fail-closed malformed network values, malformed storage root/device container mappings, unknown-field rejection, recursive mountpoint omission, failed-probe nulling, canonical writer, path confinement, CLI/script routing, snapshot behavior, and generic task validation. No test or contract file changed in this round; no complexity suppression or Sonar configuration change was used.
- Fresh exact-head green baseline before edits: at `1f0e2ca2afd5e9b41310afa0ed4812fc023fff1b`, `PYTHONPATH=src python3 -m pytest -q tests/test_hardware.py tests/test_snapshot.py tests/test_validation.py` exited `0` with `34 passed in 1.05s`.
- Focused GREEN after the refactor: the same command exited `0` with `34 passed in 1.01s`.
- Exact packet Ruff command exited `0` with `All checks passed!`; P0-T13 packet validation exited `0` with `OK: tasks/open/P0-T13-public-artifact-privacy-hardening.yaml`.
- `make ci` exited `0`: full suite `487 passed in 10.20s`, speculative suite `230 passed in 0.74s`; repository validation, formatting, simulation, and hash checks passed. `git diff --check` passed and the generated out-of-scope simulation JSON was removed.
- Review disposition: the S3776 refactor is pending fresh exact-head independent review and hosted checks. This receipt does not claim final acceptance or merge readiness.

## Final scoped re-review — fix-round 3

- Reviewer model: `gpt-5.6-luna`.
- Review package base: `1f0e2ca2afd5e9b41310afa0ed4812fc023fff1b`.
- Exact reviewed head: `20c6b3c48103d5f5bb4a461949d0fdc550c110cf`.
- Refactor commit reviewed: `446d46c66f875c3d3c40e1bc9b3460e8a43a587d`.
- Prior Sonar S3776 finding: `_sanitize_storage_data` and `sanitize_inventory` exceeded the cognitive-complexity threshold. The reviewer confirmed that the helper extraction addresses the finding without suppression, Sonar configuration changes, contract drift, caller changes, or loss of the P0-T13 fail-closed privacy semantics.
- Additional evidence: focused tests (`34 passed`), exact Ruff, packet validation, and `git diff --check` passed; a read-only randomized comparison matched base/head sanitizer behavior across `10,000` cases and inputs remained unchanged.
- Findings: `none`.
- Implementation verdict: `ACCEPT`.
- Task-quality verdict: `ACCEPT`.
- Final independent review disposition: `ACCEPT` for the exact fix-round-3 head. Hosted Sonar and hosted checks remain controller gates; this receipt makes no hosted-green claim.
