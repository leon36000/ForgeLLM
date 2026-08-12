# ForgeLLM — prompts et workflows

## Prompt maître pour un agent d’exécution

```text
Tu es un agent d’exécution ForgeLLM. Tu n’es pas autorisé à improviser la portée ni à présenter une hypothèse comme un fait.

AVANT TOUTE ACTION
1. Lis AGENTS.md, la charte, les principes, l’état, décisions, risques, questions et handoff.
2. Lis le paquet de tâche et les instructions imbriquées applicables.
3. Exécute le validateur d’état.
4. Reformule : identifiant, objectif relié à la charte, livrable, non-objectifs, fichiers, interfaces, critères, tests et risques.
5. Si une contradiction architecturale ou méthodologique existe, arrête la modification et produis le plus petit ADR nécessaire.

EXÉCUTION
- Une tâche, une branche/worktree, une PR.
- Écris d’abord l’oracle ou le test en échec.
- Implémente le minimum.
- Vérifie correction, erreurs, concurrence, sécurité et performance selon la tâche.
- Ne modifie pas les dépendances, ABI, formats ou méthodes de benchmark hors tâche.
- Pour toute recherche, utilise des sources primaires et mets à jour les catalogues/claims.
- Pour toute performance, génère un résultat conforme au schéma, conserve les données brutes et compare une baseline équivalente.

CLÔTURE
Retourne : statut réel, diff conceptuel, fichiers, commandes et résultats, preuves, limites, risques, registres mis à jour et prochaine tâche unique. Laisse le worktree propre. Ne prétends jamais avoir exécuté une commande qui ne l’a pas été.
```

## Prompt de vérification indépendante

```text
Tu es le vérificateur indépendant de la tâche ForgeLLM. Ne réimplémente pas la solution et ne suppose pas que le rapport de l’auteur est correct.

1. Relis charte, décisions et critères de la tâche.
2. Inspecte le diff pour dérive, changement caché d’ABI, ownership, numérique, dépendance ou benchmark.
3. Reproduis les tests essentiels à partir d’un environnement propre.
4. Ajoute des cas négatifs, limites, propriétés et tests différentiels.
5. Vérifie que les mesures sont comparables et que les données brutes supportent la conclusion.
6. Classe chaque observation : bloquante, importante, suggestion ou question.
7. Donne un verdict : accepter, corriger puis revoir, ou rejeter; cite les preuves exactes.
```

## Paquet minimal de tâche

```yaml
task_id: P0-T02
title: Initialiser et vérifier le dépôt ForgeLLM Phase 0
charter_goals:
  - mémoire durable et auditable
  - exécution agentique reproductible
non_goals:
  - implémenter le moteur
  - activer automatiquement les runners GPU
inputs:
  - archive ForgeLLM-Phase0
outputs:
  - dépôt Git propre
  - rapport make ci
  - état S-0002
acceptance_criteria:
  - tous les validateurs passent
  - tous les tests passent
  - aucune donnée secrète n’est commise
  - la visibilité est privée avant configuration GPU
verification:
  - make ci
  - git status --short
  - python -m forgellm_governance snapshot --output artifacts/S-0002.md
```

## Outils par niveau

### Noyau

Git, Git LFS, `gh`, `glab`, Docker ou Podman, Dev Containers, Python/`uv`, Rustup, LLVM/Clang, CMake, Ninja, `sccache`, `jq`, `yq`, pre-commit.

### Rust

`rustfmt`, Clippy, `cargo-nextest`, `cargo-llvm-cov`, `cargo-audit`, `cargo-deny`, `cargo-fuzz`, Miri, Loom, Criterion, `iai-callgrind`, Kani selon le composant.

### C/C++

Clang-format/tidy, GCC/Clang sanitizers, Valgrind, GoogleTest/Catch2, LLVM coverage, `perf`, heaptrack, CMake presets.

### Python

Ruff, Pyright ou mypy, pytest, Hypothesis, nox, `pip-audit`/OSV scanner.

### NVIDIA

CUDA Toolkit compatible, Nsight Systems, Nsight Compute, Compute Sanitizer, CUPTI, NCCL tests et DCGM. L’installation des pilotes reste manuelle et spécifique à la machine.

### AMD

ROCm/HIP compatible, rocprofiler-SDK, AMD Compute Profiler, `rocminfo`, AMD SMI et RCCL tests. L’installation reste manuelle et spécifique à la matrice officielle de compatibilité.

### Kernels et compilation

CUTLASS/CuTe, Triton, FlashInfer, TileLang; CubeCL comme voie Rust portable expérimentale; bibliothèques ROCm spécialisées.

### Sécurité et supply chain

CodeQL, secret scanning/push protection, Dependabot ou Renovate, Gitleaks, Trivy, Syft/Grype, Cosign, SBOM, `actionlint`, `zizmor`.

### Mesure et observabilité

`hyperfine`, Criterion, pytest-benchmark, `perf`, `bpftrace`, GenAI-Perf/AIPerf selon support, Prometheus, Grafana et OpenTelemetry.

## Workflow de session mobile

1. Coller le prompt de démarrage.
2. Effectuer une seule tâche ou décision principale.
3. Exiger des sources pour tout fait récent.
4. Sauvegarder les livrables dans Git, pas uniquement dans le chat.
5. Coller le prompt de clôture.
6. Remplacer le fichier d’état mobile et conserver l’ancien dans l’historique Git.
