# MAJAL — مجال

**Copilote d'intelligence territoriale.** MAJAL transforme la donnée publique dispersée en
diagnostics territoriaux chiffrés, sourcés et vérifiables. Ce dépôt contient le
démonstrateur sur deux territoires : Rabat et Tétouan.

> L'outil propose, l'urbaniste valide.

Cahier des charges : [docs/BRIEF.md](docs/BRIEF.md).

---

## 1. Installer (une seule fois)

Il faut **Git** et **Docker Desktop** sur la machine.

1. Installez Docker Desktop (Mac Apple Silicon) : https://www.docker.com/products/docker-desktop/
   Ouvrez-le une fois. Dans *Settings → Resources*, réglez la mémoire sur **6 Go**.
2. Vérifiez dans un terminal que Docker répond :
   ```bash
   docker compose version
   ```
3. Dans le dossier du projet, lancez l'installation :
   ```bash
   make setup
   ```
   La première fois, comptez quelques minutes : les images sont téléchargées puis construites.

## 2. Lancer

```bash
make dev
```

Ouvrez ensuite http://localhost:3000 dans le navigateur. Pour tout arrêter, faites `Ctrl+C`
dans le terminal, puis lancez :

```bash
make down
```

## 3. Vérifier que tout va bien

```bash
make test
```

Pour vérifier les fichiers de configuration après une modification :

```bash
make check-config
```

En cas d'erreur, le message indique le fichier, la ligne, le problème et un exemple correct.

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

Puis reconstruisez les images si des dépendances ont changé :

```bash
make setup
```

## Travailler sans Docker (facultatif)

Il faut **uv** (Python) et **Node 22 ou plus** :

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Installez ensuite les dépendances :

```bash
make setup-local
```

Lancez l'application sans base de données :

```bash
make dev-local
```

`make test` fonctionne aussi sans Docker.

## Toutes les commandes

```bash
make help
```

## Organisation

| Dossier | Contenu |
| --- | --- |
| `backend/` | API Python (FastAPI), calculs, imports de données |
| `frontend/` | Interface web (Next.js), en français et en arabe |
| `config/` | Méthode : territoires, indicateurs, thèmes, plans de rapport (modifiable sans code) |
| `data/` | Données brutes (non versionnées), données de démonstration, fonds de carte |
| `docs/` | Cahier des charges, sources, décisions, guides |
