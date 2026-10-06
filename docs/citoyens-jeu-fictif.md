# Jeu de contributions citoyennes fictives — Rabat (méthode)

> **Contributions fictives — illustration du fonctionnement de l'outil. Elles ne reflètent pas
> l'opinion réelle des habitants.**

## Pourquoi un jeu fictif

La version de démonstration n'utilise aucune contribution réelle (BRIEF §4 et §9.6). Le jeu sert
à montrer le fonctionnement de MAJAL : import, anonymisation, langue, classement, localisation,
tableau de bord, croisement avec les indicateurs.

## Fichiers

| Fichier | Contenu |
| --- | --- |
| `data/fictif/rabat/plan.csv` | Plan tiré au hasard : unité, thème(s), langue, tonalité, lieu cité ou non, commune déclarée ou non, piège d'anonymisation |
| `data/fictif/rabat/contributions.yaml` | Les 140 textes, avec l'annotation **provisoire** de Claude (thèmes, tonalité, unité, lieu, données personnelles piégées) |
| `data/fictif/rabat/contributions.csv` | Les mêmes textes au format d'import (ce que MAJAL lit) |
| `docs/evaluation/annotation-professeur.xlsx` | 30 contributions à classer par le professeur : **évaluation de référence** |
| `docs/modeles/contributions-modele.xlsx` et `.csv` | Modèle de fichier d'import, vide |
| `config/citizens/termes-interdits.yaml` | Liste modifiable des termes interdits, vérifiée par un test |

## Une répartition neutre, pour un croisement non circulaire

Si les contributions avaient été réparties pour confirmer les indicateurs réels (plus de plaintes
sur les espaces verts là où ils manquent), le croisement « ce que disent les citoyens / ce que
montrent les données » aurait l'air de fonctionner par construction. Le plan
(`scripts/plan_fictional_contributions.py`, graine 2026) suit donc ces règles :

- **nombre par unité** : au moins 2, le reste proportionnel à la population légale 2024 (HCP).
  C'est la seule donnée lue, et elle n'est liée à aucun thème ;
- **thèmes** : tirés au hasard, avec les **mêmes poids dans toutes les unités** (tous les thèmes
  à égalité, « autres » à moitié) ; 20 % des contributions reçoivent un second thème ;
- **langue, tonalité, lieu cité, commune déclarée, pièges** : tirés au hasard selon des
  proportions fixes (35 % français, 25 % arabe, 20 % darija en alphabet arabe, 15 % en alphabet
  latin, 5 % amazighe ; 40 % demandes, 35 % plaintes, 15 % propositions, 10 % satisfactions).

Les textes ont ensuite été rédigés un par un pour chaque ligne du plan. Les écarts observés au
croisement relèvent donc du hasard : **ils ne disent rien des habitants réels**. Ils montrent
seulement comment l'outil présenterait de vraies contributions.

## Résultat du tirage

- 140 contributions : français 55, arabe 45, darija en alphabet latin 21, darija en alphabet
  arabe 14, amazighe 5.
- Tonalité : plaintes 60, demandes 53, propositions 14, satisfactions 13.
- 29 contributions à deux thèmes. Thèmes les plus tirés : accessibilité des personnes à mobilité
  réduite 17, voirie 12, commerce et marchés 11, éclairage 11, eau et assainissement 11 ; les
  moins tirés : patrimoine 4, logement 4 (effet du hasard, assumé).
- 119 contributions citent un lieu ; 69 indiquent une commune ; 12 n'ont ni l'un ni l'autre
  (elles resteront « lieu non identifié »).
- 22 contributions contiennent des données personnelles **visiblement fictives** pour tester
  l'anonymisation : téléphones 06 00 00 0x xx, cartes d'identité ZZ0000xx, adresses e-mail
  @example.com, adresses « n° 00 », plaque 00000-ب-99, prénoms seuls.

## Règles de rédaction (vérifiées automatiquement quand c'est possible)

- Aucune personne réelle, aucun élu ni responsable, ni sa fonction ; aucune entreprise, école,
  clinique ou commerce réel nommé. Les lieux réels (quartiers, places, avenues d'OpenStreetMap)
  ne sont que des repères neutres ; les noms de lieux qui désignent un organisme ou une
  entreprise ont été écartés.
- Aucune accusation, aucun contenu politique, religieux ou injurieux.
- Test `backend/tests/test_fictional_contributions.py` : aucun terme interdit ; conformité au
  plan ; pièges présents et visiblement fictifs ; aucun nom propre inconnu en alphabet latin.
- Les textes en amazighe sont approximatifs : à relire par un locuteur.

## Deux évaluations distinctes

- **Provisoire** : sur l'annotation de Claude (qui a aussi rédigé les textes : évaluation en
  partie circulaire, affichée comme telle).
- **De référence** : sur les 30 contributions classées par le professeur
  (`docs/evaluation/annotation-professeur.xlsx`), indépendante.
