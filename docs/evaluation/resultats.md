# Évaluation de l'analyse des contributions citoyennes

> Contributions fictives — illustration du fonctionnement de l'outil. Elles ne reflètent pas l'opinion réelle des habitants.

Généré par `make citizens` (`python -m app.services.citizens evaluate rabat`).

## Évaluation provisoire

Base : sur le jeu de test fictif (140 contributions annotées par Claude, qui les a aussi rédigées : évaluation provisoire, en partie circulaire).

| Mesure | IA locale | Mots-clés (sans IA) |
| --- | --- | --- |
| Thèmes — précision | 83 % | 63 % |
| Thèmes — rappel | 82 % | 70 % |
| Thèmes — F1 | 82 % | 66 % |
| Thème principal parmi les thèmes annotés | 88 % | — |
| Tonalité — exactitude | 79 % | 85 % |
| Langue — exactitude | 94 % | 94 % |

Localisation (unité d'analyse) : 117 justes, 0 fausses, 23 non localisées sur 140. Un lieu n'est rattaché que s'il est connu (quartiers, places, avenues d'OpenStreetMap) ou si la commune est déclarée ; sinon « lieu non identifié ».

Contributions analysées par l'IA : 140 sur 140.

## Évaluation indépendante par un second modèle d'IA

Base : Évaluation indépendante par un second modèle d'IA (28 contributions fictives, amazighe exclu) — en attente de validation par le professeur.

| Mesure | IA locale | Mots-clés (sans IA) |
| --- | --- | --- |
| Thèmes — précision | 77 % | 56 % |
| Thèmes — rappel | 74 % | 61 % |
| Thèmes — F1 | 75 % | 58 % |
| Thème principal parmi les thèmes annotés | 75 % | — |
| Tonalité — exactitude | 71 % | 82 % |

Contributions analysées par l'IA : 28 sur 28.

## Désaccords entre la fiche d'annotation et l'IA locale

| Contribution | Thèmes (fiche) | Thèmes (IA locale) | Tonalité (fiche) | Tonalité (IA locale) |
| --- | --- | --- | --- | --- |
| RBT-005 | espaces_verts | proprete | proposition | proposition |
| RBT-017 | emploi_jeunesse | emploi_jeunesse | demande | proposition |
| RBT-019 | patrimoine | patrimoine | demande | plainte |
| RBT-045 | bruit | autres | satisfaction | satisfaction |
| RBT-051 | emploi_jeunesse | emploi_jeunesse | demande | plainte |
| RBT-054 | espaces_verts | espaces_verts | demande | satisfaction |
| RBT-060 | eau_assainissement | proprete | demande | plainte |
| RBT-079 | eau_assainissement | proprete | satisfaction | satisfaction |
| RBT-096 | education | emploi_jeunesse | demande | plainte |
| RBT-109 | education, voirie | sante, education | satisfaction | satisfaction |
| RBT-117 | circulation, voirie | voirie | demande | demande |
| RBT-124 | voirie | voirie | demande | plainte |
| RBT-127 | espaces_verts | circulation | plainte | plainte |
| RBT-134 | eau_assainissement | eau_assainissement | demande | plainte |
