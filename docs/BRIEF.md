# MAJAL — Cahier des charges complet pour Claude Code

**Version 3 · Démonstrateur sur deux territoires (Rabat et Tétouan) puis pilote · Octobre 2026**

> **Pour le porteur du projet (à lire avant de lancer Claude Code)**
> 1. Créez un dossier vide `majal`, puis un sous-dossier `docs`, et enregistrez ce fichier sous `docs/BRIEF.md`.
> 2. Ouvrez Claude Code dans le dossier `majal` et écrivez : « Lis docs/BRIEF.md en entier, puis exécute la section 22 (première tâche). Réponds-moi en français. »
> 3. Répondez à ses questions. Les questions de méthode (indicateurs, normes, thèmes) sont à transmettre au professeur.
> 4. Validez chaque étape avant de passer à la suivante. Ne sautez pas les démonstrations de fin d'étape.

---

## 1. Ton rôle

Tu es l'**ingénieur logiciel principal** et le **conseiller technique** du projet MAJAL. Tu conçois, codes, testes et documentes l'application.

Tu travailles avec deux personnes :

- **Le porteur du projet** : il développe l'outil avec toi et le présentera. Il n'est pas forcément un développeur expérimenté. Tu lui expliques simplement ce que tu fais, pourquoi, et comment vérifier que ça marche. Tu lui donnes les commandes exactes à lancer.
- **Le référent scientifique** : Professeur Habilité à l'École Nationale d'Architecture de Tétouan, spécialiste en urbanisme, gouvernance urbaine, intelligence territoriale et marketing territorial. Il est l'autorité sur la méthode (indicateurs, normes, seuils, thèmes, contenu des rapports). Il utilisera le démonstrateur pour convaincre des décideurs (walis et gouverneurs, présidents de région, de commune et d'arrondissement, directeurs d'agence urbaine, HCP, ministères) et obtenir l'accès à leurs données.

Langue de travail : tu réponds en **français**. Le code, les noms de variables et les messages de commit sont en **anglais**. L'interface est en **français et en arabe**.

## 2. L'enjeu : pourquoi ce démonstrateur existe

Le Maroc lance en 2026 une nouvelle génération de **programmes de développement territorial intégré (PDTI)** : environ 210 milliards de dirhams sur 8 ans, fondés sur des **diagnostics territoriaux** et des **concertations citoyennes** dans les 75 provinces. Ces diagnostics sont aujourd'hui produits par des études longues, coûteuses et vite dépassées.

MAJAL (« territoire » en arabe) est un **copilote IA d'intelligence territoriale** : il transforme la donnée publique dispersée en diagnostics chiffrés, cartes, synthèse des attentes citoyennes et rapports, en quelques minutes.

**Le démonstrateur a un objectif précis : permettre au professeur de convaincre des décideurs en moins de 20 minutes, pour qu'ils lui ouvrent l'accès à leurs données.** Cela implique cinq priorités, dans cet ordre :

1. **Crédibilité** : des données réelles chaque fois que possible, une source et une date visibles sur chaque chiffre, aucun chiffre inventé, une honnêteté totale sur les limites.
2. **Clarté** : un décideur non technicien comprend chaque écran en quelques secondes.
3. **Effet démonstratif** : carte, fiche commune, rapport généré en direct, synthèse citoyenne, tout fluide.
4. **Polyvalence** : le même outil, sans changer une ligne de code, s'adapte à une capitale entièrement urbaine (Rabat) et à une province mêlant ville et campagne (Tétouan).
5. **Appel à l'action** : l'outil montre explicitement **ce qu'il pourrait faire de plus avec les données du décideur** (module « Besoins en données », section 9.8).

Principe directeur : **l'outil propose, l'urbaniste valide.** MAJAL est une aide à la décision, jamais un décideur.

## 3. Définition du succès

Le démonstrateur est réussi quand :

- le professeur peut dérouler seul le **scénario de démonstration** (section 8) en moins de 20 minutes, sur un ordinateur portable, en passant d'un territoire à l'autre, **même sans connexion internet** ;
- tous les chiffres affichés sur les deux territoires de démonstration proviennent de **sources réelles et citées**, ou sont **clairement marqués** comme estimés ou fictifs ;
- un **rapport de diagnostic** d'un arrondissement de Rabat et d'une commune de Tétouan est généré en moins d'une minute, en français, et en arabe à l'étape 7 ;
- une **note de demande de données** prête à signer est produite pour chaque institution détentrice, sur chacun des deux territoires ;
- le second territoire a été ajouté **uniquement par configuration et import de données**, sans modifier la logique métier ;
- le porteur du projet sait installer, lancer, mettre à jour et sauvegarder l'application grâce au README.

## 4. Périmètre

Le projet avance en deux versions.

**Version D — Démonstrateur (environ 8 semaines, priorité absolue)**
Deux territoires de démonstration contrastés (Rabat et Tétouan), données ouvertes et publiques, contributions citoyennes fictives, fonctionnement sur un portable.

**Version P — Pilote (après accord d'un décideur)**
Données officielles du partenaire, vraies contributions citoyennes, hébergement au Maroc, comptes pour les agents de la province, IA hébergée localement.

Priorisation de la version D :

| Priorité | Fonction |
| --- | --- |
| Indispensable | Carte du territoire, fiche commune, moteur d'indicateurs configurable, badges de fiabilité des données, rapport IA vérifié en français, module « Besoins en données », mode présentation, fonctionnement hors ligne |
| Important | Écoute citoyenne (sur données fictives), comparaison de communes, rapport en arabe, interface en arabe |
| Souhaitable | Assistant documentaire sur documents d'urbanisme, typologie automatique des communes, export de la carte en image |
| Hors périmètre | Priorisation et suivi des projets (module 3), attractivité et foncier (module 4), application mobile, collecte citoyenne en ligne, plus de deux territoires en démonstration (l'architecture doit pourtant le permettre) |

Conçois le modèle de données pour pouvoir ajouter les modules 3 et 4 et autant de territoires que nécessaire sans refonte.

## 5. Deux territoires de démonstration

Le démonstrateur couvre **deux territoires volontairement contrastés**, pour prouver que MAJAL s'adapte à tous les contextes marocains.

| | Rabat | Tétouan |
| --- | --- | --- |
| Profil | Capitale entièrement urbaine | Province mêlant communes urbaines et rurales, littoral et montagne |
| Région | Rabat-Salé-Kénitra | Tanger-Tétouan-Al Hoceïma |
| Unité d'analyse principale | Arrondissements de la commune de Rabat et autres communes de la préfecture | Communes urbaines et rurales de la province |
| Unité fine | Quartiers ou maillage régulier (par exemple carreaux de 500 m) | Douars et centres ruraux, ou maillage régulier |
| Grille d'indicateurs | Profil `urbain` | Profil `mixte` (urbain + rural) |
| Thèmes citoyens | Profil `urbain` | Profil `mixte` |
| Intérêt pour la démonstration | Capitale, siège des décideurs nationaux, ville hôte de la Coupe du monde 2030 | Territoire de l'École Nationale d'Architecture et du réseau du professeur ; enjeux ruraux typiques des programmes territoriaux |

**Règles communes**

- Chaque territoire est décrit par un fichier `config/territories/<code>.yaml` : nom en français et en arabe, niveaux d'analyse, sources, profil de grille, profil de taxonomie, référentiel des institutions. **Ajouter un territoire = ajouter un fichier de configuration et lancer les imports**, jamais modifier la logique métier.
- Un **sélecteur de territoire** est visible en permanence dans l'interface. Le changement de territoire est instantané (données préchargées).
- Dans la suite de ce document, **« commune » désigne l'unité d'analyse principale** (arrondissement à Rabat, commune à Tétouan) et **« province » désigne le territoire étudié** (préfecture de Rabat ou province de Tétouan). L'interface emploie toujours les vrais termes.
- Rabat : la préfecture ne compte que très peu de communes et la commune de Rabat est découpée en arrondissements. Prévois un **niveau élargi optionnel** (agglomération Rabat-Salé-Skhirate-Témara) pour disposer de plus d'unités à comparer ; confirme le niveau retenu avec le porteur du projet avant l'import.
- La **liste des unités, leurs codes et leurs limites** viennent d'une source réelle (section 10). Tu ne dois **jamais inventer** un arrondissement, une commune, un douar, un quartier, un code officiel ou une limite. Si des limites ne sont pas disponibles dans une source fiable, dis-le, propose une alternative (maillage régulier, source à demander) et alimente le module Besoins en données.
- **Vue « Deux territoires »** : un écran met côte à côte Rabat et Tétouan sur les seuls indicateurs communs aux deux profils, avec un avertissement sur les limites de la comparaison (contextes différents). Son but est de montrer la polyvalence de l'outil, pas de classer les territoires.

**Ordre de construction** : Rabat d'abord, de bout en bout (étapes 1 à 5), puis Tétouan à l'étape 6. Cet ordre sert de preuve : si ajouter Tétouan oblige à modifier le code métier, c'est que la conception doit être corrigée, et tu dois le signaler.

## 6. Utilisateurs et rôles

Pour la version D, trois rôles suffisent :

| Rôle | Peut faire |
| --- | --- |
| Présentateur (le professeur, le porteur) | Tout consulter, générer des rapports, lancer le mode présentation |
| Référent scientifique | Modifier la grille d'indicateurs, la taxonomie et les plans de rapport ; valider les rapports |
| Administrateur | Importer les données, gérer les sources et les utilisateurs |

Prévois dans le modèle les rôles de la version P : analyste (province), décideur (lecture seule), lecteur public.

## 7. Principes de conception non négociables

1. **Traçabilité** : chaque valeur affichée ou écrite par l'IA est reliée à sa source, sa date, et sa méthode de calcul. Un clic ou un survol permet de les voir.
2. **Niveau de confiance visible** : chaque valeur porte un badge parmi quatre :
   - **Officiel** : source institutionnelle (HCP, ministère, agence urbaine) ;
   - **Ouvert** : source ouverte reconnue (OpenStreetMap, imagerie satellite) ;
   - **Estimé** : calculé ou modélisé par MAJAL à partir d'autres données ;
   - **Fictif** : donnée de démonstration inventée, avec un bandeau d'avertissement.
3. **Zéro chiffre inventé par l'IA** : le modèle de langage ne produit jamais un nombre lui-même (mécanisme en section 9.5).
4. **Méthode déclarative** : indicateurs, normes, seuils, thèmes et plans de rapport sont dans des fichiers YAML que le professeur peut modifier sans toucher au code.
5. **Données personnelles protégées** : anonymisation avant tout traitement IA ; aucune donnée personnelle réelle dans la version D.
6. **Souveraineté possible** : le fournisseur d'IA est interchangeable par configuration ; l'application doit pouvoir tourner sans aucun service étranger (version P).
7. **Simplicité d'exploitation** : une seule commande pour tout lancer ; un README que le porteur du projet peut suivre seul.

## 8. Scénario de démonstration (moins de 20 minutes)

C'est le fil conducteur de toute la version D. Chaque écran doit servir ce scénario.

1. **Accueil (1 min)** : page d'accueil sobre, logo MAJAL, phrase d'accroche, carte du Maroc situant les deux territoires de démonstration. Bouton « Commencer la présentation ». La démonstration commence par Rabat (ou par Tétouan selon l'interlocuteur : choix au lancement).
2. **Vue province (2 min)** : carte des communes colorée par un indicateur choisi (par exemple les espaces verts par habitant ou l'accès au tramway et au bus). Légende claire, badge de confiance, source en bas. Sélecteur d'indicateur par thème.
3. **Fiche commune (3 min)** : clic sur une commune → indicateurs clés en cartes, rang dans la province, écart à la moyenne, déficits signalés en couleur (avec texte, pas seulement couleur), mini-carte des équipements, évolution de la tache bâtie entre deux dates.
4. **Comparaison (1 min)** : deux à quatre communes côte à côte.
5. **Ce que disent les citoyens (2 min)** : tableau de bord des contributions (fictives en version D, clairement marquées) : thèmes dominants, carte, verbatims, et le croisement « ce que disent les citoyens / ce que montrent les données ».
6. **Rapport généré en direct (3 min)** : clic sur « Générer le diagnostic » → rapport rédigé en moins d'une minute, avec tableaux et cartes, téléchargeable en Word et PDF, en français (et en arabe à l'étape 7).
7. **Changement de territoire (3 min)** : bascule vers Tétouan. La carte montre des communes urbaines et rurales ; les indicateurs changent (accès aux routes revêtues, raccordement à l'eau et à l'électricité, temps d'accès au chef-lieu) ; l'écoute citoyenne fait remonter d'autres préoccupations (eau potable, pistes rurales, transport scolaire) localisées par douar ; un rapport d'une commune rurale est généré. Puis la vue « Deux territoires » résume : un seul outil, deux réalités.
8. **Besoins en données (3 min)** : écran « Ce que MAJAL pourrait faire avec vos données » : complétude actuelle par thème (par exemple « Santé : 2 indicateurs sur 6 disponibles »), liste des données manquantes avec l'institution qui les détient, et bouton « Générer la note de demande de données ». Cet écran s'affiche pour le territoire de l'interlocuteur.

Le mode présentation (section 9.9) permet de dérouler ces étapes en plein écran avec une navigation simple.

## 9. Spécifications fonctionnelles détaillées

### 9.1 Carte et navigation territoriale

- Carte MapLibre GL avec fond de carte **utilisable hors ligne** (fichier PMTiles local de la zone, généré une fois ; fond en ligne en option).
- Couches : limites des communes, choroplèthe de l'indicateur choisi (classes par quantiles ou seuils de la grille, palette accessible aux daltoniens), équipements par type, tache bâtie par année.
- Survol : nom de la commune (français et arabe), valeur, badge de confiance. Clic : fiche commune.
- Légende, échelle, source et date toujours visibles.
- Export de la carte affichée en PNG.

### 9.2 Moteur d'indicateurs (grille déclarative)

La grille est définie dans `config/indicators/*.yaml`. Exemple de format attendu (à affiner, avec un schéma de validation) :

```yaml
grid_version: "0.1-provisoire"
indicators:
  - code: DEM_POP_2024
    theme: demographie
    label_fr: "Population totale"
    label_ar: "مجموع السكان"
    unit: "habitants"
    formula: { type: raw, input: population_2024 }
    source_expected: "HCP, RGPH 2024"
    direction: neutral        # higher_better | lower_better | neutral
    norm: null
    status: TODO_REFERENT     # à valider par le professeur

  - code: SAN_CS_10K
    theme: sante
    label_fr: "Établissements de santé de base pour 10 000 habitants"
    label_ar: "مؤسسات الصحة الأساسية لكل 10000 نسمة"
    unit: "pour 10 000 hab."
    formula: { type: ratio, numerator: count_facilities_health_primary, denominator: population_2024, per: 10000 }
    source_expected: "Ministère de la Santé (officiel) ; OpenStreetMap (ouvert, provisoire)"
    direction: higher_better
    norm: { value: null, source: TODO_REFERENT }
    status: TODO_REFERENT
```

Exigences :

- Types de formules : `raw`, `ratio`, `rate` (pourcentage), `density` (par km²), `change` (variation entre deux dates, absolue et en %), `cagr` (taux de croissance annuel moyen), `distance_mean` (distance moyenne de la population ou des centroïdes au plus proche équipement d'un type), `share` (part d'une catégorie).
- Validation stricte au chargement avec messages d'erreur **en français** compréhensibles par le professeur (ligne, champ, problème, exemple correct).
- Pour chaque commune et indicateur : valeur, unité, année, source, badge de confiance, rang dans la province, écart à la moyenne provinciale (et régionale ou nationale si disponible), comparaison à la norme, statut (conforme, déficit, excédent, non évaluable).
- **Score de fiabilité** (0 à 100) par valeur : nature de la source, ancienneté, complétude, méthode (directe ou estimée). Méthode de calcul documentée.
- Une valeur manquante n'est jamais remplacée par zéro : elle est affichée « non disponible » et alimente le module Besoins en données.
- Résultat d'un diagnostic : objet JSON versionné (version de la grille, date, sources utilisées), stocké en base.
- Performance : diagnostic complet de la province en moins de 30 secondes.

### 9.3 Grille provisoire de démarrage

En attendant la grille du professeur, crée une grille provisoire organisée en **indicateurs communs** et **indicateurs propres à un profil** (`urbain` pour Rabat, `mixte` pour Tétouan, qui combine indicateurs urbains et ruraux). Chaque indicateur déclare les profils où il s'applique (`profiles: [urbain, mixte]`). Vise 20 à 25 indicateurs par profil, tous marqués `status: TODO_REFERENT`, inspirée de cette liste (vérifie pour chacun quelle source réelle existe ; sinon marque-le « à demander ») :

| Thème | Indicateurs proposés |
| --- | --- |
| Démographie | Population 2024 ; taux de croissance annuel 2014-2024 ; densité ; part des moins de 15 ans ; part des 60 ans et plus ; taille moyenne des ménages ; part de la population urbaine |
| Éducation | Taux d'analphabétisme (10 ans et plus) ; écoles pour 1 000 enfants d'âge scolaire ; distance moyenne à l'école la plus proche |
| Santé | Établissements de santé de base pour 10 000 habitants ; distance moyenne au centre de santé le plus proche |
| Emploi | Taux de chômage ; taux d'activité des femmes |
| Logement et services | Raccordement au réseau d'eau potable ; à l'électricité ; à l'assainissement ; part des logements précaires |
| Accessibilité et mobilité | Part de la population à moins de 500 m d'un arrêt de tramway ou de bus ; distance moyenne aux équipements de proximité ; part de la population ayant école, centre de santé et marché à moins de 15 minutes à pied |
| Cadre de vie | Espaces verts par habitant ; part de la population à moins de 300 m d'un espace vert ; densité de bâti ; surface imperméabilisée |
| Dynamique urbaine | Surface bâtie ; croissance de la surface bâtie sur deux dates ; surface bâtie par habitant ; couverture par un document d'urbanisme homologué ; part du territoire en zone patrimoniale protégée |
| Vulnérabilité | Taux de pauvreté (si une carte officielle récente existe) ; exposition aux risques (si une donnée existe) |
| Spécifiques rural (profil `mixte`) | Distance moyenne à une route revêtue ; temps d'accès estimé au chef-lieu de province ; part de la population rurale ; raccordement à l'eau potable et à l'électricité en milieu rural ; distance à l'école et au centre de santé pour les douars ; surface agricole si une donnée existe |

Les indicateurs de mobilité urbaine et de cadre de vie (tramway, espaces verts, 15 minutes à pied) s'appliquent au profil `urbain` et aux communes urbaines du profil `mixte`. Le moteur doit savoir qu'un indicateur ne s'applique pas à une unité (statut « non applicable », distinct de « non disponible »).

Fournis aussi un fichier `docs/grille-indicateurs-guide.md` qui explique au professeur, sans jargon informatique, comment ajouter, modifier ou désactiver un indicateur.

### 9.4 Fiche commune et comparaison

- En-tête : nom en français et en arabe, province, population, surface, badge de complétude des données.
- Cartes d'indicateurs regroupées par thème : valeur, unité, année, badge, rang, écart, flèche de tendance si deux dates.
- Bloc « Points d'attention » : les 3 à 5 déficits les plus marqués (règles déterministes, pas l'IA).
- Mini-carte : limites, équipements, tache bâtie.
- Comparaison : jusqu'à 4 communes, tableau et graphiques simples, export PNG et CSV.
- Typologie (souhaitable) : regroupement automatique des communes en 3 à 5 profils à partir des indicateurs disponibles (méthode simple et explicable, par exemple k-means sur variables standardisées), avec description de chaque profil.

### 9.5 Rapport de diagnostic rédigé par l'IA

**Mécanisme anti-invention de chiffres (obligatoire)**

1. Le moteur prépare une **fiche de faits** : liste d'éléments identifiés (`F001`, `F002`…) avec valeur formatée, unité, année, source, badge, rang, écart, statut.
2. Le modèle de langage reçoit uniquement cette fiche, le plan du rapport et des consignes de style. Il rédige en **référençant les faits par identifiant** (par exemple `{{F012}}`) au lieu d'écrire des nombres. Sortie en JSON structuré par section.
3. Un moteur de rendu remplace chaque identifiant par la valeur formatée (règles françaises : espace insécable pour les milliers, virgule décimale ; règles arabes adaptées) et ajoute la source en note.
4. **Vérification finale** : le texte rendu est analysé ; tout nombre qui ne provient pas d'un identifiant (chiffres latins ou arabes-indiens, pourcentages, nombres écrits en lettres) bloque la publication et est signalé à l'utilisateur. Exceptions autorisées et listées : numéros de section, années présentes dans la fiche de faits.
5. Tests unitaires couvrant au minimum 15 cas pièges (nombre inventé, arrondi différent, nombre en lettres, chiffres arabes-indiens, pourcentage recalculé…).

**Contenu du rapport** (plan dans `config/report_templates/diagnostic_commune.yaml`, modifiable par le professeur) :

1. Présentation du territoire
2. Dynamiques démographiques
3. Équipements et services de base
4. Accessibilité
5. Dynamique urbaine et foncière
6. Vulnérabilités
7. Ce que disent les citoyens
8. Synthèse des enjeux et pistes de réflexion (formulées comme des questions ou des pistes, jamais comme des décisions)
9. Sources, méthode et limites des données (générée automatiquement à partir de la fiche de faits)

**Exigences**

- Ton institutionnel, phrases courtes, pas de superlatifs, pas de jargon inutile.
- En-tête et pied de page MAJAL, date de génération, version de la grille.
- Tant que le rapport n'est pas validé : filigrane « Document de travail généré par MAJAL — à valider par un urbaniste ».
- Exports Word (DOCX) et PDF, avec tableaux et cartes intégrées en image.
- Rapport en arabe à l'étape 7 : même mécanisme, mise en page de droite à gauche, police arabe adaptée.
- Cycle de statut : brouillon → relu → validé, avec historique (qui, quand).
- **Mode hors ligne** : les rapports déjà générés sont mis en cache ; en démonstration sans internet, l'application rejoue le dernier rapport généré et l'indique discrètement.

### 9.6 Écoute citoyenne

**Version D** : jeu de **120 à 150 contributions fictives réalistes par territoire**, rédigées en français, en arabe standard, en darija (alphabet arabe et latin) et quelques-unes en amazighe (transcription latine), réparties entre communes et thèmes de façon plausible. Toutes marquées « Fictif ». Elles ne contiennent aucune personne réelle.

**Fonctions**

- Import CSV ou Excel (modèle de fichier fourni), texte libre ; audio en version P (transcription locale avec Whisper).
- **Anonymisation avant tout traitement IA** : noms de personnes, numéros de téléphone marocains, numéros de CIN, adresses précises, e-mails, plaques d'immatriculation. Module dédié, testé sur un jeu d'exemples pièges, avec rapport de ce qui a été masqué.
- Détection de langue ; traduction en français pour l'analyse ; conservation et affichage possible de l'original.
- Classification selon une taxonomie par profil (`config/taxonomy/urbain.yaml`, `config/taxonomy/mixte.yaml`, provisoires, `TODO_REFERENT`). Profil `urbain` : mobilité et transport en commun, circulation et stationnement, voirie et trottoirs, logement et loyers, espaces verts et espaces publics, propreté et déchets, eau et assainissement, éclairage public, santé, éducation, emploi et jeunesse, sécurité, bruit et nuisances, commerce et marchés, culture, sport et loisirs, patrimoine, administration et services, accessibilité des personnes à mobilité réduite, autres. Profil `mixte` : thèmes urbains, plus eau potable en milieu rural, pistes et routes rurales, électrification, transport scolaire, agriculture et irrigation, forêts et ressources naturelles, tourisme littoral et de montagne. Plusieurs thèmes possibles par contribution.
- Extraction du lieu cité (quartier, rue, place, équipement connu à Rabat ; douar, centre rural, commune à Tétouan) et rattachement à l'unité d'analyse ; en version D, les contributions fictives citent des lieux réels mais aucune personne réelle.
- Tonalité : demande, plainte, proposition, satisfaction.
- Tableau de bord : thèmes par fréquence, par commune, par langue ; carte ; 3 verbatims représentatifs par thème (anonymisés) ; filtres.
- **Croisement** : pour chaque commune et thème, mise en regard de la demande citoyenne et de l'indicateur correspondant (par exemple « espaces verts : 34 contributions ; 2,1 m² d'espace vert par habitant »), avec signalement des écarts notables.
- **Évaluation** : script qui mesure précision et rappel de la classification sur un échantillon annoté à la main (fourni plus tard par le professeur ; en version D, sur un sous-ensemble des contributions fictives annotées par toi et marquées comme telles).

### 9.7 Assistant documentaire (souhaitable en version D)

- Import de PDF (plans d'aménagement, règlements, SDAU, textes de loi publics comme la loi 12-90 relative à l'urbanisme), extraction du texte, découpage, embeddings.
- Questions en français ou en arabe ; réponse **uniquement** à partir des passages retrouvés, avec citation (document, page) ; si aucun passage pertinent : « Je ne trouve pas cette information dans les documents disponibles. »
- Avertissement visible : « Réponse indicative, à vérifier dans le document source. »

### 9.8 Module « Besoins en données » (clé pour le professeur)

Ce module transforme les lacunes de données en arguments et en demandes concrètes.

- Pour chaque indicateur de la grille : statut (disponible officiel, disponible ouvert ou proxy, estimé, manquant), **institution détentrice** (liste par territoire dans sa configuration. Pour Rabat : wilaya de la région Rabat-Salé-Kénitra et préfecture de Rabat, commune de Rabat et conseils d'arrondissement, agence urbaine compétente, direction régionale du HCP, conseil régional, délégations des ministères de la Santé et de l'Éducation, opérateur de distribution d'eau, d'électricité et d'assainissement, opérateur de transport urbain, sociétés de développement local. Pour Tétouan : province de Tétouan, communes, agence urbaine de Tétouan, conseil régional Tanger-Tétouan-Al Hoceïma, direction régionale du HCP, délégations de la Santé, de l'Éducation et de l'Agriculture, Agence du Nord, opérateurs de l'eau et de l'électricité ; la liste exacte et les intitulés officiels sont à vérifier et à compléter par le professeur), niveau de détail souhaité (arrondissement, quartier ou îlot à Rabat ; commune, douar à Tétouan), format, fréquence, et valeur ajoutée pour le décideur.
- Le référentiel des institutions et des données demandées est dans `config/data_holders/<territoire>.yaml`, modifiable.
- Écran de synthèse : complétude par thème (barres simples), et phrase claire du type « Avec les données de la délégation de la Santé, MAJAL pourrait calculer 4 indicateurs supplémentaires ».
- **Génération d'une note de demande de données** (DOCX et PDF) par institution : objet, contexte (programmes territoriaux intégrés), présentation courte de MAJAL, liste précise des données demandées, usage prévu, engagements de confidentialité (loi 09-08, anonymisation, hébergement), contact. Champs à compléter entre crochets : `[Nom et titre du professeur]`, `[Destinataire]`, `[Date]`. Ton respectueux et institutionnel. Le texte est rédigé à partir d'un modèle fixe complété par les données du module, pas improvisé par l'IA.
- Export d'un tableau récapitulatif (Excel) des données demandées.

### 9.9 Mode présentation

- Plein écran, typographie agrandie, navigation par étapes du scénario (section 8) avec flèches du clavier.
- Bandeau discret indiquant le territoire, la date des données et la mention « Démonstrateur ».
- Si des données fictives sont affichées, un bandeau « Données fictives » toujours visible.
- Préchargement de toutes les données et cartes au lancement pour une démonstration fluide hors ligne.
- Bouton de bascule français / arabe.

### 9.10 Administration

- Gestion des sources (liste, date, licence, statut), relance des imports, journal des imports.
- Édition de la grille, de la taxonomie et des plans de rapport : en version D, édition des fichiers YAML avec validation et aperçu des erreurs ; un éditeur visuel est souhaitable plus tard.
- Gestion des utilisateurs et des rôles.
- Sauvegarde et restauration de la base en une commande.

## 10. Données

### 10.1 Sources à mobiliser pour la version D

Pour chaque source : **vérifie qu'elle existe, son niveau de détail, sa date et sa licence avant de l'utiliser**, et documente-la dans `docs/sources.md`. Si une source est inaccessible depuis ton environnement, demande au porteur du projet de télécharger le fichier et de le placer dans `data/raw/`.

| Donnée | Pistes de sources | Badge |
| --- | --- | --- |
| Limites administratives (région, province, communes) | Jeux de limites administratives publiés pour le Maroc (par exemple HDX, geoBoundaries, ou portails marocains de données SIG) ; à vérifier : date, niveau communal, cohérence avec le découpage en vigueur | Officiel ou Ouvert selon la source |
| Population et indicateurs du recensement 2024 et 2014 | Publications et portail du HCP (résultats du RGPH par commune) ; si seules des tables publiées existent, crée un modèle CSV de saisie et un contrôle de cohérence | Officiel |
| Équipements (écoles, santé, marchés, administrations, mosquées si utile, transport) | Extrait OpenStreetMap du Maroc | Ouvert |
| Réseau routier, voirie piétonne | OpenStreetMap | Ouvert |
| Espaces verts, places, arrêts de tramway et de bus | OpenStreetMap ; données de l'opérateur de transport urbain et de la commune à demander | Ouvert, puis Officiel |
| Zones patrimoniales | Périmètres publiés des sites protégés de Rabat, si disponibles en données géographiques ; sinon à demander | Officiel |
| Tache bâtie et son évolution | Couches mondiales de bâti issues de l'imagerie satellite (par exemple Global Human Settlement Layer) ; Sentinel-2 en option | Ouvert ou Estimé |
| Répartition fine de la population | Grilles de population mondiales (par exemple WorldPop), uniquement pour des estimations sous-communales clairement marquées | Estimé |
| Documents d'urbanisme | Documents publics de l'agence urbaine et du Géoportail national, sous réserve d'accès | Officiel |
| Agriculture, forêts (Tétouan) | Données ouvertes d'occupation du sol issues de l'imagerie satellite ; données sectorielles à demander | Ouvert, puis Officiel |
| Contributions citoyennes | Jeu fictif (section 9.6), un par territoire | Fictif |

Règles :

- Ne jamais présenter une donnée fictive ou estimée comme officielle.
- Ne jamais inventer une statistique marocaine. Si une valeur n'est pas trouvée, elle est « non disponible ».
- Conserver les fichiers bruts dans `data/raw/` (non versionnés si lourds, avec un script de téléchargement ou une procédure documentée), les données transformées dans la base.
- Toutes les données géographiques en EPSG:4326 en base ; calculs de surfaces et de distances dans une projection métrique adaptée au Maroc (à documenter).

### 10.2 Ingestion

- Un importeur par source, **idempotent** (relancer ne crée pas de doublons), journalisé, avec un résumé lisible (« 23 communes importées, 2 avertissements »).
- Fichier de correspondance configurable pour les colonnes des fichiers tabulaires (les fichiers officiels de la version P auront d'autres formats).
- Contrôles de cohérence : totaux provinciaux, communes sans géométrie, valeurs aberrantes, unités.
- Commande unique : `make data` pour tout (re)construire.

## 11. Architecture et stack technique

Stack retenue (toute modification fait l'objet d'une note de décision dans `docs/decisions/`) :

- **Backend** : Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2.
- **Base de données** : PostgreSQL 16 avec PostGIS et pgvector.
- **Géotraitements** : GeoPandas, Shapely, Rasterio, et un outil de calcul d'accessibilité simple (distance euclidienne d'abord, réseau routier ensuite).
- **Tâches longues** : file de tâches simple (RQ et Redis) pour les imports et la génération de rapports.
- **Frontend** : Next.js (App Router) en TypeScript, Tailwind CSS, MapLibre GL JS, bibliothèque de graphiques légère ; internationalisation français et arabe avec RTL complet.
- **Rapports** : DOCX (python-docx) et PDF (par exemple via un rendu HTML vers PDF) avec polices intégrées.
- **IA** : interfaces `LLMProvider`, `EmbeddingProvider`, `TranscriptionProvider`.
  - Version D : API Anthropic Claude pour la rédaction et l'analyse (clé dans `.env`, jamais dans le code) ; embeddings et traduction selon ce qui est le plus simple et fiable, documenté.
  - Version P : serveur local compatible avec l'API OpenAI (par exemple vLLM avec un modèle open source) ; aucun appel externe en mode `SOVEREIGN_MODE=true`.
  - Sorties structurées (JSON validé par schéma), température basse pour la rédaction, nouvelle tentative contrôlée en cas de JSON invalide, journal des coûts et du nombre d'appels, cache des réponses.
- **Infrastructure** : Docker Compose ; commandes `make` : `make setup`, `make data`, `make dev`, `make demo`, `make test`, `make backup`, `make restore`.
- **Qualité** : pytest, Ruff, mypy ; ESLint, Prettier ; quelques tests de bout en bout avec Playwright sur le scénario de démonstration ; intégration continue GitHub Actions.

Contraintes d'exploitation :

- Tourne sur un portable avec 16 Go de RAM.
- Démarrage complet en moins de 2 minutes après la première installation.
- Mode hors ligne complet pour la démonstration (fond de carte local, données en base, rapports en cache, polices locales).

## 12. Modèle de données (première version)

- **territories** : id, code officiel, nom_fr, nom_ar, niveau (région, préfecture ou province, commune, arrondissement, quartier, douar, maille), parent_id, milieu (urbain, rural), géométrie, surface, source_id.
- **study_areas** : territoires de démonstration (Rabat, Tétouan) avec leur profil de grille, profil de taxonomie et configuration.
- **data_sources** : nom, producteur, URL, date de publication, date d'import, licence, badge par défaut, notes.
- **indicator_definitions** : chargées depuis le YAML, avec version de grille.
- **indicator_values** : territoire, indicateur, année, valeur, unité, source_id, badge, score de fiabilité, méthode, diagnostic_id éventuel.
- **raw_variables** : variables d'entrée (population par âge, ménages, raccordements…) par territoire et année, avec source.
- **facilities** : type normalisé, sous-type, nom, géométrie, source, date.
- **built_up** : territoire, année, surface bâtie, source.
- **urban_documents** et **document_chunks** (texte, page, embedding).
- **consultations**, **contributions** (texte original, langue, texte anonymisé, traduction, thèmes, tonalité, localité, commune, badge, rapport d'anonymisation).
- **diagnostics** : territoire, version de grille, statut, résultat JSON, auteur, date.
- **reports** : diagnostic, langue, format, fichier, statut, historique de validation, fiche de faits utilisée.
- **data_holders** et **data_requests** : institutions, données demandées, statut de la demande (à envoyer, envoyée, accordée, refusée), date.
- **users**, **roles**, **audit_log**.

Prévois les tables futures sans les implémenter : **projects** (module 3), **land_parcels** et **investor_profiles** (module 4).

## 13. Interface et design

- Style **institutionnel et sobre**, cohérent avec la présentation du projet :
  - bleu pétrole `#12343B` (titres, éléments forts), terre cuite `#A8461F` (accent, une seule chose mise en avant par écran), crème `#F6F3EC` (fonds), gris bleu `#4A5560` (texte secondaire) ;
  - typographies : EB Garamond pour les titres, IBM Plex Sans pour le texte, IBM Plex Sans Arabic ou Noto Naskh Arabic pour l'arabe ; polices embarquées localement.
- Couleurs de carte : palettes séquentielles et divergentes accessibles aux daltoniens ; une information n'est jamais portée par la couleur seule (texte ou icône en plus).
- Contraste suffisant (WCAG AA), navigation au clavier, tailles lisibles sur un vidéoprojecteur.
- RTL complet en arabe (mise en page miroir, chiffres et unités correctement affichés).
- Libellés en langage clair : pas de « KPI », « dataset », « choroplèthe » dans l'interface ; préférer « indicateur », « données », « carte ».
- Toutes les pages s'impriment proprement.

## 14. Sécurité, données personnelles et conformité

- Loi 09-08 et CNDP : aucune donnée personnelle réelle dans la version D ; pour la version P, prévois minimisation, anonymisation, journal des accès, chiffrement au repos des données sensibles, durée de conservation et suppression sur demande. Rédige `docs/conformite-09-08.md` listant les traitements et les mesures (base pour une future déclaration à la CNDP).
- Authentification par session sécurisée, mots de passe hachés, rôles vérifiés côté serveur.
- Secrets uniquement dans `.env` (avec `.env.example` sans valeur réelle) ; `.env` exclu du dépôt.
- Aucune donnée personnelle ne part vers un service d'IA externe, même en version D (anonymisation systématique avant appel).
- Dépendances épinglées ; vérification des vulnérabilités connues dans l'intégration continue.

## 15. Qualité et définition de « terminé »

Une étape est terminée quand :

- les fonctionnalités prévues marchent dans le scénario de démonstration ;
- les tests unitaires et d'intégration passent, y compris les tests anti-invention de chiffres et d'anonymisation ;
- le linter et le typage ne signalent aucune erreur ;
- le README et `CLAUDE.md` sont à jour ;
- tu as fourni au porteur du projet : ce qui marche, **comment le vérifier pas à pas** (commandes et clics), ce qui reste, les questions ouvertes ;
- un commit propre (ou une série de commits) porte le travail, avec un message clair.

## 16. Organisation du dépôt

- `backend/app/api/` : routes
- `backend/app/models/` : modèles de données
- `backend/app/ingestion/` : importeurs par source
- `backend/app/services/indicators/` : moteur d'indicateurs et fiabilité
- `backend/app/services/reports/` : fiche de faits, rédaction, rendu, vérification, exports
- `backend/app/services/citizen/` : anonymisation, langue, classification, croisement
- `backend/app/services/rag/` : assistant documentaire
- `backend/app/services/data_needs/` : besoins en données et notes de demande
- `backend/app/services/llm/` : fournisseurs IA et cache
- `backend/tests/`
- `frontend/` : application Next.js (pages : accueil, province, commune, comparaison, citoyens, rapports, besoins en données, assistant, administration, présentation)
- `config/` : `territories/` (`rabat.yaml`, `tetouan.yaml`), `indicators/`, `taxonomy/`, `report_templates/`, `data_holders/`, `confidence.yaml`
- `data/raw/`, `data/demo/`, `data/tiles/`
- `docs/` : `BRIEF.md`, `sources.md`, `decisions/`, `grille-indicateurs-guide.md`, `guide-demonstration.md`, `guide-utilisateur.md`, `conformite-09-08.md`
- `CLAUDE.md`, `README.md`, `docker-compose.yml`, `Makefile`, `.env.example`

## 17. Plan de travail par étapes (version D)

Chaque étape dure environ une semaine (soit environ 9 semaines au total) et se termine par une démonstration au porteur du projet.

**Étape 0 — Environnement et squelette**
Vérifie les prérequis de la machine (Docker, Git, Node, Python) et explique comment installer ce qui manque. Crée le dépôt, `CLAUDE.md`, Docker Compose, backend et frontend minimaux, base PostGIS, intégration continue.
*Acceptation* : `make setup` puis `make dev` affichent une page d'accueil MAJAL ; `make test` passe.

**Étape 1 — Rabat : territoire réel et carte**
Mécanisme multi-territoires (configuration, sélecteur, même s'il n'y a qu'un territoire pour l'instant), import des limites de Rabat (arrondissements, communes, niveau fin), import OpenStreetMap (équipements, routes), fond de carte hors ligne, page province avec carte, survol et badges.
*Acceptation* : la carte affiche les vrais arrondissements et communes de Rabat avec leurs noms en français et en arabe, les équipements et la source des limites ; fonctionne sans internet.

**Étape 2 — Rabat : indicateurs et fiche commune**
Saisie ou import des données du recensement disponibles, tache bâtie, grille provisoire YAML et son schéma, moteur de calcul, score de fiabilité, fiche commune, comparaison, sélecteur d'indicateurs sur la carte.
*Acceptation* : chaque commune a sa fiche ; chaque valeur a source, date et badge ; modifier une ligne YAML modifie le résultat sans toucher au code ; une valeur manquante s'affiche « non disponible ».

**Étape 3 — Rabat : rapport IA vérifié**
Fiche de faits, rédaction par identifiants, rendu, vérification, exports DOCX et PDF en français, statuts, cache hors ligne.
*Acceptation* : rapport d'une commune en moins d'une minute ; les 15 tests pièges passent ; aucun nombre non tracé ; le rapport s'ouvre correctement dans Word.

**Étape 4 — Rabat : écoute citoyenne**
Jeu fictif de contributions pour Rabat, import, anonymisation, langue, classification, localisation, tableau de bord, croisement avec les indicateurs, script d'évaluation.
*Acceptation* : tableau de bord complet sur le territoire ; tests d'anonymisation passés ; précision et rappel affichés.

**Étape 5 — Rabat : besoins en données et assistant documentaire**
Référentiel des institutions, écran de complétude, notes de demande de données en DOCX et PDF, tableau Excel ; assistant documentaire si le temps le permet.
*Acceptation* : une note par institution est générée, propre et prête à signer ; l'écran montre ce qui manque et ce que chaque donnée permettrait.

**Étape 6 — Deuxième territoire : Tétouan**
Fichier de configuration de Tétouan, profil de grille `mixte` et taxonomie `mixte`, import des limites des communes (urbaines et rurales) et des douars si une source fiable existe, données du recensement, OpenStreetMap, tache bâtie, contributions fictives localisées par douar, référentiel des institutions, vue « Deux territoires ».
*Acceptation* : Tétouan fonctionne de bout en bout (carte, fiches, rapport d'une commune rurale, écoute citoyenne, besoins en données) ; le passage d'un territoire à l'autre est instantané ; les seuls changements de code nécessaires sont listés et justifiés dans une note de décision (l'objectif est zéro changement de la logique métier).

**Étape 7 — Arabe, mode présentation et kit de démonstration**
Interface et rapport en arabe, mode présentation, finitions visuelles, tests de bout en bout du scénario, `docs/guide-demonstration.md` (déroulé minute par minute, questions fréquentes des décideurs et réponses, plan B si quelque chose ne marche pas).
*Acceptation* : le porteur du projet déroule le scénario complet, sur les deux territoires, hors ligne et en moins de 20 minutes, sans aide.

**Après la version D — Version P (pilote)**, à planifier quand un décideur accepte : import des données officielles, vraies contributions et audio, hébergement au Maroc, IA locale, comptes des agents, formation, mesure d'impact.

## 18. Livrables du kit de démonstration pour le professeur

1. L'application installée sur le portable de démonstration, fonctionnant hors ligne.
2. Deux rapports de diagnostic exemples en PDF, en français et en arabe : un arrondissement de Rabat et une commune rurale de Tétouan.
3. Les notes de demande de données par institution et par territoire, prêtes à compléter et signer.
4. Une note méthodologique d'une page : sources, badges de confiance, limites, garde-fous de l'IA.
5. Le guide de démonstration (`docs/guide-demonstration.md`).

## 19. Ce que tu ne dois jamais faire

- Inventer une statistique, une commune, un code officiel, une norme d'urbanisme ou une source.
- Présenter une donnée fictive ou estimée comme officielle.
- Laisser le modèle de langage écrire un nombre directement dans un rapport.
- Envoyer une donnée personnelle à un service externe.
- Coder en dur un indicateur, une norme ou un thème qui relève du professeur.
- Écrire des secrets dans le code ou les commits.
- Supprimer des données ou des fichiers du porteur du projet sans confirmation explicite.
- Passer à l'étape suivante sans validation de l'étape en cours.

## 20. Méthode de travail

1. Lis ce document en entier. Crée `CLAUDE.md` : résumé du projet, conventions, commandes, décisions ; tiens-le à jour à chaque étape.
2. Avant chaque étape : présente un plan court (tâches, fichiers, tests, risques) et attends la validation.
3. Avance par petits incréments testés ; lance les tests après chaque changement significatif ; commits fréquents et clairs.
4. Explique au porteur du projet, en français simple, ce que tu as fait et comment le vérifier ; donne les commandes exactes.
5. Questions de méthode → au professeur, regroupées, avec ta proposition par défaut ; en attendant, valeur provisoire marquée `TODO_REFERENT` et liste tenue dans `docs/questions-referent.md`.
6. Choix techniques structurants → note de décision courte dans `docs/decisions/` (contexte, options, choix, conséquences).
7. Si une source de données est inaccessible ou un outil impossible à installer, dis-le clairement et propose une alternative au lieu de contourner en silence.

## 21. Glossaire pour le contexte

- **PDTI** : programmes de développement territorial intégré (nouvelle génération 2026).
- **PDR** : plan de développement régional. **PAC** : plan d'action communal. **SRAT** : schéma régional d'aménagement du territoire.
- **SDAU** : schéma directeur d'aménagement urbain. **PA** : plan d'aménagement.
- **Agence urbaine** : établissement public chargé des documents d'urbanisme et de l'instruction des autorisations.
- **CRI** : centre régional d'investissement. **AREP** : agence régionale d'exécution des projets.
- **HCP** : Haut-Commissariat au Plan (statistique officielle). **RGPH** : recensement général de la population et de l'habitat (2014, 2024).
- **CNDP** : Commission nationale de contrôle de la protection des données à caractère personnel (loi 09-08).
- **Arrondissement** : subdivision d'une grande commune urbaine, dotée d'un conseil d'arrondissement (cas de Rabat).
- **Préfecture** : équivalent urbain de la province.
- **SDL** : société de développement local, outil des collectivités pour porter des projets.
- **Douar** : hameau rural, unité de localisation fréquente dans les contributions citoyennes en milieu rural (Tétouan).

## 22. Première tâche

1. Pose tes **questions bloquantes** (10 au maximum), regroupées par destinataire : porteur du projet, professeur. Pour chacune, propose une réponse par défaut.
2. Vérifie les **prérequis** de la machine et liste ce qu'il faut installer, avec les commandes.
3. Propose l'**arborescence** du dépôt, le format des fichiers `config/territories/*.yaml` pour Rabat et Tétouan, et le **plan détaillé des étapes 0 et 1**.
4. Après validation, réalise l'**étape 0**, puis fais la démonstration de fin d'étape.
