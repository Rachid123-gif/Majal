# CLAUDE.md — MAJAL

Copilote IA d'intelligence territoriale : démonstrateur sur deux territoires (Rabat, profil
`urbain` ; Tétouan, profil `mixte`). La spécification complète et faisant foi est
[docs/BRIEF.md](docs/BRIEF.md) — la relire avant toute étape.

## Règles absolues (BRIEF §19)

- Ne jamais inventer une statistique, une commune, un code officiel, une limite, une norme ou
  une source. Valeur introuvable → « non disponible » (jamais 0).
- Chaque valeur porte source, date et badge : Officiel / Ouvert / Estimé / Fictif.
- Le LLM n'écrit jamais un nombre : il cite des faits `{{F012}}` (BRIEF §9.5).
- Rien de ce qui relève du référent (indicateurs, normes, seuils, thèmes, plans de rapport,
  périmètres) n'est codé en dur : tout est dans `config/*.yaml`, marqué `TODO_REFERENT` tant
  que non validé.
- Ajouter un territoire = un fichier `config/territories/<code>.yaml` + imports, zéro
  changement de logique métier.
- Aucune donnée personnelle vers un service externe ; secrets uniquement dans `.env`.
- Ne pas passer à l'étape suivante sans validation explicite du porteur du projet.

## Conventions

- Réponses au porteur du projet en **français**, simples, avec les commandes exactes.
- Code, identifiants, commits en **anglais**. Interface en français et en arabe (RTL).
- Messages d'erreur de configuration en français, pour un lecteur non développeur
  (fichier, ligne, champ, problème, exemple correct) : `app/config_loader/validation.py`.
- Choix technique structurant → note dans `docs/decisions/NNNN-titre.md`.
- Question de méthode → `docs/questions-referent.md`.
- Pousser sur `origin/main` à la fin de chaque étape.

## Commandes

| Commande | Effet |
| --- | --- |
| `make setup` | Première installation Docker (images, base, migrations) |
| `make dev` | Lance tout dans Docker → http://localhost:3000 (API : :8000) |
| `make setup-local` / `make dev-local` | Sans Docker (uv + npm), sans base de données |
| `make test` | pytest + vitest (dans Docker si présent, sinon en local) |
| `make lint` | ruff, ruff format, mypy strict, eslint, prettier, tsc |
| `make check-config` | Valide `config/territories/*.yaml`, erreurs en français |
| `make backup` / `make restore FILE=…` | Sauvegarde / restauration de la base |

## Architecture

- `backend/` : Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, géré par **uv**
  (`uv.lock` versionné). Base PostgreSQL 16 + PostGIS + pgvector (`docker/db/`).
  - `app/config_loader/` : lecture YAML avec numéros de ligne, validation Pydantic générique
    (`load_model`) réutilisable pour les grilles, taxonomies et plans de rapport.
  - `app/api/` : `/health` (état base + config), `/api/territories`.
  - Dans Docker, `config/` est monté sur `/config` (= `REPO_ROOT/config`, car le code est sous `/app`).
- `frontend/` : Next.js 16 (App Router, voir `frontend/AGENTS.md` : lire la doc embarquée dans
  `node_modules/next/dist/docs/` avant d'écrire du code Next), Tailwind 4, Vitest.
  - i18n maison : `src/i18n/{fr,ar}.json` + `LocaleProvider` (bascule `dir="rtl"`).
  - Polices embarquées via `@fontsource/*` (aucun appel réseau : hors ligne).
  - Palette (BRIEF §13) en tokens Tailwind : `petrol`, `terracotta`, `cream`, `slate`.

## État d'avancement

- Étape 0 — en cours (2026-10-05) : tout ce qui ne demande pas Docker est fait et testé.
  Reste, une fois Docker installé : `make setup`, `make dev`, vérification base (PostGIS,
  pgvector) via `/health`, `make test` dans Docker.
- Décisions prises : périmètre Rabat par défaut = agglomération Rabat-Salé-Skhirate-Témara ;
  unité fine Rabat = carreaux 500 m ; Tétouan = province seule, douars sinon carreaux 1 km.
