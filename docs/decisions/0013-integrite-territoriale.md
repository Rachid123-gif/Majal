# 0013 — Intégrité territoriale du Royaume du Maroc sur toutes les cartes

- **Date** : 2026-10-05 · **Statut** : accepté — principe non négociable

## Contexte
Le fond de carte (Protomaps, données OpenStreetMap et Natural Earth) dessinait en pointillés des
limites marquées « contestées », dont une ligne séparant le Maroc de ses provinces du Sud. C'est
inacceptable pour un outil destiné aux institutions marocaines.

## Choix
- **Affichage filtré, données intactes** : seules les frontières d'État non contestées du fond de
  carte sont affichées. Les limites `disputed`, `unrecognized_country`, et toutes les limites
  infra-nationales du fond (régions, macro-régions) sont masquées. Les étiquettes qui
  désigneraient les provinces du Sud comme un territoire distinct sont masquées, en toutes langues.
  Règles : `frontend/src/content/cartography-rules.json` ; style : `frontend/src/lib/basemapStyle.ts`.
- **Contour du Royaume dessiné par MAJAL** : Natural Earth, version « point de vue du Maroc »
  (provinces du Sud comprises), affiché au-dessus du fond de carte jusqu'au zoom 10. C'est le même
  contour que la carte animée de la vitrine.
- **Vue nationale** : fond national du Royaume (`data/tiles/maroc.pmtiles`, zoom 0 à 7), servi en
  repli par l'API des tuiles quand on dézoome au-delà du territoire étudié.
- **Images exportées** : elles reprennent le rendu de la carte, donc les mêmes règles. Les cartes
  des futurs rapports Word et PDF devront être produites à partir du même style.

## Garde-fous automatiques
- `frontend/src/lib/basemapStyle.test.ts` : une seule couche de limites, filtrée ; une limite
  contestée ou non reconnue n'est jamais affichée ; les étiquettes non conformes sont masquées.
- `backend/tests/test_cartography.py` : décode les vraies tuiles et échoue si une limite laissée
  visible traverse l'intérieur du Royaume ; vérifie que la ligne contestée existe bien dans les
  tuiles nationales (le test a donc un sens) et que le contour de référence inclut Laâyoune et
  Aousserd.

## Limite connue
Entre les zooms 8 et 15, le fond de carte détaillé ne couvre que l'emprise du territoire étudié :
en se déplaçant loin de celui-ci à ces zooms, le fond apparaît vide (aucune limite n'y est
dessinée).
