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

## Carte du territoire

Après connexion : **Tableau de bord → Ouvrir la carte du territoire**, ou directement
http://localhost:3000/territoire/rabat.

- **Survoler** une unité affiche son nom en français et en arabe et son niveau de confiance.
- **Cliquer** ouvre le détail : rattachement, surface, code officiel (non disponible pour
  l'instant), nombre d'équipements par catégorie.
- **Périmètre** (à gauche) : agglomération Rabat-Salé-Skhirate-Témara ou préfecture de Rabat.
- **Équipements** : cocher ou décocher chaque catégorie.
- **Exporter la carte** : télécharge une image PNG avec le titre et les sources.
- Les sources et leur date sont toujours affichées en bas de la carte.

## Catégories d'équipements (`config/mappings/osm_facilities.yaml`)

Chaque catégorie regroupe une ou plusieurs étiquettes OpenStreetMap (« clé=valeur », par
exemple `amenity=school`). Pour ajouter une étiquette, l'écrire dans `rules` ; pour écarter
certains objets, l'écrire dans `exclude` ; pour masquer une catégorie, mettre
`enabled: false`. Ensuite : `make check-config` puis `make data`.

## Mettre à jour les données

```bash
make data
```

Les données déjà téléchargées sont réutilisées (fonctionne hors ligne). Pour tout
retélécharger depuis OpenStreetMap :

```bash
REFRESH=1 make data
```

## Rapports de diagnostic (IA locale)

1. Ouvrez Ollama sur le Mac (l'icône du lama apparaît dans la barre des menus).
2. Lancez MAJAL (`make start`), ouvrez la fiche d'une commune ou d'un arrondissement.
3. En bas de la fiche, choisissez la langue puis « Générer le diagnostic ». La rédaction prend
   environ une minute ; la progression s'affiche section par section.
4. Relisez le rapport, puis « Marquer comme relu ». Seul le compte « professeur » peut le valider.
   Tant qu'il n'est pas validé, le filigrane « Document de travail » reste sur les exports.
5. Téléchargez-le en Word ou en PDF (français ; l'arabe arrive à l'étape 7).

Bon à savoir :

- **Aucune donnée ne quitte l'ordinateur** (mode souverain, réglage `SOVEREIGN_MODE=true` dans `.env`).
- **L'IA n'écrit aucun chiffre** : MAJAL les insère et les vérifie. MAJAL contrôle aussi le
  sens : une évolution doit suivre la valeur calculée (pas de « hausse » pour une population qui
  baisse), rien n'est affirmé sur une donnée manquante, pas de jugement subjectif. Une phrase
  fautive est réécrite, ou la section est rédigée sans IA. Les contrôles ne voient pas tout :
  la relecture par un urbaniste reste indispensable.
- Les mots surveillés sont dans `config/report_templates/controles.yaml` (modifiable).
- **Si Ollama est fermé**, le rapport est rédigé quand même, sans IA, à partir de phrases-types
  (l'écran l'indique).
- Les rapports sont gardés en mémoire : un rapport déjà rédigé s'affiche immédiatement. Pour tout
  préparer avant une présentation :

```bash
make reports
```

- Changer de modèle : ligne `OLLAMA_MODEL=` dans `.env`, puis `make start`. Si ce modèle n'est
  pas installé, MAJAL utilise `OLLAMA_FALLBACK_MODEL` (gemma3:4b).
