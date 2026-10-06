"""Citizen listening commands (« make citizens »).

python -m app.services.citizens import-fictif rabat
python -m app.services.citizens analyze rabat [--force] [--limit N]
python -m app.services.citizens evaluate rabat
"""

import argparse
import json
import sys
import time
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Consultation, Contribution, StudyArea, Territory
from app.services.citizens import evaluate, pipeline
from app.settings import REPO_ROOT, get_settings

FICTIF = get_settings().data_dir / "fictif"
NOTE = (
    "Contributions fictives — illustration du fonctionnement de l'outil. Elles ne reflètent pas "
    "l'opinion réelle des habitants. Méthode : docs/citoyens-jeu-fictif.md."
)


def study_area(session: Session, code: str) -> StudyArea:
    area = session.scalars(select(StudyArea).where(StudyArea.code == code)).one_or_none()
    if area is None:
        sys.exit(f"Territoire « {code} » inconnu ou non importé (lancez `make data`).")
    return area


def cmd_import(code: str) -> None:
    with Session(get_engine()) as session:
        area = study_area(session, code)
        meta, rows = pipeline.fictitious_rows(FICTIF / code / "contributions.yaml")
        consultation = pipeline.import_contributions(
            session,
            area,
            meta["code"],
            meta["title"],
            meta["badge"],
            rows,
            f"data/fictif/{code}/contributions.yaml",
            "make-citizens",
            NOTE,
        )
        print(f"✓ {len(rows)} contributions fictives importées ({consultation.code}).")


def consultations(session: Session, area: StudyArea) -> list[Consultation]:
    return list(
        session.scalars(select(Consultation).where(Consultation.study_area_id == area.id)).all()
    )


def cmd_analyze(code: str, force: bool) -> None:
    with Session(get_engine()) as session:
        area = study_area(session, code)
        started = time.perf_counter()

        def progress(index: int, total: int, c: Contribution) -> None:
            print(
                f"[{index}/{total}] {c.external_id} : {c.analysis['mode']}, "
                f"{', '.join(c.themes)}, {c.tonality}, lieu {c.analysis['location_method']}",
                flush=True,
            )

        for consultation in consultations(session, area):
            stats = pipeline.run(session, consultation, force, progress)
            print(f"✓ {consultation.code} : {stats} en {time.perf_counter() - started:.0f} s")


def cmd_evaluate(code: str) -> None:
    with Session(get_engine()) as session:
        area = study_area(session, code)
        units = {
            t.name_fr: t.id
            for t in session.scalars(
                select(Territory).where(
                    Territory.study_area_id == area.id, Territory.is_analysis_unit
                )
            )
        }
        contributions = [
            c
            for cons in consultations(session, area)
            for c in session.scalars(
                select(Contribution).where(Contribution.consultation_id == cons.id)
            )
        ]
        provisional = evaluate.score(
            contributions, evaluate.provisional_truth(FICTIF / code / "contributions.yaml", units)
        )
        reference_truth = evaluate.reference_truth(
            REPO_ROOT / "docs" / "evaluation" / "annotation-professeur.xlsx", {"amazigh_latin"}
        )
        reference = evaluate.score(contributions, reference_truth) if reference_truth else None
        out = {"provisional": provisional, "reference": reference}
        print(json.dumps(out, indent=2, ensure_ascii=False, default=str))
        path = REPO_ROOT / "docs" / "evaluation" / "resultats.md"
        path.write_text(markdown(provisional, reference), encoding="utf-8")
        print(f"→ {path.relative_to(REPO_ROOT)}")


def _pct(value: float | None) -> str:
    return "—" if value is None else f"{round(100 * value)} %"


def markdown(provisional: dict[str, Any], reference: dict[str, Any] | None) -> str:
    lines = [
        "# Évaluation de l'analyse des contributions citoyennes",
        "",
        "> Contributions fictives — illustration du fonctionnement de l'outil. Elles ne reflètent "
        "pas l'opinion réelle des habitants.",
        "",
        "Généré par `make citizens` (`python -m app.services.citizens evaluate rabat`).",
        "",
    ]
    for title, result, base in (
        ("Évaluation provisoire", provisional, evaluate.PROVISIONAL_BASE["fr"]),
        ("Évaluation de référence", reference, evaluate.REFERENCE_BASE["fr"]),
    ):
        lines += [f"## {title}", ""]
        if not result:
            lines += [
                "En attente du fichier classé par le professeur "
                "(`docs/evaluation/annotation-professeur.xlsx`).",
                "",
            ]
            continue
        lines += [f"Base : {base.format(n=result['n'])}.", ""]
        lines += ["| Mesure | IA locale | Mots-clés (sans IA) |", "| --- | --- | --- |"]
        for name, key in (
            ("Thèmes — précision", "precision"),
            ("Thèmes — rappel", "recall"),
            ("Thèmes — F1", "f1"),
        ):
            lines.append(
                f"| {name} | {_pct(result['themes']['model'][key])} "
                f"| {_pct(result['themes']['keywords'][key])} |"
            )
        main = result.get("main_theme", {}).get("model")
        if main:
            lines.append(
                f"| Thème principal parmi les thèmes annotés | {_pct(main['accuracy'])} | — |"
            )
        lines.append(
            f"| Tonalité — exactitude | {_pct(result['tonality']['model']['accuracy'])} "
            f"| {_pct(result['tonality']['keywords']['accuracy'])} |"
        )
        if "language" in result:
            lines.append(
                f"| Langue — exactitude | {_pct(result['language']['model']['accuracy'])} "
                f"| {_pct(result['language']['keywords']['accuracy'])} |"
            )
        if "location" in result:
            loc = result["location"]
            lines += [
                "",
                f"Localisation (unité d'analyse) : {loc['correct']} justes, {loc['wrong']} fausses, "
                f"{loc['not_located']} non localisées sur {result['n']}. Un lieu n'est rattaché "
                "que s'il est connu (quartiers, places, avenues d'OpenStreetMap) ou si la commune "
                "est déclarée ; sinon « lieu non identifié ».",
            ]
        lines += ["", f"Contributions analysées par l'IA : {result['n_ai']} sur {result['n']}.", ""]
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.services.citizens")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("import-fictif").add_argument("territory")
    analyze = sub.add_parser("analyze")
    analyze.add_argument("territory")
    analyze.add_argument("--force", action="store_true")
    sub.add_parser("evaluate").add_argument("territory")
    args = parser.parse_args()
    if args.command == "import-fictif":
        cmd_import(args.territory)
    elif args.command == "analyze":
        cmd_analyze(args.territory, args.force)
    else:
        cmd_evaluate(args.territory)


if __name__ == "__main__":
    main()
