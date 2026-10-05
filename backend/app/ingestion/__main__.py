"""Command line: `python -m app.ingestion run [territoires…] [--refresh] [--only …]`.

`make data` calls it for every territory, then fetches the offline base map.
"""

import argparse
import sys

from sqlalchemy.orm import Session

from app.config_loader import ConfigError, load_territories
from app.db import get_engine
from app.ingestion.runner import run_territory, study_area_bbox
from app.settings import get_settings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m app.ingestion")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="importe les données des territoires")
    run.add_argument("territories", nargs="*", help="codes (par défaut : tous)")
    run.add_argument("--refresh", action="store_true", help="retélécharge au lieu du cache")
    run.add_argument("--only", action="append", help="limite à un importeur (ex. osm_facilities)")
    bbox = sub.add_parser("bbox", help="emprise d'un territoire (pour le fond de carte)")
    bbox.add_argument("territory")
    basemaps = sub.add_parser("basemaps", help="territoires ayant un fond de carte à préparer")
    basemaps.set_defaults()
    args = parser.parse_args(argv)

    try:
        territories = load_territories(get_settings().config_dir / "territories")
    except ConfigError as exc:
        print(exc.format())
        return 1

    with Session(get_engine()) as session:
        if args.command == "bbox":
            box = study_area_bbox(session, args.territory)
            if box is None:
                print("", end="")
                return 1
            print(",".join(f"{v:.5f}" for v in box))
            return 0
        if args.command == "basemaps":
            for code, config in territories.items():
                for source in config.sources.values():
                    if source.importer == "basemap_pmtiles":
                        print(f"{code} {source.model_dump().get('maxzoom', 15)}")
            return 0
        codes = args.territories or list(territories)
        unknown = [c for c in codes if c not in territories]
        if unknown:
            available = ", ".join(territories)
            print(f"Territoire inconnu : {', '.join(unknown)}. Disponibles : {available}.")
            return 1
        only = set(args.only) if args.only else None
        ok = all(
            run_territory(session, territories[code], refresh=args.refresh, only=only)
            for code in codes
        )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
