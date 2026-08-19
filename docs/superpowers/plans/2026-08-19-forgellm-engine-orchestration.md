# ForgeLLM engine execution orchestration

**Date:** 2026-08-19  
**Canonical starting point:** `main@86bc745f99b0907049cc16eba17c6080462d12c2`  
**Primary objective:** move ForgeLLM from project-operating-system code to a verified heterogeneous inference engine without bypassing correctness/evidence gates.

## Direction

Sonar/QG-01 is no longer the program focus. It may receive only bounded maintenance needed to preserve repository quality. Product work follows the charter and roadmap: P1 laboratory evidence, P2 CPU reference core, P3 C ABI/NVIDIA, P4 AMD/portable path, P5 KV/scheduler, P6 distributed/heterogeneous execution, P7 optimization/hardening.

The current repository contains no Rust engine workspace. P0-T10 is therefore the first bounded engine-code risk-reduction increment.

## Long-term lanes

### Lane A — Core reference engine — ACTIVE

- **Current task:** P0-T10 / issue #42.
- **Goal:** real Rust CPU reference semantics: checked tensor representation, matmul, softmax, RMSNorm and deterministic argmax.
- **Why now:** independent of accelerator hardware and directly aligned with the charter's “reference before optimization” rule.
- **Promotion rule:** useful code may later be promoted into P2 only after P1/P2 gates; this task does not claim promotion.

### Lane B — Reproducibility laboratory — READY/BLOCKED ON CONTROLLER ACCESS

- **Current task:** P0-T04 / issue #12.
- **Goal:** one sanitized observation-only inventory, then P0-T05 workload/SLO profiles and P0-T06 baseline plan.
- **Execution mode:** use MCP_TO_PC only after the controller is actually accessible and a project-safe host label/execution mode can be recorded.
- **No workaround:** do not substitute an unrelated container or infer hardware from product names.

### Lane C — ABI/runtime architecture — READ-ONLY UNTIL CORE SEMANTICS LAND

- **Goal:** prepare the P3 versioned C ABI, ownership/lifecycle state machine and safe Rust wrapper design.
- **Permitted now:** adversarial design review, ABI invariant inventory, failure-mode analysis, primary-source research.
- **Not permitted yet:** production ABI/backend implementation before a separately accepted task packet and the preceding correctness gates.

### Lane D — Baseline/workload harness — PREPARATION ONLY

- **Goal:** P1 adapters for vLLM, llama.cpp and one of SGLang/TensorRT-LLM with immutable model/workload definitions.
- **Permitted now:** interface design and benchmark-schema mapping.
- **Blocked:** actual comparative benchmark claims until P0-T04/P0-T05 freeze hardware and workload profiles.

### Lane E — Accelerator/scheduler portfolio — QUEUED

- **P3:** NVIDIA backend after CPU reference and ABI gate.
- **P4:** AMD plus one portable DSL experiment.
- **P5:** paged KV, continuous batching, chunked prefill, prefix reuse, cancellation, admission control.
- **P6:** heterogeneous/distributed placement and transport.
- **P7:** measured kernel portfolio, quantization, speculative decoding promotion and production hardening.

## Worker topology

Maximum concurrent writers: one per isolated worktree/branch and never two writers on the same files.

When MCP_TO_PC worker routing is available and positively verified:

- up to **3 OpenHands seats** may be assigned to independent bounded tasks only when the runtime model is positively observed as `DeepSeek-V4-Flash-0731`; otherwise those seats do not receive write authority;
- up to **2 Codex seats** may be assigned to independent implementation/review tasks only after the actual routed model alias is observed; do not invent a `Luna Max` alias;
- critical architecture, unsafe/FFI, concurrency and performance work always receives an independent reviewer distinct from the writer.

If routing cannot be verified, execution continues through the smallest safe local/GitHub path rather than pretending the requested model ran.

## Loop Engineering contract

Every active lane iteration declares:

- **GOAL:** one falsifiable deliverable;
- **SCOPE:** exact allowed files and forbidden actions;
- **VERIFY:** executable external gate that can fail;
- **BUDGET:** normally at most 3 correction cycles before diagnosis;
- **STOP:** green gate, repeated same failure, authority conflict or exhausted budget;
- **RECEIPT:** base/head SHA, writer/reviewer, commands, test counts, evidence, limitations and next step.

A writer never declares its own risky work complete without an independent checker.

## Near-term sequence

1. Merge P0-T10 authorization only after packet validation and independent scope review.
2. TDD RED: add Rust reference-core tests first.
3. GREEN: implement the smallest complete reference semantics with no stubs/unsafe/dependencies.
4. Run hosted Rust fmt/clippy/test plus existing `make ci`; independently review exact head; merge through PR.
5. In parallel, restore MCP_TO_PC access and execute P0-T04 observation-only inventory; then promote P0-T05/P0-T06.
6. After P0-T10 evidence, draft a separate ABI/lifecycle ADR/task packet; do not mix it into the reference-core PR.

## Stop / escalation rules

Stop a lane rather than accumulating debt when:

- a required fact is being invented instead of measured;
- a task needs an ADR or packet it does not have;
- a test is green only because the oracle is weak;
- a writer crosses files owned by another active worktree;
- a third-party dependency is added without review;
- a performance result lacks comparable baseline, raw samples or correctness;
- a model/worker route cannot be positively verified;
- the same failure repeats without new information.

ForgeLLM progress is measured by verified executable capability, not commit count or number of governance documents.