# ForgeLLM Handoff

**From state:** S-0007  
**To work:** owner decision — designate P0-T04 host or authorize a bounded QG-01 investigation  
**Generated:** 2026-08-14

## Canonical status

- repository: `leon36000/ForgeLLM`;
- protected default branch: `main`;
- P0-T07: complete;
- P0-T08 / CA-03: complete;
- P0-T04: blocked only on owner host designation;
- P0-T05/P0-T06: blocked behind inventory and workload/SLO gates;
- QG-01 / issue #26: proposed Sonar `main`-analysis investigation, not yet a task packet;
- no future model, runtime or research implementation is automatically authorized.

## P0-T08 evidence

```text
Implementation PR       #24
Base                    1cd502609c7b05ac628057f79a9135b07c08e821
Reviewed head           16d65288b34a9f2f91a4c67182aab13ddfb5e17d
Implementation merge    e6c9d1ae30f1b5e161a56bf8c9b4fa25c823fe24
Phase 0 implementation  31831781322 / 94868927648
Tests complete          332 passed
Tests focused           230 passed
CodeQL implementation   31831781266 / 94868926709
Spec review             4940413742 / ACCEPT
Code-quality review     4940415259 / ACCEPT
Remediation PR          #25
Remediation head        a7f508fe1fa4787b889445c5e5986339b508217a
Remediation merge       e81c1c0ad0b161844569df46ee62246c9de56698
Phase 0 remediation     31838436974 / 94889874946
CodeQL remediation      31838436902 / 94889874310
Sonar PR gate           94889986512 / PASSED / 0 new issues
Phase 0 final main      31838603770 / 94890388826
CodeQL final main       31838603775 / 94890388594
Evidence boundary       finite_exact_reference
```

Dependency Review was skipped by repository policy. CodeQL success does not assert zero repository-wide alerts.

## SonarQube Cloud truth boundary

PR #25 passed the SonarQube Cloud Quality Gate with 0 new issues and 0 security hotspots. Automatic analysis of `main` at the remediation merge was nevertheless reported as cancelled / failed by check `94890528740`, with no GitHub annotations. Issue #26 tracks that discrepancy. Do not reinterpret the PR result as proof that branch analysis is functioning.

## Exact oracle now available

Stable reference surfaces include:

- `ExactDistribution` and `RandomTape`;
- exact one-token acceptance/rejection;
- sampled speculative rounds;
- `FiniteTableModel`;
- exact target/speculative law enumerators;
- deterministic greedy target/speculative oracles;
- `DecoderState` and `RoundTransaction`;
- canonical trace documents and bytes;
- `make verify-speculative`.

## Semantics future implementations must preserve

1. `p` is target and `q` is the recorded proposal distribution.
2. Acceptance is `min(1, p(x)/q(x))`.
3. The first rejection samples normalized `(p-q)_+` and discards the remaining proposal suffix.
4. A target bonus is legal only after a fully accepted non-EOS block with budget remaining.
5. EOS terminates output immediately.
6. Stochastic exactness means equality of output law, not identical random-number consumption.
7. Greedy decoding has a separate deterministic oracle.
8. Accepted proposal state commits; rejected suffix state does not.
9. Residual/bonus output may be one pending token until synchronization.
10. Cancellation restores the original state witness exactly.

## Evidence limits

Do not infer real-model, floating-point, KV-tensor, hardware, performance, batching, distributed or production behavior from CA-03.

## Next owner decision

The current operational task remains P0-T04. To start it, provide one project-safe host label and execution mode. QG-01 can be authorized separately to investigate SonarQube Cloud branch analysis without mixing it with hardware or runtime work.
