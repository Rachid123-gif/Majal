# 0018 — Module « Besoins en données » et notes de demande

Date : 2026-10-07 — Statut : accepté (étape 5 validée par le porteur du projet).

## Contexte
BRIEF §9.8 : transformer les lacunes de données en demandes concrètes, institution par
institution, avec une note prête à relire et signer.

## Décisions
- **Référentiel modifiable** `config/data_holders/<territoire>.yaml` : institutions (intitulés,
  titre du destinataire, entités complémentaires citées dans le texte, tous « à vérifier par le
  professeur »), demandes (destinataires, détenteurs complémentaires et alternatifs, niveau de
  détail, format, période, fréquence, indicateurs, thèmes, contexte). Chaque demande cite sa
  source : grille, taxonomie citoyenne, question au référent ou contexte. Validé par
  `make check-config` (messages en français).
- **Règles communes** `config/data_holders/regles.yaml` (TODO_REFERENT) : priorité calculée, jamais
  choisie à la main (Essentielle → Contexte → Utile, « Contexte » prime pour les projets
  programmés) ; classement par priorité, puis nombre d'indicateurs concernés, puis nombre de
  thèmes ; trois effets calculés d'après le statut actuel de l'indicateur : « calculer »
  (manquant), « fiabiliser » (ouvert ou estimé), « affiner » (officiel, échelle plus fine).
- **Complétude** (`app/services/data_needs/completeness.py`) : statut d'un indicateur = le moins
  fiable des badges de ses valeurs ; manquant si aucune valeur (jamais 0) ; phrases par
  institution construites à partir des comptes, sans IA.
- **Écran** `/territoire/<code>/besoins-donnees` : complétude par axe, simulateur « Si nous
  obtenons les données de… » (calcul dans le navigateur, mention « Simulation : aucune donnée
  n'est ajoutée », aussi en mode présentation), « Par où commencer », fiches par institution.
  Une demande à plusieurs destinataires ne compte dans la simulation que si tous sont cochés ;
  un indicateur à deux détenteurs, que si les deux le sont.
- **Suivi des demandes** par institution (à envoyer, envoyée, accordée, refusée, date,
  historique), réservé aux comptes professeur et administrateur (table
  `data_request_tracking`, migration 0008).
- **Notes de demande** (Word, PDF) à partir d'un modèle fixe
  `config/report_templates/note_demande.yaml` : première personne, destinataire unique, en-tête
  « MAJAL — projet de recherche appliquée », contrepartie, proposition de convention, une page de
  lettre et une page d'annexe (vérifié sur les PDF), pied de page « Projet de note généré par
  MAJAL — à relire et adapter avant envoi ». Mots interdits contrôlés : aucun partenariat supposé,
  aucune contribution citoyenne, aucun « nous ». Français maintenant, arabe à l'étape 7.
- **Tableau Excel** récapitulatif (Lisez-moi, Données demandées avec « Priorité » et les trois
  verbes, Institutions). `make notes` écrit notes et tableau dans `docs/notes-demande/<code>/`.

## Conséquences
- Ajouter un territoire = un fichier `config/data_holders/<code>.yaml` ; aucune logique métier à
  changer.
- Fonction future notée (Q21) : distinguer « besoin non couvert » et « besoin déjà couvert par un
  projet programmé » à partir des demandes de contexte.
