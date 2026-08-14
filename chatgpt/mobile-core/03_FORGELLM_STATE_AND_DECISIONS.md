# ForgeLLM — état, décisions et continuité

**Mise à jour :** 2026-08-14  
**Version d’état :** S-0007  
**Phase :** P0 — gouvernance, simulation et laboratoire de preuve  
**Statut global :** P0-T07 et P0-T08 terminés; P0-T04 attend la désignation d’un hôte; QG-01 suit une incohérence d’analyse Sonar sur `main`; aucun futur paquet de recherche ou runtime n’est automatiquement autorisé

## Objectif invariant

Concevoir et construire un moteur d’inférence LLM hétérogène dont correction, performance, sécurité et reproductibilité sont démontrées par des artefacts versionnés.

## Dépôt canonique

- dépôt : `leon36000/ForgeLLM`;
- branche par défaut : `main` protégée par `FLLM`;
- merge P0-T07 : `b0f3f241537b50de0dd3c0cb7bc2e6bf274a7034`;
- merge P0-T08 : `e6c9d1ae30f1b5e161a56bf8c9b4fa25c823fe24`;
- merge de remédiation Sonar : `e81c1c0ad0b161844569df46ee62246c9de56698`;
- aucun runner auto-hébergé, modèle, benchmark matériel ou code accélérateur ajouté par CA-03.

## Décisions durables

- Git est la mémoire canonique; le chat et les RAG sont dérivés.
- Le runtime futur appartient principalement à Rust, avec une ABI C stable et des backends natifs.
- Aucune performance n’est acceptée sans preuve ForgeLLM reproductible.
- Le plan microarchitectural utilise un graphe de capacités et un placement/autotuning empirique.
- ForgeCacheDraft est le premier cas CPU-cache/GPU; Transition Atlas reste expérimental et non autorisé.
- Les futures implémentations spéculatives doivent se conformer à l’oracle exact CA-03.

## P0-T07 terminé

P0-T07 fournit le simulateur synthétique cache-aware, ses schémas, son coût entier, ses placements légaux et son fallback générique obligatoire. Sa limite demeure `synthetic_only`.

## P0-T08 / CA-03 terminé

CA-03 fournit :

- distributions finies exactes en `Fraction`;
- source aléatoire immuable `RandomTape`;
- acceptation `min(1, p(x)/q(x))`;
- correction au premier rejet par `(p-q)_+` normalisé;
- token bonus cible lorsque le bloc est entièrement accepté;
- égalité exacte des lois cible et spéculative;
- oracle greedy séparé;
- état transactionnel target/draft/sampler/grammar;
- commit du préfixe accepté, abandon du suffixe rejeté et rollback exact;
- traces déterministes sans dépendance à l’environnement;
- gate `make verify-speculative`.

Preuves finales :

```text
Base                    1cd502609c7b05ac628057f79a9135b07c08e821
Tête implémentation     16d65288b34a9f2f91a4c67182aab13ddfb5e17d
Merge implémentation    e6c9d1ae30f1b5e161a56bf8c9b4fa25c823fe24
Tests complets          332 réussis
Tests ciblés            230 réussis
Phase 0 implémentation  31831781322 / 94868927648
CodeQL implémentation   31831781266 / 94868926709
Revue spécification     4940413742 / ACCEPT
Revue qualité           4940415259 / ACCEPT
Tête remédiation        a7f508fe1fa4787b889445c5e5986339b508217a
Merge remédiation       e81c1c0ad0b161844569df46ee62246c9de56698
Phase 0 remédiation     31838436974 / 94889874946
CodeQL remédiation      31838436902 / 94889874310
Sonar PR                94889986512 / PASSED / 0 nouvelle issue
Phase 0 final main      31838603770 / 94890388826
CodeQL final main       31838603775 / 94890388594
Limite                  finite_exact_reference
```

L’exactitude stochastique signifie l’égalité de la loi de sortie, pas l’identité de séquence sous le même seed.

## SonarQube Cloud

La PR de remédiation a réussi le Quality Gate Sonar avec zéro nouvelle issue et zéro hotspot. L’analyse automatique de `main` a ensuite été signalée comme annulée/échouée sans annotation par le check `94890528740`. QG-01 / issue #26 suit cette incohérence. Il est interdit de présenter le résultat PR comme preuve que l’analyse de branche fonctionne.

## Limites de preuve

CA-03 ne prouve pas les logits flottants ou quantifiés, un modèle réel, le tokenizer, le KV tensoriel, le batching, le matériel, la performance, l’énergie, le distribué ou la production.

## Tâche opérationnelle suivante

P0-T04 reste bloqué sur un label d’hôte sûr et un mode d’exécution. Il demeure observationnel uniquement. QG-01 peut être autorisé séparément. Toute autre suite — Transition Atlas, conformance modèle réel, runtime Rust, ABI C ou backend — exige un nouveau paquet explicitement autorisé.
