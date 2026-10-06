"""Neutral plan of the fictitious citizen contributions for Rabat (stage 4).

Run: `backend/.venv/bin/python scripts/plan_fictional_contributions.py`
→ data/fictif/rabat/plan.csv. The texts are then written by hand for each new line of the plan
(data/fictif/rabat/contributions.yaml).

The plan must NOT be built to confirm the indicators (otherwise the citizen/data crossing would
be circular). Rules, documented in docs/citoyens-jeu-fictif.md; parameters in
config/citizens/jeu-fictif.yaml:
- number per unit: at least 2, the rest in proportion to the legal population 2024 (HCP),
  the only input taken from the data (no thematic indicator is read);
- themes: drawn at random with the SAME realistic weights in every unit; a share of
  contributions gets a second theme;
- languages, tonalities, place cited or not, declared commune or not, anonymisation traps:
  drawn at random with fixed proportions;
- the reference sample (classified by the professor) is kept unchanged: its lines are copied
  from the previous plan, and only the other lines are drawn again;
- fixed seed: the plan is reproducible.
"""

import csv
import random
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "citizens" / "jeu-fictif.yaml"
PLAN = ROOT / "data" / "fictif" / "rabat" / "plan.csv"

# Legal population 2024 (HCP, as imported in MAJAL), used only to size the units.
UNITS = {
    "Témara": 297098, "Tabriquet": 237385, "Hssaine": 234326, "Layayda": 229838,
    "Yacoub El Mansour": 168391, "Bab Lamrissa": 167319, "El Youssoufia": 157587,
    "Skhirate": 122705, "Sidi Yahya Zaer": 116649, "Ain El Aouda": 98502, "Hassan": 92454,
    "Bettana": 76233, "Ameur": 75942, "Aïn Attig": 73985, "Agdal-Riyad": 70435,
    "Sidi Bouknadel": 43598, "Mers El Kheir": 26544, "Shoul": 24913, "Souissi": 21049,
    "Harhoura": 20950, "Sabbah": 15552, "El Menzeh": 7168, "Touarga": 5703, "Oumazza": 4322,
}


def allocate(total: int) -> dict[str, int]:
    counts = dict.fromkeys(UNITS, 2)
    rest = total - sum(counts.values())
    total_pop = sum(UNITS.values())
    shares = {u: rest * p / total_pop for u, p in UNITS.items()}
    for unit, share in shares.items():
        counts[unit] += int(share)
    leftover = total - sum(counts.values())
    for unit in sorted(shares, key=lambda u: shares[u] - int(shares[u]), reverse=True)[:leftover]:
        counts[unit] += 1
    return counts


def pick(rng: random.Random, weights: dict[str, float], exclude: set[str] | None = None) -> str:
    items = [(k, w) for k, w in weights.items() if w > 0 and k not in (exclude or set())]
    return rng.choices([k for k, _ in items], [w for _, w in items])[0]


def main() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    rng = random.Random(config["seed"])
    frozen_ids = set(config["reference_sample"])
    previous = {row["id"]: row for row in csv.DictReader(PLAN.open(encoding="utf-8"))}
    frozen = [previous[i] for i in sorted(frozen_ids)]

    # Units: the same allocation as before, minus the lines kept from the reference sample.
    needed = Counter(allocate(config["total"]))
    needed.subtract(Counter(row["unit"] for row in frozen))
    free_ids = sorted(set(previous) - frozen_ids)
    rows = []
    for unit in UNITS:
        for _ in range(needed[unit]):
            first = pick(rng, config["theme_weights"])
            themes = [first]
            if rng.random() < config["second_theme_share"]:
                themes.append(pick(rng, config["theme_weights"], exclude={first}))
            rows.append(
                {
                    "unit": unit,
                    "themes": "|".join(themes),
                    "language": pick(rng, config["languages"]),
                    "tonality": pick(rng, config["tonalities"]),
                    "place_cited": rng.random() < config["place_cited_share"],
                    "commune_declared": rng.random() < config["commune_declared_share"],
                    "pii_trap": False,
                    "reference_sample": False,
                }
            )
    assert len(rows) == len(free_ids)
    for row in rng.sample(rows, config["pii_traps"]):
        row["pii_trap"] = True
    for row, new_id in zip(rows, free_ids, strict=True):
        row["id"] = new_id
    for row in frozen:
        row["reference_sample"] = True
    out = sorted(rows + frozen, key=lambda r: r["id"])
    fields = ["id", "unit", "themes", "language", "tonality", "place_cited",
              "commune_declared", "pii_trap", "reference_sample"]
    with PLAN.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({k: r[k] for k in fields} for r in out)
    print(f"{len(out)} lignes ({len(frozen)} de l'échantillon de référence conservées)")


if __name__ == "__main__":
    main()
