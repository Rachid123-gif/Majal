"""Schema of config/data_holders/<territory>.yaml: institutions holding data and the precise data
MAJAL asks them for (module « Besoins en données », stage 5)."""

from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from app.config_loader.territory import Localized, Slug, StrictModel, Text
from app.config_loader.validation import load_model

InstitutionKind = Literal[
    "administration",
    "administration_territoriale",
    "collectivite",
    "groupement_collectivites",
    "etablissement_public",
    "operateur",
]


class Institution(StrictModel):
    code: Slug
    name: Localized
    kind: InstitutionKind
    with_data_of: Localized | None = None  # short form for sentences (« de l'AREF »)
    # Rule of the owner: every name is a proposal until the professor has checked it.
    to_verify: bool = True


class DataRequest(StrictModel):
    code: Slug
    holders: list[Slug] = Field(min_length=1)
    alternatives: list[Slug] = Field(default_factory=list)
    complementary: list[Slug] = Field(default_factory=list)
    boundaries: bool = False
    data: Localized
    detail: Localized
    format: Localized
    frequency: Localized
    enables: list[str] = Field(default_factory=list)
    requires_also: list[Slug] = Field(default_factory=list)
    improves: list[str] = Field(default_factory=list)
    finer_scale: Localized | None = None  # « affiner … à l'échelle du quartier »
    themes: list[Slug] = Field(default_factory=list)
    context: bool = False
    source: list[str] = Field(min_length=1)
    value: Localized

    @model_validator(mode="after")
    def has_a_purpose(self) -> Self:
        if not (self.enables or self.improves or self.themes or self.context or self.boundaries):
            raise ValueError(
                f"La demande « {self.code} » ne sert à rien : indiquez au moins un indicateur "
                "(enables ou improves), un thème (themes) ou « context: true »."
            )
        for item in self.source:
            if item not in ("grid", "taxonomy", "context") and not item.startswith("question:"):
                raise ValueError(
                    f"Source « {item} » inconnue pour la demande « {self.code} » : utilisez "
                    "grid, taxonomy, context ou question:Q15."
                )
        return self


class DataHolders(StrictModel):
    territory: Slug
    version: Text
    status: Text
    display_label: Localized
    to_verify_label: Localized
    institutions: list[Institution] = Field(min_length=1)
    requests: list[DataRequest] = Field(min_length=1)

    @model_validator(mode="after")
    def consistent(self) -> Self:
        codes = [i.code for i in self.institutions]
        duplicates = sorted({c for c in codes if codes.count(c) > 1})
        if duplicates:
            raise ValueError(f"Institutions en double : {', '.join(duplicates)}.")
        requests = [r.code for r in self.requests]
        duplicates = sorted({c for c in requests if requests.count(c) > 1})
        if duplicates:
            raise ValueError(f"Demandes en double : {', '.join(duplicates)}.")
        known = set(codes)
        for request in self.requests:
            cited = request.holders + request.alternatives + request.complementary
            unknown = sorted(set(cited) - known)
            if unknown:
                raise ValueError(
                    f"La demande « {request.code} » cite une institution absente de la liste "
                    f"« institutions » : {', '.join(unknown)}."
                )
            missing = sorted(set(request.requires_also) - set(requests))
            if missing:
                raise ValueError(
                    f"La demande « {request.code} » dépend d'une demande inconnue : "
                    f"{', '.join(missing)}."
                )
        used = {h for r in self.requests for h in r.holders}
        orphans = sorted(known - used)
        if orphans:
            raise ValueError(
                f"Institution sans demande qui lui soit adressée (holders) : "
                f"{', '.join(orphans)}. Ajoutez une demande ou retirez l'institution."
            )
        return self

    def institution(self, code: str) -> Institution | None:
        return next((i for i in self.institutions if i.code == code), None)


def load_data_holders(path: Path) -> DataHolders:
    return load_model(
        path,
        DataHolders,
        {
            "institutions": '- code: hcp_dr_rsk\n  name: { fr: "…", ar: "…" }',
            "holders": "holders: [hcp_dr_rsk]",
        },
    )


def reference_errors(
    holders: DataHolders, indicator_codes: set[str], theme_codes: set[str]
) -> list[str]:
    """Cross-file checks (French, for a non-developer): indicators of the grid, themes of the
    taxonomy."""
    errors = []
    for request in holders.requests:
        for code in sorted(set(request.enables + request.improves) - indicator_codes):
            errors.append(
                f"Demande « {request.code} » : l'indicateur « {code} » n'existe pas dans la "
                "grille (config/indicators/grille-v0.yaml)."
            )
        for code in sorted(set(request.themes) - theme_codes):
            errors.append(
                f"Demande « {request.code} » : le thème « {code} » n'existe pas dans la "
                "taxonomie (config/taxonomy/)."
            )
    return errors


Criterion = Literal["enables", "boundaries", "context", "improves", "themes"]
PriorityCode = Literal["essential", "useful", "context"]
SortCriterion = Literal["priority", "indicators", "themes"]


class PriorityRule(StrictModel):
    priority: PriorityCode
    when_any: list[Criterion] = Field(min_length=1)


EffectCode = Literal["computed", "reliable", "finer"]


class Effect(StrictModel):
    verb: Localized
    label: Localized


class ModuleRules(StrictModel):
    """config/data_holders/regles.yaml: rules shared by every territory."""

    status: Text
    priority_rules: list[PriorityRule] = Field(min_length=1)
    priorities: dict[PriorityCode, Localized]
    sort_by: list[SortCriterion] = Field(min_length=1)
    effects: dict[EffectCode, Effect]
    tracking_statuses: dict[Slug, Localized] = Field(min_length=1)
    indicator_statuses: dict[Literal["official", "open", "estimated", "missing"], Localized]

    @model_validator(mode="after")
    def complete(self) -> Self:
        missing = sorted({r.priority for r in self.priority_rules} - set(self.priorities))
        if missing:
            raise ValueError(f"Priorité sans libellé dans « priorities » : {', '.join(missing)}.")
        if "to_send" not in self.tracking_statuses:
            raise ValueError("« tracking_statuses » doit contenir « to_send » (statut de départ).")
        return self


def load_module_rules(path: Path) -> ModuleRules:
    return load_model(
        path,
        ModuleRules,
        {"priority_rules": "- priority: essential\n  when_any: [enables, boundaries]"},
    )
