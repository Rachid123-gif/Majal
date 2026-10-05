# 0007 — Données OpenStreetMap via Overpass, avec cache local

- **Date** : 2026-10-05 · **Statut** : accepté

## Contexte
Le cahier des charges prévoyait un extrait OpenStreetMap du Maroc. Il faut des limites
administratives (relations), des équipements et des routes pour quelques préfectures ou
provinces, de façon reproductible et utilisable hors ligne.

## Options
1. Extrait complet du Maroc (Geofabrik, plusieurs centaines de Mo) traité avec osmium.
2. Requêtes ciblées à l'API Overpass, réponses conservées dans `data/raw/<territoire>/`.

## Choix
Option 2. Pour chaque territoire, trois requêtes ciblées (limites, équipements, routes).
Chaque réponse est enregistrée avec la requête, la date de téléchargement et la date des
données OSM servies (`timestamp_osm_base`), qui est affichée comme « données du … ».
- Limites : requête par zone administrative, puis filtrage géométrique (on écarte les unités
  voisines qui ne font que toucher la frontière).
- Équipements et routes : requête par rectangle englobant (beaucoup plus rapide), puis
  découpage en base sur les unités du territoire.
- Plusieurs serveurs Overpass publics sont essayés à tour de rôle (le principal est souvent
  saturé), avec de nouvelles tentatives espacées.
- Les catégories d'équipements sont définies dans `config/mappings/osm_facilities.yaml`
  (modifiable par le référent, `TODO_REFERENT`).

## Conséquences
- `make data` est rejouable hors ligne à partir du cache ; `REFRESH=1 make data` retélécharge.
- Selon le serveur qui répond, la date des données peut différer de quelques semaines entre
  deux sources : chaque source affiche sa propre date.
- Pour la version pilote (données officielles), un importeur par source officielle s'ajoutera
  au même mécanisme (`sources` du fichier de territoire).
