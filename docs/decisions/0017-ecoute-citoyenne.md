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
