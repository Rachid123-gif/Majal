# Évaluation de l'analyse des contributions citoyennes

> Contributions fictives — illustration du fonctionnement de l'outil. Elles ne reflètent pas l'opinion réelle des habitants.

Généré par `make citizens` (`python -m app.services.citizens evaluate rabat`).

## Évaluation provisoire

Base : sur le jeu de test fictif (400 contributions annotées par Claude, qui les a aussi rédigées : évaluation provisoire, en partie circulaire).

| Mesure | IA locale | Mots-clés (sans IA) |
| --- | --- | --- |
| Thèmes — précision | 84 % | 70 % |
| Thèmes — rappel | 83 % | 75 % |
| Thèmes — F1 | 84 % | 72 % |
| Thème principal parmi les thèmes annotés | 88 % | — |
| Tonalité — exactitude (mots-clés puis IA) | 92 % | 90 % |
| Langue — exactitude | 92 % | 92 % |

Localisation (unité d'analyse) : 347 justes, 0 fausses, 53 non localisées sur 400. Un lieu n'est rattaché que s'il est connu (quartiers, places, avenues d'OpenStreetMap) ou si la commune est déclarée ; sinon « lieu non identifié ».

Contributions analysées par l'IA : 400 sur 400. Tonalité : mots-clés en priorité, IA locale seulement quand aucun mot-clé ne tranche.

## Évaluation indépendante par un second modèle d'IA

Base : Évaluation indépendante par un second modèle d'IA (28 contributions fictives, amazighe exclu) — en attente de validation par le professeur.

> Attention : la précision de la taxonomie (eau et égouts, crèches) et la règle de tonalité (mots-clés d'abord) ont été décidées après avoir vu les désaccords avec ce classement ; cette évaluation est donc en partie optimiste.

| Mesure | IA locale | Mots-clés (sans IA) |
| --- | --- | --- |
| Thèmes — précision | 75 % | 65 % |
| Thèmes — rappel | 77 % | 71 % |
| Thèmes — F1 | 76 % | 68 % |
| Thème principal parmi les thèmes annotés | 75 % | — |
| Tonalité — exactitude (mots-clés puis IA) | 86 % | 82 % |

Contributions analysées par l'IA : 28 sur 28. Tonalité : mots-clés en priorité, IA locale seulement quand aucun mot-clé ne tranche.

## Désaccords entre la fiche d'annotation et l'IA locale

| Contribution | Thèmes (fiche) | Thèmes (IA locale) | Tonalité (fiche) | Tonalité (IA locale) |
| --- | --- | --- | --- | --- |
| RBT-005 | espaces_verts | proprete | proposition | proposition |
| RBT-019 | patrimoine | patrimoine | demande | plainte |
| RBT-045 | bruit | autres | satisfaction | satisfaction |
| RBT-051 | emploi_jeunesse | emploi_jeunesse | demande | plainte |
| RBT-060 | eau_assainissement | securite | demande | demande |
| RBT-079 | eau_assainissement | bruit | satisfaction | satisfaction |
| RBT-089 | administration | administration | plainte | demande |
| RBT-096 | education | espaces_verts, emploi_jeunesse | demande | demande |
| RBT-109 | education, voirie | sante, education | satisfaction | satisfaction |
| RBT-124 | voirie | voirie | demande | plainte |
| RBT-127 | espaces_verts | circulation | plainte | plainte |
