# ForgeLLM — système d’exploitation des agents

## Contrat de démarrage

Avant toute proposition ou modification, l’agent doit :

1. lire les cinq fichiers ForgeLLM;
2. comparer l’identifiant d’état mobile au dépôt Git lorsque celui-ci est accessible;
3. identifier la phase, la tâche, les objectifs et non-objectifs;
4. relire les décisions, risques et questions ouvertes applicables;
5. distinguer ce qui est connu, périmé ou inconnu;
6. définir un oracle de correction et un plan de vérification;
7. annoncer les fichiers ou registres qui devront être mis à jour.

## Unité de travail

Une unité normale respecte :

- un identifiant de tâche;
- un problème unique;
- une branche et un worktree;
- un agent implémenteur;
- un agent vérificateur indépendant;
- des fichiers exacts;
- des interfaces explicites;
- des critères d’acceptation observables;
- des tests et commandes précis;
- une PR petite;
- un handoff complet.

## Gate anti-dérive

Avant d’ajouter du travail, répondre :

- À quel objectif invariant cela contribue-t-il?
- Est-ce nécessaire pour le jalon actif?
- Est-ce couvert par la tâche?
- Modifie-t-il architecture, ABI, format, dépendance, sécurité, numérique ou benchmark?
- Comment saura-t-on objectivement que c’est réussi?

Si la réponse n’est pas documentée, ne pas implémenter. Enregistrer l’idée dans les questions ouvertes ou créer une tâche séparée.

## Gate de décision

Un ADR est obligatoire pour :

- langage ou backend structurant;
- ABI/API publique;
- format de modèle, cache ou résultat;
- propriété et durée de vie à travers FFI;
- nouvelle dépendance critique;
- changement de méthodologie de benchmark;
- compromis correction/performance;
- stratégie distribuée ou de compatibilité.

Un ADR contient : contexte, décision, alternatives, conséquences, risques, preuve nécessaire et condition de révision.

## Gate de correction

Ordre de validation :

1. test unitaire déterministe;
2. test de propriété ou métamorphique;
3. comparaison avec implémentation de référence;
4. test différentiel entre backends/précisions;
5. budget numérique documenté;
6. sanitizers, race detection, fuzzing, fault injection;
7. benchmark.

## Gate de performance

Interdiction de conclure « plus rapide » sans :

- commits baseline/candidat et worktree propre;
- matériel, topologie, température/power state pertinents;
- OS, noyau, pilote, firmware, runtime, compilateur et dépendances;
- modèle et révision immuables;
- précision, quantification et disposition mémoire;
- prompts/sorties, concurrence, scheduler et seeds;
- warm-up, au moins cinq mesures sauf justification;
- échantillons bruts, médiane, dispersion et queues;
- résultat de correction;
- hachage des artefacts;
- statut de reproduction.

## Gate de recherche

Pour chaque source :

- identifiant stable et URL canonique;
- type et niveau de preuve;
- auteurs/organisation;
- date et version/commit;
- affirmation réellement supportée;
- hypothèses et limites;
- relation aux autres travaux;
- statut `non_lu`, `trié`, `lu`, `reproduire`, `reproduit`, `rejeté`.

Ne jamais utiliser le nombre d’étoiles comme preuve de performance. Il sert seulement de signal d’adoption à dater.

## Règles GitHub/GitLab

- `main` protégée; PR/MR obligatoire; pas de force push.
- checks stricts, approbation indépendante, discussions résolues.
- CODEOWNERS après création de l’organisation/équipe.
- actions tierces épinglées à un SHA complet.
- secrets bloqués au push; dépendances et licences revues.
- runners GPU privés, restreints et idéalement éphémères.
- aucun job de fork non approuvé sur runner auto-hébergé.
- releases avec SBOM, provenance, hachages et notes de reproductibilité.

## Rapport de clôture obligatoire

1. statut réel;
2. livrable;
3. fichiers modifiés;
4. tests/commandes et résultats;
5. sources/preuves;
6. limites et risques;
7. décisions/état mis à jour;
8. prochaine tâche unique;
9. bloc de remplacement du fichier d’état mobile.
