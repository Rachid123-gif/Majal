"""`python -m app.services.indicators compute <territoire>` — compute and store a diagnostic."""

import sys

from sqlalchemy.orm import Session

from app.config_loader import ConfigError, load_territories
from app.db import get_engine
from app.services.indicators.engine import MissingInput, compute_diagnostic
from app.settings import get_settings


def main(argv: list[str]) -> int:
    codes = argv[1:] if len(argv) > 1 and argv[0] == "compute" else []
    if not codes:
        try:
            codes = list(load_territories(get_settings().config_dir / "territories"))
        except ConfigError as exc:
            print(exc.format())
            return 1
    ok = True
    with Session(get_engine()) as session:
        for code in codes:
            try:
                diagnostic = compute_diagnostic(session, code, author="make indicators")
            except MissingInput as exc:
                print(f"- {code} : {exc.reason}")
                continue
            except ConfigError as exc:
                print(exc.format())
                ok = False
                continue
            values = [v for u in diagnostic.result["units"] for v in u["values"].values()]
            available = sum(1 for v in values if v["value"] is not None)
            print(
                f"✓ {code} : diagnostic calculé en {(diagnostic.duration_ms or 0) / 1000:.1f} s "
                f"({len(diagnostic.result['indicators'])} indicateurs, {available}/{len(values)} "
                f"valeurs disponibles, grille {diagnostic.grid_version})."
            )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
