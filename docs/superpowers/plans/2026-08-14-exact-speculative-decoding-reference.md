# Exact Speculative-Decoding Reference Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a finite exact Python oracle for stochastic and greedy speculative decoding, exhaustive equality-of-law verification and transactional token-prefix state semantics.

**Architecture:** Immutable exact-distribution primitives form the base. A functional `RandomTape` makes every random transition explicit. A one-token kernel and sampled block-round function implement modified rejection sampling. Independent analytical enumerators compare speculative and ordinary target laws exactly. A separate greedy module and transactional prefix-state module avoid conflating stochastic semantics with deterministic decoding or production KV storage.

**Tech Stack:** Python 3.11 standard library (`fractions`, `math`, `dataclasses`, `typing`), pytest 9, Ruff 0.16.2, existing ForgeLLM governance tooling. No new dependency.

## Global Constraints

- Finite table-defined synthetic models only.
- No floats or `Decimal` in governed probability calculations.
- No model download, tokenizer, neural inference or hardware access.
- No Rust runtime, C ABI, backend, kernel or performance path.
- `p` always denotes target and `q` proposal in ForgeLLM APIs/docs.
- A proposal retains the exact `q` used to sample it.
- No acceptance after first rejection.
- No bonus after EOS or exhausted budget.
- Equality of output law is the stochastic exactness oracle; same-seed identity is not.
- Every state transition returns frozen dataclasses/tuples and does not mutate its input.
- Stable exception classes and deterministic diagnostics are required.
- P0-T04 and P0-T05 remain unchanged.

---

### Task 1: Exact finite distributions and immutable random tapes

**Files:**
- Create: `src/forgellm_governance/exact_distribution.py`
- Create: `tests/test_exact_distribution.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class RandomTape:
    draws: tuple[int, ...]
    cursor: int = 0
    def draw(self, upper_bound: int) -> tuple[int, RandomTape]: ...

@dataclass(frozen=True, slots=True)
class ExactDistribution:
    probabilities: tuple[tuple[int, Fraction], ...]

    @classmethod
    def from_pairs(
        cls,
        pairs: Iterable[tuple[int, int | Fraction]],
    ) -> ExactDistribution: ...

    def probability(self, token: int) -> Fraction: ...
    def support(self) -> tuple[int, ...]: ...
    def argmax(self) -> int: ...
    def sample(self, tape: RandomTape) -> tuple[int, RandomTape]: ...
    def positive_residual(self, proposal: ExactDistribution) -> ExactDistribution: ...
```

- [ ] **Step 1: Write failing construction tests.** Cover duplicate token IDs, bool/negative tokens, bool/negative weights, zero total, zero-entry removal, exact normalization, canonical support order and frozen mutation.
- [ ] **Step 2: Run `python -m pytest -q tests/test_exact_distribution.py`.** Expected: import failure.
- [ ] **Step 3: Implement `DistributionValidationError`, canonical `Fraction` normalization, lookup, support and smallest-token argmax.**
- [ ] **Step 4: Write failing tape tests.** Cover invalid/non-integer upper bound, exhaustion, out-of-range draw, immutability and unchanged tape for deterministic choices.
- [ ] **Step 5: Implement `RandomSourceError` and functional `RandomTape.draw`.** Do not apply modulo reduction.
- [ ] **Step 6: Write failing exact sampling tests.** Use common-denominator rational distributions and assert returned advanced tape.
- [ ] **Step 7: Implement exact categorical sampling.** A one-token distribution returns immediately without drawing.
- [ ] **Step 8: Write and pass residual tests.** Cover partial overlap, disjoint support, exact normalization and `p==q -> UnreachableResidualError`.
- [ ] **Step 9: Run focused pytest and Ruff check/format.**
- [ ] **Step 10: Commit `feat(speculative): add exact finite distributions`.**

### Task 2: One-token modified rejection kernel

**Files:**
- Create: `src/forgellm_governance/speculative_decoding.py`
- Create: `tests/test_speculative_sampling.py`

**Interfaces:**

```python
def exact_bernoulli(
    probability: Fraction,
    tape: RandomTape,
) -> tuple[bool, RandomTape]: ...

@dataclass(frozen=True, slots=True)
class OneTokenDecision:
    proposed_token: int
    acceptance_probability: Fraction
    accepted: bool
    emitted_token: int
    correction_kind: Literal["accepted", "residual"]
    tape: RandomTape


def decide_one_token(
    target: ExactDistribution,
    proposal: ExactDistribution,
    proposed_token: int,
    tape: RandomTape,
) -> OneTokenDecision: ...
```

- [ ] **Step 1: Write failing exact-Bernoulli tests.** Zero/one consume no draw; proper fractions use `draw(denominator) < numerator`; invalid probabilities fail.
- [ ] **Step 2: Implement exact Bernoulli with immutable tape.**
- [ ] **Step 3: Write failing acceptance tests.** Cover `p(x)<q(x)`, `p(x)>=q(x)`, target-zero proposal and token outside positive `q` support.
- [ ] **Step 4: Implement `ProposalValidationError`, acceptance probability and accepted branch.**
- [ ] **Step 5: Write failing correction tests and implement `(p-q)_+` sampling.**
- [ ] **Step 6: Add an exhaustive branch-mass test.** For each proposal token, multiply proposal, acceptance/rejection and residual masses; aggregate and assert exact equality with `p`.
- [ ] **Step 7: Verify `p==q` never samples a residual or consumes an acceptance draw.**
- [ ] **Step 8: Run focused tests/Ruff and commit `feat(speculative): add exact rejection kernel`.**

### Task 3: Finite table models and sampled block rounds

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
class SampledRoundRequest:
    prefix: tuple[int, ...]
    draft_length: int
    remaining_budget: int
    eos_token_id: int

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


def sample_speculative_round(
    target: FiniteTableModel,
    draft: FiniteTableModel,
    request: SampledRoundRequest,
    tape: RandomTape,
) -> SampledRoundResult: ...
```

- [ ] **Step 1: Write failing table tests.** Duplicate/malformed prefixes and missing lookup must fail with `ModelTableError`.
- [ ] **Step 2: Implement immutable canonical `FiniteTableModel`.**
- [ ] **Step 3: Write request-validation and zero-budget tests.** Prove no table lookup or tape draw at budget zero.
- [ ] **Step 4: Implement bounded autoregressive proposal generation.** Record exact `q_i`; stop after proposal EOS.
- [ ] **Step 5: Write left-to-right verification tests.** Cover all accepted, first rejection, unused suffix and q-record mismatch protection.
- [ ] **Step 6: Implement verification and exactly one correction at first rejection.**
- [ ] **Step 7: Write bonus, EOS and budget tests.**
- [ ] **Step 8: Implement bonus and explicit termination precedence:** EOS, then rejection, then budget, then all-accepted non-EOS bonus.
- [ ] **Step 9: Validate every `SampledRoundResult` invariant in `__post_init__`.**
- [ ] **Step 10: Run focused tests/Ruff and commit `feat(speculative): add sampled block rounds`.**

### Task 4: Ordinary target-law enumeration

**Files:**
- Create: `src/forgellm_governance/speculative_exhaustive.py`
- Create: `tests/test_target_law.py`

**Interfaces:**

```python
@dataclass(frozen=True, slots=True)
class ExactSequenceLaw:
    probabilities: tuple[tuple[tuple[int, ...], Fraction], ...]

    @classmethod
    def from_pairs(
        cls,
        pairs: Iterable[tuple[tuple[int, ...], Fraction]],
    ) -> ExactSequenceLaw: ...

    def probability(self, sequence: tuple[int, ...]) -> Fraction: ...


def enumerate_target_law(
    target: FiniteTableModel,
    prefix: tuple[int, ...],
    budget: int,
    eos_token_id: int,
) -> ExactSequenceLaw: ...
```

- [ ] **Step 1: Write failing law-construction tests.** Aggregate duplicate sequence mass, reject negative mass and require exact total one.
- [ ] **Step 2: Implement `LawNormalizationError` and canonical ordering.**
- [ ] **Step 3: Write failing target-recursion tests.** Cover budget zero, deterministic/branching tables, EOS and missing prefix.
- [ ] **Step 4: Implement exact recursive target enumeration.** Newly emitted sequence length never exceeds budget.
- [ ] **Step 5: Run focused tests/Ruff and commit `feat(speculative): enumerate exact target law`.**

### Task 5: Analytical speculative-law enumeration

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


def enumerate_speculative_law(
    target: FiniteTableModel,
    draft: FiniteTableModel,
    prefix: tuple[int, ...],
    budget: int,
    draft_length: int,
    eos_token_id: int,
) -> ExactSequenceLaw: ...
```

- [ ] **Step 1: Write a failing one-position target/speculative law equality test.**
- [ ] **Step 2: Implement exact proposal-path and consecutive-acceptance mass.**
- [ ] **Step 3: Add failing first-rejection residual tests and implement correction branches.**
- [ ] **Step 4: Add failing fully-accepted bonus/EOS/budget tests and implement bonus branches.**
- [ ] **Step 5: Compose rounds recursively until EOS/budget.**
- [ ] **Step 6: Define adversarial finite table families.** Include p==q, partial/disjoint overlap, target-zero proposal, deterministic and prefix-dependent EOS cases.
- [ ] **Step 7: Assert exact target/speculative law equality for budgets 0–4 and draft lengths 1–3.**
- [ ] **Step 8: Perturb valid draft tables sharply and prove unchanged final target law.**
- [ ] **Step 9: Run focused tests/Ruff and commit `feat(speculative): prove bounded speculative output law`.**

### Task 6: Separate deterministic greedy oracle

**Files:**
- Create: `src/forgellm_governance/speculative_greedy.py`
- Create: `tests/test_speculative_greedy.py`

**Interfaces:**

```python
def greedy_target_decode(
    target: FiniteTableModel,
    prefix: tuple[int, ...],
    budget: int,
    eos_token_id: int,
) -> tuple[int, ...]: ...


def greedy_speculative_decode(
    target: FiniteTableModel,
    draft: FiniteTableModel,
    prefix: tuple[int, ...],
    budget: int,
    draft_length: int,
    eos_token_id: int,
) -> tuple[int, ...]: ...
```

- [ ] **Step 1: Write argmax tie tests requiring smallest-token selection.**
- [ ] **Step 2: Write matching-prefix, first-mismatch, bonus, EOS and budget tests.**
- [ ] **Step 3: Implement target and speculative greedy paths; accept no random tape.**
- [ ] **Step 4: Exhaustively compare bounded greedy outputs for every synthetic table family/draft length.**
- [ ] **Step 5: Run focused tests/Ruff and commit `feat(speculative): add deterministic greedy oracle`.**

### Task 7: Transactional prefix-state witnesses

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
    def begin(
        cls,
        state: DecoderState,
        proposed_tokens: tuple[int, ...],
    ) -> RoundTransaction: ...

    def commit(
        self,
        result: SampledRoundResult,
        eos_token_id: int,
    ) -> tuple[DecoderState, RoundTransaction]: ...

    def cancel(self) -> tuple[DecoderState, RoundTransaction]: ...


def synchronize_pending(state: DecoderState) -> DecoderState: ...
```

- [ ] **Step 1: Write failing state-invariant tests.** Target/draft materialized equality, auxiliary/output equality and pending-prefix relation.
- [ ] **Step 2: Implement `StateInvariantError` and frozen validation.**
- [ ] **Step 3: Write begin, pending/finished precondition and cancellation tests.**
- [ ] **Step 4: Implement `RoundTransaction.begin` and exact rollback without original mutation.**
- [ ] **Step 5: Add accepted-proposal materialization tests.**
- [ ] **Step 6: Add rejection tests proving suffix discard and pending residual correction.**
- [ ] **Step 7: Add bonus, accepted-EOS and pending-EOS cases.**
- [ ] **Step 8: Implement/test `synchronize_pending`.**
- [ ] **Step 9: Reject result/proposal mismatch, invalid acceptance count and double commit/cancel.**
- [ ] **Step 10: Run focused tests/Ruff and commit `feat(speculative): define transactional prefix state`.**

### Task 8: Deterministic traces and adversarial integration

**Files:**
- Create: `src/forgellm_governance/speculative_trace.py`
- Create: `tests/test_speculative_trace.py`
- Create: `tests/test_speculative_adversarial.py`
- Modify: `src/forgellm_governance/__init__.py`

**Interfaces:**

```python
def canonical_trace_document(
    result: SampledRoundResult,
    state: DecoderState | None = None,
) -> dict[str, object]: ...


def canonical_trace_bytes(
    result: SampledRoundResult,
    state: DecoderState | None = None,
) -> bytes: ...
```

- [ ] **Step 1: Write failing rational serialization tests using numerator/denominator objects.**
- [ ] **Step 2: Implement canonical timestamp/host/path-free trace serialization.**
- [ ] **Step 3: Add invalid token/weight/tape/proposal/residual/model-prefix/state adversarial tests.**
- [ ] **Step 4: Add EOS-at-each-phase, zero-budget and cancellation adversarial tests.**
- [ ] **Step 5: Verify semantic table reordering preserves exact laws and canonical traces.**
- [ ] **Step 6: Export only stable oracle interfaces in `__init__.py`.**
- [ ] **Step 7: Run focused tests/Ruff and commit `test(speculative): add adversarial exactness coverage`.**

### Task 9: Repository gates and user documentation

**Files:**
- Modify: `Makefile`
- Create: `docs/speculative/EXACT_REFERENCE.md`
- Modify: `tasks/open/P0-T08-exact-speculative-decoding.yaml`

- [ ] **Step 1: Add `.PHONY` target `verify-speculative`.** It runs all nine CA-03 test files explicitly.
- [ ] **Step 2: Add `verify-speculative` to `ci` without removing existing simulator/hardware governance gates.**
- [ ] **Step 3: Document notation, sampling law, greedy separation, transaction model and evidence limits.**
- [ ] **Step 4: Record exact base/head/plan revisions and focused command results in the task packet; keep status truthful.**
- [ ] **Step 5: Run focused tests, `make ci`, `git diff --check` and clean-worktree verification.**
- [ ] **Step 6: Commit `ci(speculative): enforce exact reference gates`.**

### Task 10: Separate reviews, hosted verification and closeout

**Files:**
- Create: `docs/reviews/P0-T08-EXACT-SPECULATIVE-SEMANTICS-REVIEW.md`
- Modify after evidence: task/state/handoff/roadmap/mobile files allowed by the packet.

- [ ] **Step 1: Request a fresh specification-compliance review against the canonical spec and packet.**
- [ ] **Step 2: Resolve every BLOCKER/MAJOR finding with a failing regression test first.**
- [ ] **Step 3: Request a separate code-quality review focused on rational arithmetic, branch mass, state invariants and deterministic errors.**
- [ ] **Step 4: Resolve findings and rerun the focused suite plus `make ci` on the exact final head.**
- [ ] **Step 5: Open the implementation PR and require hosted `Validate and test` and CodeQL success; characterize Dependency Review honestly.**
- [ ] **Step 6: Merge only after both reviews and exact-head gates.**
- [ ] **Step 7: Verify post-merge Phase 0 and CodeQL on `main`.**
- [ ] **Step 8: Close P0-T08 in a separate state PR after post-merge evidence exists.**

## Completion report

The final report records owner authorization, task packet, base/reviewed/merge commits, exact-law test ranges, stochastic and greedy API boundaries, transactional cases, focused/full/hosted gate IDs, review findings/resolutions, evidence limits and the next recommended work package.
