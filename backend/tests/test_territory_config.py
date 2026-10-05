from pathlib import Path

import pytest

from app.config_loader import ConfigError, load_territories, load_territory
from app.settings import REPO_ROOT

TERRITORIES = REPO_ROOT / "config" / "territories"
RABAT = (TERRITORIES / "rabat.yaml").read_text(encoding="utf-8")


def write(tmp_path: Path, content: str, name: str = "rabat.yaml") -> Path:
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return path


def issues_for(path: Path) -> ConfigError:
    with pytest.raises(ConfigError) as exc_info:
        load_territory(path)
    return exc_info.value


def line_of(text: str, needle: str) -> int:
    return next(i for i, line in enumerate(text.splitlines(), start=1) if needle in line)


def test_real_territory_files_are_valid() -> None:
    territories = load_territories(TERRITORIES)
    assert set(territories) == {"rabat", "tetouan"}
    assert territories["rabat"].default_scope.code == "agglomeration"
    assert territories["rabat"].profiles.indicators == "urbain"
    assert territories["tetouan"].profiles.indicators == "mixte"
    assert territories["tetouan"].analysis_levels.fine.fallback == "grid"


def test_missing_field_is_reported_in_french(tmp_path: Path) -> None:
    content = RABAT.replace(
        'region: { fr: "Rabat-Salé-Kénitra", ar: "جهة الرباط سلا القنيطرة" }\n', ""
    )
    error = issues_for(write(tmp_path, content))
    [issue] = error.issues
    assert issue.field == "region"
    assert "obligatoire" in issue.problem


def test_unknown_field_points_to_its_line(tmp_path: Path) -> None:
    content = RABAT.replace("profiles:\n", "profils:\n")
    error = issues_for(write(tmp_path, content))
    unknown = next(i for i in error.issues if i.field == "profils")
    assert "pas reconnu" in unknown.problem
    assert unknown.line == line_of(content, "profils:")


def test_wrong_level_lists_allowed_values(tmp_path: Path) -> None:
    content = RABAT.replace("  level: prefecture\n", "  level: wilaya\n", 1)
    error = issues_for(write(tmp_path, content))
    [issue] = error.issues
    assert issue.field == "study_area > level"
    assert "Valeurs possibles" in issue.problem and "province" in issue.problem
    assert issue.example == "level: commune"
    assert issue.line == line_of(content, "level: wilaya")


def test_yaml_syntax_error_is_explained(tmp_path: Path) -> None:
    content = RABAT.replace(
        'name: { fr: "Rabat", ar: "الرباط" }', 'name: { fr: "Rabat", ar: "الرباط" '
    )
    error = issues_for(write(tmp_path, content))
    [issue] = error.issues
    assert "YAML valide" in issue.problem
    assert issue.line is not None


def test_duplicate_key_is_rejected(tmp_path: Path) -> None:
    content = RABAT + "\nprofiles:\n  indicators: mixte\n  taxonomy: mixte\n"
    error = issues_for(write(tmp_path, content))
    [issue] = error.issues
    assert "deux fois" in issue.problem
    assert issue.field == "profiles"


def test_exactly_one_default_scope(tmp_path: Path) -> None:
    content = RABAT.replace("  - code: prefecture\n", "  - code: prefecture\n    default: true\n")
    error = issues_for(write(tmp_path, content))
    assert any("un seul périmètre" in i.problem for i in error.issues)


def test_code_must_match_file_name(tmp_path: Path) -> None:
    error = issues_for(write(tmp_path, RABAT, name="sale.yaml"))
    [issue] = error.issues
    assert issue.field == "code"
    assert "nom du fichier" in issue.problem


def test_arabic_label_must_contain_arabic(tmp_path: Path) -> None:
    content = RABAT.replace(
        'name: { fr: "Rabat", ar: "الرباط" }', 'name: { fr: "Rabat", ar: "Rabat" }'
    )
    error = issues_for(write(tmp_path, content))
    [issue] = error.issues
    assert issue.field == "name > ar"
    assert "caractères arabes" in issue.problem


def test_grid_requires_cell_size(tmp_path: Path) -> None:
    content = RABAT.replace("    cell_size_m: 500\n", "")
    error = issues_for(write(tmp_path, content))
    [issue] = error.issues
    assert "cell_size_m" in issue.problem


def test_slug_format(tmp_path: Path) -> None:
    content = RABAT.replace("  indicators: urbain", "  indicators: Urbain-2")
    error = issues_for(write(tmp_path, content))
    [issue] = error.issues
    assert issue.field == "profiles > indicators"
    assert "minuscules" in issue.problem


def test_errors_of_all_files_are_collected(tmp_path: Path) -> None:
    write(tmp_path, RABAT.replace("profiles:\n", "profils:\n"))
    write(tmp_path, "code: tetouan\n", name="tetouan.yaml")
    with pytest.raises(ConfigError) as exc_info:
        load_territories(tmp_path)
    files = {issue.file for issue in exc_info.value.issues}
    assert files == {"rabat.yaml", "tetouan.yaml"}


def test_formatted_message_is_readable(tmp_path: Path) -> None:
    content = RABAT.replace("  level: prefecture\n", "  level: wilaya\n", 1)
    message = issues_for(write(tmp_path, content)).format()
    assert message.startswith("1 erreur dans la configuration")
    assert "rabat.yaml, ligne" in message
    assert "Exemple correct : level: commune" in message


def test_empty_file(tmp_path: Path) -> None:
    error = issues_for(write(tmp_path, "# rien\n"))
    assert "vide" in error.issues[0].problem
