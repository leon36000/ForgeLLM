# ForgeLLM — contexte canonique compact

**Version :** 0.1.0  
**Instantané :** 2026-08-12  
**Statut :** Phase 0 — gouvernance, mémoire durable et laboratoire de preuve

## Mission

ForgeLLM doit devenir un moteur d’inférence de grands modèles de langage :

- puissant sur GPU NVIDIA, GPU AMD et CPU;
- sûr et maintenable;
- portable sans se limiter au plus petit dénominateur commun;
- capable d’inférence locale, serveur et distribuée;
- optimisé sur la base de mesures reproductibles;
- conçu pour être développé par plusieurs agents IA sous contrôle humain.

## Invariants

1. Le dépôt Git est la source de vérité durable; la mémoire du chat ne l’est pas.
2. La correction précède la performance.
3. Une affirmation importante doit être classée : fait, inférence, hypothèse, décision ou mesure.
4. Une performance de tiers est externe et non reproduite jusqu’à expérience ForgeLLM.
5. Un seul backend ne sera pas imposé à tous les matériels sans preuve.
6. Chaque changement doit être relié à un objectif, une tâche, des critères d’acceptation et des tests.
7. Une optimisation qui change le résultat hors budget numérique est une régression.
8. Les zones `unsafe`, FFI et pilotes sont petites, isolées et documentées.
9. Les résultats bruts, versions, hachages et limites sont conservés.
10. Toute dérive de portée est arrêtée ou enregistrée comme question distincte.

## Architecture directrice acceptée

- **Rust :** plan de contrôle, runtime, scheduler, KV manager, services, observabilité, réseau et abstractions sûres.
- **C ABI :** frontière stable et versionnée entre runtime et plugins.
- **NVIDIA :** CUDA C++, CuTe/CUTLASS, bibliothèques spécialisées et kernels mesurés.
- **AMD :** HIP C++, bibliothèques ROCm et kernels mesurés.
- **Portable/expérimental :** CubeCL, Triton, TileLang ou autres DSL selon les résultats.
- **CPU :** backend de référence, SIMD, tokenisation, sampling, offload, compression et tâches auxiliaires.
- **Python :** recherche, import, conversion, autotuning, benchmark et génération d’artefacts hors boucle critique.

Aucune réécriture ligne par ligne de `llama.cpp` n’est prévue. Les moteurs existants servent de références, baselines ou backends temporaires; un composant n’est remplacé que lorsque la nouvelle version est correcte et meilleure selon un protocole reproductible.

## Couches cibles

1. formats de modèles et import;
2. IR et planification mémoire;
3. runtime et cycle de vie;
4. backends CPU/GPU;
5. portefeuille de kernels et autotuning;
6. KV cache paginé et hiérarchique;
7. scheduler prefill/decode, batching continu et spéculation;
8. parallélisme et transports multi-GPU/multi-nœud;
9. API et observabilité;
10. sécurité, reproductibilité et livraison.

## Phases

- **P0 — maintenant :** mémoire durable, règles, recherche, outils, schémas, CI.
- **P1 :** laboratoire de référence; baselines sur moteurs existants et inventaire matériel.
- **P2 :** noyau CPU de référence, sémantique modèle, IR minimale et tests différentiels.
- **P3 :** ABI plugins et backend NVIDIA initial.
- **P4 :** backend AMD initial et portabilité expérimentale.
- **P5 :** KV cache, continuous batching, chunked prefill, prefix caching et scheduling.
- **P6 :** multi-GPU, MoE, désagrégation prefill/decode et hiérarchie mémoire.
- **P7 :** autotuning, quantification, spéculation, durcissement et production.

Chaque phase possède un gate d’entrée, un oracle de correction, une baseline et un gate de sortie mesurable.

## Non-objectifs actuels

- écrire immédiatement un moteur complet;
- promettre d’être le plus rapide sans charge cible définie;
- automatiser l’installation des pilotes GPU;
- choisir définitivement une licence ou une structure de gouvernance;
- accepter du code de forks sur des machines GPU privées;
- reproduire toutes les fonctions de tous les moteurs existants dès la première version.

## Source de vérité et ordre d’autorité

1. instruction explicite du propriétaire;
2. charte et ADR du dépôt;
3. état, décisions, risques et handoff versionnés;
4. paquet de tâche actif;
5. instructions agent versionnées;
6. conversation.

En cas de contradiction, arrêter la modification, montrer le conflit et proposer le plus petit ADR ou changement d’état capable de le résoudre.
