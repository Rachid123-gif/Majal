# Notes de demande de données (étape 5)

Projets de notes générés par MAJAL, **à relire et adapter avant envoi** : une note par
institution (Word et PDF : lettre d'une page et annexe technique d'une page), et le tableau
Excel récapitulatif des données demandées (onglets « Lisez-moi », « Données demandées »,
« Institutions »).

- Texte : modèle fixe `config/report_templates/note_demande.yaml` (aucun texte écrit par l'IA).
- Institutions, titres des destinataires et données demandées :
  `config/data_holders/<territoire>.yaml` — intitulés à vérifier par le professeur.
- Régénérer après toute modification : `make notes` (ou `make notes TERRITORY=tetouan`).
- Les fichiers sont numérotés dans l'ordre « Par où commencer » des institutions.
- Communes de Skhirate-Témara : une note par commune, en complétant `[nom de la commune]`.
