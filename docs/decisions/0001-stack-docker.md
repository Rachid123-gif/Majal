# 0001 — Stack technique et exécution dans Docker

- **Date** : 2026-10-05 · **Statut** : accepté

## Contexte
Le démonstrateur doit tourner sur un portable (aujourd'hui un Mac Apple Silicon, 16 Go), hors
ligne, et pouvoir passer sur une autre machine sans réinstallation complexe (BRIEF §11).

## Options
1. Tout installer directement sur la machine (Python, PostgreSQL, PostGIS, Redis, Node).
2. Tout dans Docker Compose, avec une commande `make` par action.

## Choix
Option 2, avec la stack du BRIEF §11 : FastAPI, PostgreSQL 16, PostGIS, pgvector, Redis,
Next.js. L'image de base de données est construite à partir de l'image officielle
`postgres:16-bookworm` (multi-architecture), en y ajoutant PostGIS et pgvector depuis
apt.postgresql.org. L'image `postgis/postgis` n'est pas utilisée car sa disponibilité sur
arm64 n'est pas garantie et elle ne contient pas pgvector.

## Conséquences
- Seuls Docker Desktop, Git et Make sont nécessaires sur la machine de démonstration.
- `make test` et `make lint` fonctionnent aussi sans Docker (uv et npm) : c'est utile pour
  l'intégration continue et tant que Docker n'est pas installé.
- La première construction des images demande internet ; ensuite tout fonctionne hors ligne.
