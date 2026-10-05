# 0015 — Exports Word et PDF des rapports

- **Date** : 2026-10-05 · **Statut** : accepté

## Choix
- **Word** : python-docx (document modifiable par l'urbaniste).
- **PDF** : WeasyPrint (HTML + CSS → PDF), sans navigateur ni service externe ; polices
  EB Garamond (titres), Noto Sans (texte : IBM Plex n'est pas fourni par Debian) et Noto Naskh
  Arabic installées dans l'image.
- **Carte** : matplotlib, dessinée par MAJAL à partir de ses propres données (voir 0013).
- Exports en français à l'étape 3 ; exports arabes de droite à gauche à l'étape 7 (le texte arabe
  est déjà lisible à l'écran).
- Seul un rapport terminé et contrôlé (état « done ») est exportable.
