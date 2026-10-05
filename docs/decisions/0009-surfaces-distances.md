# 0009 — Calcul des surfaces et des distances

- **Date** : 2026-10-05 · **Statut** : accepté

## Contexte
Le cahier des charges demande les géométries en EPSG:4326 et des calculs dans « une
projection métrique adaptée au Maroc ».

## Choix
Les surfaces et longueurs sont calculées par PostGIS sur l'**ellipsoïde WGS84** (type
`geography` : `ST_Area(geom::geography)`, `ST_Length(geom::geography)`), et non dans une
projection plane. C'est exact partout au Maroc, du nord (Tétouan) au sud, alors qu'une
projection conique locale (Merchich Nord Maroc, EPSG:26191, etc.) se déforme hors de sa zone.

## Conséquences
- Une seule méthode pour tous les territoires, sans paramètre à régler.
- Les surfaces affichées portent le badge « Estimé » (calculées par MAJAL à partir de limites
  non officielles).
- Pour les calculs d'accessibilité (étape 2), les distances utiliseront aussi `geography`
  (`ST_Distance`, `ST_DWithin`).
