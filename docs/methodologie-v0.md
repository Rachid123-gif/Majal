# MAJAL — Positions méthodologiques provisoires (v0)

**Statut : proposition de travail, à valider par le référent scientifique.**
Ces positions permettent d'avancer le démonstrateur. Elles s'appuient sur des pratiques courantes en urbanisme et sur des références publiques. Elles n'inventent aucune norme marocaine : quand une norme officielle existe mais n'est pas encore connue, elle reste marquée `TODO_REFERENT`.

À placer dans le projet sous `docs/methodologie-v0.md`. Dans l'interface, la grille s'affiche « Grille v0 — proposition en cours de validation ».

---

## 1. Principe d'organisation de la grille

La grille est organisée selon les **priorités des programmes de développement territorial intégré** : emploi, services sociaux de base (éducation, santé), gestion de l'eau, mise à niveau territoriale. C'est le langage des décideurs à qui le démonstrateur s'adresse : chaque indicateur doit pouvoir se rattacher à l'un de ces axes.

Huit axes :

1. Démographie et dynamiques (contexte)
2. Emploi et inclusion
3. Éducation
4. Santé
5. Eau, assainissement et services de base
6. Mobilité et accessibilité
7. Cadre de vie et environnement
8. Dynamique urbaine et foncière

## 2. Règle d'évaluation en l'absence de norme officielle

Tant que les normes officielles (grilles normatives d'équipements, normes sectorielles) ne sont pas fournies, MAJAL n'affiche **aucun jugement absolu**. Il applique une **évaluation relative**, transparente et réversible :

- **Référence** : moyenne pondérée par la population de l'ensemble étudié (agglomération Rabat-Salé-Skhirate-Témara, ou province de Tétouan).
- **Statut « déficit marqué »** : valeur inférieure à 80 % de la référence (ou supérieure à 120 % pour un indicateur où « moins = mieux »).
- **Statut « à surveiller »** : entre 80 % et 95 % (ou 105 % et 120 %).
- **Statut « dans la moyenne ou au-dessus »** : sinon.
- Libellé obligatoire dans l'interface et les rapports : « Évaluation relative à la moyenne de l'agglomération — norme officielle non encore intégrée ».
- Dès qu'une norme est fournie, elle remplace la référence relative pour l'indicateur concerné (champ `norm` du YAML).

Les seuils de 80 % et 95 % sont des paramètres modifiables (`config/indicators/evaluation.yaml`).

## 3. Grille v0

Légende des profils : **U** = urbain (Rabat), **M** = mixte (Tétouan). Source : **O** officielle, **Ou** ouverte, **E** estimée.

| Code | Axe | Indicateur | Calcul | Sens | Profils | Source attendue | Référence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEM_POP | 1 | Population 2024 | brut | neutre | U, M | HCP, RGPH 2024 (O) | — |
| DEM_TCAM | 1 | Croissance annuelle moyenne 2014-2024 | taux annuel moyen | neutre | U, M | HCP, RGPH 2014 et 2024 (O) | — |
| DEM_DENS | 1 | Densité de population | hab. / km² | neutre | U, M | HCP + limites (O/Ou) | — |
| DEM_JEUNES | 1 | Part des moins de 15 ans | % | neutre | U, M | HCP (O) | — |
| DEM_AGES | 1 | Part des 60 ans et plus | % | neutre | U, M | HCP (O) | — |
| EMP_CHOM | 2 | Taux de chômage | % | moins = mieux | U, M | HCP (O) | relative |
| EMP_ACTF | 2 | Taux d'activité des femmes | % | plus = mieux | U, M | HCP (O) | relative |
| EMP_ANALPH | 2 | Taux d'analphabétisme (10 ans et plus) | % | moins = mieux | U, M | HCP (O) | relative |
| EDU_ECOLES | 3 | Établissements d'enseignement primaire et collégial pour 1 000 enfants de 6 à 14 ans | ratio | plus = mieux | U, M | Délégation de l'Éducation (O) ; OpenStreetMap (Ou, provisoire) | `TODO_REFERENT` (grille normative) |
| EDU_PROX | 3 | Part de la population à moins de 1 km d'une école primaire | % | plus = mieux | U, M | OSM + population carroyée (E) | 1 km : distance de marche courante pour l'école primaire, à confirmer |
| SAN_ESSP | 4 | Établissements de soins de santé primaires pour 10 000 habitants | ratio | plus = mieux | U, M | Délégation de la Santé (O) ; OSM (Ou, provisoire) | `TODO_REFERENT` |
| SAN_PROX | 4 | Part de la population à moins de 2 km d'un établissement de soins primaires | % | plus = mieux | U | OSM + population carroyée (E) | relative |
| SAN_HOP | 4 | Distance moyenne à l'hôpital le plus proche | km | moins = mieux | U, M | OSM (Ou) | relative |
| EAU_RES | 5 | Logements raccordés au réseau d'eau potable | % | plus = mieux | U, M | HCP, RGPH logement (O) | relative |
| EAU_ASS | 5 | Logements raccordés à l'assainissement | % | plus = mieux | U, M | HCP (O) | relative |
| EAU_ELEC | 5 | Logements raccordés à l'électricité | % | plus = mieux | M | HCP (O) | relative |
| LOG_PREC | 5 | Part des logements sommaires ou précaires | % | moins = mieux | U, M | HCP (O) | relative |
| MOB_TC | 6 | Part de la population à moins de 500 m d'un arrêt de bus ou de tramway | % | plus = mieux | U | OSM + population carroyée (E) | 500 m : seuil de planification courant pour l'accès à pied aux transports collectifs |
| MOB_TRAM | 6 | Part de la population à moins de 500 m d'une station de tramway | % | plus = mieux | U | OSM + population carroyée (E) | idem |
| MOB_15MIN | 6 | Part de la population ayant école primaire, soins de santé primaires et marché à moins de 1 km | % | plus = mieux | U | OSM + population carroyée (E) | concept de « ville du quart d'heure » (1 km ≈ 15 min de marche) |
| MOB_ROUTE | 6 | Distance moyenne de la population à une route revêtue | km | moins = mieux | M | OSM (Ou) + population carroyée (E) | relative |
| MOB_CHEF | 6 | Temps d'accès estimé au chef-lieu de province | minutes | moins = mieux | M | réseau OSM (E) | relative |
| ENV_VERT | 7 | Espaces verts publics par habitant | m² / hab. | plus = mieux | U | OSM (Ou) | relative ; `TODO_REFERENT` pour une norme nationale |
| ENV_VERT300 | 7 | Part de la population à moins de 300 m d'un espace vert public d'au moins 0,5 ha | % | plus = mieux | U | OSM + population carroyée (E) | recommandation de l'OMS Europe (2016) sur l'accès aux espaces verts urbains |
| URB_BATI | 8 | Surface bâtie | km² et % du territoire | neutre | U, M | couche satellite de bâti (Ou) | — |
| URB_CROIS | 8 | Croissance de la surface bâtie entre deux dates | % | neutre | U, M | couche satellite de bâti (Ou) | — |
| URB_CONSO | 8 | Surface bâtie supplémentaire par habitant supplémentaire | m² / nouvel habitant | moins = mieux | U, M | bâti (Ou) + HCP (O) | relative ; indicateur clé de l'étalement urbain |
| URB_DOC | 8 | Couverture par un document d'urbanisme homologué | oui / partiel / non | plus = mieux | U, M | agence urbaine (O) | à demander |

**Notes de méthode**

- Les indicateurs « part de la population à moins de… » reposent sur une répartition de la population à l'intérieur des communes (population carroyée). Ils sont donc **estimés** et l'interface le dit.
- Les écoles et établissements de santé d'OpenStreetMap sont **incomplets et mêlent public et privé**. Les indicateurs correspondants portent le badge « Ouvert, provisoire » et figurent en tête des besoins en données (délégations de l'Éducation et de la Santé).
- `URB_CONSO` est l'indicateur le plus parlant pour un urbaniste : il mesure si la croissance se fait par densification ou par étalement. À mettre en avant dans la démonstration.

## 4. Réponses aux questions ouvertes

**Q6 — Périmètre de Rabat.** Agglomération Rabat-Salé-Skhirate-Témara en vue principale ; préfecture de Rabat en filtre. C'est l'échelle pertinente pour la mobilité, l'emploi et le foncier.

**Q7 — Unité fine.** Carreaux de 500 m pour les cartes et les calculs d'accessibilité. Les quartiers OpenStreetMap servent seulement au repérage des lieux cités.

**Q8 — Périmètre de Tétouan.** Province de Tétouan seule pour le démonstrateur. M'diq-Fnideq pourra être ajoutée plus tard comme preuve d'extension.

**Q9 — Grille et normes.** Grille v0 ci-dessus, avec évaluation relative (section 2). Aucune norme inventée. Le professeur fournira les références normatives officielles qu'il connaît (grilles d'équipements, normes sectorielles), qui remplaceront la référence relative.

**Q10 — Noms officiels en arabe.** Source de référence : la nomenclature officielle des collectivités territoriales publiée par le HCP ou le ministère de l'Intérieur. En attendant : nom arabe d'OpenStreetMap, marqué « à vérifier ».

**Q11 — Relecture des textes arabes.** Faite par le professeur ou par une personne arabophone de son équipe avant toute démonstration en arabe.

**Q12 — Chiffres de la vitrine.** N'utiliser que des chiffres sourcés : environ 210 milliards de dirhams sur 8 ans pour la nouvelle génération de programmes de développement territorial intégré (Conseil des ministres du 9 avril 2026) ; concertations dans les 75 provinces et préfectures ; 12 régions. Chaque chiffre affiche sa source.

**Q14 — Catégories d'équipements.**

| Catégorie | Retenu dans les indicateurs | Remarque |
| --- | --- | --- |
| Écoles primaires, collèges, lycées | oui | public et privé confondus dans OSM : le signaler |
| Enseignement supérieur | couche seulement | hors indicateurs de proximité |
| Soins de santé primaires (centres de santé, dispensaires) | oui | |
| Hôpitaux | oui | distance moyenne |
| Cliniques privées, pharmacies | couche seulement | |
| Parcs et jardins **publics** | oui | exclure les jardins privés ; seuil de 0,5 ha pour ENV_VERT300 |
| Places et esplanades | couche seulement | |
| Marchés municipaux | oui | pour MOB_15MIN |
| Équipements sportifs de proximité, maisons de jeunes, bibliothèques | couche seulement en v0 | indicateurs possibles en v1 |
| Administrations de proximité (annexes, arrondissements, poste) | couche seulement | |
| Arrêts de bus, stations de tramway, gares | oui | |
| Lieux de culte | non | hors du champ du diagnostic |

**Q15 — Sidi Bouknadel.** Limite manifestement incomplète dans OpenStreetMap. Ne pas corriger à la main. Avertissement affiché, commune exclue des classements, limite officielle ajoutée aux besoins en données.

## 5. Typologie des communes

Proposition de 4 profils, calculés automatiquement puis nommés à la main après lecture des résultats :

- centres consolidés (forte densité, bon niveau d'équipement) ;
- quartiers en déficit d'équipements (forte densité, faible accès) ;
- fronts d'urbanisation (forte croissance du bâti, équipements en retard) ;
- espaces périurbains ou ruraux (faible densité, accessibilité faible).

Méthode : regroupement simple sur 6 à 8 indicateurs standardisés, avec une explication en clair de ce qui caractérise chaque profil.

## 6. Ce que le professeur doit valider en priorité

1. L'organisation en huit axes alignés sur les priorités des programmes territoriaux.
2. La règle d'évaluation relative (seuils de 80 % et 95 %).
3. Les seuils de proximité (500 m, 1 km, 2 km, 300 m).
4. Les normes officielles qu'il peut fournir.
5. Les noms des profils de la typologie.
