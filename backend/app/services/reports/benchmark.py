"""Model benchmark on a real report: `python -m app.services.reports.benchmark MODEL… [--unit NAME]`.

Writes, for each model and language, the full report (rendered) and the measurements to
docs/benchmarks/, then prints a comparison table.
"""

import argparse
import json
import time
from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy.orm import Session

from app.db import get_engine
from app.services.llm.ollama import OllamaProvider
from app.services.reports.context import find_unit, latest_diagnostic, unit_identity
from app.services.reports.facts import build_fact_sheet
from app.services.reports.numbers import check_rendered, definitional_phrases
from app.services.reports.template import load_template
from app.services.reports.writer import Lang, render, write_section
from app.settings import REPO_ROOT, get_settings

OUT = REPO_ROOT / "docs" / "benchmarks"


def run(models: list[str], unit_name: str, code: str, langs: list[str]) -> list[dict[str, Any]]:
    settings = get_settings()
    template = load_template(settings.config_dir / "report_templates" / "diagnostic_commune.yaml")
    results = []
    with Session(get_engine()) as session:
        diagnostic = latest_diagnostic(session, code).result
        unit_id = find_unit(diagnostic, unit_name)
        identity = unit_identity(session, unit_id)
    OUT.mkdir(parents=True, exist_ok=True)
    for model in models:
        provider = OllamaProvider(settings.ollama_url, model, settings.llm_timeout_s)
        warm = time.perf_counter()
        provider.generate_json("Réponds en JSON.", 'Écris {"ok": true}', {"type": "object"})
        load_s = time.perf_counter() - warm
        for lang_code in langs:
            lang = cast(Lang, lang_code)
            sheet = build_fact_sheet(diagnostic, unit_id, dict(identity))
            definitional = definitional_phrases(
                [b.label["fr"] for b in sheet.briefs.values()]
                + [b.label["ar"] for b in sheet.briefs.values()]
            )
            started = time.perf_counter()
            sections = [
                write_section(provider, sheet, s, template, lang) for s in template.sections
            ]
            total = time.perf_counter() - started
            lines = [f"# {model} — {lang} — {identity['name_' + lang]}", ""]
            final_issues = 0
            for number, section in enumerate(sections, start=1):
                lines.append(
                    f"## {number}. {section.title}  _({section.mode}, {section.attempts} essai(s), {section.duration_s:.1f} s)_"
                )
                for paragraph in section.paragraphs:
                    text, used = render(paragraph, sheet, lang)
                    values = [f.text[lang] for u in used if (f := sheet.get(u)) is not None]
                    final_issues += len(check_rendered(text, values, sheet.years, definitional))
                    lines.append(text)
                    lines.append("")
                if section.issues:
                    lines.append(
                        f"> Corrections demandées au modèle : {' | '.join(section.issues)}"
                    )
                    lines.append("")
            path = OUT / f"{model.replace(':', '_')}-{lang}.md"
            path.write_text("\n".join(lines), encoding="utf-8")
            ai = [s for s in sections if s.mode in ("ai", "fallback")]
            result = {
                "model": model,
                "lang": lang,
                "load_s": round(load_s, 1),
                "total_s": round(total, 1),
                "sections_ai": sum(1 for s in ai if s.mode == "ai"),
                "sections_fallback": sum(1 for s in ai if s.mode == "fallback"),
                "attempts": sum(s.attempts for s in ai),
                "retries": sum(max(0, s.attempts - 1) for s in ai),
                "caught_numbers": sum(len(s.issues) for s in ai),
                "tokens": sum(s.output_tokens for s in ai),
                "final_untraced_numbers": final_issues,
                "file": str(path.relative_to(REPO_ROOT)),
            }
            results.append(result)
            print(json.dumps(result, ensure_ascii=False))
    # Merge with earlier runs (one model at a time): a new run replaces the same model + language.
    path_all = OUT / "resultats.json"
    previous = json.loads(path_all.read_text(encoding="utf-8")) if path_all.exists() else {}
    fresh = {(r["model"], r["lang"]) for r in results}
    merged = [
        r
        for r in previous.get("results", [])
        if previous.get("unit") == unit_name and (r["model"], r["lang"]) not in fresh
    ] + results
    path_all.write_text(
        json.dumps(
            {"date": datetime.now(UTC).isoformat(), "unit": unit_name, "results": merged},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("models", nargs="+")
    parser.add_argument("--unit", default="Yacoub El Mansour")
    parser.add_argument("--territory", default="rabat")
    parser.add_argument("--langs", nargs="+", default=["fr", "ar"])
    args = parser.parse_args()
    run(args.models, args.unit, args.territory, args.langs)


if __name__ == "__main__":
    main()
