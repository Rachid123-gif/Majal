"""Download, once, the fonts (glyphs) and icons (sprites) of the offline base map.

Source: Protomaps basemaps-assets (fonts: Noto, SIL Open Font License; sprites: BSD-3).
Only the character ranges needed for French and Arabic labels are kept.
Usage (repo root): python3 scripts/fetch_basemap_assets.py
"""

import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://protomaps.github.io/basemaps-assets"
OUT = Path(__file__).resolve().parents[1] / "frontend/public/basemap"
FONTS = ["Noto Sans Regular", "Noto Sans Medium", "Noto Sans Italic"]
# Latin, Latin-1/Extended, combining marks, Arabic (+ supplement, extended),
# punctuation, letterlike symbols, Arabic presentation forms.
RANGES = [
    "0-255", "256-511", "512-767", "768-1023", "1536-1791", "1792-2047", "2048-2303",
    "8192-8447", "8448-8703", "64256-64511", "64512-64767", "64768-65023", "65024-65279",
    "65280-65535",
]
SPRITES = ["light.json", "light.png", "light@2x.json", "light@2x.png"]


def get(url: str, target: Path) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
    except urllib.error.HTTPError as exc:
        print(f"  absent ({exc.code}) : {url}")
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return True


def main() -> int:
    count = 0
    for font in FONTS:
        for glyph_range in RANGES:
            url = f"{BASE}/fonts/{urllib.parse.quote(font)}/{glyph_range}.pbf"
            count += get(url, OUT / "fonts" / font / f"{glyph_range}.pbf")
    for sprite in SPRITES:
        count += get(f"{BASE}/sprites/v4/{sprite}", OUT / "sprites" / sprite)
    print(f"✓ {count} fichiers dans {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
