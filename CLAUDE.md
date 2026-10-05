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
| `make start` / `make stop` | **Usage du porteur** : lance en arrière-plan (rebuild auto) et ouvre le navigateur / arrête |
| `make dev` | Lance au premier plan avec les logs → http://localhost:3000 (API : :8000) |
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
  - `app/api/` : `/health` (+ `/api/health`), `/api/territories`, `/api/auth/{login,logout,me}`.
  - `app/security.py` : comptes de démo (mots de passe dans `.env`), cookie de session signé
    `majal_session`, anti-force brute (décision 0005).
  - Dans Docker, `config/` est monté sur `/config` (= `REPO_ROOT/config`, car le code est sous `/app`).
- `frontend/` : Next.js 16 (App Router, voir `frontend/AGENTS.md` : lire la doc embarquée dans
  `node_modules/next/dist/docs/` avant d'écrire du code Next), Tailwind 4, Vitest.
  - i18n maison : `src/i18n/{fr,ar}.json` + `LocaleProvider` (bascule `dir="rtl"`).
  - Polices embarquées via `@fontsource/*` (aucun appel réseau : hors ligne).
  - Palette (BRIEF §13) en tokens Tailwind : `petrol`, `terracotta`, `cream`, `slate` (+ variantes).
  - Le navigateur ne parle qu'au frontend : `next.config.ts` relaie `/api/*` vers
    `BACKEND_INTERNAL_URL`. `src/proxy.ts` protège `/tableau-de-bord` et `/presentation`.
  - Pages : `/` vitrine publique (`components/landing/`, textes dans `src/content/`),
    `/connexion`, `/tableau-de-bord`, `/presentation` (`components/app/`).
  - `src/content/features.ts` = avancement réel des fonctionnalités (lu par la vitrine et le
    tableau de bord) : passer `status` à `available` quand une étape est livrée, et remplacer la
    maquette correspondante (`Mockups.tsx`) par une vraie capture.
  - Animations : `components/motion/`, toutes coupées par `prefers-reduced-motion`.
  - Carte du Maroc : `src/content/morocco-outline.json`, généré par
    `scripts/build_morocco_outline.py` (Natural Earth, point de vue du Maroc : Sahara inclus).

## État d'avancement

- Étape 0 — validée le 2026-10-05.
- Étape 0 bis (vitrine + connexion) — livrée le 2026-10-05, en attente de validation.
  Vitrine sans aucun logo d'institution, partenaire ni témoignage (aucun partenariat ne doit être
  suggéré). Chiffres uniquement issus de l'étude d'opportunité, avec leur source.
- Publication future de la vitrine seule : décision 0006 (non réalisée).
- Note machine : la CLI Docker est dans `~/.docker/bin` (ajouté au PATH par `~/.zprofile`).
- Décisions prises : périmètre Rabat par défaut = agglomération Rabat-Salé-Skhirate-Témara ;
  unité fine Rabat = carreaux 500 m ; Tétouan = province seule, douars sinon carreaux 1 km.
