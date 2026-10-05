# 0011 — Moteur d'indicateurs et évaluation relative

- **Date** : 2026-10-05 · **Statut** : accepté

## Choix
- La méthode est entièrement déclarative : `grille-v0.yaml` (indicateurs), `evaluation.yaml`
  (seuils, référence, minimum d'équipements), `confidence.yaml` (badges, score de fiabilité),
  fichiers de correspondance. Le code ne contient ni indicateur, ni norme, ni seuil.
- Dix types de formule génériques (voir `docs/grille-indicateurs-guide.md`).
- **Référence** : moyenne pondérée par la population 2024 des unités du périmètre par défaut
  (agglomération, ou province), hors unités exclues des classements. Une norme renseignée dans
  la grille remplace la référence relative.
- **Statuts** : déficit marqué, à surveiller, dans la moyenne ou au-dessus, contexte (indicateur
  neutre), non évaluable, non disponible, non applicable. Une valeur manquante n'est jamais
  remplacée par zéro ; la raison est conservée.
- **Badge** d'une valeur calculée : celui de sa donnée d'entrée la moins fiable.
  **Score de fiabilité** : source + ancienneté + complétude + méthode (`confidence.yaml`).
- **Rang** : sur les unités du périmètre par défaut ayant une valeur, hors unités exclues ;
  pour un indicateur de contexte, le rang ordonne seulement les valeurs.
- Chaque calcul produit un **diagnostic versionné** (table `diagnostics`, résultat JSON +
  `indicator_values`), avec l'empreinte des fichiers de méthode : l'API recalcule
  automatiquement quand un fichier change. Durée mesurée : 1,5 à 4 s pour Rabat.

## Conséquences
- Modifier une ligne de YAML modifie le résultat sans toucher au code (vérifié : seuil 0,95 →
  0,99 sur EMP_ACTF fait passer 2 communes de « dans la moyenne » à « à surveiller »).
- Les 10 derniers diagnostics sont conservés par territoire.
