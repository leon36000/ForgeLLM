# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-13  
**Version d’état :** S-0002  
**Phase :** P0 — gouvernance, mémoire durable et laboratoire de preuve  
**Statut global :** P0-T02 en revue finale; dépôt GitHub privé et PR #1 actifs, CI hébergée verte sur la tête d’implémentation, politique de revue solo formalisée; rapport final, CI finale, décision de fusion et protection de `main` restantes

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont la correction, la performance, la sécurité et la reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique

- dépôt : `leon36000/ForgeLLM`;
- visibilité : privée, vérifiée le 2026-08-13;
- branche par défaut : `main`;
- commit d’amorçage : `fb4cd533ef11c08fd31c74716e2dc2bb4ca4b4a9`;
- branche active : `agent/p0-t02-initialize-repository`;
- PR : brouillon #1;
- tête d’implémentation revue : `1f2fdee1fa098e6540eb0b3366203302de56402d`.

## Preuve CI observée

GitHub Actions run `31676341783`, job `94371625460` :

- Ruff 0.16.2 réussi;
- validation projet, recherche, benchmark et paquet de tâche réussie;
- vérification de cinq fichiers mobiles et émission SHA-256 réussie;
- **13 tests réussis**;
- bootstrap Ubuntu en dry-run réussi.

CodeQL et Dependency Review ont été ignorés par leurs garde-fous de dépôt privé. Ils ne sont pas déclarés exécutés.

## Travail ajouté pendant P0-T02

- politique de revue pour projet solo;
- interdiction d’utiliser un second compte contrôlé par la même personne comme faux réviseur;
- revue par agent/contexte distinct + CI exacte + décision finale du propriétaire;
- séparation explicite entre identité Git vivante et manifeste SHA-256 d’un paquet figé;
- script déterministe de hachage des cinq fichiers mobiles;
- tests négatifs contre un sixième fichier mobile.

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

L’implémentation et la vérification sont confiées à des contextes/agents distincts pour les changements importants. En mode solo, le propriétaire prend la décision finale; un second compte lui appartenant n’est pas une revue indépendante.

### D-0006 — Runners GPU protégés

Aucun runner GPU auto-hébergé avant preuve directe de la protection de `main`, du dépôt privé et des garde-fous contre le code non approuvé.

### D-0007 — Profils avant optimisation

La Phase 1 définit modèles, charges, SLO et fonctions objectif avant toute affirmation de « meilleur moteur ».

## Risques principaux

| ID | Risque | Gravité | Contre-mesure |
|---|---|---:|---|
| R-001 | dérive vers un moteur trop large avant baseline | critique | phases et task packets petits |
| R-002 | benchmarks incomparables ou optimistes | critique | schéma obligatoire, données brutes, vérificateur |
| R-003 | fragmentation Rust/C++/CUDA/HIP/Python | élevée | ABI étroite, ownership explicite, tests contractuels |
| R-005 | runners GPU compromis | critique | protection vérifiée avant enregistrement |
| R-007 | mémoire de chat contradictoire | élevée | état versionné et projection mobile régénérée |
| R-008 | objectifs « le plus puissant » non mesurables | élevée | profils de charge et objectifs séparés en P1 |

## Limite de preuve

Aucun moteur, kernel ou benchmark LLM ForgeLLM n’existe encore. Les résultats externes restent non reproduits. La racine `MANIFEST.sha256` décrit le paquet Phase 0 initial, pas tous les commits ultérieurs.

## Prochaine action autorisée

1. ajouter le rapport de revue agentique indépendante;
2. vérifier la CI de la tête finale;
3. mettre à jour la PR et quitter le mode brouillon si le verdict est `ACCEPT`;
4. décision de fusion par le propriétaire;
5. interdire tout runner GPU tant que la protection de `main` n’est pas prouvée;
6. produire S-0003 après fusion.
