# 0016 — Typologie des communes (proposition)

- **Date** : 2026-10-05 · **Statut** : proposition, TODO_REFERENT

## Choix
- Méthodologie v0, section 5 : k-moyennes (graine fixe, résultat reproductible) sur 7 indicateurs
  standardisés (`config/indicators/typologie.yaml`).
- Chaque groupe est rapproché du profil-type dont la « signature » lui ressemble le plus. Sous le
  seuil `min_match_score`, il reste « Groupe N — profil à nommer » : aucun nom n'est forcé.
- Une unité à laquelle il manque une donnée n'est pas classée (Sidi Bouknadel aujourd'hui).
- Affichée comme « proposition, à valider » sur la fiche et dans la synthèse des rapports.
