# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-12  
**Version d’état :** S-0001  
**Phase :** P0 — gouvernance, mémoire durable et laboratoire de preuve  
**Statut global :** socle Phase 0 vérifié localement; initialisation propriétaire restante

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont la correction, la performance, la sécurité et la reproductibilité sont démontrées par des artefacts versionnés.

## Jalon actif

**P0-M1 :** rendre le projet durable entre ChatGPT mobile, Claude Code, Codex et Git; fournir instructions, registres, catalogues, schémas, validateurs, CI et plan de recherche.

## Travail accompli et vérifié

- nom ForgeLLM adopté;
- architecture hybride Rust + backends natifs retenue comme direction révisable;
- paquet mobile à cinq fichiers et instructions du projet créés;
- contrat agent, gates anti-dérive, protocole de preuve et standard de benchmark créés;
- catalogue daté de 26 dépôts, 30 articles et 55 claims créé;
- 18 revues de dépôts et 6 synthèses scientifiques transformées en tâches bornées;
- schémas, validateurs, inventaire matériel redacted, snapshots et scripts de recherche créés;
- modèles GitHub/GitLab, CI SHA-épinglée, CodeQL, audit lecture seule et workflow GPU manuel protégé créés;
- `make verify` exécuté le 2026-08-12 : catalogues, schémas, automatisation, exemples, scan de secrets et syntaxe shell valides; **11 tests réussis**.

## Limite de la preuve actuelle

Cette validation prouve la cohérence structurelle du socle P0. Aucun moteur externe n’a été benchmarké par ForgeLLM, aucun gain n’est reproduit, aucun runtime ou kernel ForgeLLM n’est implémenté.

## Décisions acceptées

### D-0001 — Mémoire durable externe

Le dépôt Git, les ADR, l’état, les preuves et les handoffs sont canoniques. La mémoire de conversation sert d’aide, jamais d’unique registre.

### D-0002 — Architecture de langages

Rust possède le plan de contrôle sûr. Les kernels restent dans les environnements natifs les plus performants. Une ABI C versionnée sépare les couches. Python reste hors du chemin par token sauf preuve contraire.

### D-0003 — Remplacement progressif

Ne pas porter intégralement un moteur existant. Encapsuler, mesurer et remplacer une brique à la fois lorsque correction et gain sont démontrés.

### D-0004 — Preuve avant revendication

Toute affirmation de performance exige baseline, environnement, données brutes, exactitude, répétitions, statistiques, hachages et portée explicite.

### D-0005 — Agents séparés

L’implémentation et la vérification sont confiées à des contextes/agents distincts pour les changements importants.

### D-0006 — Runners GPU protégés

Les runners GPU auto-hébergés ne doivent pas exécuter automatiquement du code de forks ou non approuvé. Dépôt privé, branche protégée et approbation avant activation.

### D-0007 — Profils avant optimisation

La Phase 1 définit modèles, charges, SLO et fonctions objectif avant toute affirmation de « meilleur moteur ».

## Risques principaux

| ID | Risque | Gravité | Contre-mesure |
|---|---|---:|---|
| R-001 | dérive vers un moteur trop large avant baseline | critique | phases et task packets petits |
| R-002 | benchmarks incomparables ou optimistes | critique | schéma obligatoire, données brutes, vérificateur |
| R-003 | fragmentation Rust/C++/CUDA/HIP/Python | élevée | ABI étroite, ownership explicite, tests contractuels |
| R-004 | dépendance à un fournisseur ou DSL immature | élevée | portefeuille de backends, versions épinglées |
| R-005 | runners GPU compromis | critique | privé, protégé, restreint, manuel/éphémère, aucun fork |
| R-006 | recherche volumineuse mais non actionnable | élevée | chaque source liée à une claim ou expérience |
| R-007 | mémoire de chat contradictoire | élevée | bootstrap, état versionné, remplacement du fichier mobile |
| R-008 | objectifs « le plus puissant » non mesurables | élevée | profils de charge et objectifs séparés en P1 |

## Questions ouvertes prioritaires

1. compte/organisation GitHub ou GitLab et responsables réels;
2. licence et politique de contributions;
3. inventaire exact du matériel, topologie, OS, pilotes et réseau;
4. modèles et charges de référence de P1;
5. priorités TTFT, TPOT, goodput, débit, mémoire, énergie, coût et qualité;
6. premier profil : local interactif, serveur, long contexte ou modèle surdimensionné;
7. compatibilité initiale : safetensors/Transformers, GGUF ou les deux;
8. première carte NVIDIA et première carte AMD de laboratoire.

## Prochaine tâche autorisée

**P0-T02 — Initialiser le dépôt privé et installer le contexte mobile.**

Critères :

- hachages de l’archive et du manifeste vérifiés;
- `make ci` réussi dans un environnement isolé;
- dépôt Git initialisé et worktree propre;
- visibilité privée et `main` protégée avant runner GPU;
- instructions ChatGPT collées et cinq fichiers téléversés;
- propriétaire, plateforme, commit et première machine enregistrés;
- état S-0002 produit.

## Handoff

Commencer toute nouvelle session par le prompt de bootstrap. Ne pas commencer l’implémentation du moteur avant P0-T02, l’inventaire matériel et les profils P1. À la clôture, remplacer entièrement ce fichier par un nouvel état fondé uniquement sur des faits vérifiés.
