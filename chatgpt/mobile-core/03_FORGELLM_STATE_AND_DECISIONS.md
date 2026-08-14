# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-14  
**Version d’état :** S-0007  
**Phase :** P0 — gouvernance, simulation et laboratoire de preuve  
**Statut global :** P0-T07 et P0-T08 terminés; P0-T09 est autorisé et actif en diagnostic Sonar strictement read-only; P0-T04 attend toujours la désignation d’un hôte

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont correction, performance, sécurité et reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique

- dépôt : `leon36000/ForgeLLM`;
- branche par défaut : `main` protégée par `FLLM`;
- base P0-T09 : `1b1a3621fcdf4129268663c497cdcd53aed48c29`;
- branche d’exécution : `feat/p0-t09-sonar-diagnosis`;
- paquet : `tasks/open/P0-T09-sonarqube-main-analysis.yaml`;
- issue : #26;
- autorisation : `P0-T09 / subagent-driven`, 2026-08-14.

## Décisions durables

- Git est la mémoire canonique; le chat et les RAG sont dérivés.
- Le runtime futur appartient principalement à Rust, avec une ABI C stable et des backends natifs.
- Aucune performance n’est acceptée sans preuve ForgeLLM reproductible.
- Le placement futur utilise un graphe de capacités et un autotuning empirique.
- Les futures implémentations spéculatives doivent se conformer à l’oracle exact CA-03.
- Une intégration externe ne devient pas une source de vérité sans preuve versionnée et vérifiable.

## P0-T08 / CA-03 terminé

CA-03 fournit les distributions exactes en `Fraction`, le `RandomTape`, le rejet modifié exact, l’égalité de loi, l’oracle greedy séparé, l’état transactionnel, le rollback et les traces déterministes. Sa limite reste `finite_exact_reference`.

## P0-T09 / QG-01 actif

Le baseline public est enregistré dans :

```text
artifacts/governance/P0-T09-sonar-baseline.json
docs/quality/P0-T09-SONAR-BASELINE.md
```

Trois cycles reproduisent le même motif :

```text
PR #25  Sonar success    → main 94890528740 cancelled
PR #27  Sonar success    → main 94892860919 cancelled
PR #28  Sonar success    → main 94894966719 cancelled
```

Phase 0 et CodeQL réussissent sur les PR et les commits `main` correspondants. Les checks `main` Sonar n’ont aucune annotation GitHub.

Le dépôt canonique ne contient ni workflow Sonar CI, ni `sonar-project.properties`, ni `.sonarcloud.properties`. Cela est compatible avec l’analyse automatique, mais ne prouve pas la valeur administrateur **Analysis Method**.

## Bloc actuel

```text
classification          unknown_due_to_missing_authenticated_evidence
méthode sélectionnée    aucune
changement configuration aucun
```

Il manque le readback Sonar authentifié en lecture seule : binding, méthode, activité de l’échec, quality gate, new code, portée/exclusions, plan et scanner externe éventuel.

## Garde-fous P0-T09

- aucun changement Sonar/GitHub avant le diagnostic et ADR-0004;
- jamais analyse automatique et scanner CI simultanément;
- aucun token ou payload administrateur privé dans Git;
- aucun problème accepté, supprimé ou exclu uniquement pour verdir le gate;
- un check absent, annulé, ignoré ou sans annotation n’est pas un succès;
- P0-T08, Phase 0, CodeQL, GitGuardian, la protection de `main`, P0-T04 et P0-T05 restent intacts.

## Décision après le readback

ADR-0004 choisira exactement :

```text
automatic_only
```

ou :

```text
ci_based_only
```

Aucune méthode ne sera choisie par supposition.

## Limites de preuve

P0-T09 établit actuellement un motif reproductible dans les checks GitHub, pas la cause interne Sonar. CA-03 ne prouve toujours pas un modèle réel, le KV tensoriel, le matériel, la performance ou la production.

## Tâche matérielle parallèle

P0-T04 reste bloqué sur un label d’hôte sûr et un mode d’exécution. Il demeure observationnel uniquement.
