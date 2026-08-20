# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-20
**Version d’état :** S-0008
**Phase :** P0 — gouvernance, simulation et laboratoire de preuve  
**Statut global :** P0-T07 et P0-T08 terminés; P0-T11/P0-T12 fournissent maintenant une ligne de référence Rust CPU bornée et fusionnée sur `main`; P0-T09 est actif en diagnostic Sonar read-only; la méthode Sonar actuelle est confirmée comme analyse automatique activée et recommandée; P0-T04 attend toujours la désignation d’un hôte

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont correction, performance, sécurité et reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique

- dépôt : `leon36000/ForgeLLM`;
- branche par défaut : `main` protégée par `FLLM`;
- base initiale P0-T09 : `1b1a3621fcdf4129268663c497cdcd53aed48c29`;
- dernier `main` canonique : `7962abe6c08a79da28e083735507fbae29529d74`;
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

Le baseline et le readback sont enregistrés dans :

```text
artifacts/governance/P0-T09-sonar-baseline.json
artifacts/governance/P0-T09-sonar-analysis-method-readback.json
docs/quality/P0-T09-SONAR-BASELINE.md
```

Le probe post-import donne :

```text
PR #30   Sonar 94945852247  success / 0 nouvelle issue
main     Sonar 94946081665  cancelled / 0 annotation
```

Phase 0 et CodeQL réussissent sur le probe. L’import du projet n’a donc pas suffi à réparer le chemin `main`.

## Méthode Sonar maintenant confirmée

Une capture authentifiée fournie par le propriétaire montre la page **Analysis method** de ForgeLLM :

```text
Automatic analysis     activée
Recommendation         Recommended
Méthode CI sélectionnée non
```

La capture brute n’est pas commitée. La transcription assainie conserve son SHA-256 comme preuve d’identité.

## Bloc actuel

```text
méthode configurée       automatic_enabled
compatibilité            recommended
classification           automatic_analysis_enabled_root_cause_unknown
méthode finale choisie   aucune
changement configuration aucun
```

La preuve la plus importante qui manque est désormais le message détaillé **Project Activity / failed main analysis** correspondant au commit `bd03e479…` / check `94946081665`.

Il manque aussi avant ADR-0004 : binding, quality gate, new code, portée/exclusions, plan et confirmation d’un scanner externe éventuel.

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

Aucune méthode finale ne sera choisie par supposition.

## Limites de preuve

P0-T09 établit maintenant la méthode automatique configurée et le motif reproductible PR-success/`main`-failure, mais pas encore la cause interne Sonar. CA-03 ne prouve toujours pas un modèle réel, le KV tensoriel, le matériel, la performance ou la production.

## Tâche matérielle parallèle

P0-T04 reste bloqué sur un label d’hôte sûr et un mode d’exécution. Il demeure observationnel uniquement.
