# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-14  
**Version d’état :** S-0006  
**Phase :** P0 — gouvernance, simulation et laboratoire de preuve  
**Statut global :** P0-T07 terminé avec preuve synthétique; P0-T04 attend un hôte; CA-03 est autorisé en mode subagent-driven mais doit commencer par une spécification, un plan et un paquet borné

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont correction, performance, sécurité et reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique

- dépôt : `leon36000/ForgeLLM`;
- visibilité : publique sous ADR-0003;
- branche par défaut : `main`;
- protection : ruleset `FLLM` actif;
- commit d’implémentation P0-T07 : `b0f3f241537b50de0dd3c0cb7bc2e6bf274a7034`;
- aucun runner auto-hébergé, modèle, benchmark matériel ou code accélérateur ajouté.

## Décisions durables

- Git est la mémoire canonique; le chat et les RAG sont dérivés.
- Le runtime futur appartient principalement à Rust, avec une ABI C stable et des backends natifs.
- Les moteurs existants sont des baselines/adaptateurs remplacés progressivement.
- Aucune performance n’est acceptée sans preuve ForgeLLM reproductible.
- Les travaux significatifs séparent implémentation, revue fraîche et autorisation propriétaire.
- Les profils de charge précèdent les déclarations de meilleur moteur.
- Le dépôt source est public; les actifs restreints vivent dans un plan privé.
- `FLLM` protège `main` en mode mainteneur solo.
- Le plan microarchitectural utilise un graphe de capacités et un placement/autotuning empirique.
- ForgeCacheDraft est le premier cas CPU-cache/GPU; Transition Atlas reste expérimental.

## P0-T07 terminé

P0-T07 livre :

- schémas stricts de topologie, composants et résultats;
- modèles immuables et neutres vis-à-vis des produits;
- coût entier en octets, taux et nanosecondes;
- placements légaux, rejets stables et fallback générique obligatoire;
- sortie atomique confinée sous `artifacts/`;
- scénario cache-draft synthétique;
- tests adversariaux.

Preuves finales :

```text
PR head                99c1c1488f622a6d4290e21a17ff313a1c3568c6
Merge main             b0f3f241537b50de0dd3c0cb7bc2e6bf274a7034
Tests                   102 réussis
Phase 0 PR              31784275654 / 94716606110
CodeQL PR               31784275655 / 94716597658
Phase 0 post-merge      31784610893 / 94717633943
CodeQL post-merge       31784610881 / 94717633957
Limite                  synthetic_only
```

Les nanosecondes simulées ne sont pas des mesures matérielles.

## Travail autorisé : CA-03

Le propriétaire a autorisé `CA-03 / subagent-driven`.

CA-03 doit définir et tester :

- distributions cible et proposition;
- acceptation/rejet exact;
- résidu positif normalisé;
- token bonus lorsque tout le draft est accepté;
- oracle greedy séparé;
- commit/rollback KV et états auxiliaires;
- annulation, EOS et budget;
- égalité exhaustive de loi sur petits modèles synthétiques.

CA-03 interdit les téléchargements de modèles, l’inférence matérielle, le runtime Rust, l’ABI C, les kernels et les affirmations de performance.

## Tâche matérielle parallèle

P0-T04 reste bloqué sur un label d’hôte sûr et un mode d’exécution. Il demeure observationnel uniquement.

## Prochaine séquence

1. sources primaires et claims CA-03;
2. spécification écrite;
3. plan TDD;
4. paquet P0-T08/CA-03;
5. implémentation de référence exacte;
6. revue et gates hébergés;
7. aucune intégration runtime avant les gates ultérieurs.
