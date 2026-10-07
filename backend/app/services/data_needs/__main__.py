"""`python -m app.services.data_needs notes <territory> [--out DIR]`: writes every data request
note (Word and PDF) of a territory, from the fixed template (no AI)."""

import argparse
import sys
from pathlib import Path

from app.settings import REPO_ROOT, get_settings


def main() -> int:
    parser = argparse.ArgumentParser(prog="python -m app.services.data_needs")
    sub = parser.add_subparsers(dest="command", required=True)
    notes = sub.add_parser("notes", help="Notes de demande de données (Word et PDF)")
    notes.add_argument("territory")
    notes.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()

    from app.api.data_needs import _config, _data_needs
    from app.services.data_needs.notes import build_note, load_note_template, to_docx, to_pdf

    holders, _rules = _config(args.territory)
    template = load_note_template(
        get_settings().config_dir / "report_templates" / "note_demande.yaml"
    )
    data = _data_needs(args.territory)
    out: Path = args.out or REPO_ROOT / "docs" / "notes-demande" / args.territory
    out.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(data["institutions"], start=1):
        note = build_note(data, row["code"], holders, template)
        stem = f"{index:02d}-{row['code']}"
        (out / f"{stem}.docx").write_bytes(to_docx(note))
        (out / f"{stem}.pdf").write_bytes(to_pdf(note))
        print(f"✓ {stem} : {row['name']['fr']}")
    from app.services.data_needs.excel import to_xlsx

    sheet = out / f"besoins-donnees-{args.territory}.xlsx"
    sheet.write_bytes(to_xlsx(data, holders.note_territory.fr))
    print(f"{len(data['institutions'])} notes (Word et PDF) et le tableau Excel dans {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
