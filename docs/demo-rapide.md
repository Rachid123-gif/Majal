# Démonstration rapide (10 minutes)

1. Ouvrir l'application **Ollama** (icône du lama dans la barre des menus), puis dans le Terminal, dossier MAJAL : `make start`. Le navigateur s'ouvre sur http://localhost:3000 et le Mac ne se met plus en veille (`make stop` à la fin).
2. **Vitrine** : faire défiler la page d'accueil (enjeu des programmes territoriaux, carte du Maroc entier, fonctions disponibles), puis « Se connecter » avec le compte `professeur` (mot de passe dans `.env`).
3. **Carte** : ouvrir Rabat ; choisir l'indicateur « Espaces verts publics par habitant » puis « Part de la population à moins de 500 m d'un arrêt de bus ou de tramway » ; montrer la légende, les badges de confiance et le bandeau « Grille v0 — proposition ».
4. **Fiche** : cliquer sur **Agdal-Riyad** (centre consolidé, sans déficit marqué), puis revenir et ouvrir **Layayda** (très dense, en forte croissance, très peu d'espaces verts) : points d'attention, mini-carte des équipements, typologie (proposition).
5. **Comparaison** : bouton « Comparer » sur Layayda, ajouter Agdal-Riyad et **Oumazza** (commune rurale) : le contraste se lit d'un coup d'œil.
6. **Rapport** : sur la fiche de Layayda, section « Rapport de diagnostic » : le rapport déjà préparé s'affiche aussitôt (cache) ; montrer « Rédigé par l'IA locale », le filigrane « Document de travail », les sources en fin de rapport.
7. Basculer sur « en arabe » : même rapport, de droite à gauche ; puis « Télécharger (PDF) » en français pour montrer la carte avec le Royaume entier en médaillon.
8. Pour montrer la rédaction en direct : « Régénérer » (environ une minute et demie, progression affichée section par section).
9. Message clé : l'IA n'écrit aucun chiffre ; MAJAL vérifie chaque nombre et le sens des phrases ; l'urbaniste relit et valide (statuts brouillon → relu → validé, validation réservée au professeur).
10. À la fin : `make stop` (arrête MAJAL et rétablit la mise en veille). Préparer tous les rapports à l'avance : `make reports`.
