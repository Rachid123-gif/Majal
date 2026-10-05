# 0005 — Connexion au démonstrateur

- **Date** : 2026-10-05 · **Statut** : accepté (version D)

## Contexte
La vitrine est publique ; l'application (tableau de bord, mode présentation) doit être réservée
au référent scientifique et aux présentateurs. Le porteur du projet doit pouvoir changer les mots
de passe sans toucher au code (BRIEF §14 : session sécurisée, rôles vérifiés côté serveur).

## Choix
- Deux comptes de démonstration, `professeur` (rôles référent et présentateur) et
  `presentateur` (rôle présentateur). Leurs mots de passe sont dans `.env`
  (`DEMO_PROFESSEUR_PASSWORD`, `DEMO_PRESENTATEUR_PASSWORD`). Un mot de passe vide désactive le
  compte.
- Le backend vérifie le mot de passe (comparaison en temps constant) et pose un cookie de session
  **signé** (`itsdangerous`, clé `SESSION_SECRET`), `HttpOnly`, `SameSite=Lax`, `Secure` en
  production, valable 12 heures. Cinq échecs bloquent le compte une minute.
- Le navigateur ne parle qu'au frontend : `/api/*` est relayé vers le backend par Next.js, donc
  le cookie reste interne au site et le backend n'a pas besoin d'être exposé.
- Les pages `/tableau-de-bord` et `/presentation` sont protégées par `src/proxy.ts`, qui fait
  confirmer la session par le backend avant d'afficher la page.
- En production, le backend refuse de démarrer sans `SESSION_SECRET`.

## Conséquences
- Simple à exploiter : changer un mot de passe = modifier `.env` puis relancer.
- Limite assumée de la version D : les mots de passe de démonstration sont en clair dans
  `.env` (fichier local, non versionné). La version P stockera les comptes en base avec
  mots de passe hachés (tables `users`, `roles`) et journal des accès.
