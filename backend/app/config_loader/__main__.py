"""`python -m app.config_loader` — check every configuration file and explain errors in French."""

import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.config_loader import ConfigError, load_territories
from app.config_loader.facility_mapping import load_facility_mapping
from app.config_loader.indicators import load_confidence, load_evaluation, load_grid
from app.settings import get_settings


def check(label: str, loader: Callable[[Path], Any], path: Path) -> bool:
    try:
        loader(path)
    except ConfigError as exc:
        print(exc.format())
        return False
    print(f"✓ {label} : valide")
    return True


def main() -> int:
    settings = get_settings()
    root = settings.config_dir
    ok = True
    try:
        territories = load_territories(root / "territories")
    except ConfigError as exc:
        print(exc.format())
        return 1
    for code in territories:
        print(f"✓ territories/{code}.yaml : valide")
    ok &= check("indicators/grille-v0.yaml", load_grid, root / "indicators" / "grille-v0.yaml")
    ok &= check(
        "indicators/evaluation.yaml", load_evaluation, root / "indicators" / "evaluation.yaml"
    )
    ok &= check("confidence.yaml", load_confidence, root / "confidence.yaml")
    # Imported here: these schemas live with the services that use them.
    from app.services.indicators.typology import load_typology
    from app.services.reports.meaning import load_controls
    from app.services.reports.template import load_template

    ok &= check("indicators/typologie.yaml", load_typology, root / "indicators" / "typologie.yaml")
    templates = root / "report_templates"
    ok &= check(
        "report_templates/diagnostic_commune.yaml",
        load_template,
        templates / "diagnostic_commune.yaml",
    )
    ok &= check("report_templates/controles.yaml", load_controls, templates / "controles.yaml")
    from app.config_loader.taxonomy import load_taxonomy
    from app.services.citizens.anonymize import load_anonymisation

    ok &= check(
        "citizens/anonymisation.yaml",
        load_anonymisation,
        root / "citizens" / "anonymisation.yaml",
    )

    for profile in sorted({t.profiles.taxonomy for t in territories.values()}):
        path = root / "taxonomy" / f"{profile}.yaml"
        if path.exists():
            ok &= check(f"taxonomy/{profile}.yaml", load_taxonomy, path)
        else:
            print(f"- taxonomy/{profile}.yaml : pas encore rédigé")
    mappings = {
        source.model_dump().get("mapping")
        for territory in territories.values()
        for source in territory.sources.values()
        if source.importer == "osm_facilities"
    } - {None}
    for mapping in sorted(m for m in mappings if m):
        ok &= check(mapping, load_facility_mapping, root.parent / mapping)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
