"""Anti-invention control: no number may appear in generated text unless it comes from a fact.

Run on the model's raw text (before substitution). Any number written by the model blocks
publication: digits (Latin, Arabic-Indic, Persian), percentages, numbers written in words
(French and Arabic). Listed exceptions only:
- years present in the fact sheet (e.g. « 2024 »);
- the definitional numbers of indicator labels (« moins de 15 ans », « à moins de 500 m »),
  accepted only together with their unit, exactly as written in the grid;
- section numbers are never written by the model (they are added by the renderer).
"""

import re
from dataclasses import dataclass

PLACEHOLDER = re.compile(r"\{\{\s*(F\d{3})\s*\}\}")
# Variants the models write for a fact reference: {F012}, [F012], {{F012, F013}}, bare F012.
_GROUPED_REF = re.compile(r"[\{\[]+\s*(F\d{3}(?:\s*[,;/|]\s*F\d{3})*)\s*[\}\]]+")
_SPACED_REF = re.compile(r"(?<![\w])F[\s\-_](\d{3})(?!\d)")
_BARE_REF = re.compile(r"(?<![\w{])(F\d{3})(?![\w}])")


def normalize_refs(text: str) -> str:
    """Rewrite every way of citing a fact as {{Fxxx}}. Only the form changes: unknown
    identifiers are still rejected by the check, and no number is ever let through."""
    text = _SPACED_REF.sub(r"F\1", text)  # « F 011 », « F-011 »
    text = _GROUPED_REF.sub(lambda m: ", ".join(re.findall(r"F\d{3}", m.group(1))), text)
    return _BARE_REF.sub(r"{{\1}}", text)


DIGIT = "0-9٠-٩۰-۹"
NUMBER = re.compile(rf"[{DIGIT}]+(?:[.,   ][{DIGIT}]+)*")
PERCENT = re.compile(
    r"%|٪|\bpour\s?cent\b|\bpourcent(?:age)?s?\b|بالمائة|بالمئة|في\s?المائة|في\s?المئة",
    re.IGNORECASE,
)

# French number words. « un/une » are excluded: they are articles far more often than numbers.
FR_WORDS = [
    "zéro",
    "deux",
    "trois",
    "quatre",
    "cinq",
    "six",
    "sept",
    "huit",
    "neuf",
    "dix",
    "onze",
    "douze",
    "treize",
    "quatorze",
    "quinze",
    "seize",
    "vingt",
    "vingts",
    "trente",
    "quarante",
    "cinquante",
    "soixante",
    "septante",
    "octante",
    "nonante",
    "cent",
    "cents",
    "mille",
    "million",
    "millions",
    "milliard",
    "milliards",
    "demi",
    "demie",
    "moitié",
    "tiers",
    "quart",
    "quarts",
    "double",
    "triple",
    "quadruple",
    "dizaine",
    "dizaines",
    "douzaine",
    "centaine",
    "centaines",
    "millier",
    "milliers",
    "deuxième",
    "troisième",
    "quatrième",
    "cinquième",
    "sixième",
    "septième",
    "huitième",
    "neuvième",
    "dixième",
    "vingtième",
    "centième",
    "millième",
]
FR_PATTERN = re.compile(r"(?<![\w-])(" + "|".join(FR_WORDS) + r")(?![\w-])", re.IGNORECASE)

# Arabic number words, with the usual attached prefixes (و ف ب ل ك ال).
AR_WORDS = [
    "صفر",
    "اثنان",
    "اثنين",
    "اثنتان",
    "اثنتين",
    "ثلاثة",
    "ثلاث",
    "أربعة",
    "أربع",
    "خمسة",
    "خمس",
    "ستة",
    "سبعة",
    "ثمانية",
    "ثماني",
    "تسعة",
    "تسع",
    "عشرة",
    "عشر",
    "عشرون",
    "عشرين",
    "ثلاثون",
    "ثلاثين",
    "أربعون",
    "أربعين",
    "خمسون",
    "خمسين",
    "ستون",
    "ستين",
    "سبعون",
    "سبعين",
    "ثمانون",
    "ثمانين",
    "تسعون",
    "تسعين",
    "مائة",
    "مئة",
    "مئات",
    "مائتان",
    "مائتين",
    "ألف",
    "آلاف",
    "ألفين",
    "مليون",
    "ملايين",
    "مليار",
    "مليارات",
    "نصف",
    "ربع",
    "ثلث",
    "خمس",
    "ضعف",
    "ضعفي",
    "أضعاف",
    "عشرات",
]
AR_PATTERN = re.compile(r"(?<![ء-ي])(?:و|ف|ب|ل|ك)?(?:ال)?(" + "|".join(AR_WORDS) + r")(?![ء-ي])")

DEFINITION = re.compile(
    rf"[{DIGIT}][{DIGIT}   ,.]*\s?(?:à\s[{DIGIT}]+\s)?(?:إلى\s[{DIGIT}]+\s)?"
    r"(?:ans|an|km|m|ha|habitants|hab\.|enfants|سنة|سنوات|كلم|م|هكتار|نسمة|طفل)\b"
)


MEANING_KINDS = ("trend", "missing", "absence", "adjacent", "subjective", "status", "wording")


@dataclass(frozen=True)
class Issue:
    kind: str  # number | percent | word | unknown_fact | trend | missing | adjacent | subjective
    token: str

    def describe(self) -> str:
        if self.kind in MEANING_KINDS:  # meaning checks: the token is the message
            return self.token
        return {
            "number": f"nombre écrit directement : « {self.token} »",
            "percent": f"pourcentage écrit directement : « {self.token} »",
            "word": f"nombre écrit en lettres : « {self.token} »",
            "unknown_fact": f"identifiant de fait inconnu : « {self.token} »",
        }[self.kind]


def definitional_phrases(labels: list[str]) -> list[str]:
    """Number + unit phrases taken verbatim from indicator labels (« moins de 15 ans »)."""
    phrases: set[str] = set()
    for label in labels:
        for match in DEFINITION.finditer(label):
            phrases.add(match.group(0).strip())
    return sorted(phrases, key=len, reverse=True)


def check_text(
    text: str,
    known_facts: set[str],
    allowed_years: set[int],
    definitional: list[str] | None = None,
) -> list[Issue]:
    issues: list[Issue] = []
    for match in PLACEHOLDER.finditer(text):
        if match.group(1) not in known_facts:
            issues.append(Issue("unknown_fact", match.group(0)))
    stripped = PLACEHOLDER.sub(" ", text)
    for phrase in definitional or []:
        stripped = stripped.replace(phrase, " ")
    for match in NUMBER.finditer(stripped):
        token = match.group(0).strip(" .,")
        if token.isascii() and token.isdigit() and len(token) == 4 and int(token) in allowed_years:
            continue
        issues.append(Issue("number", match.group(0)))
    issues += [Issue("percent", m.group(0)) for m in PERCENT.finditer(stripped)]
    issues += [Issue("word", m.group(0)) for m in FR_PATTERN.finditer(stripped)]
    issues += [Issue("word", m.group(0)) for m in AR_PATTERN.finditer(stripped)]
    return issues


def check_rendered(
    rendered: str,
    substituted: list[str],
    allowed_years: set[int],
    definitional: list[str] | None = None,
) -> list[Issue]:
    """Final check on the rendered text: every number must come from a substituted fact."""
    remaining = rendered
    # The renderer may drop the sign after a decrease verb (« recule de 1,4 % »).
    variants = set(substituted) | {v.lstrip("-−") for v in substituted}
    for value in sorted(variants, key=len, reverse=True):
        remaining = remaining.replace(value, " ")
    return check_text(remaining, set(), allowed_years, definitional)
