"""Pre-generate the reports of every unit, for demonstrations (« make reports »).

    python -m app.services.reports pregenerate rabat [--langs fr ar] [--force]

Reports already in the cache (same data, model and outline) are skipped unless --force.
"""

import argparse
import sys
import time
from typing import cast

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Territory
from app.services.reports.context import latest_diagnostic
from app.services.reports.generate import request_report, run_report
from app.services.reports.writer import Lang


def pregenerate(code: str, langs: list[str], force: bool) -> int:
    failures = 0
    with Session(get_engine()) as session:
        diagnostic = latest_diagnostic(session, code)
        units = session.scalars(
            select(Territory)
            .where(Territory.study_area_id == diagnostic.study_area_id, Territory.is_analysis_unit)
            .order_by(Territory.name_fr)
        ).all()
        total = len(units) * len(langs)
        done = 0
        for unit in units:
            for lang in langs:
                done += 1
                started = time.perf_counter()
                report, cached = request_report(
                    session,
                    code,
                    unit.id,
                    cast(Lang, lang),
                    "make-reports",
                    force,
                )
                label = f"[{done}/{total}] {unit.name_fr} ({lang})"
                if cached:
                    print(f"{label} : déjà en cache")
                    continue
                try:
                    report = run_report(session, report.id, code)
                except Exception as exc:
                    failures += 1
                    print(f"{label} : ÉCHEC — {exc}")
                    continue
                print(
                    f"{label} : {report.state}, rédaction {report.writing_mode}, "
                    f"{time.perf_counter() - started:.0f} s"
                )
    return failures


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.services.reports")
    sub = parser.add_subparsers(dest="command", required=True)
    pre = sub.add_parser(
        "pregenerate", help="Génère et met en cache les rapports de toutes les unités"
    )
    pre.add_argument("territory")
    pre.add_argument("--langs", nargs="+", default=["fr", "ar"], choices=["fr", "ar"])
    pre.add_argument("--force", action="store_true")
    args = parser.parse_args()
    failures = pregenerate(args.territory, args.langs, args.force)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
