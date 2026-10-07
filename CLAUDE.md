# CLAUDE.md — MAJAL

Copilote IA d'intelligence territoriale : démonstrateur sur deux territoires (Rabat, profil
`urbain` ; Tétouan, profil `mixte`). La spécification complète et faisant foi est
[docs/BRIEF.md](docs/BRIEF.md) — la relire avant toute étape.

## Règles absolues (BRIEF §19)

- **Intégrité territoriale du Royaume du Maroc — principe non négociable.** Toute carte (application,
  vitrine, images exportées, cartes des rapports Word et PDF, et toute carte future) représente le
  Maroc dans son intégralité, provinces du Sud comprises, conformément à la cartographie officielle
  marocaine : aucune limite contestée (« disputed ») ni limite de pays ou de région séparant les
  provinces du Sud, aucune étiquette les désignant comme un territoire distinct (FR, AR, amazighe).
  Règles d'affichage : `frontend/src/content/cartography-rules.json`, appliquées par
  `frontend/src/lib/basemapStyle.ts` (ne jamais utiliser `layers()` de Protomaps sans ce filtre) ;
  contour du Royaume : Natural Earth « point de vue du Maroc » (`scripts/build_morocco_outline.py`
  → `data/reference/maroc-natural-earth-pov.geojson`, `frontend/src/content/maroc-contour.json`,
  `morocco-outline.json`). Tests qui doivent rester verts : `frontend/src/lib/basemapStyle.test.ts`,
  `backend/tests/test_cartography.py` (décode les vraies tuiles). Les données sources ne sont pas
  modifiées, seulement leur affichage. Décision 0013.

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
| `make check-config` | Valide `config/territories/*.yaml` et les correspondances, erreurs en français |
| `make data` | Imports (limites, recensement HCP, équipements, routes, grilles GHSL) depuis le cache `data/raw/`, fond de carte, puis indicateurs ; `REFRESH=1` retélécharge |
| `make indicators` | Recalcule le diagnostic (`python -m app.services.indicators compute`) |
| `make backup` / `make restore FILE=…` | Sauvegarde / restauration de la base |

## Architecture

- `backend/` : Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2, géré par **uv**
  (`uv.lock` versionné). Base PostgreSQL 16 + PostGIS + pgvector (`docker/db/`).
  - `app/config_loader/` : lecture YAML avec numéros de ligne, validation Pydantic générique
    (`load_model`) réutilisable pour les grilles, taxonomies et plans de rapport.
  - `app/api/` : `/health` (+ `/api/health`), `/api/territories`, `/api/auth/{login,logout,me}`.
  - `app/api/maps.py` : tuiles du fond de carte (`/api/tiles/<code>/…`, sans connexion),
    unités et équipements en GeoJSON (`/api/territories/<code>/units|facilities`, connexion requise).
  - `app/ingestion/` : `python -m app.ingestion run|bbox|basemaps`. Importeurs déclarés dans
    `sources` du fichier de territoire (`osm_boundaries`, `osm_facilities`, `osm_roads`,
    `basemap_pmtiles` géré par `scripts/fetch_basemap.sh`). Idempotents (upsert par
    `(study_area_id, external_id)` + suppression des disparus), journalisés dans `import_runs`.
    `boundaries.assemble_units` est pur (testé sans base). Overpass : cache + rotation de serveurs.
  - Modèles : `data_sources`, `study_areas`, `territories` (MultiPolygon 4326, `is_analysis_unit`,
    `scopes` JSONB), `facilities`, `roads`, `import_runs` (migration 0002). Surfaces et
    longueurs sur l'ellipsoïde (`::geography`, décision 0009).
  - Importeurs étape 2 : `hcp_census` (population légale 2014/2024 Excel + plateforme
    resultats2024.rgphapps.ma → `raw_variables`, codes officiels, noms arabes officiels) et
    `ghsl_grids` (population carroyée recalée sur le HCP → `population_cells`, bâti 2015/2020).
  - Méthode (étape 2) : `config/indicators/grille-v0.yaml`, `evaluation.yaml`,
    `config/confidence.yaml`, `config/mappings/hcp_rgph.yaml` ; schémas dans
    `app/config_loader/indicators.py`. Source : `docs/methodologie-v0.md` (grille v0, réponses
    provisoires Q6-Q15). Ne rien coder en dur ; normes = `TODO_REFERENT`.
  - Moteur : `app/services/indicators/engine.py` (formules, badge = entrée la moins fiable,
    fiabilité, référence = moyenne pondérée par la population du périmètre par défaut, statuts,
    rangs) + `spatial.py` (PostGIS). Diagnostics versionnés (`diagnostics`, `indicator_values`,
    migration 0003) ; `/api/territories/<code>/diagnostic` recalcule si l'empreinte des fichiers
    de méthode change. `quality_flags` du territoire (Sidi Bouknadel) : spatial non évaluable,
    exclu des classements.
  - Tests de base de données (`tests/test_ingestion_db.py`) ignorés si PostGIS est absent (CI).
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
  - Carte : vue de départ cadrée sur le territoire étudié (bouton « Recentrer »), vue nationale en
    dézoomant (fond national `data/tiles/maroc.pmtiles`, z0-7, servi en repli par l'API des tuiles).
  - Carte du territoire : `/territoire/[code]` (`components/app/TerritoryMapView.tsx`,
    `TerritoryMap.tsx` avec MapLibre 6 + `@protomaps/basemaps`). Worker MapLibre servi par
    `src/app/maplibre/[file]/route.ts`. Polices/icônes du fond : `public/basemap/`.
  - Étape 2 : carte colorée par indicateur (valeur en quantiles YlGnBu ou évaluation),
    fiche `/territoire/[code]/unite/[id]` (`UnitSheetView`), comparaison
    `/territoire/[code]/comparer?ids=` (`CompareView`, CSV + PNG). Bandeau obligatoire
    « Grille v0 — proposition en cours de validation » + libellé d'évaluation relative
    (`GridBanner`). Statuts : `StatusChip` (couleur + symbole + texte).
  - Badges de confiance : `components/app/ConfidenceBadge.tsx` (texte + symbole, jamais la
    couleur seule).
  - Carte du Maroc : `src/content/morocco-outline.json`, généré par
    `scripts/build_morocco_outline.py` (Natural Earth, point de vue du Maroc : Sahara inclus).

## État d'avancement

- Étape 0 — validée le 2026-10-05.
- Étape 0 bis (vitrine + connexion) — validée le 2026-10-05 (l'utilisateur a lancé l'étape 1).
- Étape 1 (Rabat : territoire réel et carte) — validée le 2026-10-05.
- Étape 2 (indicateurs, fiche, comparaison) — validée le 2026-10-05.
  Données officielles HCP trouvées au niveau des arrondissements. Points ouverts : Q13, Q16-Q20.
  Typologie des communes (méthodologie §5) : à faire pendant l'étape 3, présentée comme « proposition ».
- Engagement (Q20) : remplacer les distances à vol d'oiseau par des distances le long des rues
  (réseau OSM) au plus tard à l'étape 7.
- Étape 3 (rapport IA) — plan validé le 2026-10-05 : IA locale Ollama sur le Mac (hors Docker,
  `host.docker.internal:11434`), SOVEREIGN_MODE=true par défaut (aucun appel extérieur pendant
  l'utilisation ; `make data` reste une commande d'administration), fournisseur Anthropic codé mais
  désactivé, secours sans IA (textes à trous), anti-invention obligatoire, cache + `make reports`,
  exports FR (Word, PDF) ; exports arabes RTL à l'étape 7.
  Code : `backend/app/services/llm/` (fournisseurs, garde souveraine dans `get_provider`),
  `backend/app/services/reports/` (facts → writer → numbers → generate ; export, maps, jobs,
  benchmark, `__main__` pour `make reports`), plan du rapport
  `config/report_templates/diagnostic_commune.yaml`, typologie `config/indicators/typologie.yaml`.
  Interface : `frontend/src/components/app/ReportPanel.tsx` (sur la fiche d'unité).
  Le modèle ne voit que des identifiants de faits `{{F012}}` ; jamais de chiffre écrit par l'IA.
  Modèle : qwen3:8b par défaut, gemma3:4b en repli (choix du porteur, 2026-10-05).
  Contrôles du sens (`meaning.py` + `config/report_templates/controles.yaml`) : tendances,
  données manquantes, fausse absence, statuts, jugements subjectifs, nombres collés en arabe —
  à garder verts (`tests/test_meaning.py`). `make reports` recontrôle les rapports existants et
  ne réécrit que ceux qui échouent.
- Étape 3 — validée le 2026-10-06. `make start` lance `caffeinate` (Mac éveillé, 12 h au plus),
  arrêté par `make stop`. Démonstration : `docs/demo-rapide.md`.
  Banc d'essai : `docs/benchmarks/` ; décisions 0014-0016.
- Étape 4 (écoute citoyenne, Rabat) — plan validé le 2026-10-06 ; 4.1 validé avec ajustements.
  Jeu fictif : `data/fictif/rabat/contributions.yaml` (plan neutre `scripts/plan_fictional_contributions.py`,
  poids `config/citizens/jeu-fictif.yaml`, termes interdits `config/citizens/termes-interdits.yaml`,
  méthode `docs/citoyens-jeu-fictif.md`). L'échantillon de référence (30 contributions remises au
  professeur, `docs/evaluation/annotation-professeur.xlsx`) n'est jamais régénéré ; amazighe exclu
  de l'évaluation de référence. Taxonomie `config/taxonomy/urbain.yaml` : `data_request` des thèmes
  sans indicateur = entrées du futur module « Besoins en données » (étape 5). Bandeau obligatoire
  « Contributions fictives — illustration du fonctionnement de l'outil… » partout (tableau de bord,
  fiche, croisement, section 7 des rapports, exports). Tout résultat d'anonymisation ou
  d'évaluation affiché précise sa base de mesure (ex. « 100 % sur le jeu de test fictif
  (22 pièges) »). 4.2 (anonymisation, `app/services/citizens/anonymize.py`) validé le 2026-10-06.
  4.3 à 4.6 validés le 2026-10-06 (analyse, tableau de bord, croisement, section 7) ; 400
  contributions fictives ; échelle « commune » ; décision 0017 (compléments).
  `make citizens` = import + analyse + évaluation (`docs/evaluation/resultats.md`).
  Croisement (`stats.crossing`) : libellé = statut réel (« déficit marqué » / « à surveiller »),
  « sans demande exprimée » seulement à partir de 30 contributions dans l'unité.
  File de validation (`app/services/citizens/review.py`, écran `/territoire/<code>/citoyens/verifier`,
  professeur et admin) : la correction humaine remplace la proposition partout (champs themes /
  tonality / territory_id), proposition conservée dans `ai_proposal` (migration 0007), jamais
  écrasée par une nouvelle analyse ; évaluation humaine comptée à part. L'évaluation par Claude
  (xlsx, onglet « Annotateur ») = « second modèle d'IA », jamais « de référence » avant relecture.
- Étape 4 — validée le 2026-10-07.
- Étape 5 (besoins en données, Rabat) — validée le 2026-10-07 ; décision 0018. Référentiel
  `config/data_holders/rabat.yaml` (18 institutions, 24 demandes, intitulés et titres des
  destinataires « à vérifier »), règles `config/data_holders/regles.yaml` (priorité calculée,
  classement, trois effets calculer / fiabiliser / affiner, statuts), code
  `backend/app/services/data_needs/` (priority, completeness, notes, excel, `__main__`), API
  `app/api/data_needs.py`, suivi en base (migration 0008), écran
  `/territoire/<code>/besoins-donnees` (`DataNeedsView`, `DataNeedsSimulator`, aussi dans le mode
  présentation), notes `config/report_templates/note_demande.yaml` → `make notes`
  (`docs/notes-demande/<code>/`). Kit du professeur : `docs/kit-professeur/`. Assistant
  documentaire reporté après Tétouan.
- Mode présentation — avancé avant Tétouan à la demande du porteur, livré le 2026-10-07 ;
  décision 0019. Scénario `config/presentation/<code>.yaml` (9 étapes), API
  `app/api/presentation.py`, `PresentationView` (diapositives = vrais écrans en contexte
  « intégré », `components/app/Embedded.tsx`), préchargement hors ligne. Arabe plus tard.
  Prochaine : étape 6 (Tétouan) — plan présenté, réponses du porteur attendues.
- Publication future de la vitrine seule : décision 0006 (non réalisée).
- Note machine : la CLI Docker est dans `~/.docker/bin` (ajouté au PATH par `~/.zprofile`).
- Décisions prises : périmètre Rabat par défaut = agglomération Rabat-Salé-Skhirate-Témara ;
  unité fine Rabat = carreaux 500 m ; Tétouan = province seule, douars sinon carreaux 1 km.
