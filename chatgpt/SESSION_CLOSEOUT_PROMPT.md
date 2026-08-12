# Prompt de clôture d’une session ForgeLLM

Clôture cette session sans supposer qu’une discussion future conservera le contexte.

Produis :

1. résultat obtenu et statut (`terminé`, `partiel`, `bloqué`);
2. décisions nouvelles ou modifiées avec justification;
3. preuves et sources ajoutées;
4. commandes/tests/benchmarks réellement exécutés et résultats;
5. artefacts générés avec chemins et hachages lorsque disponibles;
6. risques résiduels et hypothèses non vérifiées;
7. prochaine tâche unique, petite et testable;
8. un bloc Markdown complet remplaçant `03_FORGELLM_STATE_AND_DECISIONS.md`;
9. les patches nécessaires pour le dépôt Git.

Ne transforme pas une intention en travail accompli. Tout élément non exécuté doit être marqué `non exécuté`.
