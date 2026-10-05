# 0010 — Données officielles du HCP et codes géographiques

- **Date** : 2026-10-05 · **Statut** : accepté

## Contexte
Les indicateurs démographiques, d'emploi et de services de base relèvent du recensement
(RGPH). Il fallait vérifier ce que le HCP publie réellement au niveau communal.

## Constat
- Le HCP publie la **population légale 2024** et **2014** en Excel, jusqu'aux arrondissements,
  avec le **code géographique officiel** et le **nom officiel en arabe**.
- La plateforme de diffusion des résultats 2024 (`resultats2024.rgphapps.ma`) expose
  publiquement des tables communales (démographie, activité, éducation, habitat).

## Choix
- Importeur `hcp_census` : télécharge et conserve les fichiers dans `data/raw/hcp/` et les
  réponses de la plateforme dans `data/raw/<territoire>/`, rattache chaque unité à sa ligne du
  HCP **par le nom, au sein de sa préfecture**, enregistre le code officiel, et remplace le nom
  arabe OSM par le nom officiel (réponse Q10). Le nom OSM est conservé (`source_meta`).
- 2014 : rattachement par la clé « province + cercle + commune » (7 chiffres), puis par le nom
  quand le découpage en cercles a changé (Shoul, Ameur).
- Correspondance indicateurs du HCP → variables MAJAL dans `config/mappings/hcp_rgph.yaml`.

## Conséquences
- Badge « Officiel » pour toutes ces valeurs ; score de fiabilité maximal pour les données 2024.
- Les codes officiels permettent de rattacher sans ambiguïté les futures données des partenaires.
