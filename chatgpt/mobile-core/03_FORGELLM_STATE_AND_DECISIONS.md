# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-13  
**Version d’état :** S-0004  
**Phase :** P0 — gouvernance, mémoire durable et laboratoire de preuve  
**Statut global :** dépôt public accepté par ADR-0003; les gates hébergés et la revue passent; P0-T03 reste bloqué uniquement sur la protection administrative de `main`

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont correction, performance, sécurité et reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique

- dépôt : `leon36000/ForgeLLM`;
- visibilité : publique, décision propriétaire intentionnelle;
- branche par défaut : `main`;
- commit avant P0-T03 : `843f8127f76a0c7f2ef9863853dccaddeff90aa8`;
- état direct : `main` non protégée, checks non imposés, aucun ruleset;
- endpoints administratifs de protection, permissions Actions et alertes CodeQL : `403` pour l’intégration actuelle.

Les anciennes mentions « dépôt privé » sont supersédées.

## Décisions

- **D-0001 :** Git est la mémoire canonique; le chat est auxiliaire.
- **D-0002 :** runtime Rust, C ABI et kernels natifs mesurés.
- **D-0003 :** remplacer progressivement les composants existants.
- **D-0004 :** aucune performance sans preuve reproductible.
- **D-0005 :** revue par contexte distinct + CI exacte + décision du propriétaire.
- **D-0006 :** aucun runner auto-hébergé avant protection et isolation prouvées.
- **D-0007 :** profils de charge avant optimisation.
- **D-0008 :** dépôt source public; actifs restreints dans un plan privé séparé.
- **D-0009 :** RAG et outils externes sont dérivés; Git reste canonique.

## Frontière publique

Tout contenu Git, issue, PR, log et artefact est considéré public et copiable. Secrets, poids restreints, datasets/prompts privés, traces non expurgées, IP privées et UUID matériels sont interdits.

La visibilité publique ne constitue pas une licence. Les contributions externes de code exigent une tâche liée et un traitement explicite des droits entrants jusqu’à l’ADR de licence.

## Outils externes

- GitHub, CodeQL et Codex Engineering Guardrails : utilisés maintenant.
- SonarQube : pertinent quand un serveur/projet callable est connecté; aucune analyse Sonar n’est revendiquée.
- Fallow : non pertinent pour la surface Python/Markdown actuelle.
- Consensus : futur outil de synthèse scientifique bornée.
- Neon Postgres : futur index RAG dérivé seulement après ADR/tâche.
- Temporal : futur orchestrateur après spécification des workflows.
- skills NVIDIA/AMD : phases matériel/backend protégées, pas avant.

## Preuves de la tête revue

Tête : `9d3b47365aa017f37b16a6f8c7e307677a7526cf`.

- Phase 0 `31681837631` / `94388820133` : succès; Ruff, validateurs, hachages mobiles, **17 tests** et bootstrap dry-run réussis.
- CodeQL `31681837665` / `94388813356` : succès; 62 modules, 52 requêtes, SARIF traité; alertes inconnues.
- Dependency Review `31681837651` : ignoré par opt-in.
- Probe antérieur `31681032967` / `94386280488` : échec parce que Dependency Graph est désactivé; aucun résultat de dépendance.
- Revue fraîche : `ACCEPT` pour la PR de gouvernance, P0-T03 restant `in_progress`.

La revue a corrigé un faux positif de sécurité : un ruleset non lié ou désactivé ne peut plus être interprété comme protection de `main`.

## Gate propriétaire bloquant

Protéger `main` ou appliquer un ruleset équivalent exigeant PR, `Validate and test`, résolution des conversations, administrateur/propriétaire inclus, aucun force-push ni suppression. Zéro faux reviewer humain est utilisé en mode solo.

Dependency Graph peut ensuite être activé pour rendre Dependency Review exécutable. Les alertes CodeQL doivent être inspectées séparément.

## Blocage

Aucun runner GPU/CPU auto-hébergé, workflow portant des secrets, inventaire matériel P0-T04 ou code moteur tant que la protection n’est pas directement prouvée.
