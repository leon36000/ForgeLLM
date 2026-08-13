# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-13  
**Version d’état :** S-0003  
**Phase :** P0 — gouvernance, mémoire durable et laboratoire de preuve  
**Statut global :** P0-T02 terminé; fondation Phase 0 fusionnée et vérifiée; P0-T03 de durcissement GitHub est en cours, avec exécution CodeQL réussie mais protection de `main` et visibilité des alertes encore inconnues

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont la correction, la performance, la sécurité et la reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique vérifié

- dépôt privé : `leon36000/ForgeLLM`;
- branche par défaut : `main`;
- PR Phase 0 : #1, fusionnée par squash;
- tête finale revue : `aa978989a5f6ad3524618eda5cd8b650288c7a67`;
- commit de fusion : `20bc5fa061aa039d32c2702d47eeba07dd353363`;
- arbre de fusion : `c75bc10c17744cba0bf0c5a284cd40f4285a2e10`;
- PR de clôture S-0003 : #4.

## Preuves de P0-T02

### CI finale de la PR #1

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

## Preuves de la proposition S-0003

Sur la tête PR #4 `113b0e8cf86fa40c2f05e2742a635de17cef5afd` :

### Gate Phase 0

- run : `31677360240`;
- job : `94374759191`;
- conclusion : succès;
- Ruff, tous les validateurs actifs, les deux paquets P0-T02/P0-T03, les cinq hachages mobiles, **13 tests** et le bootstrap dry-run ont réussi.

### CodeQL

- run : `31677360037`;
- job : `94374758365`;
- conclusion : succès;
- CodeQL Action 4.37.6 et CLI 2.26.2;
- 61 modules Python extraits;
- 52 requêtes `security-extended` exécutées;
- SARIF téléversé et traitement GitHub terminé.

L’endpoint des alertes CodeQL retourne `403 Resource not accessible by integration`. La réussite d’exécution est donc prouvée, mais le nombre, la gravité et l’état de triage des alertes restent **inconnus**. Il est interdit de reformuler cette réussite en « aucune alerte ».

### Dependency Review

- run : `31677360127`;
- conclusion : ignoré par le garde-fou du dépôt privé.

Dependency Review n’est pas une preuve active et ne doit pas devenir un check requis tant qu’il reste ignoré.

## Hachage mobile observé avant la dernière mise à jour d’état

```text
506b740aeff18d6e96a3db2550caa710995a9e93059b7ab5513b8f20020592f0  03_FORGELLM_STATE_AND_DECISIONS.md
```

La tête finale de la PR #4 doit produire le nouveau hachage de ce fichier avant fusion.

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

La Phase 0 prouve la structure du projet, ses validateurs, sa CI et son contexte mobile. Elle ne prouve aucun moteur, kernel, résultat numérique, support matériel ou gain de performance ForgeLLM. Elle ne prouve pas que CodeQL ne contient aucune alerte, ni que Dependency Review ou la protection de `main` sont actifs.

## Tâche active

**P0-T03 — durcir et vérifier directement le plan de contrôle GitHub.**

Statut : `in_progress`.

Paquet : `tasks/open/P0-T03-repository-hardening.yaml`.

Progrès vérifié :

- identité privée du dépôt et branche par défaut;
- gate `Validate and test` répétable;
- CodeQL exécuté, SARIF chargé et traité;
- Dependency Review identifié comme ignoré.

Objectifs restants :

1. capturer l’état réel de la protection/ruleset de `main`;
2. vérifier directement les permissions GitHub Actions et la politique des actions autorisées;
3. consulter les alertes CodeQL ou conserver explicitement leur état inconnu;
4. exécuter Dependency Review avec succès avant toute exigence;
5. conserver les commandes administratives et leurs rollbacks;
6. exécuter CI exacte et revue indépendante pour P0-T03.

## Blocages explicites

- protection de branche : endpoint `403`, état inconnu;
- alertes CodeQL : endpoint `403`, détails inconnus;
- Dependency Review : ignoré;
- tout runner auto-hébergé et P0-T04 restent bloqués.

## Prochain ordre d’exécution

1. P0-T03 : protection et sécurité du dépôt;
2. P0-T04 : inventaire matériel/topologique seulement après protection vérifiée;
3. P0-T05 : profils de charge et objectifs;
4. P0-T06 : plan du laboratoire de baselines;
5. aucun code moteur avant ces gates.
