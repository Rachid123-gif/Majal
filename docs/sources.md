# Sources de données

Chaque source est vérifiée (existence, niveau de détail, date, licence) **avant** d'être
utilisée (BRIEF §10.1). Aucune donnée territoriale n'est encore importée : les premières arrivent à l'étape 1
(limites administratives, OpenStreetMap).

Régénérer le contour du Maroc : `scripts/build_morocco_outline.py` (instructions en tête du fichier).

| Donnée | Source | Producteur | Date | Licence | Niveau de détail | Badge | Statut |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Contour du Maroc (page vitrine) | Natural Earth 1:10m, pays, point de vue du Maroc (`ne_10m_admin_0_countries_mar`) | Natural Earth | v5.x, téléchargé le 2026-10-05 | Domaine public | Pays (simplifié) | Ouvert | Utilisé (illustration) |
| Limites administratives (Rabat-Salé-Skhirate-Témara) | OpenStreetMap, relations `boundary=administrative` (admin_level 5, 8, 10) via Overpass | Contributeurs OSM | Données du 2026-10-05 | ODbL 1.0 | Préfecture, commune, arrondissement | Ouvert (à vérifier) | Importé (24 unités d'analyse) |
| Équipements (Rabat) | OpenStreetMap via Overpass, catégories `config/mappings/osm_facilities.yaml` | Contributeurs OSM | Voir « données du » dans l'application | ODbL 1.0 | Point / polygone | Ouvert | Importé (≈ 2 500 objets) |
| Routes (Rabat) | OpenStreetMap via Overpass (motorway → track) | Contributeurs OSM | Idem | ODbL 1.0 | Tronçon | Ouvert | Importé (≈ 9 500 tronçons) |
| Fond de carte (Rabat) | Protomaps, construction du 2026-10-05, extrait z0-15 | Protomaps / contributeurs OSM | 2026-10-05 | ODbL 1.0 | Tuiles vectorielles | Ouvert | Téléchargé (11 Mo) |
| Polices et icônes du fond de carte | Protomaps basemaps-assets (Noto Sans) | Protomaps, Google Noto | 2026-10 | OFL 1.1 / BSD-3 | — | — | Téléchargé |
| Population légale 2024, ménages, codes géographiques et noms officiels (FR, AR) | HCP — fichier Excel de la population légale (décret n° 2.24.1009), https://www.hcp.ma/file/242341/ | HCP | 2024-11-07 | Publication officielle | Commune et arrondissement | Officiel | Importé (24/24 unités de Rabat) |
| Population légale 2014 | HCP — fichier Excel « Population légale … RGPH 2014 », https://www.hcp.ma/region-drda/attachment/565048/ | HCP | 2015 | Publication officielle | Commune et arrondissement | Officiel | Importé (rattachement par code, puis par nom si le code a changé) |
| Indicateurs communaux du RGPH 2024 (âge, chômage, activité des femmes, analphabétisme, eau, assainissement, électricité, logement sommaire, distance à la route goudronnée…) | HCP — plateforme de diffusion https://resultats2024.rgphapps.ma (tables publiques TAB_VF_*) ; liste dans `config/mappings/hcp_rgph.yaml` | HCP | 2024 | Publication officielle | Commune et arrondissement | Officiel | Importé (306 valeurs pour Rabat) |
| Population carroyée | JRC GHSL — GHS-POP R2023A, époque 2020, 3″ (≈ 90 m), tuile R6_C18 | Commission européenne (JRC) | 2023 | CC BY 4.0 | Cellule ≈ 90 m | Estimé | Importé (≈ 50 000 cellules, recalées sur la population légale 2024) |
| Surface bâtie 2015 et 2020 | JRC GHSL — GHS-BUILT-S R2023A, 3″ | Commission européenne (JRC) | 2023 | CC BY 4.0 | Cellule ≈ 90 m | Ouvert | Importé |
| Chiffres clés de la vitrine | Étude d'opportunité MAJAL (oct. 2026), citant Le Desk (Conseil des ministres du 9 avril 2026), FNH, Infomédiaire | Porteur du projet | Oct. 2026 | — | National | — | Utilisé, à valider (Q12) |

## Limites administratives — vérification du 2026-10-05 (étape 1.1)

| Source | Niveaux disponibles | Date | Licence | Verdict |
| --- | --- | --- | --- | --- |
| geoBoundaries (gbOpen MAR) | Pays, 12 régions, 75 préfectures et provinces | Données 2017 (dérivées d'OSM), MAJ 2023 | ODbL | Pas de communes ni d'arrondissements : insuffisant |
| HDX / OCHA COD-AB Maroc | Pays, 10 régions, 69 provinces | Limites de 2023, revues en déc. 2024 | CC BY-IGO | **Écarté** : 10 régions au lieu de 12 (régions du Sahara absentes), pas de communes |
| OpenStreetMap (relations `boundary=administrative`) | Régions (4), préfectures et provinces (5), cercles et pachaliks (6), caïdats (7), communes (8), arrondissements (10) | Données vivantes, extraites le 2026-10-05 | ODbL | **Retenu (proposition)**, badge « Ouvert », à vérifier par une source officielle |

### Contrôles effectués sur OpenStreetMap (agglomération Rabat-Salé-Skhirate-Témara)

- 3 préfectures, 18 communes, 10 arrondissements (5 à Rabat, 5 à Salé), tous avec nom arabe.
- Géométries valides. Les 10 communes de Skhirate-Témara totalisent exactement la surface de
  leur préfecture (1 077,6 km²). Les arrondissements couvrent 100 % de Salé et 99 % de Rabat
  (le 1 % restant correspond à l'enclave de Touarga).
- Points à vérifier : Sidi Bouknadel (2,1 km² seulement) ; aucun code officiel (codes HCP)
  dans OSM, donc rapprochement avec le recensement par le nom, à contrôler à l'étape 2.

### Tétouan (pour l'étape 6)

- Province de Tétouan : 22 communes dans OSM, avec nom arabe ; certaines orthographes arabes
  sont manifestement fautives (« ااخروب », « اابغغزة », « بن قريش ») : à corriger par une liste
  officielle (question Q10).
- 595 douars et hameaux sous forme de points (pas de contours) : utilisables pour localiser
  les contributions citoyennes, pas comme unités d'analyse surfaciques.

### Source officielle à demander

Limites et codes officiels des communes et arrondissements : agence urbaine, direction
régionale du HCP ou Géoportail national. À inscrire dans le module « Besoins en données ».
