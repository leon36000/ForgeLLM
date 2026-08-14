# Exact Speculative-Decoding Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a finite exact Python oracle for stochastic and greedy speculative decoding, exhaustive equality-of-law verification and transactional token-prefix state semantics.

**Architecture:** Immutable exact-distribution primitives form the base. A sampled one-token kernel and block-round function implement modified rejection sampling. Independent analytical enumerators compare speculative and ordinary target laws exactly. A separate greedy module and transactional prefix-state module avoid conflating stochastic semantics with deterministic decoding or production KV storage.

**Tech Stack:** Python 3.11 standard library (`fractions`, `math`, `dataclasses`, `typing`), pytest 9, Ruff 0.16.2, existing ForgeLLM governance tooling. No new dependency.

## Global Constraints

- Finite table-defined synthetic models only.
- No floats in governed probability calculations.
- No model download, tokenizer, neural inference or hardware access.
- No Rust runtime, C ABI, backend, kernel or performance path.
- `p` always denotes target and `q` proposal in ForgeLLM APIs/docs.
- A proposal must retain the exact `q` used to sample it.
- No acceptance after first rejection.
- No bonus after EOS or exhausted budget.
- Equality of output law is the exactness oracle; same-seed identity is not.
- Every mutable-looking operation returns immutable dataclasses/tuples.
- Stable exception classes and deterministic diagnostics are required.
- P0-T04 and P0-T05 remain unchanged.

---

### Task 1: Implement exact finite distributions and deterministic random tapes

**Files:**
- Create: `src/forgellm_governance/exact_distribution.py`
- Create: `tests/test_exact_distribution.py`

**Interfaces:**

```python
Token = int

class IntegerSource(Protocol):
    def randbelow(self, upper_bound: int) -> int: ...

@dataclass(frozen=True, slots=True)
class RandomTape:
    draws: tuple[int, ...]
    cursor: int = 0
    def randbelow(self, upper_bound: int) -> tuple[int, RandomTape]: ...

@dataclass(frozen=True, slots=True)
class ExactDistribution:
    probabilities: tuple[tuple[int, Fraction], ...]
    @classmethod
    def from_pairs(cls, pairs: Iterable[tuple[int, int | Fraction]]) -> ExactDistribution: ...
    def probability(self, token: int) -> Fraction: ...
    def support(self) -> tuple[int, ...]: ...
    def argmax(self) -> int: ...
    def sample(self, tape: RandomTape) -> tuple[int, RandomTape]: ...
    def positive_residual(self, proposal: ExactDistribution) -> ExactDistribution: ...
```

- [ ] Write failing construction tests: duplicate token, bool token, negative token/weight, zero total, zero-entry removal, exact normalization, canonical order and frozen mutation.
- [ ] Run `python -m pytest -q tests/test_exact_distribution.py` and confirm import/test failures.
- [ ] Implement `DistributionValidationError`, `UnreachableResidualError`, canonical normalization and lookup/argmax.
- [ ] Add failing `RandomTape` tests for exhaustion, invalid upper bound, out-of-range draw, deterministic no-draw distribution and exact rational categorical sampling.
- [ ] Implement immutable tape advancement and common-denominator integer sampling; never use modulo reduction.
- [ ] Add and pass residual tests for partial overlap, disjoint support, `p==q` and exact normalization.
- [ ] Run focused tests, Ruff check and format check.
- [ ] Commit: `feat(speculative): add exact finite distributions`.

### Task 2: Implement the one-token modified rejection kernel

**Files:**
- Create: `src/forgellm_governance/speculative_decoding.py`
- Create: `tests/test_speculative_sampling.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class OneTokenDecision:
    proposed_token: int
    acceptance_probability: Fraction
    accepted: bool
    emitted_token: int
    correction_kind: Literal["accepted", "residual"]
    tape: RandomTape


def exact_bernoulli(probability: Fraction, tape: RandomTape) -> tuple[bool, RandomTape]: ...
def decide_one_token(
    target: ExactDistribution,
    proposal: ExactDistribution,
    proposed_token: int,
    tape: RandomTape,
) -> OneTokenDecision: ...
```

- [ ] Write failing tests for acceptance probability below/equal/above one, target-zero proposal, deterministic accept/reject and proposal outside positive `q` support.
- [ ] Verify tests fail before implementation.
- [ ] Implement `ProposalValidationError`, exact Bernoulli and acceptance branch.
- [ ] Add failing residual-correction tests and implement normalized `(p-q)_+` sampling.
- [ ] Add an exhaustive single-token law test that sums exact branch masses for every token and equals `p` for several adversarial `p/q` pairs.
- [ ] Verify `p==q` never enters residual and consumes no acceptance draw when probability is one.
- [ ] Run focused tests, Ruff and commit: `feat(speculative): add exact rejection kernel`.

### Task 3: Implement finite table models and sampled block rounds

**Files:**
- Create: `src/forgellm_governance/speculative_models.py`
- Modify: `src/forgellm_governance/speculative_decoding.py`
- Create: `tests/test_speculative_round.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class FiniteTableModel:
    table: tuple[tuple[tuple[int, ...], ExactDistribution], ...]
    def distribution(self, prefix: tuple[int, ...]) -> ExactDistribution: ...

@dataclass(frozen=True, slots=True)
class ProposalRecord:
    prefix: tuple[int, ...]
    distribution: ExactDistribution
    token: int

@dataclass(frozen=True, slots=True)
class SampledRoundResult:
    prefix: tuple[int, ...]
    proposed_tokens: tuple[int, ...]
    accepted_count: int
    emitted_tokens: tuple[int, ...]
    acceptance_probabilities: tuple[Fraction, ...]
    correction_kind: Literal["none", "residual", "bonus"]
    termination: Literal["budget", "eos", "rejection", "all_accepted"]
    tape: RandomTape


def sample_speculative_round(... ) -> SampledRoundResult: ...
```

- [ ] Write failing model-table tests for duplicate prefix, missing prefix, invalid prefix token and deterministic lookup.
- [ ] Implement immutable canonical `FiniteTableModel` and `ModelTableError`.
- [ ] Write failing zero-budget tests proving no model lookup and no tape consumption.
- [ ] Implement autoregressive proposal generation bounded by `min(draft_length, budget)` and EOS.
- [ ] Write failing left-to-right verification tests for all-accepted, first rejection, discarded suffix and recorded `q_i` usage.
- [ ] Implement verification and one correction only.
- [ ] Write failing bonus/EOS/budget tests and implement the legal bonus phase.
- [ ] Assert every `SampledRoundResult` invariant in `__post_init__`.
- [ ] Run focused tests, Ruff and commit: `feat(speculative): add sampled block rounds`.

### Task 4: Implement ordinary target-law enumeration

**Files:**
- Create: `src/forgellm_governance/speculative_exhaustive.py`
- Create: `tests/test_target_law.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class ExactSequenceLaw:
    probabilities: tuple[tuple[tuple[int, ...], Fraction], ...]
    @classmethod
    def from_pairs(... ) -> ExactSequenceLaw: ...
    def probability(self, sequence: tuple[int, ...]) -> Fraction: ...


def enumerate_target_law(
    target: FiniteTableModel,
    prefix: tuple[int, ...],
    budget: int,
    eos_token_id: int,
) -> ExactSequenceLaw: ...
```

- [ ] Write failing law-normalization and duplicate-sequence aggregation tests.
- [ ] Implement canonical exact sequence laws and `LawNormalizationError`.
- [ ] Write failing target-recursion tests for budget 0, deterministic model, branching model and EOS termination.
- [ ] Implement recursive enumeration with exact `Fraction` mass and missing-prefix failure.
- [ ] Verify total law mass is exactly one and output lengths never exceed budget.
- [ ] Run focused tests, Ruff and commit: `feat(speculative): enumerate exact target law`.

### Task 5: Implement analytical speculative-law enumeration

**Files:**
- Modify: `src/forgellm_governance/speculative_exhaustive.py`
- Create: `tests/test_speculative_exhaustive.py`

**Interfaces:**

```python
def enumerate_speculative_round_law(
    target: FiniteTableModel,
    draft: FiniteTableModel,
    prefix: tuple[int, ...],
    budget: int,
    draft_length: int,
    eos_token_id: int,
) -> ExactSequenceLaw: ...


def enumerate_speculative_law(... ) -> ExactSequenceLaw: ...
```

- [ ] Write failing exact-law tests for a one-position model and compare to target law.
- [ ] Implement exact proposal-path mass and consecutive acceptance mass.
- [ ] Add failing first-rejection residual branch tests and implement correction mass.
- [ ] Add failing all-accepted bonus tests and implement bonus mass.
- [ ] Recursively compose rounds until budget/EOS.
- [ ] Build finite adversarial table families and assert exact equality with target law for budgets 0–4 and draft lengths 1–3.
- [ ] Add draft-perturbation tests showing identical final law with changed acceptance branches.
- [ ] Verify laws sum exactly to one; no Monte Carlo or float is used.
- [ ] Run focused tests, Ruff and commit: `feat(speculative): prove bounded speculative output law`.

### Task 6: Implement the separate greedy oracle

**Files:**
- Create: `src/forgellm_governance/speculative_greedy.py`
- Create: `tests/test_speculative_greedy.py`

**Interfaces:**

```python
def greedy_target_decode(... ) -> tuple[int, ...]: ...
def greedy_speculative_round(... ) -> tuple[int, ...]: ...
def greedy_speculative_decode(... ) -> tuple[int, ...]: ...
```

- [ ] Write failing argmax tie tests requiring smallest-token selection.
- [ ] Write failing matching-prefix, first-mismatch, fully-matched bonus, EOS and budget tests.
- [ ] Implement target and speculative greedy functions without accepting a random source.
- [ ] Exhaustively compare bounded greedy outputs for all synthetic table families and draft lengths.
- [ ] Run focused tests, Ruff and commit: `feat(speculative): add deterministic greedy oracle`.

### Task 7: Implement transactional prefix-state witnesses

**Files:**
- Create: `src/forgellm_governance/speculative_state.py`
- Create: `tests/test_speculative_state.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class DecoderState: ...

@dataclass(frozen=True, slots=True)
class RoundTransaction:
    original: DecoderState
    proposed_tokens: tuple[int, ...]
    closed: bool = False
    @classmethod
    def begin(cls, state: DecoderState, proposed_tokens: tuple[int, ...]) -> RoundTransaction: ...
    def commit(self, result: SampledRoundResult, eos_token_id: int) -> tuple[DecoderState, RoundTransaction]: ...
    def cancel(self) -> tuple[DecoderState, RoundTransaction]: ...

def synchronize_pending(state: DecoderState) -> DecoderState: ...
```

- [ ] Write failing `DecoderState` invariant tests.
- [ ] Implement `StateInvariantError` and frozen-state validation.
- [ ] Write failing begin/precondition/cancellation tests and implement exact rollback.
- [ ] Add accepted-proposal materialization tests.
- [ ] Add rejection tests proving rejected suffix never commits and correction becomes pending.
- [ ] Add bonus and EOS pending/materialized cases.
- [ ] Add `synchronize_pending` tests and reject starting a new round with pending state.
- [ ] Reject double commit/cancel, result/proposal mismatch and invalid acceptance count.
- [ ] Run focused tests, Ruff and commit: `feat(speculative): define transactional prefix state`.

### Task 8: Add deterministic traces and adversarial integration tests

**Files:**
- Create: `src/forgellm_governance/speculative_trace.py`
- Create: `tests/test_speculative_adversarial.py`
- Create: `tests/test_speculative_trace.py`
- Modify: `src/forgellm_governance/__init__.py`

**Interfaces:**

```python
def canonical_trace_document(result: SampledRoundResult, state: DecoderState | None = None) -> dict[str, object]: ...
def canonical_trace_bytes(... ) -> bytes: ...
```

- [ ] Write failing deterministic rational-serialization tests using `{numerator, denominator}`.
- [ ] Implement timestamp-free, host-free canonical trace serialization.
- [ ] Add adversarial tests for bool/negative tokens, duplicate entries/prefixes, invalid draws, q mismatch, unreachable residual, missing model prefix, zero budget, EOS at every phase, cancellation and corrupted state.
- [ ] Verify reordered table entries preserve semantic law and canonical traces where inputs are semantically identical.
- [ ] Export only stable reference interfaces in `__init__.py`.
- [ ] Run all CA-03 focused tests, Ruff and commit: `test(speculative): add adversarial exactness coverage`.

### Task 9: Integrate repository gates and documentation

**Files:**
- Modify: `Makefile`
- Create: `docs/speculative/EXACT_REFERENCE.md`
- Modify: `tasks/open/P0-T08-exact-speculative-decoding.yaml`

- [ ] Add `verify-speculative` to `.PHONY` and execute all seven CA-03 test modules.
- [ ] Add `verify-speculative` to `ci` without removing P0-T04 or P0-T07 gates.
- [ ] Document notation, stochastic law, greedy separation, state boundaries and evidence limits.
- [ ] Record focused command outputs and exact source/plan revisions in the task packet; keep status truthful (`in_progress` or `review`).
- [ ] Run `make ci`, `git diff --check` and a clean-worktree check.
- [ ] Commit: `ci(speculative): enforce exact reference gates`.

### Task 10: Fresh reviews, hosted verification and closeout

**Files:**
- Create: `docs/reviews/P0-T08-EXACT-SPECULATIVE-SEMANTICS-REVIEW.md`
- Modify after evidence: task/state/handoff/roadmap/mobile files allowed by the packet.

- [ ] Request a fresh specification-compliance review against the canonical spec and task packet.
- [ ] Resolve every BLOCKER/MAJOR finding with a failing regression test first.
- [ ] Request a separate code-quality review focused on probability arithmetic, branch mass, state invariants and deterministic errors.
- [ ] Run the complete focused suite and `make ci` on the exact final head.
- [ ] Open a PR; require hosted `Validate and test` and CodeQL success. Treat Dependency Review honestly according to policy.
- [ ] Merge only after review and exact-head gates.
- [ ] Verify post-merge Phase 0 and CodeQL on `main`.
- [ ] Close P0-T08 in a separate state PR only after post-merge evidence exists.

## Completion report

The final report records:

1. owner authorization and task packet;
2. base, reviewed head and merge commits;
3. exact arithmetic and law-equality tests;
4. stochastic and greedy API boundaries;
5. transactional state cases;
6. focused/full/hosted gate identifiers;
7. fresh review findings and resolutions;
8. evidence limits and unsupported production behavior;
9. next recommended work package.
