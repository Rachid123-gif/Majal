# 0017 — Écoute citoyenne : anonymisation, analyse locale, localisation, tableau de bord

- **Date** : 2026-10-06 · **Statut** : accepté (étape 4, Rabat)

## Contexte
BRIEF §9.6 : contributions en français, arabe, darija et amazighe ; anonymisation avant tout
traitement par l'IA ; classement selon une taxonomie ; localisation ; tableau de bord ; croisement
avec les indicateurs ; évaluation. Version D : contributions fictives, clairement marquées.

## Choix
- **Données** : tables `places` (lieux nommés OpenStreetMap, importeur `osm_places`),
  `consultations`, `contributions` (migrations 0005, 0006). Import CSV ou Excel (modèle
  `docs/modeles/contributions-modele.xlsx`), réservé aux comptes professeur et administrateur.
- **Anonymisation d'abord** (`app/services/citizens/anonymize.py`, listes dans
  `config/citizens/anonymisation.yaml`) : règles (e-mails, téléphones marocains, CIN, plaques,
  adresses), prénoms et tournures de présentation, lieux connus protégés, gentilés et métiers
  exclus ; l'IA ne voit que le texte anonymisé ; le rapport donne type et position, jamais la
  valeur.
- **Analyse par l'IA locale** (un appel par contribution, sortie structurée) : langue,
  traduction française (noms de lieux translittérés, jamais traduits), thème principal et second
  thème seulement s'il est explicite — vérifié : un mot-clé du second thème doit figurer dans le
  texte ou sa traduction, sinon il est retiré —, tonalité, lieu cité (retenu seulement s'il est
  écrit dans le texte ; la consigne ne contient aucun nom de lieu réel, qu'un modèle recopierait). Réponses contrôlées ; repli par
  mots-clés (`config/citizens/analyse.yaml`, mots-clés de la taxonomie), aussi utilisé comme point
  de comparaison. Langue des marqueurs retenue pour la darija et l'amazighe.
- **Localisation par la liste des lieux connus seulement** (unités, lieux, avenues) : un nom
  ambigu (présent dans deux unités) ne se rattache qu'avec la commune déclarée ; un nom de lieu
  qui est aussi un mot courant en arabe exige un mot de lieu devant (« حي … »). Jamais de lieu
  inventé : sinon « lieu non identifié ».
- **Statistiques** : le thème principal seulement ; les thèmes secondaires sur demande, avec une
  mention de moindre fiabilité ; en dessous de 20 contributions, des nombres, pas de
  pourcentages ; pas de conclusion en dessous de 5. Verbatims : contributions dont la langue et le
  thème principal sont sûrs d'abord (IA et mots-clés d'accord), original anonymisé toujours à côté
  de la traduction marquée « traduction automatique ».
- **Évaluation** : précision, rappel, exactitude, toujours avec leur base de mesure ; provisoire
  (annotation de Claude, en partie circulaire) et de référence (classement du professeur,
  amazighe exclu).
- **Bandeau permanent** « Contributions fictives — illustration du fonctionnement de l'outil.
  Elles ne reflètent pas l'opinion réelle des habitants. » sur toute vue de contributions
  fictives.

## Compléments (2026-10-06, après l'évaluation par un second modèle)
- **Jeu fictif porté à 400 contributions** (même méthode neutre, 140 textes conservés).
- **Échelle « commune »** : Rabat et Salé regroupent leurs arrondissements ; les autres unités
  restent telles quelles. Aucune valeur d'indicateur agrégée n'est calculée : un indicateur est
  jugé défavorable pour la commune si les unités en « déficit marqué » ou « à surveiller »
  réunissent au moins la moitié de sa population (`aggregate_unfavourable_share`, TODO_REFERENT).
- **Tonalité** : mots-clés en priorité, IA locale seulement quand aucun mot-clé ne tranche.
- **Taxonomie précisée** : eau potable, coupures, égouts et bouches d'égout relèvent toujours
  de « eau et assainissement » ; crèche et préscolaire de « éducation ».
- Ces deux derniers points ont été décidés après avoir vu les désaccords avec l'annotation du
  second modèle d'IA : l'évaluation sur ce classement est donc en partie optimiste (mention
  affichée avec les résultats).
- **Section 7 du rapport** : phrase modèle « {{F920}} contributions citoyennes ont été
  localisées dans l'unité ; les thèmes principaux sont… » ; la tournure « s'établissent à »
  est refusée.

## Compléments (2026-10-06, après validation du croisement)
- **Libellés des constats** : ils reprennent le statut réel de l'indicateur. « Déficit marqué »
  seulement pour ce statut, sinon « indicateur à surveiller » (exemple : « Indicateur à
  surveiller, sans demande exprimée »). À l'échelle de la commune, « déficit marqué » seulement
  si les unités dans ce statut réunissent à elles seules la part de population requise.
- **Absence de demande** : « sans demande exprimée » n'est permis que si l'unité compte au moins
  30 contributions au total (`absence_min_total`, TODO_REFERENT) ; en dessous : « Trop peu de
  contributions pour juger de l'absence de demande ».
- **File de validation — l'outil propose, l'urbaniste valide.** Une contribution est marquée
  « à vérifier » quand l'IA et les mots-clés ne donnent pas le même thème principal (y compris,
  réglable, quand les mots-clés ne trouvent aucun thème) ou quand la langue est incertaine
  (amazighe, langue non reconnue, désaccord IA / repères) — `config/citizens/analyse.yaml`,
  section `review`. L'écran « À vérifier » (`/territoire/<code>/citoyens/verifier`) est réservé
  aux comptes professeur et administrateur : original, traduction, propositions de l'outil et
  des mots-clés, correction du thème, de la tonalité et du lieu en un clic.
- Une correction humaine est écrite dans les champs que lisent les statistiques, le croisement
  et la section 7 : elle remplace donc la proposition partout, avec « validé par [compte] ». La
  proposition de l'outil est conservée à part (`ai_proposal`, migration 0007) : les évaluations
  de l'IA portent toujours sur sa propre proposition, et une nouvelle analyse n'efface jamais
  une validation humaine.
- Les corrections forment progressivement un **jeu d'évaluation humain**, compté à part dans
  « Fiabilité de l'analyse », avec sa base : surtout des cas difficiles, donc non représentatif
  de l'ensemble.
- Section 7 : tant qu'aucune correction n'existe, le rapport est inchangé ; dès qu'une
  contribution de l'unité est validée, une phrase « Classement vérifié par une personne pour
  N contributions (validé par …) » est ajoutée et le rapport de l'unité est à régénérer.
