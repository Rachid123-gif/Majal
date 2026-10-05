"""`python -m app.config_loader` — check every configuration file and explain errors in French."""

import sys

from app.config_loader import ConfigError, load_territories
from app.settings import get_settings


def main() -> int:
    directory = get_settings().config_dir / "territories"
    try:
        territories = load_territories(directory)
    except ConfigError as exc:
        print(exc.format())
        return 1
    for code in territories:
        print(f"✓ territories/{code}.yaml : valide")
    return 0


if __name__ == "__main__":
    sys.exit(main())
