# Questions au référent scientifique

Les réponses proviennent des **positions méthodologiques provisoires v0**
(`docs/methodologie-v0.md`, section 4). Elles sont appliquées dans le démonstrateur, mais
chacune reste une **réponse provisoire v0, à valider par le professeur**.
Dernière mise à jour : 2026-10-07. Version triée par importance : `docs/kit-professeur/questions-referent.md`.

| # | Question | Réponse provisoire v0 (appliquée) | Statut |
| --- | --- | --- | --- |
| Q6 | Périmètre d'analyse de Rabat | Agglomération Rabat-Salé-Skhirate-Témara en vue principale ; préfecture de Rabat en filtre | Réponse provisoire v0, à valider par le professeur |
| Q7 | Unité fine à Rabat | Carreaux de 500 m pour les cartes et l'accessibilité ; quartiers OSM seulement pour situer les lieux cités. Dans l'étape 2, les calculs d'accessibilité utilisent la grille de population GHSL (≈ 90 m), plus fine ; l'affichage en carreaux de 500 m viendra avec l'écoute citoyenne | Réponse provisoire v0, à valider par le professeur |
| Q8 | Périmètre de Tétouan | Province de Tétouan seule ; M'diq-Fnideq possible plus tard comme preuve d'extension | Réponse provisoire v0, à valider par le professeur |
| Q9 | Grille et normes | Grille v0 (8 axes, 28 indicateurs), évaluation relative à la moyenne pondérée par la population (seuils 80 % et 95 %), aucune norme inventée (`TODO_REFERENT`) | Réponse provisoire v0, à valider par le professeur |
| Q10 | Source des noms officiels en arabe | Nomenclature officielle du HCP : appliquée pour les 24 unités de Rabat à partir du fichier de population légale 2024 (ex. « سيدي أبي القنادل ») ; le nom OpenStreetMap est conservé pour mémoire | Réponse provisoire v0, à valider par le professeur |
| Q11 | Relecture des textes arabes | Par le professeur ou une personne arabophone de son équipe, avant toute démonstration en arabe | Réponse provisoire v0, à valider par le professeur |
| Q12 | Chiffres de la vitrine | Uniquement des chiffres sourcés (210 MMDH sur 8 ans, 75 provinces et préfectures, 12 régions), chacun avec sa source | Réponse provisoire v0, à valider par le professeur |
| Q13 | Le professeur relit les textes de la page vitrine (français et arabe) et fournit son nom, sa photo et l'adresse de contact à afficher | Par défaut : la vitrine reste publiable en interne avec les emplacements `[Nom du professeur]`, `[Photo]`, `[email]` et le bouton « Nous contacter » grisé ; la relecture de l'arabe suit la règle Q11 (personne arabophone avant toute démonstration en arabe) ; rien n'est publié sur internet avant ces éléments | **Ouverte** (réponse par défaut appliquée) |
| Q14 | Catégories d'équipements | Écoles, soins de santé primaires, hôpitaux, parcs publics (≥ 0,5 ha pour ENV_VERT300), marchés, arrêts de bus et de tramway, gares dans les indicateurs ; enseignement supérieur, cliniques privées, pharmacies, places, sport, culture, administrations en couche seulement ; lieux de culte exclus | Réponse provisoire v0, à valider par le professeur |
| Q15 | Limite de Sidi Bouknadel | Non corrigée à la main ; avertissement affiché, indicateurs spatiaux non évaluables, commune exclue des classements, limite officielle à demander | Réponse provisoire v0, à valider par le professeur |

## Nouveaux points à valider (étape 2)

| # | Point | Choix provisoire | Statut |
| --- | --- | --- | --- |
| Q16 | Soins de santé primaires : OpenStreetMap n'en recense que 5 pour toute l'agglomération (repérés par leur nom : « centre de santé », « مركز صحي »…) | Indicateurs SAN_ESSP, SAN_PROX et MOB_15MIN « non disponibles — recensement insuffisant » (minimum fixé à 10 dans `evaluation.yaml`) ; carte sanitaire à demander à la délégation de la Santé | À valider |
| Q17 | EDU_ECOLES : le nombre d'enfants de 6 à 14 ans n'est pas publié par commune, et OSM ne distingue pas le niveau des écoles | « Non disponible », à demander à la délégation de l'Éducation ; EDU_PROX calculé avec toutes les écoles OSM (provisoire) | À valider |
| Q18 | MOB_ROUTE (Tétouan) : le HCP publie directement la distance moyenne des logements à la route goudronnée | Source officielle HCP préférée au calcul OpenStreetMap prévu dans la v0 (accord du porteur du projet, 2026-10-05) | Réponse provisoire v0, à valider par le professeur |
| Q19 | Bâti : l'imagerie GHSL observe 2015 et 2020 ; les recensements sont de 2014 et 2024 | URB_CROIS sur 2015-2020, les deux dates observées, sans année projetée ; URB_CONSO avec une population 2015 et 2020 interpolée entre les recensements (badge Estimé) | Réponse provisoire v0, à valider par le professeur |
| Q20 | Indicateurs de proximité | Population répartie dans chaque unité selon la grille GHSL 2020, recalée sur la population légale 2024 ; distances à vol d'oiseau en v0, signalées comme limite dans « Source · Méthode » ; passage aux distances le long des rues au plus tard à l'étape 7 | Réponse provisoire v0, à valider par le professeur |

## Écoute citoyenne (étape 4)

| # | Point | Choix provisoire | Statut |
| --- | --- | --- | --- |
| Q24 | Évaluation de référence de l'analyse des contributions | `docs/evaluation/annotation-professeur.xlsx` (28 contributions fictives, amazighe exclu) est aujourd'hui classé par un second modèle d'IA : affiché « Évaluation indépendante par un second modèle d'IA … — en attente de validation par le professeur », jamais « de référence » | **Ouverte** : classement ou relecture par le professeur |
| Q25 | Seuils du croisement citoyens / données | Pas de conclusion en dessous de 5 contributions ; nombres et non pourcentages en dessous de 20 ; « sans demande exprimée » seulement à partir de 30 contributions dans l'unité ; demande « forte » au-delà de 15 % des contributions ; à l'échelle de la commune, indicateur défavorable si les unités concernées réunissent la moitié de la population (`config/taxonomy/urbain.yaml`, `crossing`) | TODO_REFERENT, à valider |
| Q26 | Taxonomie urbaine des contributions | 19 thèmes, mots-clés en français, arabe et darija, indicateurs liés, données à demander (`config/taxonomy/urbain.yaml`) ; eau et assainissement distincts de la propreté, crèches en éducation | À valider |
| Q27 | File « À vérifier » | Contribution à vérifier si l'IA et les mots-clés ne donnent pas le même thème principal, ou si la langue est incertaine ; les cas où les mots-clés ne trouvent aucun thème s'affichent « confiance moyenne » sans entrer dans la file (choix du porteur, 2026-10-07) | À valider |

## Besoins en données (étape 5)

| # | Point | Choix provisoire | Statut |
| --- | --- | --- | --- |
| Q21 | Demandes de « contexte » (projets programmés : Wilaya – programmes de développement territorial intégré, Conseil de la Région, Agence du Bouregreg) | Gardées dans une catégorie distincte « Contexte » (`context: true` dans `config/data_holders/rabat.yaml`). **Fonction future, non développée** : une fois ces données obtenues, MAJAL distinguera pour chaque déficit mesuré « besoin non couvert » et « besoin déjà couvert par un projet programmé » (choix du porteur, 2026-10-07) | À préciser avec le professeur : règle de correspondance entre un projet et un déficit (secteur, localisation, horizon) |
| Q22 | Priorité des demandes de données | Calculée, jamais choisie à la main : « Essentielle » si la demande rend calculables des indicateurs aujourd'hui non disponibles ou porte sur les limites officielles ; « Utile » si elle améliore des indicateurs estimés ou ouverts ou objective un thème citoyen ; « Contexte » pour les projets programmés, même s'ils améliorent aussi un indicateur (`app/services/data_needs/priority.py`) | Réponse provisoire du porteur, à valider par le professeur |
| Q23 | Intitulés des institutions (FR et AR) | Liste proposée par le porteur (2026-10-07), complétée de la Direction régionale chargée de la Jeunesse et de l'Entraide nationale ; chaque intitulé marqué « à vérifier par le professeur » | À vérifier par le professeur |
| Q28 | Modèle de la note de demande de données | `config/report_templates/note_demande.yaml` : première personne (un seul signataire), en-tête « MAJAL — projet de recherche appliquée », en-tête de l'établissement seulement avec son autorisation, contrepartie, proposition de convention ; paragraphe « Hautes Orientations Royales » désactivé par défaut ; formule « Je serais honoré » au masculin, à adapter au signataire | À relire par le professeur ; décider l'activation du paragraphe optionnel |
| Q29 | Titres des destinataires des notes | Un destinataire unique par institution, titre complet au masculin et au féminin (« Monsieur / Madame le / la … ») dans `config/data_holders/rabat.yaml` ; communes de Skhirate-Témara : une note par commune | À vérifier par le professeur |
