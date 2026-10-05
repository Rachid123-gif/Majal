# 0006 — Publier la vitrine seule sur internet (à faire plus tard)

- **Date** : 2026-10-05 · **Statut** : proposé, non réalisé

## Contexte
La page vitrine doit pouvoir être en ligne à une adresse publique, tandis que l'application
(données, connexion, rapports) reste sur le portable de démonstration.

## Ce qui est déjà prêt
- La vitrine (`/`) est une page **statique** : elle n'appelle ni la base ni le backend, et
  n'utilise aucune ressource externe (polices et carte embarquées).
- Ses textes sont dans `frontend/src/content/` ; les champs à compléter dans
  `frontend/src/content/site.ts`.

## Ce qu'il faudra faire
1. **Construire la vitrine seule** : une variante de compilation qui exporte uniquement `/` en
   fichiers HTML/CSS/JS statiques (export statique de Next.js), sans les pages de l'application.
2. **Adapter le bouton « Se connecter »** sur la version publique : le remplacer par « Demander
   une démonstration » (lien vers le contact), puisque l'application n'est pas en ligne.
3. **Nom de domaine** : par exemple en `.ma`, réservé auprès d'un registraire agréé par l'ANRT.
4. **Hébergement statique avec HTTPS** : de préférence chez un hébergeur au Maroc, cohérent
   avec le discours de souveraineté ; un hébergeur statique international est possible mais
   moins cohérent.
5. **Contenu à finaliser** : nom, photo et e-mail du professeur, mentions légales (éditeur,
   hébergeur, directeur de publication), relecture des textes arabes, validation des chiffres.
6. **Données personnelles** : le bouton « Nous contacter » ouvre la messagerie (aucune donnée
   stockée). Un formulaire de contact demanderait une mention d'information loi 09-08.

## Ce qu'il faudra fournir
Le nom de domaine choisi, un compte chez l'hébergeur, et les éléments du point 5.
