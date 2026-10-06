# Évaluation de l'analyse des contributions citoyennes

> Contributions fictives — illustration du fonctionnement de l'outil. Elles ne reflètent pas l'opinion réelle des habitants.

Généré par `make citizens` (`python -m app.services.citizens evaluate rabat`).

## Évaluation provisoire

Base : sur le jeu de test fictif (140 contributions annotées par Claude, qui les a aussi rédigées : évaluation provisoire, en partie circulaire).

| Mesure | IA locale | Mots-clés (sans IA) |
| --- | --- | --- |
| Thèmes — précision | 83 % | 62 % |
| Thèmes — rappel | 81 % | 70 % |
| Thèmes — F1 | 82 % | 66 % |
| Thème principal parmi les thèmes annotés | 86 % | — |
| Tonalité — exactitude | 80 % | 85 % |
| Langue — exactitude | 94 % | 94 % |

Localisation (unité d'analyse) : 116 justes, 0 fausses, 24 non localisées sur 140. Un lieu n'est rattaché que s'il est connu (quartiers, places, avenues d'OpenStreetMap) ou si la commune est déclarée ; sinon « lieu non identifié ».

Contributions analysées par l'IA : 140 sur 140.

## Évaluation de référence

En attente du fichier classé par le professeur (`docs/evaluation/annotation-professeur.xlsx`).

