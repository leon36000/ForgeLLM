# Prompt de démarrage d’une session ForgeLLM

Lis intégralement les cinq sources ForgeLLM du projet avant de répondre.

Retourne d’abord un **contrôle de continuité** contenant exactement :

1. objectif invariant du projet;
2. phase et jalon actuels;
3. tâche active ou prochaine tâche autorisée;
4. décisions acceptées qui contraignent cette tâche;
5. trois principaux risques;
6. non-objectifs pertinents;
7. contradictions ou données périmées détectées;
8. éléments qui exigent une vérification Web ou dans Git;
9. plan de preuve et tests pour cette session;
10. fichiers d’état à mettre à jour à la clôture.

N’invente aucun état absent. Marque explicitement `inconnu` ce qui n’est pas documenté. Ensuite seulement, exécute la demande courante en respectant les gates anti-dérive et de preuve.
