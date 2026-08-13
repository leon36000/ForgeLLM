# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-13  
**Version d’état :** S-0005  
**Phase :** P0 — gouvernance, mémoire durable et laboratoire de preuve  
**Statut global :** P0-T03 terminé; ruleset `FLLM` actif sur `main`; P0-T04 bloqué uniquement sur la désignation du premier hôte autorisé

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont correction, performance, sécurité et reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique

- dépôt : `leon36000/ForgeLLM`;
- visibilité : publique sous ADR-0003;
- branche par défaut : `main`;
- commit avant S-0005 : `c1ec3db1613d9bc6a9a4cd0cd7a1c7e4eabaaa7f`;
- GitHub rapporte maintenant `main.protected=true`;
- ruleset actif : `FLLM`, id `20820530`;
- cible : exactement `refs/heads/main`;
- bypass : aucun.

## Protection FLLM vérifiée

- suppression protégée;
- mises à jour non fast-forward protégées;
- historique linéaire obligatoire;
- pull request obligatoire;
- zéro approbation GitHub artificielle en mode solo;
- conversations de revue résolues;
- squash uniquement;
- check strict `Validate and test` de GitHub Actions id `15368`.

Issue #10 est fermée comme complétée.

## Décisions

- **D-0001 :** Git est la mémoire canonique; le chat est auxiliaire.
- **D-0002 :** runtime Rust, C ABI et kernels natifs mesurés.
- **D-0003 :** remplacer progressivement les composants existants.
- **D-0004 :** aucune performance sans preuve reproductible.
- **D-0005 :** revue par contexte distinct + CI exacte + décision du propriétaire.
- **D-0006 :** l’exécution matérielle privilégiée exige des gates protégés et une revue séparée.
- **D-0007 :** profils de charge avant optimisation.
- **D-0008 :** dépôt source public; actifs restreints dans un plan privé séparé.
- **D-0009 :** RAG et outils externes sont dérivés; Git reste canonique.
- **D-0010 :** `FLLM` est la politique de protection active de `main` en mode solo jusqu’à décision révisée.

## Tâche active

**P0-T04 — premier inventaire matériel et logiciel assaini.**

Paquet : `tasks/open/P0-T04-first-hardware-inventory.yaml`  
Issue : #12  
Statut : `blocked`

Entrée propriétaire requise : un label de machine sûr et le mode d’exécution indiqué dans l’issue #12.

P0-T04 est observationnel uniquement. Aucun benchmark d’inférence ni code moteur ne fait partie de cette tâche.

## Limite de preuve

S-0005 prouve le durcissement du dépôt et les gates déjà enregistrés. Il ne prouve encore aucun inventaire matériel, support accélérateur, résultat numérique ou performance ForgeLLM.

## Prochain ordre

1. propriétaire : désigner un hôte et le mode d’exécution;
2. P0-T04 : inventaire assaini et revue;
3. P0-T05 : profils de charge et objectifs;
4. P0-T06 : plan des baselines;
5. aucun code moteur avant ces gates.
