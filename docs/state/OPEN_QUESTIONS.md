# ForgeLLM Open Questions

## Owner-controlled choices

1. Which GitHub or GitLab account/organization owns ForgeLLM?
2. Will the initial repository remain private, and when may it become public?
3. Which license and contributor agreement policy will apply?
4. Who may approve architecture, security and performance changes?

## Laboratory definition

5. What is the exact inventory of CPU, RAM, GPU, VRAM, motherboard, PCIe topology, network and storage?
6. Which OS, kernel and driver versions are acceptable on each machine?
7. Which machines may be reimaged and which are production-sensitive?
8. Which GPU is the first protected CI target for NVIDIA and AMD?

## Product and benchmark profiles

9. Which profile is first: interactive local, throughput server, long context, oversized model or heterogeneous cluster?
10. Which models and immutable revisions form the first correctness set?
11. Which prompt/output distributions and concurrency levels represent real use?
12. What TTFT, TPOT, goodput, memory, energy and quality constraints matter most?
13. Are GGUF, safetensors/Transformers or both required in the first executable milestone?

## Architecture experiments

14. What is the maximum acceptable FFI overhead per execution plan?
15. Which KV page sizes and layouts should P1/P2 sweep?
16. Which operations require native kernels first?
17. Which portable DSLs remain experimental versus production candidates?
18. Under what topology is prefill/decode disaggregation allowed?

Each question becomes a decision or experiment only when its owner, acceptance criterion and deadline are assigned in an issue.
