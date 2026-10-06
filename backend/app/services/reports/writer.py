"""Section writing: the model writes with fact identifiers; numbers are checked; fallback
templates (no AI) take over when the model fails, with the same facts and the same checks."""

import re
import time
from dataclasses import dataclass, field
from typing import Any, Literal

from app.services.llm.base import LLMError, LLMProvider
from app.services.reports.facts import FactSheet, IndicatorBrief
from app.services.reports.meaning import (
    Controls,
    cached_controls,
    check_adjacent,
    check_meaning,
    check_subjective,
    normalize,
    word_pattern,
)
from app.services.reports.numbers import (
    PLACEHOLDER,
    Issue,
    check_text,
    definitional_phrases,
    normalize_refs,
)
from app.services.reports.template import ReportTemplate, Section
from app.settings import get_settings

Lang = Literal["fr", "ar"]
SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "paragraphs": {"type": "array", "items": {"type": "string"}, "minItems": 1, "maxItems": 3}
    },
    "required": ["paragraphs"],
}

SYSTEM = {
    "fr": (
        "Tu rédiges une section d'un diagnostic territorial destiné à une administration "
        "marocaine.\nRègles absolues :\n"
        "1. N'écris AUCUN nombre : ni chiffre, ni nombre en lettres, ni pourcentage, ni rang. "
        "Pour citer une valeur, insère l'identifiant du fait entre doubles accolades, exactement "
        "comme dans la liste, par exemple {{F012}} : il sera remplacé automatiquement par la "
        "valeur et son unité. N'ajoute donc pas d'unité après l'identifiant.\n"
        "2. N'utilise que les faits fournis. N'invente aucune donnée ni aucune cause.\n"
        "3. Si une donnée est non disponible, dis seulement qu'elle manque : n'en conclus pas "
        "que l'équipement ou le service est absent.\n"
        "4. Ne commente ni les années ni la fiabilité des données : MAJAL l'indique ailleurs.\n"
        "5. Écris en français.\n6. Style : {style}\n"
        "Exemples à imiter (leurs identifiants sont fictifs : utilise seulement ceux de la "
        "liste fournie) :\n{examples}\n"
        'Réponds uniquement en JSON : {{"paragraphs": ["…", "…"]}}.'
    ),
    "ar": (
        "أنت تحرر قسماً من تشخيص ترابي موجه إلى إدارة مغربية.\nقواعد صارمة:\n"
        "1. لا تكتب أي عدد: لا أرقام، ولا أعداد بالحروف، ولا نسب مئوية، ولا رتب. لذكر قيمة، أدرج "
        "معرّف الواقعة بين قوسين معقوفين مزدوجين كما هو في القائمة، مثلاً {{F012}}، وسيُعوَّض "
        "تلقائياً بالقيمة ووحدتها. لا تضف الوحدة بعد المعرّف.\n"
        "2. لا تستعمل سوى الوقائع المقدمة. لا تختلق أي معطى أو سبب.\n"
        "3. إذا كان معطى غير متوفر، فاذكر فقط أنه ناقص، ولا تستنتج أن التجهيز أو الخدمة غير موجودة.\n"
        "4. لا تعلق على السنوات ولا على موثوقية المعطيات: يشير «مجال» إلى ذلك في موضع آخر.\n"
        "5. اكتب باللغة العربية الفصحى.\n6. الأسلوب: {style}\n"
        "أمثلة يُحتذى بها (معرّفاتها افتراضية: استعمل فقط معرّفات القائمة المقدمة):\n{examples}\n"
        'أجب فقط بصيغة JSON: {{"paragraphs": ["…", "…"]}}.'
    ),
}

LABELS = {
    "fr": {
        "unit": "Unité",
        "section": "Section",
        "instruction": "Consigne",
        "length": "Longueur",
        "words": "environ {n} mots, en un ou deux paragraphes",
        "facts": "Faits disponibles",
        "value": "valeur",
        "status": "statut",
        "reference": "moyenne de référence",
        "rank": "rang",
        "gap": "écart",
        "na": "donnée manquante (indicateur non calculé)",
        "requested": "à demander à",
        "years": "Années que tu peux citer",
        "area": "surface",
        "typology": "Profil-type (proposition)",
        "contributions": "Contributions citoyennes localisées dans l'unité",
        "main_theme": "Thème principal",
        "fictitious": "Ne parle pas du caractère fictif des contributions : MAJAL l'indique dans un bandeau au-dessus du texte.",
        "too_few": "Trop peu de contributions pour conclure : dis-le dans le texte.",
        "retry": (
            "Ta réponse précédente ne respecte pas les règles : {issues}. Réécris la section "
            "sans aucun nombre : remplace chaque valeur par l'identifiant de son fait."
        ),
    },
    "ar": {
        "unit": "الوحدة",
        "section": "القسم",
        "instruction": "التعليمات",
        "length": "الطول",
        "words": "حوالي {n} كلمة، في فقرة أو فقرتين",
        "facts": "الوقائع المتوفرة",
        "value": "القيمة",
        "status": "الوضعية",
        "reference": "المتوسط المرجعي",
        "rank": "الرتبة",
        "gap": "الفارق",
        "na": "معطى ناقص (مؤشر غير محتسب)",
        "requested": "يُطلب من",
        "years": "السنوات التي يمكنك ذكرها",
        "area": "المساحة",
        "typology": "الصنف النموذجي (مقترح)",
        "contributions": "مساهمات المواطنين المحددة في الوحدة",
        "main_theme": "الموضوع الرئيسي",
        "fictitious": "لا تتحدث عن الطابع الافتراضي للمساهمات: يشير «مجال» إلى ذلك في شريط فوق النص.",
        "too_few": "عدد المساهمات غير كاف للاستنتاج: اذكر ذلك في النص.",
        "retry": (
            "إجابتك السابقة لا تحترم القواعد: {issues}. أعد كتابة القسم دون أي عدد، "
            "وعوّض كل قيمة بمعرّف الواقعة الخاصة بها."
        ),
    },
}


@dataclass
class SectionResult:
    code: str
    title: str
    paragraphs: list[str]  # raw text with {{Fxxx}} placeholders
    mode: Literal["ai", "fallback", "auto"]
    attempts: int = 0
    duration_s: float = 0.0
    output_tokens: int = 0
    issues: list[str] = field(default_factory=list)
    error: str | None = None


def section_codes(section: Section, sheet: FactSheet) -> list[str]:
    if section.indicators == "attention":
        return sheet.attention
    return [c for c in section.indicators if c in sheet.briefs]


def _brief_line(brief: IndicatorBrief, lang: Lang) -> str:
    t = LABELS[lang]
    label = brief.label[lang]
    if not brief.available:
        line = f"- {label} : {t['na']}"
        if brief.requested_from:
            line += f" ({t['requested']} {brief.requested_from})"
        return line
    parts = [f"{t['value']} {{{{{brief.fact_ids['value']}}}}}"]
    status = brief.status_label[lang]
    if brief.descriptor[lang]:
        status = f"{status}, {brief.descriptor[lang]}"
    parts.append(f"{t['status']} : {status}")
    # No rank: the models used it as a comparison value (« contre 5e sur 23 »).
    for kind in ("reference", "gap"):
        if kind in brief.fact_ids:
            parts.append(f"{t[kind]} {{{{{brief.fact_ids[kind]}}}}}")
    return f"- {label} : " + " ; ".join(parts)


def build_prompt(
    sheet: FactSheet, section: Section, template: ReportTemplate, lang: Lang, typology: str | None
) -> str:
    t = LABELS[lang]
    identity = sheet.identity
    lines = [
        f"{t['unit']} : {identity[f'name_{lang}']} — {identity[f'description_{lang}']}",
        f"{t['section']} : {section.title.model_dump()[lang]}",
        f"{t['instruction']} : {section.instruction.model_dump()[lang] if section.instruction else ''}",
        f"{t['length']} : {t['words'].format(n=section.words)}",
        "",
        f"{t['facts']} :",
    ]
    if section.include_identity and identity.get("area_fact"):
        lines.append(f"- {t['area']} : {{{{{identity['area_fact']}}}}}")
    lines += [_brief_line(sheet.briefs[code], lang) for code in section_codes(section, sheet)]
    if section.include_typology and typology:
        lines.append(f"- {t['typology']} : {typology}")
    if section.include_citizens and sheet.citizens and sheet.citizens["total_fact"]:
        citizens = sheet.citizens
        lines.append(f"- {t['contributions']} : {{{{{citizens['total_fact']}}}}}")
        for label, fact_id in citizens["themes"]:
            lines.append(f"- {t['main_theme']} « {label[lang]} » : {{{{{fact_id}}}}}")
        if citizens["fictitious"]:
            lines.append(f"- {t['fictitious']}")
        if citizens["too_few"]:
            lines.append(f"- {t['too_few']}")
    # Only the years that name the data (census, built-up epochs), not extraction dates: the
    # models otherwise comment on them. The check still accepts every year of the sheet.
    labels = " ".join(b.label["fr"] for b in sheet.briefs.values())
    years = ", ".join(str(y) for y in sorted(sheet.years) if str(y) in labels)
    lines += ["", f"{t['years']} : {years}"]
    return "\n".join(lines)


def check_paragraphs(
    paragraphs: list[str],
    sheet: FactSheet,
    lang: Lang = "fr",
    controls: Controls | None = None,
    meaning: bool = True,
) -> list[Issue]:
    """Numbers first (nothing written by the model), then meaning (trends, missing data)."""
    known = {f.id for f in sheet.facts}
    definitional = definitional_phrases(
        [b.label["fr"] for b in sheet.briefs.values()]
        + [b.label["ar"] for b in sheet.briefs.values()]
    )
    controls = controls or default_controls()
    issues: list[Issue] = []
    for paragraph in paragraphs:
        issues += check_text(paragraph, known, sheet.years, definitional)
        if meaning:
            issues += check_meaning(paragraph, sheet, controls, lang)
        else:  # citizens section: no indicator claims, but tone and Arabic layout still checked
            issues += check_subjective(paragraph, controls, lang) + check_adjacent(paragraph, lang)
    return issues


def default_controls() -> Controls:
    return cached_controls(get_settings().config_dir / "report_templates" / "controles.yaml")


def write_section(
    provider: LLMProvider | None,
    sheet: FactSheet,
    section: Section,
    template: ReportTemplate,
    lang: Lang,
    typology: str | None = None,
    max_retries: int = 2,
) -> SectionResult:
    title = section.title.model_dump()[lang]
    if section.mode == "auto" or (section.include_citizens and not sheet.citizens):
        text = section.auto_text.model_dump()[lang] if section.auto_text else ""
        return SectionResult(section.code, title, [text] if text else [], "auto")
    if section.include_citizens and sheet.citizens and not sheet.citizens["total"]:
        text = section.empty_text.model_dump()[lang] if section.empty_text else ""
        return SectionResult(section.code, title, [text] if text else [], "auto")
    if provider is None:
        return fallback_section(sheet, section, lang, title, typology, error="IA désactivée")

    examples = "\n".join(f"- {e}" for e in template.examples.get(lang, []))
    system = SYSTEM[lang].format(style=template.style.model_dump()[lang], examples=examples)
    prompt = build_prompt(sheet, section, template, lang, typology)
    started = time.perf_counter()
    attempts = 0
    tokens = 0
    issues_seen: list[str] = []
    error: str | None = None
    while attempts <= max_retries:
        attempts += 1
        try:
            result = provider.generate_json(system, prompt, SCHEMA)
        except LLMError as exc:
            error = str(exc)
            break
        tokens += result.output_tokens or 0
        paragraphs = (result.data or {}).get("paragraphs")
        if (
            not isinstance(paragraphs, list)
            or not paragraphs
            or not all(isinstance(p, str) and p.strip() for p in paragraphs)
        ):
            issues_seen.append("JSON invalide ou vide")
            prompt_retry = LABELS[lang]["retry"].format(issues="JSON invalide")
            prompt = f"{build_prompt(sheet, section, template, lang, typology)}\n\n{prompt_retry}"
            continue
        paragraphs = [normalize_refs(p) for p in paragraphs]
        issues = check_paragraphs(paragraphs, sheet, lang, meaning=section.meaning_checks)
        if not issues:
            return SectionResult(
                section.code,
                title,
                [p.strip() for p in paragraphs],
                "ai",
                attempts,
                time.perf_counter() - started,
                tokens,
                issues_seen,
            )
        described = "; ".join(i.describe() for i in issues[:6])
        issues_seen.append(described)
        retry = LABELS[lang]["retry"].format(issues=described)
        prompt = f"{build_prompt(sheet, section, template, lang, typology)}\n\n{retry}"
    fallback = fallback_section(
        sheet, section, lang, title, typology, error=error or "; ".join(issues_seen[-1:])
    )
    fallback.attempts = attempts
    fallback.duration_s = time.perf_counter() - started
    fallback.output_tokens = tokens
    fallback.issues = issues_seen
    return fallback


# ---------------------------------------------------------------- fallback (no AI)

FALLBACK = {
    "fr": {
        "value": "{label} : {value} ({status}).",
        "value_gap": "{label} : {value}, soit {gap} ({status}).",
        "na": "{label} : donnée non disponible.",
        "na_requested": "{label} : donnée non disponible, à demander à : {holder}.",
        "identity": "{name} est un(e) {description}. Sa surface est de {area}.",
        "attention_intro": "Points d'attention, du plus marqué au moins marqué :",
        "question": "Quels facteurs expliquent la situation observée pour « {label} », et quelles pistes pourraient être étudiées avec les acteurs concernés ?",
        "typology": "Profil-type proposé : {typology}.",
        "citizens": "Contributions localisées dans l'unité : {total}.",
        "citizens_themes": "Thèmes principaux les plus cités : {themes}.",
        "citizens_few": "Elles sont trop peu nombreuses pour conclure.",
        "none": "Aucun déficit marqué ni point à surveiller selon les indicateurs disponibles.",
    },
    "ar": {
        "value": "{label}: {value} ({status}).",
        "value_gap": "{label}: {value}، أي {gap} ({status}).",
        "na": "{label}: معطى غير متوفر.",
        "na_requested": "{label}: معطى غير متوفر، يُطلب من: {holder}.",
        "identity": "{name}: {description}. تبلغ مساحتها {area}.",
        "attention_intro": "نقاط الانتباه، من الأكثر وضوحاً إلى الأقل:",
        "question": "ما العوامل التي تفسر الوضعية الملاحظة بخصوص «{label}»، وما المسارات التي يمكن دراستها مع الفاعلين المعنيين؟",
        "typology": "الصنف النموذجي المقترح: {typology}.",
        "citizens": "المساهمات المحددة في الوحدة: {total}.",
        "citizens_themes": "المواضيع الرئيسية الأكثر ذكراً: {themes}.",
        "citizens_few": "عددها غير كاف للاستنتاج.",
        "none": "لا يوجد خصاص واضح ولا نقطة تستدعي المتابعة حسب المؤشرات المتوفرة.",
    },
}


def _fact(fact_id: str) -> str:
    return "{{" + fact_id + "}}"


def fallback_section(
    sheet: FactSheet,
    section: Section,
    lang: Lang,
    title: str,
    typology: str | None,
    error: str | None,
) -> SectionResult:
    t = FALLBACK[lang]
    sentences: list[str] = []
    if section.include_identity and sheet.identity.get("area_fact"):
        sentences.append(
            t["identity"].format(
                name=sheet.identity[f"name_{lang}"],
                description=sheet.identity[f"description_{lang}"],
                area=_fact(sheet.identity["area_fact"]),
            )
        )
    codes = section_codes(section, sheet)
    if section.indicators == "attention":
        if codes:
            sentences.append(t["attention_intro"])
        else:
            sentences.append(t["none"])
    for code in codes:
        brief = sheet.briefs[code]
        label = brief.label[lang]
        if not brief.available:
            key = "na_requested" if brief.requested_from else "na"
            sentences.append(t[key].format(label=label, holder=brief.requested_from or ""))
            continue
        status = brief.status_label[lang].lower() if lang == "fr" else brief.status_label[lang]
        gap = brief.fact_ids.get("gap")
        sentences.append(
            (t["value_gap"] if gap else t["value"]).format(
                label=label,
                value=_fact(brief.fact_ids["value"]),
                gap=_fact(gap) if gap else "",
                status=status,
            )
        )
    paragraphs = [" ".join(sentences)] if sentences else []
    if section.indicators == "attention" and codes:
        paragraphs.append(
            " ".join(t["question"].format(label=sheet.briefs[c].label[lang]) for c in codes[:3])
        )
    if section.include_typology and typology:
        paragraphs.append(t["typology"].format(typology=typology))
    if section.include_citizens and sheet.citizens and sheet.citizens["total_fact"]:
        citizens = sheet.citizens
        parts = [t["citizens"].format(total=_fact(citizens["total_fact"]))]
        if citizens["themes"]:
            themes = "، ".join if lang == "ar" else ", ".join
            parts.append(
                t["citizens_themes"].format(
                    themes=themes(
                        f"{label[lang]} ({_fact(fid)})" for label, fid in citizens["themes"]
                    )
                )
            )
        if citizens["too_few"]:
            parts.append(t["citizens_few"])
        paragraphs.append(" ".join(parts))
    return SectionResult(section.code, title, paragraphs, "fallback", error=error)


def render(paragraph: str, sheet: FactSheet, lang: Lang) -> tuple[str, list[str]]:
    """Substitute {{Fxxx}} by the formatted values; return the text and the facts used."""
    used: list[str] = []
    down = [word_pattern(w, lang) for w in default_controls().trend.words.down.get(lang)]

    def substitute(match: Any) -> str:
        fact = sheet.get(match.group(1))
        if fact is None:
            return str(match.group(0))
        used.append(fact.id)
        value = fact.text[lang]
        # « recule de {{F002}} » : the verb already says the decrease, the sign would double it.
        if value[:1] in ("-", "−"):
            # Within the same sentence, up to 80 characters before the value.
            before = re.split(r"[.!?؟;؛]", paragraph[max(0, match.start() - 80) : match.start()])[
                -1
            ]
            before = normalize(before, lang)
            if any(p.search(before) for p in down):
                value = value[1:]
        return value

    text = PLACEHOLDER.sub(substitute, paragraph)
    # Models often repeat the unit after the reference (« {{F003}} habitants », « {{F002}} par
    # an ») although the value already carries it: drop the repeated words.
    for fact_id in set(used):
        fact = sheet.get(fact_id)
        if fact is None:
            continue
        value = fact.text[lang].lstrip("-−")
        words = value.split()
        for size in (3, 2, 1):
            tail = words[-size:]
            if len(words) <= size or any(w[0].isdigit() for w in tail):
                continue
            unit = " ".join(tail)
            pattern = re.escape(value) + r"\s+" + re.escape(unit) + r"(?!\w)"
            text = re.sub(pattern, value, text)
    return text, used
