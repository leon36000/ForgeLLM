# ForgeLLM — recherche et preuves

**Instantané :** 2026-08-12. Toute donnée d’activité, version ou adoption doit être rafraîchie avant une décision.

## Hiérarchie des sources

1. article évalué par les pairs et artefacts;
2. prépublication officielle et code associé;
3. dépôt, documentation et spécification officiels;
4. benchmark publié avec méthode et données;
5. billet technique d’auteur;
6. source secondaire utilisée uniquement pour découvrir une source primaire.

Un résultat publié par ses auteurs reste `externe_non_reproduit` tant qu’il n’a pas été reproduit dans le laboratoire ForgeLLM.

## Dix grands référentiels de base à analyser

Cette sélection combine échelle d’écosystème, maturité, pertinence et couverture des langages; elle n’est pas un classement absolu.

| Référentiel | Rôle ForgeLLM | Langages/écosystème | Traitement |
|---|---|---|---|
| PyTorch | oracle tensoriel, sémantique modèle, baseline | Python, C++, CUDA | référence et différentiel |
| Transformers | modèles, tokenizers, configurations, import | Python, Rust/C++ auxiliaires | compatibilité |
| vLLM | PagedAttention, scheduling, serving | Python, CUDA, C++, Rust | baseline serveur |
| llama.cpp / GGML | CPU, quantification, portabilité | C, C++, CUDA/HIP/Metal/Vulkan | baseline locale/CPU |
| SGLang | RadixAttention, structured generation, serving | Python, CUDA/C++ | baseline scheduler/cache |
| DeepSpeed | distribué, kernels et inference | Python, C++, CUDA | référence distribué |
| TensorRT-LLM | chemin NVIDIA spécialisé | Python, C++, CUDA | plafond NVIDIA |
| MLC-LLM | compilation et déploiement multi-cible | Python, C++, TVM | référence portabilité |
| CUTLASS/CuTe | primitives et kernels NVIDIA | C++, Python DSL | backend NVIDIA |
| DeepEP | communication MoE | C++, CUDA | référence expert parallelism |

## Référentiels spécialistes obligatoires

- **Rust :** `mistral.rs`, Candle, Burn, CubeCL.
- **Kernels/DSL :** Triton, FlashInfer, TileLang, Composable Kernel/ROCm libraries.
- **Runtime/distribué :** NVIDIA Dynamo, NIXL, NCCL, RCCL, UCX.
- **Hétérogène :** KTransformers, LMDeploy, FlexGen et travaux de hiérarchie mémoire.
- **Serveur historique :** Text Generation Inference comme étude d’architecture Rust, pas comme base présumée.

## Corpus scientifique prioritaire

### Mémoire, scheduling et serving

- PagedAttention / vLLM — arXiv:2309.06180.
- Orca, iteration-level scheduling — OSDI 2022.
- SGLang / RadixAttention — arXiv:2312.07104.
- SARATHI, chunked prefills — arXiv:2308.16369.
- DistServe, prefill/decode disaggregation — arXiv:2401.09670.
- Splitwise — arXiv:2311.18677.
- Mooncake, KVCache-centric disaggregation — arXiv:2407.00079 / FAST 2025.
- vAttention — arXiv:2405.04437.
- NanoFlow — OSDI 2025.
- Jenga — arXiv:2503.18292.
- eLLM — arXiv:2506.15155.
- SolidAttention — FAST 2026.
- FlexLLM et Libra — NSDI 2026.
- PagedWeight — arXiv:2607.16184, expérimental récent.

### Attention et kernels

- FlashAttention — arXiv:2205.14135.
- FlashAttention-2 — arXiv:2307.08691.
- FlashAttention-3 — arXiv:2407.08608.
- FlashInfer — arXiv:2501.01005.

### Quantification

- GPTQ — arXiv:2210.17323.
- SmoothQuant — arXiv:2211.10438.
- AWQ — arXiv:2306.00978.
- QServe — arXiv:2405.04532.
- SpinQuant — arXiv:2405.16406.
- Marlin — arXiv:2408.11743.

### Décodage spéculatif

- Speculative Decoding — arXiv:2211.17192.
- Speculative Sampling — arXiv:2302.01318.
- Medusa — arXiv:2401.10774.
- EAGLE — arXiv:2401.15077.
- EAGLE-2 — arXiv:2406.16858.

## Questions de recherche à traiter expérimentalement

1. Rust réduit-il réellement les défauts du plan de contrôle sans coûter de débit ou de latence?
2. Quelle frontière FFI minimise les appels et conserve la sûreté?
3. Quelle taille de page KV gagne selon modèle, contexte et matériel?
4. Quand séparer prefill/decode malgré le coût de transfert KV?
5. Quel portefeuille de kernels gagne selon M/N/K, batch, dtype et architecture?
6. Quel DSL portable approche suffisamment les kernels natifs?
7. Quand l’offload CPU/NVMe ou la compression KV améliore-t-il capacité et goodput?
8. Quelle stratégie de quantification par couche conserve la qualité cible?
9. Quel spéculateur maximise le gain net après coût de vérification?
10. Quelle stratégie hétérogène NVIDIA/AMD/CPU évite les synchronisations destructrices?

## Taxonomie des statuts de preuve

- `hypothèse` : proposition à tester.
- `décision` : choix d’architecture justifié, révisable.
- `externe_non_reproduit` : supporté par une source primaire externe.
- `reproduction_partielle` : une partie de la méthode ou du domaine a été reproduite.
- `reproduit` : protocole et domaine déclarés reproduits avec artefacts.
- `réfuté` : expérience correcte incompatible avec la formulation testée.
- `inconclusif` : données insuffisantes ou variance excessive.

Aucune généralisation au-delà du matériel, des modèles et charges mesurés.
