# Conformité à la loi 09-08 (protection des données personnelles) — première version

> Document de travail, base pour une future déclaration auprès de la CNDP. À relire par un
> juriste avant toute version de production (version P).

## Version de démonstration (version D)

- **Aucune donnée personnelle réelle.** Les contributions citoyennes sont fictives et marquées
  comme telles partout. Leurs données personnelles (« pièges » de test) sont visiblement
  fictives : téléphones 06 00 00 0x xx, cartes d'identité ZZ0000xx, adresses @example.com.
- **Comptes de démonstration** : deux comptes (« professeur », « presentateur »), mots de passe
  dans `.env`, hors du dépôt. Aucune autre donnée sur les utilisateurs.
- **Aucun envoi vers un service extérieur** pendant l'utilisation : l'IA tourne sur l'ordinateur
  (Ollama, mode souverain `SOVEREIGN_MODE=true`).

## Traitements et mesures

| Traitement | Données | Mesures |
| --- | --- | --- |
| Import de contributions citoyennes | Texte libre, commune déclarée, date, canal | Import réservé aux comptes professeur et administrateur ; aucun champ nominatif demandé dans le modèle de fichier |
| Anonymisation (avant tout traitement par l'IA) | Noms de personnes, téléphones, e-mails, numéros de CIN, adresses précises, plaques | Règles testées sur un jeu de pièges (`backend/tests/test_anonymization.py`) ; passage complémentaire de l'IA locale ; le rapport d'anonymisation indique le type et la position, **jamais la valeur masquée** |
| Analyse par l'IA (langue, traduction, thèmes, tonalité, lieu) | Texte **anonymisé** uniquement | IA locale ; aucun texte original transmis au modèle |
| Tableau de bord et rapports | Statistiques et extraits **anonymisés** | Aucun texte original affiché dans les verbatims ; bandeau « Contributions fictives » en version D |
| Authentification | Identifiant, session | Session signée, anti-force brute, rôles vérifiés côté serveur (décision 0005) |

## À prévoir pour une version de production (version P)

- Déclaration ou demande d'autorisation auprès de la CNDP, selon la finalité retenue.
- Minimisation : ne collecter que le texte et la commune ; aucune donnée d'identité.
- Conservation du texte original : chiffrement au repos, accès restreint et journalisé, durée
  de conservation limitée, puis suppression ; suppression sur demande de la personne.
- Information des habitants sur la finalité et sur leurs droits (accès, rectification,
  opposition).
- Journal des accès et des exports ; revue régulière des droits des comptes.
- Hébergement au Maroc ; IA hébergée localement (BRIEF §4, version P).
