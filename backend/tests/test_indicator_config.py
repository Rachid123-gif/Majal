from pathlib import Path

import pytest

from app.config_loader import ConfigError
from app.config_loader.indicators import load_confidence, load_evaluation, load_grid
from app.settings import REPO_ROOT

GRID = REPO_ROOT / "config" / "indicators" / "grille-v0.yaml"
EVALUATION = REPO_ROOT / "config" / "indicators" / "evaluation.yaml"


def test_grid_v0_follows_the_methodology() -> None:
    grid = load_grid(GRID)
    assert grid.grid_version == "v0"
    assert grid.display_label.fr == "Grille v0 — proposition en cours de validation"
    assert len(grid.axes) == 8
    assert len(grid.indicators) == 28
    assert len(grid.for_profile("urbain")) == 25
    assert len(grid.for_profile("mixte")) == 22
    # No norm is invented: every norm value is empty and marked TODO_REFERENT.
    for indicator in grid.indicators:
        assert indicator.status == "TODO_REFERENT"
        if indicator.norm is not None:
            assert indicator.norm.value is None
            assert indicator.norm.source == "TODO_REFERENT"


def test_evaluation_thresholds_from_the_methodology() -> None:
    evaluation = load_evaluation(EVALUATION)
    assert evaluation.thresholds.higher_better.deficit_marked == 0.80
    assert evaluation.thresholds.higher_better.watch == 0.95
    assert evaluation.thresholds.lower_better.deficit_marked == 1.20
    assert "norme officielle non encore intégrée" in evaluation.label.fr
    load_confidence(REPO_ROOT / "config" / "confidence.yaml")


def write(tmp_path: Path, source: Path, old: str, new: str) -> Path:
    text = source.read_text(encoding="utf-8")
    assert old in text
    path = tmp_path / source.name
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return path


def test_neutral_indicator_cannot_be_evaluated(tmp_path: Path) -> None:
    path = write(
        tmp_path,
        GRID,
        "    reference: none\n    status: TODO_REFERENT",
        "    reference: relative\n    status: TODO_REFERENT",
    )
    with pytest.raises(ConfigError) as exc_info:
        load_grid(path)
    assert any("neutral" in issue.problem for issue in exc_info.value.issues)


def test_unknown_formula_type_is_explained(tmp_path: Path) -> None:
    path = write(tmp_path, GRID, "type: cagr", "type: croissance")
    with pytest.raises(ConfigError) as exc_info:
        load_grid(path)
    issue = exc_info.value.issues[0]
    assert "Valeurs possibles" in issue.problem or "type" in issue.field


def test_thresholds_must_be_ordered(tmp_path: Path) -> None:
    path = write(tmp_path, EVALUATION, "watch: 0.95", "watch: 0.70")
    with pytest.raises(ConfigError) as exc_info:
        load_evaluation(path)
    assert "deficit_marked < watch" in exc_info.value.issues[0].problem
