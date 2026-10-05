# 0002 — Gestion de Python avec uv

- **Date** : 2026-10-05 · **Statut** : accepté

## Contexte
La machine n'a que Python 3.9 (système). Le backend exige Python 3.12. Il faut des dépendances
épinglées (BRIEF §14).

## Choix
`uv` gère la version de Python (3.12), l'environnement virtuel et le fichier de verrouillage
`backend/uv.lock` (versionné). La même commande `uv sync --frozen` sert dans Docker, dans
l'intégration continue et en local.

## Conséquences
- Installations reproductibles : chaque version de dépendance est fixée par `uv.lock`.
- Python système non modifié.
- Audit des vulnérabilités : `uv export` puis `pip-audit` dans l'intégration continue.
