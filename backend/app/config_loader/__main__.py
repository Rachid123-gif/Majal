"""`python -m app.config_loader` — check every configuration file and explain errors in French."""

import sys

from app.config_loader import ConfigError, load_territories
from app.config_loader.facility_mapping import load_facility_mapping
from app.settings import get_settings


def main() -> int:
    settings = get_settings()
    try:
        territories = load_territories(settings.config_dir / "territories")
    except ConfigError as exc:
        print(exc.format())
        return 1
    ok = True
    for code, territory in territories.items():
        print(f"✓ territories/{code}.yaml : valide")
        facilities = territory.sources.get("facilities")
        mapping = facilities.model_dump().get("mapping") if facilities else None
        if mapping:
            try:
                load_facility_mapping(settings.config_dir.parent / mapping)
                print(f"✓ {mapping} : valide")
            except ConfigError as exc:
                print(exc.format())
                ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
