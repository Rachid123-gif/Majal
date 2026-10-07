# 0019 — Mode présentation (avancé avant Tétouan)

Date : 2026-10-07 — Statut : accepté (changement d'ordre demandé par le porteur du projet :
le mode présentation, prévu à l'étape 7, est livré avant l'étape 6 pour être montré au
professeur ; Tétouan s'y ajoutera, l'arabe plus tard).

## Décisions
- **Scénario modifiable** `config/presentation/<territoire>.yaml` : 9 étapes (accueil, l'enjeu,
  carte, fiche, comparaison, écoute citoyenne, rapport, besoins en données, « Ce que nous vous
  proposons »), indicateur de départ, unités désignées par leur nom officiel (résolues par
  `/api/presentation/<code>`, erreur en français si un nom est introuvable), textes de l'enjeu et
  de la proposition, contact entre crochets. Validé par `make check-config`.
- **Les diapositives sont les vrais écrans** de l'application, affichés sans en-tête ni liens de
  sortie grâce à un contexte « intégré » (`components/app/Embedded.tsx`) ; quelques propriétés
  de départ ajoutées aux écrans (indicateur de la carte, unités de la comparaison, croisement de
  l'écoute citoyenne) ; aucune logique métier modifiée.
- **Hors ligne** : toutes les diapositives sont montées au lancement (données chargées avant la
  démonstration), préchargement contrôlé et témoin « Prêt hors ligne » ; toutes les requêtes
  sont locales (vérifié : 96 requêtes, toutes vers localhost ; test automatique).
- **Navigation** : ← → et Page préc. / Page suiv. (télécommandes), 1 à 9, Début / Fin, F (plein
  écran), Échap ; étape dans l'adresse (`&etape=N`) ; les flèches ne déplacent pas la carte.
- **Bandeaux** : « Démonstrateur » et la date des données toujours visibles ; « Données
  fictives » sur les étapes qui montrent des contributions fictives (écoute citoyenne, rapport).
- Typographie agrandie (112,5 %) pendant la présentation.

## Correction faite au passage
Le contrôle des rapports déjà rédigés (`make reports`) considérait une taxonomie illisible comme
« aucune contribution » : 44 rapports avaient ainsi été conservés sans leur section 7 à jour
(taxonomie modifiée pendant la régénération du 2026-10-06). `citizens_for` ne renvoie plus
« aucune contribution » que si la taxonomie du profil n'existe pas ; toute autre erreur est
signalée. Les 44 rapports ont été régénérés.
