# 0014 — Rédaction des rapports par une IA locale, en mode souverain

- **Date** : 2026-10-05 · **Statut** : accepté — qwen3:8b par défaut, gemma3:4b en repli (choix du porteur après banc d'essai)

## Contexte
Les rapports de diagnostic doivent être rédigés en français et en arabe sans clé API payante et
sans que les données quittent l'ordinateur pendant l'utilisation.

## Choix
- **Ollama installé directement sur le Mac** (pas dans Docker : accès au processeur graphique
  Apple, mémoire Docker limitée à 6 Go). Les conteneurs le joignent par
  `http://host.docker.internal:11434`.
- **Mode souverain par défaut** (`SOVEREIGN_MODE=true`) : aucun appel externe pendant
  l'utilisation. Le fournisseur Anthropic est codé mais refusé tant que ce mode est actif
  (`get_provider` lève une erreur). `make data` reste une commande d'administration.
- **L'IA n'écrit aucun chiffre** : elle reçoit une fiche de faits (F001…) et des qualificatifs,
  écrit des repères `[F012]` que MAJAL remplace par les valeurs formatées. Un contrôle refuse tout
  chiffre (latin, arabe-indien, persan), pourcentage ou nombre en toutes lettres non tracé ;
  2 nouvelles tentatives avec le motif de l'erreur, puis repli.
- **Contrôles du sens** (`config/report_templates/controles.yaml`) : un mot de tendance doit
  suivre le signe de la valeur (aucun pour un indicateur observé à une seule date) ; rien n'est
  affirmé sur une donnée manquante ; un statut cité doit être le statut calculé ; pas de jugement
  subjectif ; en arabe, jamais deux nombres collés ; pas de « fausse absence » (dire qu'une
  donnée manque alors que l'indicateur est connu). Même traitement qu'un chiffre inventé.
- **Recontrôle** : quand les contrôles ou le plan changent, `make reports` repasse les contrôles
  sur les rapports existants (mêmes données, même modèle) ; seuls ceux qui échouent sont
  réécrits, les autres gardent leur texte et reçoivent la nouvelle clé de cache.
- **Ton institutionnel** : consignes et phrases modèles dans le plan du rapport
  (`style`, `examples`), identifiants d'exemple fictifs (F9xx).
- **Modèle de repli** : `OLLAMA_FALLBACK_MODEL=gemma3:4b`, choisi à la demande si
  `OLLAMA_MODEL` n'est pas installé.
- **Repli sans IA** : si le modèle est absent, en panne ou n'obéit pas, la section est rédigée à
  partir de phrases-types et des mêmes faits ; l'interface et les exports l'indiquent.
- **Contrôle final** : un rapport contenant un nombre non tracé est « bloqué » et ne peut pas
  être exporté.
- **Cache** : clé = données de l'unité + langue + fournisseur + modèle + plan du rapport. Les
  démonstrations ne dépendent pas du modèle (`make reports` pré-génère tout).
- **File d'attente** : RQ + Redis (service `worker`) ; repli sur un fil d'exécution si Redis
  manque.
- **Statuts** : brouillon → relu → validé (validation réservée au référent scientifique).
  Filigrane « Document de travail… à valider par un urbaniste » tant que le rapport n'est pas validé.

## Banc d'essai
`python -m app.services.reports.benchmark MODELE…` ; résultats dans `docs/benchmarks/`.
