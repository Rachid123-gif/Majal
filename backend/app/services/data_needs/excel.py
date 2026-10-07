"""Summary spreadsheet of the data requests (stage 5.5): one row per request, ranked as on the
screen (« Par où commencer »), with the « Priorité » column and the three effects (« calculer »,
« fiabiliser », « affiner »); a sheet per institution with its follow-up; a « Lisez-moi » sheet.
"""

import io
from datetime import date
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

HEADER_FILL = PatternFill("solid", fgColor="12343B")
HEADER_FONT = Font(bold=True, color="F6F3EC")
WRAP = Alignment(wrap_text=True, vertical="top")


def _sheet(ws: Any, headers: list[tuple[str, int]], rows: list[list[Any]]) -> None:
    for index, (title, width) in enumerate(headers, start=1):
        cell = ws.cell(row=1, column=index, value=title)
        cell.fill, cell.font, cell.alignment = HEADER_FILL, HEADER_FONT, WRAP
        ws.column_dimensions[get_column_letter(index)].width = width
    for row in rows:
        ws.append(row)
    for line in ws.iter_rows(min_row=2):
        for cell in line:
            cell.alignment = WRAP
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions


def _effect(codes: list[str], labels: dict[str, str]) -> str:
    return f"{len(codes)} : " + " ; ".join(labels[c] for c in codes) if codes else ""


def to_xlsx(data: dict[str, Any], territory_label: str) -> bytes:
    names = {i["code"]: i["name"]["fr"] for i in data["institutions"]}
    tracking = {i["code"]: i["tracking"] for i in data["institutions"] if "tracking" in i}
    labels = {i["code"]: i["label"]["fr"] for i in data["indicators"]}
    verbs = {k: v["verb"]["fr"].capitalize() for k, v in data["effects"].items()}
    statuses = data.get("tracking_statuses", {})

    def follow_up(code: str) -> str:
        item = tracking.get(code)
        if not item:
            return ""
        label = statuses.get(item["status"], {}).get("fr", item["status"])
        return f"{label} ({item['date']})" if item.get("date") else label

    workbook = Workbook()
    requests = workbook.create_sheet("Données demandées")
    workbook.remove(workbook.worksheets[0])
    rows = []
    for rank, request in enumerate(data["requests"], start=1):
        rows.append(
            [
                rank,
                request["priority_label"]["fr"],
                request["data"]["fr"],
                " ; ".join(names[h] for h in request["holders"]),
                " ; ".join(names[h] for h in request["complementary"]),
                " ; ".join(names[h] for h in request["alternatives"]),
                request["detail"]["fr"],
                request["format"]["fr"],
                request["period"]["fr"],
                request["frequency"]["fr"],
                _effect(request["effects"]["computed"], labels),
                _effect(request["effects"]["reliable"], labels),
                _effect(request["effects"]["finer"], labels)
                + (
                    f" (à l'échelle {request['finer_scale']['fr']})"
                    if request["effects"]["finer"] and request["finer_scale"]
                    else ""
                ),
                ", ".join(data["themes"].get(t, {}).get("fr", t) for t in request["themes"]),
                "Oui" if request["context"] else "",
                request["value"]["fr"],
                " ; ".join(follow_up(h) for h in request["holders"]),
            ]
        )
    _sheet(
        requests,
        [
            ("Rang", 6),
            ("Priorité", 12),
            ("Donnée demandée", 42),
            ("Destinataire(s)", 34),
            ("Détenteurs complémentaires", 26),
            ("Autres détenteurs possibles", 26),
            ("Niveau de détail", 20),
            ("Format", 20),
            ("Période", 18),
            ("Fréquence", 14),
            (verbs["computed"], 34),
            (verbs["reliable"], 34),
            (verbs["finer"], 34),
            ("Thèmes sans indicateur", 26),
            ("Contexte (projets programmés)", 14),
            ("Ce que cela permettrait", 46),
            ("Suivi de la demande", 22),
        ],
        rows,
    )

    institutions = workbook.create_sheet("Institutions")
    _sheet(
        institutions,
        [
            ("Institution", 40),
            ("Intitulé à vérifier", 12),
            ("Priorité", 12),
            (verbs["computed"], 10),
            (verbs["reliable"], 10),
            (verbs["finer"], 10),
            ("Thèmes sans indicateur", 12),
            ("Ce que ses données permettraient", 60),
            ("Suivi de la demande", 16),
            ("Date", 12),
            ("Mis à jour par", 14),
        ],
        [
            [
                i["name"]["fr"],
                "Oui" if i["to_verify"] else "",
                (i["priority_label"] or {}).get("fr", ""),
                len(i["effects"]["computed"]),
                len(i["effects"]["reliable"]),
                len(i["effects"]["finer"]),
                len(i["themes"]),
                i["sentence"]["fr"],
                statuses.get(i["tracking"]["status"], {}).get("fr", "") if "tracking" in i else "",
                (i.get("tracking") or {}).get("date") or "",
                (i.get("tracking") or {}).get("updated_by") or "",
            ]
            for i in data["institutions"]
        ],
    )

    readme = workbook.create_sheet("Lisez-moi")
    lines = [
        f"MAJAL — besoins en données : {territory_label}",
        f"Généré le {date.today().isoformat()} par MAJAL (projet de recherche appliquée).",
        data["label"]["fr"],
        f"Grille : {data['summary']['available']} indicateurs disponibles sur "
        f"{data['summary']['total']} pour ce territoire.",
        "Priorité calculée, jamais choisie à la main (config/data_holders/regles.yaml, à valider "
        "par le professeur) : « Essentielle » si la donnée rend calculables des indicateurs "
        "aujourd'hui non disponibles ou porte sur les limites officielles ; « Contexte » pour les "
        "projets programmés, même s'ils améliorent un indicateur ; « Utile » si elle améliore "
        "des indicateurs ou mesure un thème aujourd'hui sans indicateur.",
        "Classement : priorité, puis nombre total d'indicateurs concernés, puis nombre de thèmes.",
        "Effets : « calculer » un indicateur aujourd'hui manquant ; « fiabiliser » un indicateur "
        "aujourd'hui ouvert ou estimé ; « affiner » un indicateur officiel à une échelle plus "
        "fine.",
    ]
    readme.column_dimensions["A"].width = 120
    for line in lines:
        readme.append([line])
        readme.cell(row=readme.max_row, column=1).alignment = WRAP
    readme["A1"].font = Font(bold=True, size=13, color="12343B")
    workbook.move_sheet("Lisez-moi", offset=-2)
    workbook.active = 1

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
