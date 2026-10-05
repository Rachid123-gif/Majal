# Questions au référent scientifique

Les réponses proviennent des **positions méthodologiques provisoires v0**
(`docs/methodologie-v0.md`, section 4). Elles sont appliquées dans le démonstrateur, mais
chacune reste une **réponse provisoire v0, à valider par le professeur**.
Dernière mise à jour : 2026-10-05.

| # | Question | Réponse provisoire v0 (appliquée) | Statut |
| --- | --- | --- | --- |
| Q6 | Périmètre d'analyse de Rabat | Agglomération Rabat-Salé-Skhirate-Témara en vue principale ; préfecture de Rabat en filtre | Réponse provisoire v0, à valider par le professeur |
| Q7 | Unité fine à Rabat | Carreaux de 500 m pour les cartes et l'accessibilité ; quartiers OSM seulement pour situer les lieux cités. Dans l'étape 2, les calculs d'accessibilité utilisent la grille de population GHSL (≈ 90 m), plus fine ; l'affichage en carreaux de 500 m viendra avec l'écoute citoyenne | Réponse provisoire v0, à valider par le professeur |
| Q8 | Périmètre de Tétouan | Province de Tétouan seule ; M'diq-Fnideq possible plus tard comme preuve d'extension | Réponse provisoire v0, à valider par le professeur |
| Q9 | Grille et normes | Grille v0 (8 axes, 28 indicateurs), évaluation relative à la moyenne pondérée par la population (seuils 80 % et 95 %), aucune norme inventée (`TODO_REFERENT`) | Réponse provisoire v0, à valider par le professeur |
| Q10 | Source des noms officiels en arabe | Nomenclature officielle du HCP : appliquée pour les 24 unités de Rabat à partir du fichier de population légale 2024 (ex. « سيدي أبي القنادل ») ; le nom OpenStreetMap est conservé pour mémoire | Réponse provisoire v0, à valider par le professeur |
| Q11 | Relecture des textes arabes | Par le professeur ou une personne arabophone de son équipe, avant toute démonstration en arabe | Réponse provisoire v0, à valider par le professeur |
| Q12 | Chiffres de la vitrine | Uniquement des chiffres sourcés (210 MMDH sur 8 ans, 75 provinces et préfectures, 12 régions), chacun avec sa source | Réponse provisoire v0, à valider par le professeur |
| Q13 | Relecture des textes de la vitrine, nom et photo du professeur | Pas de réponse dans les positions v0 : emplacements `[Nom du professeur]`, `[Photo]`, `[email]` conservés | **Ouverte** |
| Q14 | Catégories d'équipements | Écoles, soins de santé primaires, hôpitaux, parcs publics (≥ 0,5 ha pour ENV_VERT300), marchés, arrêts de bus et de tramway, gares dans les indicateurs ; enseignement supérieur, cliniques privées, pharmacies, places, sport, culture, administrations en couche seulement ; lieux de culte exclus | Réponse provisoire v0, à valider par le professeur |
| Q15 | Limite de Sidi Bouknadel | Non corrigée à la main ; avertissement affiché, indicateurs spatiaux non évaluables, commune exclue des classements, limite officielle à demander | Réponse provisoire v0, à valider par le professeur |

## Nouveaux points à valider (étape 2)

| # | Point | Choix provisoire | Statut |
| --- | --- | --- | --- |
| Q16 | Soins de santé primaires : OpenStreetMap n'en recense que 5 pour toute l'agglomération (repérés par leur nom : « centre de santé », « مركز صحي »…) | Indicateurs SAN_ESSP, SAN_PROX et MOB_15MIN « non disponibles — recensement insuffisant » (minimum fixé à 10 dans `evaluation.yaml`) ; carte sanitaire à demander à la délégation de la Santé | À valider |
| Q17 | EDU_ECOLES : le nombre d'enfants de 6 à 14 ans n'est pas publié par commune, et OSM ne distingue pas le niveau des écoles | « Non disponible », à demander à la délégation de l'Éducation ; EDU_PROX calculé avec toutes les écoles OSM (provisoire) | À valider |
| Q18 | MOB_ROUTE (Tétouan) : le HCP publie directement la distance moyenne des logements à la route goudronnée | Source officielle HCP préférée au calcul OpenStreetMap prévu dans la v0 | À valider |
| Q19 | Bâti : l'imagerie GHSL observe 2015 et 2020 ; les recensements sont de 2014 et 2024 | URB_CROIS sur 2015-2020 ; URB_CONSO avec une population 2015 et 2020 interpolée entre les recensements (badge Estimé) | À valider |
| Q20 | Indicateurs de proximité | Population répartie dans chaque unité selon la grille GHSL 2020, recalée sur la population légale 2024 ; distances à vol d'oiseau | À valider |
