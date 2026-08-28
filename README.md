# ForgeLLM — Phase 0: mémoire, preuves et exécution agentique

ForgeLLM vise un moteur d’inférence LLM hétérogène, mesurable et progressivement optimisé :

- **Rust** pour le plan de contrôle, l’ordonnanceur, la gestion sûre des ressources et le réseau.
- **ABI C stable** comme frontière entre le runtime et les backends.
- **CUDA C++ / CuTe / CUTLASS** pour NVIDIA.
- **HIP C++ / bibliothèques ROCm** pour AMD.
- **CubeCL et autres DSL portables** comme voies expérimentales ou de repli.
- **CPU SIMD** pour référence, vérification, tokenisation, sampling, offload et tâches auxiliaires.
- **Python** pour la recherche, l’import de modèles, l’autotuning et l’orchestration hors chemin critique.

Ce dépôt ne contient pas encore le moteur. Il constitue le **système d’exploitation du projet** : mémoire durable, garde-fous anti-dérive, protocole de recherche, schémas de preuves, tâches pour agents, CI et laboratoire de reproductibilité.

> **Dépôt public, projet non encore licencié.** Tout contenu Git est public. Ne soumettez aucun secret, poids restreint, dataset privé, prompt confidentiel, identifiant matériel stable ou trace non expurgée. La visibilité publique ne constitue pas une licence d'utilisation ou de redistribution. Voir `docs/architecture/ADR-0003-public-repository-and-private-assets.md`.

## Source de vérité

L’ordre d’autorité est :

1. demande explicite du propriétaire du projet ;
2. `docs/architecture/PROJECT_CHARTER.md` ;
3. ADR acceptés dans `docs/architecture/` ;
4. `docs/state/CURRENT_STATE.md` et registres associés ;
5. paquet de tâche actif ;
6. `AGENTS.md`, puis instructions locales plus spécifiques ;
7. conversation courante.

La mémoire implicite d’un assistant n’est jamais la source de vérité. Les décisions, expériences et changements d’état doivent être écrits dans Git. Un RAG externe ou une base Neon éventuelle reste un index dérivé et reconstruisible.

<!-- forgellm:current-state:begin -->
State ID: `S-0016`
Canonical source commit: `55d08c76b7fcdc3b6c256d35a4d74b275652964c`
Task statuses: P0-T03=complete; P0-T04=blocked; P0-T07=complete; P0-T08=complete; P0-T09=in_progress; P0-T10=review; P0-T11=complete; P0-T12=complete; P0-T13=complete; P0-T14=complete; P0-T15=in_progress; P0-T16=complete; P0-T17=in_progress
<!-- forgellm:current-state:end -->

## Dépôt public et actifs privés

Le code, les ADR, la recherche publique et les preuves expurgées vivent ici. Les futurs poids, datasets, prompts, inventaires sensibles et traces privées doivent utiliser un plan d’actifs privé séparé et n’être référencés que par identifiant, révision et hash.

Aucun runner auto-hébergé n’est autorisé tant que `main` n’est pas directement protégée et que les workflows de forks, secrets, environnements et isolation éphémère ne sont pas validés.

## Démarrage local

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
make ci
```

## Utilisation avec ChatGPT mobile

1. Ouvrir `chatgpt/PROJECT_INSTRUCTIONS.txt` et copier son contenu dans les instructions du projet ChatGPT.
2. Téléverser exactement les cinq fichiers de `chatgpt/mobile-core/`.
3. Au début d’une nouvelle discussion, utiliser `chatgpt/SESSION_BOOTSTRAP_PROMPT.md`.
4. À la fin, utiliser `chatgpt/SESSION_CLOSEOUT_PROMPT.md`, puis remplacer le fichier d’état mobile par sa version mise à jour.
5. Garder ce dépôt Git comme archive auditable et canonique.

## Commandes

```bash
make validate          # structure, état, catalogues et exemples
make test              # tests unitaires
make lint              # Ruff sur src/, scripts/ et tests/
make verify            # validate + test
make ci                # lint + verify; gate complet de PR
make inventory         # inventaire matériel local redacted dans artifacts/
make snapshot          # instantané de continuité dans artifacts/
```

## Limites volontaires de la Phase 0

- Aucun chiffre de performance n’est présenté comme reproduit.
- Aucun backend n’est déclaré gagnant sans benchmark ForgeLLM.
- Aucune installation de pilote GPU n’est automatisée.
- Aucun runner auto-hébergé n’exécute du code non approuvé provenant de forks.
- Aucun choix définitif de licence ou de structure juridique n’est supposé.

Lire ensuite :

- `AGENTS.md`
- `docs/architecture/PROJECT_CHARTER.md`
- `docs/governance/PUBLIC_REPOSITORY_POLICY.md`
- `docs/research/RESEARCH_PROTOCOL.md`
- `docs/benchmarks/BENCHMARK_STANDARD.md`
- `docs/roadmap/PHASES.md`
