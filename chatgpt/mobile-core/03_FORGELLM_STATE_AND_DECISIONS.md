# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-29
**Version d’état :** S-0017
**Canonical state ID:** S-0017
**Canonical source commit:** `cc5a90d0190bf84e3124a7e81bbe52bc7d0820bc`
**Derived manifest:** `chatgpt/mobile-core/DERIVED-MANIFEST.yaml`
**Phase :** P0 — gouvernance, simulation et laboratoire de preuve  
**Statut global :** P0-T07, P0-T08/CA-03, P0-T11/P0-T12, P0-T13, P0-T14, P0-T16, P0-T17, P0-T18, P0-T19 et l’implémentation bornée P0-T20 sont terminés dans le candidat; P0-T10 reste en `review` avec ADR-0005 `proposed`; P0-T15 reste `in_progress` comme tâche de conception uniquement avec ADR-0006 `proposed`; P0-T09/QG-01 reste actif mais inactif côté scanner; P0-T04 attend la désignation d’un hôte autorisé.

Le dépôt Git est la source canonique. Ce fichier est une projection mobile dérivée et reconstruisible; son manifest porte les empreintes des sources canoniques et ne peut pas remplacer `docs/state/CURRENT_STATE.md`.

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont correction, performance, sécurité et reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique

- dépôt : `leon36000/ForgeLLM`;
- branche par défaut : `main` protégée par `FLLM`;
- dernier `main` protégé avant P0-T20 : `cc5a90d0190bf84e3124a7e81bbe52bc7d0820bc` (PR #89, fermeture P0-T19);
- issue de réconciliation : #73;
- paquet Sonar actif : `tasks/open/P0-T09-sonarqube-main-analysis.yaml`.

## État réconcilié P0-T14

- P0-T03 possède un seul paquet canonique fermé et `complete`;
- P0-T10 reste dans `tasks/open` avec `review`; ADR-0005 est `proposed` et aucune acceptation architecturale n’est inférée de la fusion d’implémentation;
- P0-T13 est fermé et `complete` après le merge protégé `ad079c0`;
- P0-T14 est fermé et `complete` pour la validation du cycle de vie et des projections; son ancrage post-squash est `c1fd915…`;
- P0-T16 est fermé avec `complete` pour une composition CPU dense à un token, entièrement en mémoire et sans runtime;
- P0-T17, P0-T18 et P0-T19 sont fermés avec `complete` pour la ligne de référence Rust, l’oracle différentiel et l’attention transpose/single-query;
- P0-T20 est fermé avec `complete` pour une composition multi-query CPU à softmax par ligne; sa revue indépendante et ses gates de publication restent à faire;
- P0-T15 reste dans `tasks/open` avec `in_progress`; ADR-0006 est `proposed` et aucun ABI, binding, backend ou runtime n’est livré;
- les validateurs refusent les inversions de statut, doublons d’identifiants, dépendances non résolues et successeurs ADR incomplets.

## P0-T07 — simulateur synthétique terminé

Le simulateur de topologie et de placement est borné à `synthetic_only`. Sa revue `ACCEPT` et ses 102 tests ne constituent ni une mesure matérielle, ni une preuve de performance, ni une implémentation de runtime.

## P0-T08 / CA-03 terminé

CA-03 fournit les distributions exactes, le `RandomTape`, le rejet modifié, l’égalité de loi, l’oracle greedy séparé, l’état transactionnel, le rollback et les traces déterministes. Sa limite reste `finite_exact_reference`.

## P0-T13 — confidentialité terminée

P0-T13 est fermé et complet au merge protégé `ad079c0`. La frontière d’artefacts publics et l’assainissement fail-closed ont passé 34 tests ciblés, 487 tests complets, 230 tests spéculatifs, les validateurs, Ruff et les gates de CI; aucun probe réel de l’hôte n’a été exécuté.

## P0-T10 — intégration en revue

Le merge public `87a1dde` contient l’intégration statique bornée du Loop Engineering. P0-T10 reste `review` car ADR-0005 est encore `proposed` et le rapport final indépendant d’architecture/sécurité requis manque. Les traces historiques ne valent pas acceptation architecturale.

## P0-T15 — conception ABI uniquement

Le merge protégé `9932a5a` contient uniquement ADR-0006 proposée, recherche, plan, paquet et revue. Aucun header ABI, symbole, binding, backend, runtime ou code C/C++ n’est autorisé par cet état.

## P0-T09 / QG-01 actif mais inactif

Le chemin Sonar `ci_based_only` demeure préparation-only; l’analyse automatique reste la méthode active de la plateforme. Ne pas lire `SONAR_TOKEN`, modifier Sonar ou GitHub, activer le scanner, soumettre une analyse ou faire fonctionner les deux méthodes simultanément. Les données et preuves historiques sont dans `artifacts/governance/` et `docs/quality/`.

## P0-T17 à P0-T20 — ligne de référence attention

P0-T17, P0-T18 et P0-T19 sont protégés et complets. P0-T20 ajoute uniquement `attention_decode_multi_query` sur des tenseurs en mémoire, avec une normalisation softmax distincte par requête, un oracle stdlib-only et un fixture hashé. Le candidat de remédiation final figé à `0554747` et basé sur `main@cc5a90d` passe `make ci` avec 569 tests Python, 230 tests spéculatifs et 101 tests Rust, plus 12 tests Rust multi-query et 66 tests oracle ciblés. Le packet est désormais `tasks/closed/P0-T20-multi-query-attention.yaml`; les revues et gates exact-head restent requis avant publication. Aucun masque causal, multi-head/RoPE, KV cache, modèle, hardware, CUDA/ROCm, runtime/backend/ABI, performance, secret ou validation LiteLLM n’est couvert.

## Garde-fous et limites de preuve

- un check absent, annulé, ignoré ou sans annotation n’est pas un succès;
- P0-T04 reste observationnel et bloqué sur un hôte désigné;
- aucun modèle, runtime, backend, kernel, ABI, matériel ou benchmark n’est couvert par cette projection;
- les futures implémentations spéculatives doivent utiliser CA-03 comme oracle de correction;
- toute prochaine tâche CPU doit obtenir un identifiant libre dans Git et son propre paquet, plan et gates.
