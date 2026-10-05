# MAJAL — مجال

**Copilote d'intelligence territoriale.** MAJAL transforme la donnée publique dispersée en
diagnostics territoriaux chiffrés, sourcés et vérifiables. Ce dépôt contient le
démonstrateur sur deux territoires : Rabat et Tétouan.

> L'outil propose, l'urbaniste valide.

Cahier des charges : [docs/BRIEF.md](docs/BRIEF.md).

---

## Utilisation au quotidien (2 commandes)

Ouvrez le **Terminal**, allez dans le dossier du projet, puis :

```bash
make start
```

MAJAL démarre et le navigateur s'ouvre tout seul sur **http://localhost:3000**. La première
fois, ou après une mise à jour, comptez quelques minutes.

Pour arrêter MAJAL :

```bash
make stop
```

### Ce que vous voyez

| Adresse | Page |
| --- | --- |
| http://localhost:3000 | Page vitrine (publique) |
| http://localhost:3000/connexion | Connexion |
| http://localhost:3000/tableau-de-bord | Tableau de bord (après connexion) |

### Comptes de démonstration et mots de passe

Deux comptes existent : **professeur** et **presentateur**. Leurs mots de passe se trouvent dans
le fichier **`.env`**, à la racine du projet :

```
DEMO_PROFESSEUR_PASSWORD=...
DEMO_PRESENTATEUR_PASSWORD=...
```

Pour les changer : ouvrez `.env` avec TextEdit, remplacez la valeur après le signe `=`,
enregistrez, puis lancez `make stop` et `make start`. Laisser une valeur vide désactive le compte.
Le fichier `.env` est invisible dans le Finder : appuyez sur `Cmd + Maj + .` pour afficher les
fichiers cachés.

### Compléter la page vitrine

Le nom, la photo et l'e-mail du référent sont dans
[`frontend/src/content/site.ts`](frontend/src/content/site.ts). Les textes de la page sont dans
[`frontend/src/content/landing.ts`](frontend/src/content/landing.ts) et
[`frontend/src/content/features.ts`](frontend/src/content/features.ts).

---

## 1. Installer (une seule fois)

Il faut **Git** et **Docker Desktop** sur la machine.

1. Installez Docker Desktop (Mac Apple Silicon) : https://www.docker.com/products/docker-desktop/
   Ouvrez-le une fois. Dans *Settings → Resources*, réglez la mémoire sur **6 Go**.
2. Vérifiez dans un nouveau terminal que Docker répond :
   ```bash
   docker compose version
   ```
3. Dans le dossier du projet, lancez l'installation :
   ```bash
   make setup
   ```

Docker Desktop doit être ouvert (icône de baleine dans la barre de menus) avant `make start`.

## 2. Vérifier que tout va bien

```bash
make test
```

Pour vérifier les fichiers de configuration après une modification :

```bash
make check-config
```

En cas d'erreur, le message indique le fichier, la ligne, le problème et un exemple correct.

## 3. Voir les messages en cas de problème

```bash
make logs
```

## 4. Sauvegarder et restaurer la base

```bash
make backup
```

Pour restaurer une sauvegarde (la base actuelle est remplacée après confirmation), indiquez
son fichier :

```bash
make restore FILE=backups/majal-AAAAMMJJ-HHMMSS.dump
```

## 5. Mettre à jour le code

```bash
git pull
```

Puis relancez : `make start` reconstruit automatiquement ce qui a changé.

## Toutes les commandes

```bash
make help
```

## Organisation

| Dossier | Contenu |
| --- | --- |
| `backend/` | API Python (FastAPI), calculs, imports de données, connexion |
| `frontend/` | Interface web (Next.js), en français et en arabe |
| `config/` | Méthode : territoires, indicateurs, thèmes, plans de rapport (modifiable sans code) |
| `data/` | Données brutes (non versionnées), données de démonstration, fonds de carte |
| `docs/` | Cahier des charges, sources, décisions, guides |
