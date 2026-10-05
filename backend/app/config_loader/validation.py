"""Generic YAML → Pydantic validation with French error messages.

Reused by every configuration family (territories now; indicators, taxonomies, report
templates later).
"""

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError
from pydantic_core import ErrorDetails

from app.config_loader.errors import ConfigError, ConfigIssue
from app.config_loader.yaml_source import locate_line, read_yaml

SLUG_HINT = (
    "Format incorrect : uniquement des lettres minuscules sans accent, des chiffres et « _ », "
    "en commençant par une lettre."
)


def load_model[M: BaseModel](
    path: Path, model: type[M], examples: Mapping[str, str] | None = None
) -> M:
    data, root, issues = read_yaml(path)
    if issues:
        raise ConfigError(issues)
    if not isinstance(data, dict):
        raise ConfigError(
            [ConfigIssue(path.name, 1, "", "Le fichier est vide ou ne contient pas de champs.")]
        )
    try:
        return model.model_validate(data, context={"file_stem": path.stem})
    except ValidationError as exc:
        raise ConfigError(
            [
                ConfigIssue(
                    file=path.name,
                    line=locate_line(root, tuple(err["loc"])),
                    field=_field_label(err["loc"]),
                    problem=translate_error(err),
                    example=_example(err["loc"], examples or {}),
                )
                for err in exc.errors()
            ]
        ) from None


def _field_label(loc: tuple[int | str, ...]) -> str:
    return " > ".join(f"élément n°{p + 1}" if isinstance(p, int) else p for p in loc)


def _example(loc: tuple[int | str, ...], examples: Mapping[str, str]) -> str | None:
    for part in reversed(loc):
        if isinstance(part, str) and part in examples:
            return examples[part]
    return None


def translate_error(err: ErrorDetails) -> str:
    kind = err["type"]
    ctx: dict[str, Any] = dict(err.get("ctx") or {})
    match kind:
        case "missing":
            return "Ce champ est obligatoire mais il est absent."
        case "extra_forbidden":
            return "Ce champ n'est pas reconnu (faute de frappe ou champ mal placé ?)."
        case "string_type":
            return "Une valeur texte est attendue."
        case "string_too_short":
            return "Le texte ne doit pas être vide."
        case "string_pattern_mismatch":
            return SLUG_HINT
        case "enum" | "literal_error":
            return f"Valeur non autorisée. Valeurs possibles : {ctx.get('expected', '?')}."
        case "int_type" | "int_parsing" | "int_from_float":
            return "Un nombre entier est attendu."
        case "float_type" | "float_parsing":
            return "Un nombre est attendu."
        case "bool_type" | "bool_parsing":
            return "La valeur doit être « true » (oui) ou « false » (non)."
        case "greater_than_equal":
            return f"La valeur doit être supérieure ou égale à {ctx.get('ge')}."
        case "less_than_equal":
            return f"La valeur doit être inférieure ou égale à {ctx.get('le')}."
        case "list_type":
            return "Une liste est attendue (une ligne par élément, commençant par « - »)."
        case "too_short":
            return f"Au moins {ctx.get('min_length')} élément(s) attendu(s)."
        case "dict_type" | "model_type" | "model_attributes_type":
            return "Un bloc de champs est attendu (champs indentés en dessous)."
        case "tuple_type" | "too_long":
            return "Le nombre d'éléments ne correspond pas à ce qui est attendu."
        case "value_error" | "assertion_error":
            return str(ctx.get("error", err["msg"]))
        case _:
            return f"Valeur incorrecte (détail technique : {err['msg']})."
