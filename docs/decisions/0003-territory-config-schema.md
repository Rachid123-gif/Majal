# 0003 — Schéma des fichiers de territoire

- **Date** : 2026-10-05 · **Statut** : accepté

## Contexte
Ajouter un territoire doit se faire par configuration uniquement (BRIEF §5). À Rabat, il faut
un périmètre élargi (agglomération) en plus de la préfecture.

## Choix
- Un fichier `config/territories/<code>.yaml` par territoire, validé par un schéma Pydantic
  strict (`backend/app/config_loader/territory.py`). Tout champ inconnu est refusé (pour
  attraper les fautes de frappe).
- Une liste générique de **périmètres** (`scopes`), avec un seul périmètre par défaut, au lieu
  d'un champ propre à Rabat. Chaque périmètre décrit les unités administratives qui le
  composent (`members`) ; les importeurs s'en servent pour filtrer les sources.
- Le `code` doit être identique au nom du fichier, ce qui garantit l'unicité.
- Les libellés arabes doivent contenir des caractères arabes.
- Les codes officiels, les limites et le milieu (urbain ou rural) ne sont **jamais** saisis
  dans ces fichiers : ils viennent des imports de sources réelles.
- Les erreurs sont rédigées en français, avec le fichier, la ligne, le champ, le problème et un
  exemple correct. Toutes les erreurs de tous les fichiers sont signalées en une fois.

## Conséquences
- Le mécanisme de validation (`load_model`) sera réutilisé pour la grille d'indicateurs, les
  taxonomies et les plans de rapport.
- Les paramètres propres à chaque importeur (`sources`) sont validés par l'importeur lui-même
  (étape 1).
