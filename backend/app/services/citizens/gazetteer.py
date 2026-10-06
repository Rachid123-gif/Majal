"""Locating contributions: a place cited is attached to an analysis unit only if it is found in
the gazetteer (units, named places and named roads from OpenStreetMap). Nothing is invented:
an unknown place stays « lieu non identifié », unless the contributor declared a commune.

A name shared by several units (« Nahda » exists in Témara and in El Youssoufia) is
ambiguous: it is resolved by the declared commune when there is one, otherwise not at all.
"""

import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
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


def fold_with_map(value: str) -> tuple[str, list[int]]:
    """Folded text (as `fold`, without collapsing spaces) and, for each folded character, the
    index of the original character it comes from."""
    out: list[str] = []
    index: list[int] = []
    for i, char in enumerate(value):
        if re.match("[\u064b-\u0652\u0640]", char):
            continue
        piece = "".join(
            c for c in unicodedata.normalize("NFKD", char) if not unicodedata.combining(c)
        )
        piece = piece.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ى", "ي")
        piece = piece.replace("’", "'").replace("-", " ").casefold()
        for c in piece:
            out.append(c)
            index.append(i)
    return "".join(out), index


@dataclass
class Entry:
    label: str  # folded
    name: str  # as displayed
    kind: str  # unit | place | road
    territory_ids: set[int] = field(default_factory=set)
    place_id: int | None = None
    latin: str | None = None  # official form in Latin letters (never translated)


@dataclass
class Span:
    entry: Entry
    start: int  # in the original text
    end: int


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

    def _pattern(self, entry: Entry, loose: bool = False) -> re.Pattern[str]:
        label = re.escape(entry.label)
        if not re.search(f"[{AR}]", entry.label):
            return re.compile(rf"(?<![\w])(?P<n>{label})(?![\w])")
        article = "" if entry.label.startswith("ال") else "(?:ال)?"
        if entry.label in self.common and loose:
            # For translation only: also after a place preposition (« في النهضة », « فالنهضة »).
            return re.compile(
                rf"(?:(?<![{AR}])(?:{self.cues})\s+|(?<![{AR}])في\s+|(?<![{AR}])[وفب]?[فب])"
                rf"(?P<n>{article}{label})(?![{AR}])"
            )
        if entry.label in self.common:  # also a common word: only after « حي », « دوار »…
            return re.compile(
                rf"(?<![{AR}])[وفبل]?(?P<n>(?:{self.cues})\s+{article}{label})(?![{AR}])"
            )
        return re.compile(rf"(?<![{AR}])[وفبلك]?(?P<n>{article}{label})(?![{AR}])")

    def find_spans(self, text_: str, loose: bool = False) -> list[Span]:
        """Places of the gazetteer written in the text, with their position (longest first,
        no overlap)."""
        source, index = fold_with_map(text_)
        spans: list[Span] = []
        for entry in self.entries:
            for match in self._pattern(entry, loose).finditer(source):
                start, end = match.span("n")
                if any(start < s.end and s.start < end for s in spans):
                    continue
                spans.append(Span(entry, start, end))
                break
        out = [Span(s.entry, index[s.start], index[s.end - 1] + 1) for s in spans]
        return sorted(out, key=lambda s: s.start)

    def find(self, text_: str) -> list[Entry]:
        return [s.entry for s in sorted(self.find_spans(text_), key=lambda s: -len(s.entry.label))]

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


def _latin(value: str | None) -> str | None:
    return value if value and not re.search(f"[{AR}]", value) else None


def load_equivalences(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return dict(data.get("places") or {})


def load_gazetteer(
    session: Session,
    study_area_id: int,
    common_words: list[str] | None = None,
    place_cues: list[str] | None = None,
    equivalences: dict[str, dict[str, Any]] | None = None,
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
                entries.append(Entry(fold(name), name, "unit", {tid}, latin=name_fr))
    for pid, tid, name, name_ar, alt in session.execute(
        text(
            "SELECT id, territory_id, name, name_ar, alt_names FROM places "
            "WHERE study_area_id = :sa AND territory_id IS NOT NULL"
        ),
        {"sa": study_area_id},
    ):
        latin = _latin(name) or next((a for a in alt or [] if _latin(a)), None)
        for value in [name, name_ar, *(alt or [])]:
            if value:
                entries.append(Entry(fold(value), value, "place", {tid}, pid, latin))
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
        entries.append(Entry(fold(name), name, "road", set(tids), latin=_latin(name)))
    # Equivalences (config/citizens/lieux-equivalences.yaml): other spellings of EXISTING places.
    by_name: dict[str, list[Entry]] = {}
    for entry in entries:
        by_name.setdefault(entry.name, []).append(entry)
    for key, extra in (equivalences or {}).items():
        for entry in by_name.get(key, []):
            if extra.get("latin"):
                entry.latin = extra["latin"]
            for alias in extra.get("ar") or []:
                entries.append(
                    Entry(
                        fold(alias),
                        alias,
                        entry.kind,
                        set(entry.territory_ids),
                        entry.place_id,
                        entry.latin,
                    )
                )
    for entry in entries:  # aliases and original names share the official Latin form
        if entry.name in (equivalences or {}) and (equivalences or {})[entry.name].get("latin"):
            entry.latin = (equivalences or {})[entry.name]["latin"]
    return Gazetteer(entries, common_words, place_cues)
