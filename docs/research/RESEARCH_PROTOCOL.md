# ForgeLLM Research Protocol

## 1. Research questions, not browsing themes

Every research task begins with a falsifiable question tied to a project decision or experiment. Example:

> For decode batch sizes 1–32 on the first NVIDIA target, which attention backend minimizes TPOT while meeting the numerical budget for the selected model revision?

“Research attention libraries” is too broad to execute or close.

## 2. Search strategy

### Discovery pass

Search arXiv, DBLP/OpenReview or conference proceedings, university/laboratory pages, official vendor documentation, GitHub and GitLab. Use backward and forward citation chaining. Search aliases, paper titles, project names, authors and core mechanisms.

### Primary-source pass

Replace secondary summaries with canonical sources. Confirm:

- exact paper/repository identity;
- latest official version and date;
- authorship and affiliation;
- source and artifact availability;
- target hardware and software assumptions;
- license and maintenance status.

### Adversarial pass

Search for limitations, failed reproductions, regressions, issue reports, unsupported hardware, numerical discrepancies, memory leaks and benchmark criticism. A literature review that only gathers success claims is incomplete.

## 3. Repository analysis rubric

For every major repository, score or document:

1. purpose and supported model families;
2. control-plane language and kernel languages;
3. hardware/backend coverage;
4. memory/KV-cache design;
5. scheduler and batching model;
6. quantization and speculative decoding;
7. distributed topology and transport;
8. build/release reproducibility;
9. test depth, differential tests and benchmark harness;
10. extension/plugin boundaries;
11. unsafe/FFI surface and failure handling;
12. license, governance, release cadence and dependency risk;
13. open issues that affect ForgeLLM targets;
14. claims to reproduce;
15. reusable components versus concepts only.

Pin the inspected commit. Do not analyze only README claims; inspect implementation, tests, CI, benchmarks and representative issues.

## 4. Paper analysis rubric

For every high-priority paper, capture:

- problem and system boundary;
- contribution and mechanism;
- assumptions;
- baselines and whether they remain relevant;
- hardware, models, precision and workloads;
- metrics and statistical method;
- correctness/quality evaluation;
- ablations;
- artifacts and reproducibility;
- threats to validity;
- what ForgeLLM should adopt, reject or test;
- smallest reproduction experiment.

## 5. Reproduction protocol

1. Freeze paper/project revision.
2. Recreate the declared environment using a container or explicit manifest.
3. Validate correctness on a small deterministic case.
4. Reproduce one headline condition exactly or as closely as documented.
5. Record deviations before running.
6. Run baseline and candidate interleaved where thermal drift matters.
7. Store raw data, logs and hashes.
8. Have an independent verifier replay the result.
9. Narrow the claim to the actually reproduced domain.

## 6. Research outputs

A completed research task produces:

- updated `research/repos.yaml` or `research/papers.yaml`;
- one or more entries in `research/claims.yaml`;
- a decision memo or experiment task when action is justified;
- citations and immutable revisions;
- a concise landscape change log;
- explicit unresolved questions.

## 7. Continuous refresh

Run repository and paper refresh scripts on a schedule, but never auto-accept new claims or dependencies. Automated discovery creates review candidates. Human/agent review assigns evidence and reproduction status.

## 8. Stopping rule

Stop a literature subtask when:

- the decision-relevant mechanisms and major alternatives are represented;
- new sources are mostly duplicates;
- key claims have primary sources;
- limitations and counter-evidence are captured;
- the next uncertainty is better resolved by experiment than more reading.
