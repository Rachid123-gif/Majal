"""Validation queue (stage 4): the tool proposes, the urban planner validates.

- A contribution is « à vérifier » when the local model and the keywords do not give the same
  main theme, or when its language is uncertain (rules in config/citizens/analyse.yaml, `review`).
- A human correction (professor or administrator account) replaces the tool's proposal
  everywhere — statistics, crossing, report section 7 — because it is written in the same fields
  (themes, tonality, territory); the proposal is kept in `ai_proposal`, with « validé par ».
- The validated contributions form, little by little, a HUMAN evaluation set: the tool's
  proposal compared with the human choice, counted apart in « Fiabilité de l'analyse ».
"""

from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

from app.models import Contribution
from app.services.citizens.fallback import ReviewRules

FIELDS = ("themes", "tonality", "territory_id", "place_id", "place_text")


def human_values(c: Contribution) -> dict[str, Any]:
    return {
        "themes": list(c.themes or []),
        "tonality": c.tonality,
        "territory_id": c.territory_id,
        "place_id": c.place_id,
        "place_text": c.place_text,
    }


def set_values(c: Contribution, values: dict[str, Any]) -> None:
    for name in FIELDS:
        setattr(c, name, values.get(name))


def proposed(c: Contribution) -> Any:
    """The contribution as the TOOL classified it (before any human correction): what the
    evaluations of the model must score."""
    proposal = getattr(c, "ai_proposal", None)
    if not proposal:
        return c
    values = {name: getattr(c, name) for name in ("external_id", "language", "analysis")}
    return SimpleNamespace(**values, **{**human_values(c), **proposal})


def reasons(c: Contribution, rules: ReviewRules) -> list[str]:
    """Why the tool's proposal must be checked by a person (empty: nothing to check)."""
    tool = proposed(c)
    keywords = (c.analysis or {}).get("keywords") or {}
    out: list[str] = []
    if (c.analysis or {}).get("mode") == "ai" and tool.themes:
        main_kw = (keywords.get("themes") or ["autres"])[0]
        if main_kw != tool.themes[0] and (
            main_kw != "autres" or rules.keywords_silent_is_disagreement
        ):
            out.append("theme" if main_kw != "autres" else "theme_unconfirmed")
    model_language = (c.analysis or {}).get("model_language")
    if c.language in rules.uncertain_languages or (
        model_language and keywords.get("language") and model_language != keywords["language"]
    ):
        out.append("language")
    return out


def pending(c: Contribution, rules: ReviewRules) -> bool:
    return not c.validated_by and bool(reasons(c, rules))


def validate(
    c: Contribution,
    themes: list[str],
    tonality: str,
    territory_id: int | None,
    username: str,
) -> None:
    """Records the human choice (it may confirm the proposal unchanged)."""
    if not c.ai_proposal:
        c.ai_proposal = human_values(c)
    values = human_values(c)
    values["themes"] = list(dict.fromkeys(t for t in themes if t))[:2]
    values["tonality"] = tonality
    if territory_id != c.territory_id:
        values["territory_id"] = territory_id
        values["place_id"] = None  # the gazetteer match no longer applies
    set_values(c, values)
    c.validated_by = username
    c.validated_at = datetime.now(UTC)


def _main(themes: list[str] | None) -> str | None:
    return themes[0] if themes else None


def _agreement(pairs: list[tuple[Any, Any]]) -> dict[str, Any]:
    correct = sum(1 for tool, human in pairs if tool == human)
    return {
        "accuracy": correct / len(pairs) if pairs else None,
        "n": len(pairs),
        "correct": correct,
    }


HUMAN_BASE = {
    "fr": "Évaluation humaine dans l'outil ({n} contribution{s} vérifiée{s} par {by}) — "
    "surtout des cas signalés « à vérifier », donc les plus difficiles : non représentatif "
    "de l'ensemble",
    "ar": "تقييم بشري داخل الأداة ({n} مساهمة تم التحقق منها من طرف {by}) — "
    "أغلبها حالات مُعلَّمة « للتحقق »، أي الأصعب: غير ممثل للمجموع",
}


def human_evaluation(contributions: list[Contribution]) -> dict[str, Any] | None:
    """The tool's proposal compared with the human choice, on the validated contributions."""
    rows = [c for c in contributions if c.validated_by and c.ai_proposal]
    if not rows:
        return None
    accounts = sorted({c.validated_by for c in rows if c.validated_by})
    by = ", ".join(accounts)
    n = len(rows)
    return {
        "n": n,
        "accounts": accounts,
        "main_theme": _agreement(
            [(_main((c.ai_proposal or {}).get("themes")), _main(c.themes)) for c in rows]
        ),
        "tonality": _agreement([((c.ai_proposal or {}).get("tonality"), c.tonality) for c in rows]),
        "location": _agreement(
            [((c.ai_proposal or {}).get("territory_id"), c.territory_id) for c in rows]
        ),
        "base": {
            "fr": HUMAN_BASE["fr"].format(n=n, s="s" if n > 1 else "", by=by),
            "ar": HUMAN_BASE["ar"].format(n=n, by=by),
        },
    }


def validation_note(c: Contribution) -> dict[str, str] | None:
    if not c.validated_by:
        return None
    return {"fr": f"Validé par {c.validated_by}", "ar": f"تم التحقق من طرف {c.validated_by}"}
