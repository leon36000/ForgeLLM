# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-13  
**Version d’état :** S-0004  
**Phase :** P0 — gouvernance, mémoire durable et laboratoire de preuve  
**Statut global :** dépôt public accepté par ADR-0003; P0-T03 est en cours et bloqué uniquement sur la preuve administrative de protection de `main` après les gates CI/revue

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont correction, performance, sécurité et reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique

- dépôt : `leon36000/ForgeLLM`;
- visibilité : publique, décision propriétaire intentionnelle;
- branche par défaut : `main`;
- commit avant S-0004 : `843f8127f76a0c7f2ef9863853dccaddeff90aa8`;
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

La visibilité publique ne constitue pas une licence. Les contributions de code externes exigent une tâche liée et un traitement explicite des droits entrants jusqu’à l’ADR de licence.

## Outils externes

- GitHub, CodeQL et Codex Engineering Guardrails : utilisés maintenant.
- SonarQube : pertinent quand un serveur/projet callable est connecté; aucune analyse Sonar n’est revendiquée ici.
- Fallow : non pertinent pour la surface Python/Markdown actuelle.
- Consensus : futur outil de synthèse scientifique bornée.
- Neon Postgres : futur index RAG dérivé seulement après ADR/tâche.
- Temporal : futur orchestrateur après spécification des workflows.
- skills NVIDIA/AMD : phases matériel/backend protégées, pas avant.

## P0-T03

Cette branche ajoute ADR/politiques publics, audit typé, tests de protection et Dependency Review pour les PR internes publiques.

Gates à prouver par la PR : `make ci`, CodeQL, Dependency Review, revue fraîche et hachage mobile.

Gate propriétaire restant : protéger `main` ou appliquer un ruleset équivalent exigeant PR, `Validate and test`, résolution des conversations, administrateurs inclus, aucun force-push ni suppression. Zéro faux reviewer humain est utilisé en mode solo.

## Blocage

Aucun runner GPU/CPU auto-hébergé, secret-bearing workflow, inventaire matériel P0-T04 ou code moteur tant que la protection n’est pas directement prouvée.
