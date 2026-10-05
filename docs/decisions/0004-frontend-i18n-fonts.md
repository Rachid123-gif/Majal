# 0004 — Frontend : traduction et polices hors ligne

- **Date** : 2026-10-05 · **Statut** : accepté

## Contexte
L'interface doit être en français et en arabe (RTL complet), basculer instantanément en mode
présentation et fonctionner sans internet (BRIEF §9.9, §13).

## Choix
- **Traduction** : dictionnaires `src/i18n/fr.json` et `ar.json`, avec un fournisseur React
  léger qui bascule `lang` et `dir="rtl"` sur la page sans la recharger. Le choix de langue est
  mémorisé dans le navigateur. Aucune bibliothèque de routage par langue, car la bascule doit
  rester instantanée pendant une démonstration.
- **Polices** : EB Garamond, IBM Plex Sans et IBM Plex Sans Arabic, fournies par les paquets
  npm `@fontsource/*` et intégrées à la compilation. Aucun appel à Google Fonts, donc
  fonctionnement hors ligne.
- En arabe, tous les textes (titres compris) utilisent IBM Plex Sans Arabic, sans italique.
  La partie latine du logo reste en EB Garamond.

## Conséquences
- Pas d'URL distincte par langue (sans importance pour un démonstrateur local).
- Les libellés arabes sont à faire relire par le référent (voir questions-referent.md).
