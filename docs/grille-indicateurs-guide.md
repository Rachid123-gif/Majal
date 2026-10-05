# Guide de la grille d'indicateurs

Ce guide s'adresse au référent scientifique. Il explique comment modifier la méthode de
MAJAL **sans programmer**. La grille actuelle est la **grille v0** (`docs/methodologie-v0.md`),
affichée dans l'application comme « Grille v0 — proposition en cours de validation ».

## Les quatre fichiers de la méthode

| Fichier | Contenu |
| --- | --- |
| `config/indicators/grille-v0.yaml` | Les 8 axes et les 28 indicateurs |
| `config/indicators/evaluation.yaml` | La règle d'évaluation relative et ses seuils (80 %, 95 %) |
| `config/mappings/osm_facilities.yaml` | Ce qui compte comme école, centre de santé, parc… dans OpenStreetMap |
| `config/confidence.yaml` | Les badges (Officiel, Ouvert, Estimé, Fictif) et le score de fiabilité |

Ce sont de simples fichiers texte. Ils s'ouvrent avec TextEdit ou n'importe quel éditeur.

## Après chaque modification

1. Enregistrez le fichier.
2. Vérifiez-le (dans le Terminal, dossier du projet) :
   ```bash
   make check-config
   ```
   En cas d'erreur, le message indique le fichier, la **ligne**, le problème et un exemple correct.
3. Rouvrez la carte ou la fiche : MAJAL détecte la modification et **recalcule tout seul**.
   Un bouton « Recalculer » existe aussi sur la carte.

## Lire un indicateur

```yaml
  - code: EMP_CHOM                       # identifiant, en majuscules, unique
    axis: emploi                         # l'un des 8 axes
    label: { fr: "Taux de chômage", ar: "معدل البطالة" }
    unit: { fr: "%", ar: "%" }
    profiles: [urbain, mixte]            # urbain = Rabat, mixte = Tétouan
    direction: lower_better              # higher_better (plus = mieux), lower_better (moins = mieux), neutral
    formula: { type: raw, input: unemployment_rate, year: 2024 }
    decimals: 1                          # chiffres après la virgule à l'affichage
    source_expected: "HCP, RGPH 2024 (officiel)"
    reference: relative                  # relative = comparé à la moyenne ; none = indicateur de contexte
    norm: { value: null, source: TODO_REFERENT }
    status: TODO_REFERENT
```

## Ajouter une norme officielle

Dès qu'une norme est connue, remplacez `null` par sa valeur et indiquez sa source :

```yaml
    norm: { value: 2.5, source: "Grille normative des équipements, ministère X, 2019" }
```

L'indicateur n'est alors plus comparé à la moyenne mais à la norme : « déficit marqué » sous la
norme, « dans la norme » au-dessus (au-dessous pour un indicateur « moins = mieux »).

## Modifier un seuil de distance

Dans les indicateurs de proximité, `distance_m` est en mètres :

```yaml
    formula: { type: proximity_share, all_of: [[bus_stop, tram_stop]], distance_m: 500 }
```

Pour passer à 400 m, écrivez `distance_m: 400`.

## Modifier les seuils d'évaluation

Dans `config/indicators/evaluation.yaml` :

```yaml
thresholds:
  higher_better: { deficit_marked: 0.80, watch: 0.95 }
  lower_better:  { deficit_marked: 1.20, watch: 1.05 }
```

`0.80` signifie « 80 % de la moyenne de l'agglomération ». Les seuils doivent rester dans
l'ordre (pour « plus = mieux » : `deficit_marked` < `watch` ≤ 1).

## Désactiver un indicateur

Ajoutez `enabled: false` dans son bloc. Il disparaît de la carte, des fiches et des rapports,
sans être supprimé.

## Ajouter un indicateur

Copiez un bloc existant, changez le `code` (unique), le libellé et la formule. Types de formule
disponibles :

| Type | Ce qu'il calcule | Exemple |
| --- | --- | --- |
| `raw` | Une valeur publiée telle quelle | Taux de chômage du HCP |
| `ratio` | Un rapport (× `per`) | Établissements pour 10 000 habitants |
| `density` | Valeur par km² | Densité de population |
| `cagr` | Taux de croissance annuel moyen entre deux années | Croissance 2014-2024 |
| `change` | Variation en % entre deux années | Croissance de la surface bâtie |
| `proximity_share` | Part de la population à moins de X m d'un ou plusieurs types d'équipements | Accès aux transports |
| `distance_mean` | Distance moyenne de la population à l'équipement le plus proche | Distance à l'hôpital |
| `area_per_capita` | Surface d'équipements par habitant | Espaces verts par habitant |
| `built_up` | Surface bâtie (imagerie satellite) | Tache bâtie 2020 |
| `consumption` | Surface bâtie ajoutée par habitant supplémentaire | Étalement urbain |

Les données d'entrée disponibles (`input`) sont listées dans
`config/mappings/hcp_rgph.yaml` (variables du recensement) ; les catégories d'équipements dans
`config/mappings/osm_facilities.yaml`. Si une donnée d'entrée n'existe pas encore, l'indicateur
s'affiche « non disponible » avec la donnée manquante : il n'est **jamais** mis à zéro.

## Règles d'honnêteté appliquées automatiquement

- **Non disponible** : donnée absente (avec la raison) ; l'indicateur alimente les besoins en
  données.
- **Recensement insuffisant** : un indicateur fondé sur des équipements OpenStreetMap n'est
  calculé que si l'ensemble étudié en compte au moins `facility_minimum` (10 par défaut, dans
  `evaluation.yaml`).
- **Non évaluable** : unité signalée (ex. limite incorrecte de Sidi Bouknadel, dans
  `config/territories/rabat.yaml` → `quality_flags`) ; ses indicateurs spatiaux ne sont pas
  calculés et elle est exclue des classements.
- **Contexte** : indicateurs « neutral » (population, âge, bâti) : présentés sans jugement.
