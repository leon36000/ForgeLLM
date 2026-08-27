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
