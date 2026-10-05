# Banc d'essai des modèles locaux — 2026-10-05

Unité : Yacoub El Mansour (Rabat). Mac 16 Go, Ollama 0.35.1, Docker limité à 6 Go.
Même fiche de faits, même plan de rapport, même contrôle anti-invention pour les trois modèles.
Commande : `python -m app.services.reports.benchmark MODELE --unit "Yacoub El Mansour"`.

| Modèle | Mémoire | Langue | Durée | Sections IA / 7 | Nouvelles tentatives | Chiffres non tracés à la fin |
| --- | --- | --- | --- | --- | --- | --- |
| qwen3:8b | 6,2 Go | FR | 61 s | 7 | 0 | 0 |
| qwen3:8b | 6,2 Go | AR | 50 s | 7 | 0 | 0 |
| aya-expanse:8b | 6,4 Go | FR | 72 s | 7 | 2 | 0 |
| aya-expanse:8b | 6,4 Go | AR | 115 s | 7 | 4 | 0 |
| gemma3:4b | 3,9 Go | FR | 25 s | 7 | 0 | 0 |
| gemma3:4b | 3,9 Go | AR | 31 s | 7 | 0 | 0 |

## Fidélité (relecture manuelle des textes)

Le contrôle automatique garantit qu'aucun chiffre n'est inventé. Il ne juge pas les
appréciations : elles ont été relues à la main.

- **qwen3:8b** — le plus fidèle dans les deux langues. Défauts : formulations parfois lourdes
  en français (« croissance annuelle moyenne -1,43 % par an »), quelques commentaires vagues.
- **aya-expanse:8b** — style le plus fluide, mais le plus d'affirmations fausses : population
  « en pleine expansion » alors qu'elle baisse, écoles et centres de santé « présents » alors que
  la donnée manque, accès aux marchés affirmé sans donnée, « passant de 2,33 km² à 0,9 % ».
- **gemma3:4b** — le plus rapide et le plus léger ; arabe très proche des faits. Mais invente
  en français une « région de Rabat-Tidjikelt » qui n'existe pas, se trompe d'année (bâti « en
  2024 » au lieu de 2020) et laisse de côté des indicateurs dans plusieurs sections.

## Recommandation

**qwen3:8b** par défaut. **gemma3:4b** en solution de repli si la mémoire manque.
aya-expanse:8b déconseillé (affirmations inventées).

Choix du porteur du projet (2026-10-05) : **qwen3:8b par défaut, gemma3:4b en repli**
(`OLLAMA_FALLBACK_MODEL`, utilisé si qwen3 n'est pas installé). aya-expanse:8b écarté.

## Après ajout des contrôles du sens (même jour)

Le contrôle des chiffres ne suffit pas : un modèle peut affirmer une chose fausse sans écrire de
chiffre. Contrôles ajoutés (`config/report_templates/controles.yaml`,
`backend/app/services/reports/meaning.py`, tests `backend/tests/test_meaning.py`) :
sens des évolutions, données manquantes, statuts calculés, jugements subjectifs, et en arabe
deux nombres collés. Une section qui ne les respecte pas est réécrite (2 fois au plus), puis
rédigée sans IA.

| Modèle | Langue | Durée | Sections IA / 7 | Erreurs rattrapées puis corrigées | Repli sans IA |
| --- | --- | --- | --- | --- | --- |
| qwen3:8b | FR | 64 s | 7 | 1 | 0 |
| qwen3:8b | AR | 64 s | 7 | 2 | 0 |
| gemma3:4b | FR | 31 s | 7 | 1 | 0 |
| gemma3:4b | AR | 58 s | 6 | 5 | 1 |

Exemples d'erreurs rattrapées : « نمو » (croissance) pour une population en baisse ; affirmation
sur la couverture par un document d'urbanisme, donnée manquante ; « ملحوظ » (jugement subjectif) ;
« سنة 2024 168 391 » (deux nombres collés).

Ce qui reste à la relecture humaine : les contrôles ne comprennent pas tout le sens d'une phrase
(exemple vu : « les informations sur son niveau d'urbanisation ne sont pas disponibles » alors que
la surface bâtie est connue).
