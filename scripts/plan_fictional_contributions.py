"""Neutral plan of the fictitious citizen contributions for Rabat (stage 4).

Run once: `python3 scripts/plan_fictional_contributions.py` → data/fictif/rabat/plan.csv.
The texts are then written by hand for each line of the plan (contributions.yaml).

The plan must NOT be built to confirm the indicators (otherwise the citizen/data crossing would
be circular). Rules, documented in docs/citoyens-jeu-fictif.md:
- number per unit: at least 2, the rest in proportion to the legal population 2024 (HCP),
  the only input taken from the data (no thematic indicator is read);
- themes: drawn at random with the SAME weights in every unit (all themes equal, « autres »
  half weight); 20 % of contributions get a second theme;
- languages, tonalities, place cited or not, declared commune or not, anonymisation traps:
  drawn at random with fixed proportions;
- fixed seed: the plan is reproducible.
"""

import csv
import random
from pathlib import Path

SEED = 2026
TOTAL = 140
ROOT = Path(__file__).resolve().parents[1]

# Legal population 2024 (HCP, as imported in MAJAL), used only to size the units.
UNITS = {
    "Témara": 297098, "Tabriquet": 237385, "Hssaine": 234326, "Layayda": 229838,
    "Yacoub El Mansour": 168391, "Bab Lamrissa": 167319, "El Youssoufia": 157587,
    "Skhirate": 122705, "Sidi Yahya Zaer": 116649, "Ain El Aouda": 98502, "Hassan": 92454,
    "Bettana": 76233, "Ameur": 75942, "Aïn Attig": 73985, "Agdal-Riyad": 70435,
    "Sidi Bouknadel": 43598, "Mers El Kheir": 26544, "Shoul": 24913, "Souissi": 21049,
    "Harhoura": 20950, "Sabbah": 15552, "El Menzeh": 7168, "Touarga": 5703, "Oumazza": 4322,
}
THEMES = [
    "mobilite", "circulation", "voirie", "logement", "espaces_verts", "proprete",
    "eau_assainissement", "eclairage", "sante", "education", "emploi_jeunesse", "securite",
    "bruit", "commerce_marches", "culture_sport", "patrimoine", "administration",
    "accessibilite_pmr", "autres",
]
THEME_WEIGHTS = [1.0] * 18 + [0.5]
LANGUAGES = {"fr": 0.35, "ar": 0.25, "darija_ar": 0.20, "darija_latin": 0.15, "amazigh_latin": 0.05}
TONALITIES = {"demande": 0.40, "plainte": 0.35, "proposition": 0.15, "satisfaction": 0.10}
SECOND_THEME = 0.20
PLACE_CITED = 0.85
COMMUNE_DECLARED = 0.50
PII_TRAPS = 22


def allocate() -> dict[str, int]:
    counts = dict.fromkeys(UNITS, 2)
    rest = TOTAL - sum(counts.values())
    total_pop = sum(UNITS.values())
    shares = {u: rest * p / total_pop for u, p in UNITS.items()}
    for unit, share in shares.items():
        counts[unit] += int(share)
    leftover = TOTAL - sum(counts.values())
    for unit in sorted(shares, key=lambda u: shares[u] - int(shares[u]), reverse=True)[:leftover]:
        counts[unit] += 1
    return counts


def main() -> None:
    rng = random.Random(SEED)
    rows = []
    number = 0
    for unit, count in allocate().items():
        for _ in range(count):
            number += 1
            first = rng.choices(THEMES, THEME_WEIGHTS)[0]
            themes = [first]
            if first != "autres" and rng.random() < SECOND_THEME:
                second = rng.choices([t for t in THEMES[:-1] if t != first])[0]
                themes.append(second)
            rows.append(
                {
                    "id": f"RBT-{number:03d}",
                    "unit": unit,
                    "themes": "|".join(themes),
                    "language": rng.choices(list(LANGUAGES), list(LANGUAGES.values()))[0],
                    "tonality": rng.choices(list(TONALITIES), list(TONALITIES.values()))[0],
                    "place_cited": rng.random() < PLACE_CITED,
                    "commune_declared": rng.random() < COMMUNE_DECLARED,
                    "pii_trap": False,
                }
            )
    for row in rng.sample(rows, PII_TRAPS):
        row["pii_trap"] = True
    out = ROOT / "data" / "fictif" / "rabat" / "plan.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"{len(rows)} lignes → {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
