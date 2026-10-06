"""Typology of the units (proposal): k-means on standardized indicators, then each group is
matched to the methodology profile whose signature it resembles most (provisional names)."""

import itertools
import math
from pathlib import Path
from typing import Any

import numpy as np
from pydantic import Field

from app.config_loader.territory import Localized, Slug, StrictModel, Text
from app.config_loader.validation import load_model

GROUP_LETTERS = {"fr": "ABCDEFGH", "ar": "أبجدهوزح"}


class TypologyVariable(StrictModel):
    code: str
    log: bool = False


class TypologyProfile(StrictModel):
    code: Slug
    label: Localized
    description: Localized
    signature: dict[str, int]


class TypologyConfig(StrictModel):
    typology_version: Text
    status: Text
    label: Localized
    clusters: int = Field(ge=2, le=8)
    seed: int = 42
    min_match_score: float = Field(default=1.0, ge=0)
    variables: list[TypologyVariable] = Field(min_length=2)
    profiles: list[TypologyProfile] = Field(min_length=2)


def load_typology(path: Path) -> TypologyConfig:
    return load_model(
        path,
        TypologyConfig,
        {"clusters": "clusters: 4", "variables": "- { code: DEM_DENS, log: true }"},
    )


def _kmeans(
    x: np.ndarray, k: int, seed: int, iterations: int = 100
) -> tuple[np.ndarray, np.ndarray]:
    """Plain k-means with k-means++ initialisation and a fixed seed (reproducible)."""
    rng = np.random.default_rng(seed)
    centers = [x[rng.integers(len(x))]]
    for _ in range(1, k):
        d2 = np.min([((x - c) ** 2).sum(axis=1) for c in centers], axis=0)
        probabilities = d2 / d2.sum() if d2.sum() > 0 else np.full(len(x), 1 / len(x))
        centers.append(x[rng.choice(len(x), p=probabilities)])
    c = np.array(centers)
    labels = np.zeros(len(x), dtype=int)
    for _ in range(iterations):
        distances = ((x[:, None, :] - c[None, :, :]) ** 2).sum(axis=2)
        new = distances.argmin(axis=1)
        if (new == labels).all() and _ > 0:
            break
        labels = new
        for j in range(k):
            if (labels == j).any():
                c[j] = x[labels == j].mean(axis=0)
    return labels, c


def _words(z: float, label: dict[str, str]) -> dict[str, str] | None:
    if abs(z) < 0.5:
        return None
    strong = abs(z) >= 1
    if z > 0:
        return {
            "fr": f"{label['fr']} {'nettement ' if strong else ''}au-dessus de la moyenne",
            "ar": f"{label['ar']} {'أعلى بوضوح من' if strong else 'أعلى من'} المتوسط",
        }
    return {
        "fr": f"{label['fr']} {'nettement ' if strong else ''}au-dessous de la moyenne",
        "ar": f"{label['ar']} {'أقل بوضوح من' if strong else 'أقل من'} المتوسط",
    }


def compute_typology(
    config: TypologyConfig, units: list[dict[str, Any]], labels: dict[str, dict[str, str]]
) -> dict[str, Any]:
    codes = [v.code for v in config.variables]
    rows, ids, unclassified = [], [], []
    for unit in units:
        values = []
        for variable in config.variables:
            entry = unit["values"].get(variable.code)
            value = entry.get("value") if entry else None
            if value is None:
                break
            values.append(math.log(max(value, 1e-6)) if variable.log else value)
        if len(values) == len(codes):
            rows.append(values)
            ids.append(unit["id"])
        else:
            unclassified.append(unit["id"])
    if len(rows) < config.clusters * 2:
        return {
            "available": False,
            "reason": "Trop peu d'unités complètes pour regrouper.",
            "unclassified": unclassified,
        }

    x = np.array(rows, dtype=float)
    std = x.std(axis=0)
    std[std == 0] = 1
    z = (x - x.mean(axis=0)) / std
    cluster_of, centers = _kmeans(z, config.clusters, config.seed)

    # Match groups to methodology profiles (best total resemblance, each profile used once).
    profiles = config.profiles
    score = np.array(
        [
            [
                sum(
                    sign * centers[g][codes.index(var)]
                    for var, sign in p.signature.items()
                    if var in codes
                )
                for p in profiles
            ]
            for g in range(config.clusters)
        ]
    )
    best, best_total = None, -math.inf
    for chosen in itertools.permutations(range(len(profiles)), min(config.clusters, len(profiles))):
        total = sum(score[g][p] for g, p in enumerate(chosen))
        if total > best_total:
            best, best_total = chosen, total
    assert best is not None

    groups = []
    for g in range(config.clusters):
        profile = profiles[best[g]] if g < len(best) else None
        if profile is not None and score[g][best[g]] < config.min_match_score:
            profile = None  # no convincing resemblance: the group stays unnamed
        traits = [w for i, var in enumerate(codes) if (w := _words(centers[g][i], labels[var]))]
        groups.append(
            {
                "group": g,
                "profile": profile.code if profile else f"groupe_{g + 1}",
                "label": profile.label.model_dump()
                if profile
                else {
                    # Letters, not numbers: a report may never show a number that is not a fact.
                    "fr": f"Groupe {GROUP_LETTERS['fr'][g]} — profil à nommer",
                    "ar": f"المجموعة ({GROUP_LETTERS['ar'][g]}) — صنف يتعين تسميته",
                },
                "description": profile.description.model_dump() if profile else None,
                "traits": traits[:4],
                "members": [ids[i] for i in range(len(ids)) if cluster_of[i] == g],
            }
        )
    per_unit = {}
    for i, unit_id in enumerate(ids):
        g = int(cluster_of[i])
        order = np.argsort(-np.abs(z[i]))[:3]
        traits = [w for j in order if (w := _words(z[i][j], labels[codes[j]]))]
        per_unit[unit_id] = {
            "group": g,
            "profile": groups[g]["profile"],
            "label": groups[g]["label"],
            "traits": traits,
        }
    return {
        "available": True,
        "label": config.label.model_dump(),
        "status": config.status,
        "variables": codes,
        "groups": groups,
        "units": per_unit,
        "unclassified": unclassified,
    }
