# 0008 — Fond de carte hors ligne

- **Date** : 2026-10-05 · **Statut** : accepté

## Choix
- **Tuiles** : extrait de la construction quotidienne Protomaps (données OpenStreetMap,
  ODbL), découpé sur l'emprise du territoire jusqu'au zoom 15 avec l'outil `go-pmtiles`
  (image Docker officielle), stocké dans `data/tiles/<territoire>.pmtiles` (≈ 11 Mo pour
  l'agglomération de Rabat). Script : `scripts/fetch_basemap.sh`, appelé par `make data`.
- **Service** : le backend lit le fichier PMTiles et sert des tuiles classiques
  `/api/tiles/<territoire>/{z}/{x}/{y}.mvt` (relayées par Next.js), sans module PMTiles
  côté navigateur.
- **Style** : `@protomaps/basemaps` (variante claire, teintée aux couleurs MAJAL), libellés
  en français ou en arabe selon la langue de l'interface. Polices (Noto Sans, plages latines
  et arabes) et icônes stockées dans `frontend/public/basemap/` (3,2 Mo) :
  `scripts/fetch_basemap_assets.py`.
- **MapLibre** : le module de calcul (« worker ») est servi par la route
  `/maplibre/[file]` directement depuis le paquet installé. MapLibre 6 affiche l'arabe de
  droite à gauche sans extension.

## Conséquences
- Aucune requête vers internet pendant l'utilisation (vérifié : toutes les ressources
  viennent de `localhost`).
- Les caractères tifinagh présents dans certains noms OSM n'ont pas de police locale : ils
  peuvent ne pas s'afficher sur le fond de carte.
