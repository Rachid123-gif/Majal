# 0012 — Population carroyée et tache bâtie (GHSL)

- **Date** : 2026-10-05 · **Statut** : accepté

## Contexte
Les indicateurs « part de la population à moins de… » exigent de savoir où vivent les
habitants à l'intérieur des communes. Aucune donnée officielle infra-communale n'est publiée.

## Choix
- **GHS-POP R2023A** (JRC, 2020, 3″ ≈ 90 m) : la population de chaque cellule est recalée pour
  que la somme des cellules d'une unité égale sa **population légale 2024** (méthode
  dasymétrique simple). Les cellules sont rattachées à l'unité par leur centre.
- **GHS-BUILT-S R2023A** (2015 et 2020) : surface bâtie par unité. Les époques 2025 et 2030
  du GHSL étant des projections, seules les époques observées sont utilisées.
- Distances à vol d'oiseau, sur l'ellipsoïde ; l'équipement le plus proche est cherché dans
  l'ensemble étudié (effet de bord possible aux limites extérieures).
- Badge **Estimé** pour tous les indicateurs de proximité.

## Conséquences
- Indicateurs de proximité calculables partout, honnêtement marqués comme estimations.
- À remplacer par une répartition officielle (îlots, districts du recensement) en version P.
