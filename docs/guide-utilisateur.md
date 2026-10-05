# Guide utilisateur

Ce guide sera complété à chaque étape.

## Territoires (`config/territories/<code>.yaml`)

Chaque territoire de démonstration est décrit par un fichier texte. Modifier ce fichier ne
demande aucune compétence en programmation. Après chaque modification, lancez
`make check-config` : en cas d'erreur, MAJAL indique le fichier, la ligne et un exemple correct.

| Champ | Signification |
| --- | --- |
| `code` | Identifiant court, identique au nom du fichier (`rabat` pour `rabat.yaml`) |
| `name`, `region` | Nom du territoire et de sa région, en français (`fr`) et en arabe (`ar`) |
| `study_area` | Le territoire étudié : `level` (`prefecture` ou `province`) et son libellé |
| `scopes` | Périmètres d'analyse proposés. Un seul porte `default: true`. `members` liste les préfectures ou provinces qui le composent |
| `analysis_levels.main` | Unités d'analyse principales (`arrondissement`, `commune`…) et leur nom affiché |
| `analysis_levels.fine` | Unité fine : `grid` (carreaux, avec `cell_size_m` en mètres) ou `douar` (avec `fallback: grid` si aucune source fiable) |
| `profiles` | Grille d'indicateurs et liste de thèmes citoyens utilisées (`urbain` ou `mixte`) |
| `sources` | Sources de données à importer (renseigné à partir de l'étape 1) |
| `data_holders` | Fichier des institutions détentrices de données (étape 5) |
| `map` | Centre et zoom de la carte ; `null` = calculé automatiquement |
| `demo` | Fichier des contributions citoyennes fictives (étape 4) |

Valeurs possibles pour les niveaux : `region`, `prefecture`, `province`, `commune`,
`arrondissement`, `quartier`, `douar`, `grid`.

Ces fichiers ne contiennent jamais de code officiel ni de limite : ces éléments viennent
toujours d'une source réelle importée.
