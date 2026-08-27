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
