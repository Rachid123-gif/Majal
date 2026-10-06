"""Locating contributions: a place cited is attached to an analysis unit only if it is found in
the gazetteer (units, named places and named roads from OpenStreetMap). Nothing is invented:
an unknown place stays « lieu non identifié », unless the contributor declared a commune.

A name shared by several units (« Nahda » exists in Témara and in El Youssoufia) is
ambiguous: it is resolved by the declared commune when there is one, otherwise not at all.
"""

import re
import unicodedata
from dataclasses import dataclass, field

from sqlalchemy import text
from sqlalchemy.orm import Session

AR = "ء-ي"


def fold(value: str) -> str:
    """Comparison form: lower case, no accents, Arabic letters unified, no short vowels."""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub("[ً-ْـ]", "", value)
    value = value.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")
    value = value.replace("’", "'").replace("-", " ")
    return re.sub(r"\s+", " ", value).strip().casefold()


@dataclass
class Entry:
    label: str  # folded
    name: str  # as displayed
    kind: str  # unit | place | road
    territory_ids: set[int] = field(default_factory=set)
    place_id: int | None = None


@dataclass
class Location:
    territory_id: int | None
    place_id: int | None
    matched: str | None
    method: str  # text | model | declared | ambiguous | none


class Gazetteer:
    def __init__(
        self,
        entries: list[Entry],
        common_words: list[str] | None = None,
        place_cues: list[str] | None = None,
    ) -> None:
        # Arabic place names that are also common words: only after a place cue (« حي … »).
        self.common = {fold(w) for w in common_words or []}
        self.cues = "|".join(re.escape(fold(c)) for c in place_cues or []) or "حي"
        merged: dict[str, Entry] = {}
        for entry in entries:
            if len(entry.label) < 3:
                continue
            if entry.label in merged:
                merged[entry.label].territory_ids |= entry.territory_ids
                if merged[entry.label].kind != entry.kind:
                    merged[entry.label].place_id = merged[entry.label].place_id or entry.place_id
            else:
                merged[entry.label] = entry
        self.entries = sorted(merged.values(), key=lambda e: -len(e.label))
        self.units = {next(iter(e.territory_ids)): e.name for e in self.entries if e.kind == "unit"}

    def protected_names(self) -> list[str]:
        """Names never to be masked as a person by the anonymisation."""
        return [e.name for e in self.entries]

    def find(self, text_: str) -> list[Entry]:
        source = f" {fold(text_)} "
        found: list[Entry] = []
        for entry in self.entries:
            arabic = bool(re.search(f"[{AR}]", entry.label))
            prefix = (
                rf"(?<![{AR}])(?:[وفبلك]?(?:ال)?)"
                if arabic and not entry.label.startswith("ال")
                else (rf"(?<![{AR}])[وفبلك]?" if arabic else r"(?<![\w])")
            )
            if arabic and entry.label in self.common:
                prefix = rf"(?<![{AR}])[وفبل]?(?:{self.cues})\s+(?:[وفبلك]?(?:ال)?)?"
                if entry.label.startswith("ال"):
                    prefix = rf"(?<![{AR}])[وفبل]?(?:{self.cues})\s+"
            pattern = prefix + re.escape(entry.label) + (rf"(?![{AR}])" if arabic else r"(?![\w])")
            match = re.search(pattern, source)
            if match:
                found.append(entry)
                source = (
                    source[: match.start()]
                    + " " * (match.end() - match.start())
                    + source[match.end() :]
                )
        return found

    def unit_by_name(self, name: str | None) -> int | None:
        if not name:
            return None
        label = fold(name)
        for entry in self.entries:
            if entry.kind == "unit" and entry.label == label:
                return next(iter(entry.territory_ids))
        return None

    def locate(self, text_: str, model_place: str | None, declared_commune: str | None) -> Location:
        declared = self.unit_by_name(declared_commune)
        candidates = self.find(text_)
        method = "text"
        if not candidates and model_place:
            candidates = self.find(model_place)
            method = "model"
        for entry in candidates:
            if len(entry.territory_ids) == 1:
                return Location(next(iter(entry.territory_ids)), entry.place_id, entry.name, method)
            if declared in entry.territory_ids:
                return Location(declared, entry.place_id, entry.name, method)
        if declared is not None:
            return Location(declared, None, declared_commune, "declared")
        if candidates:
            return Location(None, None, candidates[0].name, "ambiguous")
        return Location(None, None, None, "none")


def load_gazetteer(
    session: Session,
    study_area_id: int,
    common_words: list[str] | None = None,
    place_cues: list[str] | None = None,
) -> Gazetteer:
    entries: list[Entry] = []
    for tid, name_fr, name_ar in session.execute(
        text(
            "SELECT id, name_fr, name_ar FROM territories "
            "WHERE study_area_id = :sa AND is_analysis_unit"
        ),
        {"sa": study_area_id},
    ):
        for name in (name_fr, name_ar):
            if name:
                entries.append(Entry(fold(name), name, "unit", {tid}))
    for pid, tid, name, name_ar, alt in session.execute(
        text(
            "SELECT id, territory_id, name, name_ar, alt_names FROM places "
            "WHERE study_area_id = :sa AND territory_id IS NOT NULL"
        ),
        {"sa": study_area_id},
    ):
        for value in [name, name_ar, *(alt or [])]:
            if value:
                entries.append(Entry(fold(value), value, "place", {tid}, pid))
    # Named roads: every unit they cross (a long avenue is ambiguous without a commune).
    for name, tids in session.execute(
        text(
            "SELECT r.name, array_agg(DISTINCT t.id) FROM roads r JOIN territories t "
            "ON t.study_area_id = r.study_area_id AND t.is_analysis_unit "
            "AND ST_Intersects(t.geom, r.geom) "
            "WHERE r.study_area_id = :sa AND r.name IS NOT NULL GROUP BY r.name"
        ),
        {"sa": study_area_id},
    ):
        entries.append(Entry(fold(name), name, "road", set(tids)))
    return Gazetteer(entries, common_words, place_cues)
