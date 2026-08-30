# P0-T20 implementation plan: bounded multi-query attention

> Execute this plan in the isolated P0-T20 worktree only. Keep the packet's
> allowed paths closed; do not widen scope when a discovery is convenient.

## 1. Establish the packet and RED evidence

- Validate the in-progress packet and record the protected base `cc5a90d`.
- Add the independent Rust row-wise oracle tests before production code.
- Add Python oracle tests/imports before adding the Python implementation.
- Run focused Rust/Python tests and preserve the exact failing output as RED
  evidence in the quality report.

## 2. Implement the smallest Rust slice

- Add `attention_decode_multi_query` to the reference crate.
- Preserve existing operation code paths and use one existing `softmax` call per
  query row.
- Return only the final `[query_count, head_dim]` tensor and propagate existing
  typed failures.
- Run focused Rust tests, formatting, and Clippy before touching the fixture.

## 3. Extend the independent oracle and fixture

- Add `multi_query_attention_oracle` as a per-row composition of the reviewed
  attention oracle, with explicit shape checks and a documented tolerance matrix.
- Add deterministic fixture cases and extend the restricted Rust dispatch.
- Regenerate only through the repository generator, then verify `--check` and
  the committed SHA-256 pin.
- Run focused Python tests and fixture-driven Rust tests.

## 4. Synchronize state and evidence

- Move the packet from `tasks/open` to `tasks/closed` only after all acceptance
  criteria pass and set it to `complete`.
- Update the quality report, review receipt, README, roadmap, current state,
  handoff, mobile state projection, derived manifest, and exact TREE.
- Keep the protected source anchor ancestral and do not edit the Loop
  Engineering declarations/receipts.

## 5. Independent review and publication gate

- Run the full local gates and diff/path audits on the exact candidate head.
- Obtain one Luna read-only correctness/state review and close it immediately.
- Obtain one GPT-5.6-Sol critical gate verdict on the exact candidate head and
  close it immediately; resolve any blocker before publication.
- Push only the reviewed exact head, open one PR, reconcile the exact head/base,
  wait for all applicable required checks, and merge only after they pass.

## 6. Post-merge receipt and stop condition

- Detach a fresh worktree at the actual merge SHA, rerun the required fresh
  gates, and append the external SDD ledger with exact evidence identifiers.
- If an external required gate cannot be established without forbidden
  mutation, stop and report that concrete blocker. Do not substitute model
  output, hardware results, or an unverified agent claim.
