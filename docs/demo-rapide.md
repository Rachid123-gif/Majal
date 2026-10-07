# Démonstration rapide (20 minutes)

## Version « mode présentation » (recommandée devant un décideur)

1. Ouvrir **Ollama**, puis `make start` ; se connecter avec le compte `professeur`.
2. Tableau de bord → **Mode présentation** (ou http://localhost:3000/presentation?territoire=rabat), puis **F** pour le plein écran. Attendre « ✓ Prêt hors ligne » en haut à droite : tout est chargé, internet n'est plus nécessaire.
3. Dérouler avec **→** (ou une télécommande de présentation), revenir avec **←**, aller directement à une étape avec **1 à 9**, quitter avec **Échap** :
   1 Accueil · 2 L'enjeu · 3 Carte (espaces verts) · 4 Fiche de Layayda · 5 Comparaison Layayda / Agdal-Riyad / Oumazza · 6 Écoute citoyenne (bandeau « Données fictives », croisement sur Salé) · 7 Rapport de Layayda (déjà préparé ; « Régénérer » pour la rédaction en direct) · 8 Besoins en données (cocher la Santé puis le Ministère de l'Intérieur) · 9 Ce que nous vous proposons.
4. Le scénario (unités, indicateur, textes) se modifie dans `config/presentation/rabat.yaml`.

## Version détaillée, écran par écran


1. Ouvrir l'application **Ollama** (icône du lama dans la barre des menus), puis dans le Terminal, dossier MAJAL : `make start`. Le navigateur s'ouvre sur http://localhost:3000 et le Mac ne se met plus en veille (`make stop` à la fin).
2. **Vitrine** : faire défiler la page d'accueil (enjeu des programmes territoriaux, carte du Maroc entier, fonctions disponibles), puis « Se connecter » avec le compte `professeur` (mot de passe dans `.env`).
3. **Carte** : ouvrir Rabat ; choisir l'indicateur « Espaces verts publics par habitant » puis « Part de la population à moins de 500 m d'un arrêt de bus ou de tramway » ; montrer la légende, les badges de confiance et le bandeau « Grille v0 — proposition ».
4. **Fiche** : cliquer sur **Agdal-Riyad** (centre consolidé, sans déficit marqué), puis revenir et ouvrir **Layayda** (très dense, en forte croissance, très peu d'espaces verts) : points d'attention, mini-carte des équipements, typologie (proposition).
5. **Comparaison** : bouton « Comparer » sur Layayda, ajouter Agdal-Riyad et **Oumazza** (commune rurale) : le contraste se lit d'un coup d'œil.
6. **Rapport** : sur la fiche de Layayda, section « Rapport de diagnostic » : le rapport déjà préparé s'affiche aussitôt (cache) ; montrer « Rédigé par l'IA locale », le filigrane « Document de travail », les sources en fin de rapport.
7. Basculer sur « en arabe » : même rapport, de droite à gauche ; puis « Télécharger (PDF) » en français pour montrer la carte avec le Royaume entier en médaillon.
8. Pour montrer la rédaction en direct : « Régénérer » (environ une minute et demie, progression affichée section par section).
9. **Écoute citoyenne** (menu « Écoute citoyenne ») : montrer le bandeau « Contributions fictives », les thèmes (thème principal seul), la carte des contributions, puis l'échelle « Commune » et le croisement sur **Salé** (« Demande modérée et déficit marqué » pour les espaces verts) et sur **Layayda** (emploi : « trop peu de contributions pour juger de l'absence de demande »).
10. **À vérifier** : bouton « Ouvrir la file de vérification » ; une contribution avec son original, sa traduction automatique et les deux propositions (IA, mots-clés) ; corriger le thème en un clic → « validé par professeur ». Bas de page : « Fiabilité de l'analyse » et ses bases de mesure. Section 7 du rapport de Layayda : « Ce que disent les citoyens ».
11. **Besoins en données** (menu « Besoins en données ») : « 20 indicateurs disponibles sur 25 » et les barres par axe. Dans le simulateur « Si nous obtenons les données de… », cocher la **Direction régionale de la Santé** (Santé passe à 3 / 3 : « +3 grâce à la simulation ») puis le **Ministère de l'Intérieur** (« Fiabilisés : 10 » avec les limites officielles) ; rappeler la mention « Simulation : aucune donnée n'est ajoutée ». Descendre sur « Par où commencer » (limites officielles en tête), puis ouvrir la note de la Santé en PDF depuis sa fiche. En mode présentation, la flèche droite affiche le même simulateur.
12. Message clé : l'IA n'écrit aucun chiffre ; MAJAL vérifie chaque nombre et le sens des phrases ; l'outil propose, l'urbaniste valide (contributions « à vérifier », rapports brouillon → relu → validé, validation réservée au professeur).
13. À la fin : `make stop` (arrête MAJAL et rétablit la mise en veille). Préparer tous les rapports à l'avance : `make reports`. Après des corrections dans « À vérifier », relancer `make reports` : seuls les rapports des unités concernées sont réécrits. Notes de demande et tableau Excel : `make notes` (dans `docs/notes-demande/rabat/`).
