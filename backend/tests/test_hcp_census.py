from app.ingestion.ghsl import tiles_for
from app.ingestion.hcp_census import HcpRow, match_units

ROWS = [
    HcpRow("4421", "Préfecture de Rabat", "عمالة الرباط", 515619, 157183),
    HcpRow("4441", "Préfecture de Salé", "عمالة سلا", 1089554, 290311),
    HcpRow("4421010", "Commune de Rabat", "جماعة الرباط", 509916, 156398),
    HcpRow("44210105", "Arrondissement de Hassan", "مقاطعة حسان", 92454, 32327),
    HcpRow("44210101", "Arrondissement d'Agdal Riyad", "مقاطعة أكدال الرياض", 70435, 24248),
    HcpRow("44410108", "Commune de Sidi Bouknadel", "جماعة سيدي أبي القنادل", 43598, 10439),
    HcpRow("50810505", "Commune de Bni Hassane", "جماعة بني حسان", 12390, 2687),
]


def test_units_are_matched_by_name_within_their_prefecture() -> None:
    units = [
        (1, "prefecture", "Préfecture de Rabat"),
        (2, "prefecture", "Préfecture de Salé"),
        (3, "arrondissement", "Hassan"),
        (4, "arrondissement", "Agdal-Riyad"),
        (5, "commune", "Sidi Bouknadel"),
        (6, "commune", "Inconnue"),
    ]
    matched, missing = match_units(units, ROWS)
    assert matched[3].code == "44210105"  # not « Bni Hassane », outside the prefectures
    assert matched[4].code == "44210101"  # dash vs space
    assert matched[5].population == 43598
    assert missing == ["Inconnue"]


def test_census_key_is_stable_between_2014_and_2024() -> None:
    assert HcpRow("44210105", "", "", None, None).key == HcpRow("104210105", "", "", None, None).key


def test_ghsl_tile_of_rabat_and_tetouan() -> None:
    assert tiles_for((-7.15, 33.52, -6.44, 34.19)) == [(6, 18)]
    assert tiles_for((-5.6, 35.2, -5.0, 35.7)) == [(6, 18)]
