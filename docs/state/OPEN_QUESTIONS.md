# ForgeLLM Open Questions

## Resolved owner decisions

- GitHub owner/repository: `leon36000/ForgeLLM`.
- Repository visibility: public under ADR-0003 until superseded.
- Review model while solo: fresh agent/context review + exact-head CI + owner disposition; no fake second account.

## Repository hardening

1. Which owner-authorized path will configure and directly verify the `main` protection/ruleset?
2. Can the connected GitHub installation expose Actions-permission and CodeQL-alert endpoints, or must the owner use authenticated `gh`/UI evidence?
3. After its first successful public run, should Dependency Review become a required check?
4. When should a separate private asset plane be created, and which storage/repository technology should own it?

## Licensing and governance

5. Which project license and contributor agreement policy will apply?
6. Who may approve architecture, security and performance changes after additional maintainers join?

## Laboratory definition

7. What is the exact inventory of CPU, RAM, GPU, VRAM, motherboard, PCIe topology, network and storage?
8. Which OS, kernel and driver versions are acceptable on each machine?
9. Which machines may be reimaged and which are production-sensitive?
10. Which GPU is the first protected CI target for NVIDIA and AMD?

## Product and benchmark profiles

11. Which profile is first: interactive local, throughput server, long context, oversized model or heterogeneous cluster?
12. Which models and immutable revisions form the first correctness set?
13. Which prompt/output distributions and concurrency levels represent real use?
14. What TTFT, TPOT, goodput, memory, energy and quality constraints matter most?
15. Are GGUF, safetensors/Transformers or both required in the first executable milestone?

## Architecture experiments

16. What is the maximum acceptable FFI overhead per execution plan?
17. Which KV page sizes and layouts should P1/P2 sweep?
18. Which operations require native kernels first?
19. Which portable DSLs remain experimental versus production candidates?
20. Under what topology is prefill/decode disaggregation allowed?

Each question becomes a decision or experiment only when its owner, acceptance criterion and deadline are assigned in an issue.
