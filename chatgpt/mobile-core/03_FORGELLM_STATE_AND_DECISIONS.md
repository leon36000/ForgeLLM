# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-13  
**Version d’état :** S-0003  
**Phase :** P0 — gouvernance, mémoire durable et laboratoire de preuve  
**Statut global :** P0-T02 terminé; fondation Phase 0 fusionnée dans le dépôt GitHub privé et vérifiée après fusion; P0-T03 de durcissement GitHub est actif

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont la correction, la performance, la sécurité et la reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique vérifié

- dépôt privé : `leon36000/ForgeLLM`;
- branche par défaut : `main`;
- PR Phase 0 : #1, fusionnée par squash;
- tête finale revue : `aa978989a5f6ad3524618eda5cd8b650288c7a67`;
- commit de fusion : `20bc5fa061aa039d32c2702d47eeba07dd353363`;
- arbre de fusion : `c75bc10c17744cba0bf0c5a284cd40f4285a2e10`.

## Preuves de P0-T02

### CI finale de la PR

- run : `31676559801`;
- job : `94372299029`;
- résultat : succès.

### CI après fusion sur `main`

- run : `31676680397`;
- job : `94372665642`;
- résultat : succès.

Le journal post-fusion observé montre :

- Ruff 0.16.2 réussi;
- validation projet, recherche, benchmark et paquet de tâche réussie;
- vérification déterministe de cinq fichiers mobiles réussie;
- **13 tests réussis**;
- bootstrap Ubuntu en dry-run réussi;
- permissions du jeton limitées à la lecture des métadonnées et du contenu.

## Hachages mobiles vérifiés sur le commit fusionné

```text
8a189b9dab3f60fe370099504c39d2196872ebc1977a5c91e34423a124766fbe  00_FORGELLM_CORE_CONTEXT.md
e76b7813eae0d8003bd5941d9dc07c28894c8acd0d835545a1b7b12bf865b26b  01_FORGELLM_AGENT_OPERATING_SYSTEM.md
10830969febb4234a61b0c36857be561d5185a0b64b7b9015fe055b6a0790801  02_FORGELLM_RESEARCH_AND_EVIDENCE.md
9315d61b2a8c4b4f8ab19e2fb23fbe2367a1089f293c41c7882b94f4cdab853c  03_FORGELLM_STATE_AND_DECISIONS.md
9697f7b35aa1924bdd9c07cf259fad41209d6e174cd7b2ecec3f65ab71932ff9  04_FORGELLM_PROMPTS_AND_WORKFLOWS.md
```

Le présent fichier S-0003 remplace le quatrième hachage; la CI du PR de clôture doit produire sa nouvelle valeur.

## Décisions acceptées

### D-0001 — Dépôt Git canonique

Les ADR, l’état, les preuves, les tâches et les handoffs versionnés sont la mémoire durable. La conversation est auxiliaire.

### D-0002 — Architecture hybride

Rust possède le plan de contrôle; les kernels utilisent les piles natives CUDA/HIP/CPU/DSL qui gagnent sous mesure; une ABI C versionnée sépare les couches.

### D-0003 — Remplacement progressif

Les moteurs existants sont des baselines et adaptateurs. Une brique n’est remplacée qu’après correction et avantage mesuré.

### D-0004 — Preuve avant revendication

Toute performance exige baseline comparable, environnement, données brutes, exactitude, répétitions, statistiques, hachages et portée.

### D-0005 — Revue du projet solo

Un agent ou contexte distinct vérifie le travail, la CI valide la tête exacte et le propriétaire autorise la fusion. Un second compte contrôlé par le même propriétaire n’est pas indépendant.

### D-0006 — Runners GPU interdits sans protection prouvée

Aucun runner auto-hébergé n’est enregistré avant preuve directe du dépôt privé, de la protection de `main` et de l’isolation du code non approuvé.

### D-0007 — Profils avant optimisation

Les modèles, charges, SLO et fonctions objectif de Phase 1 précèdent toute affirmation de « meilleur moteur ».

## Limites de la preuve

La Phase 0 prouve la structure du projet, ses validateurs, sa CI et son contexte mobile. Elle ne prouve aucun moteur, kernel, résultat numérique, support matériel ou gain de performance ForgeLLM. CodeQL et Dependency Review ont été ignorés par leurs garde-fous privés et ne sont pas déclarés actifs.

## Tâche active

**P0-T03 — durcir et vérifier directement le plan de contrôle GitHub.**

Paquet : `tasks/open/P0-T03-repository-hardening.yaml`.

Objectifs immédiats :

1. capturer l’état réel de la protection/ruleset de `main`;
2. vérifier les permissions GitHub Actions;
3. activer CodeQL et Dependency Review seulement s’ils sont supportés et réussissent avant d’être requis;
4. conserver les commandes administratives et leurs rollbacks;
5. exécuter CI exacte et revue indépendante.

## Blocage explicite

L’intégration GitHub a retourné `403 Resource not accessible by integration` pour l’endpoint de protection de branche. Cela signifie **état inconnu**, pas protection active ou inactive. Par conséquent P0-T04 et tout runner auto-hébergé restent bloqués.

## Prochain ordre d’exécution

1. P0-T03 : protection et sécurité du dépôt;
2. P0-T04 : inventaire matériel/topologique seulement après protection vérifiée;
3. P0-T05 : profils de charge et objectifs;
4. P0-T06 : plan du laboratoire de baselines;
5. aucun code moteur avant ces gates.
