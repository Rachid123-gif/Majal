"""End-to-end report generation against the real Rabat diagnostic (skipped without PostGIS)."""

import re
from collections.abc import Iterator
from typing import Any

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import check_database, get_engine
from app.models import Report, StudyArea
from app.services.llm.base import LLMError, LLMResult
from app.services.reports import generate
from app.services.reports.context import find_unit, latest_diagnostic

pytestmark = pytest.mark.skipif(not check_database().ok, reason="base PostGIS non disponible")


class EchoProvider:
    """Writes one sentence citing the first fact of the prompt (as a well-behaved model would)."""

    name, model, local = "fake", "fake", True

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls = 0

    def generate_json(
        self, system: str, prompt: str, schema: dict[str, Any], temperature: float = 0.2
    ) -> LLMResult:
        self.calls += 1
        if self.fail:
            raise LLMError("Ollama injoignable")
        facts = re.findall(r"\{\{F\d{3}\}\}", prompt)
        sentence = f"La valeur observée est {facts[0]}." if facts else "Aucune donnée disponible."
        return LLMResult({"paragraphs": [sentence]}, sentence, 0.01, 12)


@pytest.fixture
def session() -> Iterator[Session]:
    with Session(get_engine()) as db:
        if db.scalars(select(StudyArea).where(StudyArea.code == "rabat")).one_or_none() is None:
            pytest.skip("données de Rabat non importées")
        yield db
        db.execute(text("DELETE FROM reports WHERE provider = 'test'"))
        db.commit()


def unit_id(session: Session) -> int:
    return find_unit(latest_diagnostic(session, "rabat").result, "Yacoub El Mansour")


def test_report_with_a_model(session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generate, "get_provider", lambda settings, model=None: EchoProvider())
    content, _sheet, calls, mode = generate.build_report(session, "rabat", unit_id(session), "fr")
    assert mode == "ai" and calls > 0
    assert content["verification"]["ok"]
    codes = [s["code"] for s in content["sections"]]
    assert codes[-1] == "sources" and len(codes) == 9
    sources = content["sections"][-1]
    assert any("HCP" in line for line in sources["sources"])
    first = content["sections"][0]["paragraphs"][0]["text"]
    assert "{{" not in first  # every identifier was replaced by its value


def test_unreachable_model_gives_a_full_report_without_ai(
    session: Session, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        generate, "get_provider", lambda settings, model=None: EchoProvider(fail=True)
    )
    content, _, _, mode = generate.build_report(session, "rabat", unit_id(session), "ar")
    assert mode == "fallback"
    assert content["verification"]["ok"]
    texts = " ".join(p["text"] for s in content["sections"] for p in s["paragraphs"])
    assert "معدل البطالة" in texts


def test_reports_are_cached(session: Session, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(generate, "get_provider", lambda settings, model=None: EchoProvider())
    monkeypatch.setattr(generate, "provider_identity", lambda: ("test", "fake"))
    uid = unit_id(session)
    report, cached = generate.request_report(session, "rabat", uid, "fr", "test")
    assert not cached
    generate.run_report(session, report.id, "rabat")
    again, cached = generate.request_report(session, "rabat", uid, "fr", "test")
    assert cached and again.id == report.id
    forced, cached = generate.request_report(session, "rabat", uid, "fr", "test", force=True)
    assert not cached and forced.id != report.id
    assert session.get(Report, report.id).state == "done"  # type: ignore[union-attr]
