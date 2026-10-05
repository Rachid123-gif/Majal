"""Model choice: qwen3:8b by default, gemma3:4b when qwen3 is not installed."""

import pytest

from app.services.llm.ollama import OllamaProvider
from app.services.reports import generate
from app.settings import Settings


@pytest.mark.parametrize(
    ("installed", "expected"),
    [
        (["qwen3:8b", "gemma3:4b"], "qwen3:8b"),
        (["gemma3:4b"], "gemma3:4b"),
        ([], "qwen3:8b"),  # Ollama closed: keep the main model, the text without AI takes over
        (["llama3:8b"], "qwen3:8b"),
    ],
)
def test_fallback_model(
    monkeypatch: pytest.MonkeyPatch, installed: list[str], expected: str
) -> None:
    settings = Settings(
        llm_provider="ollama", ollama_model="qwen3:8b", ollama_fallback_model="gemma3:4b"
    )
    monkeypatch.setattr(generate, "get_settings", lambda: settings)
    monkeypatch.setattr(OllamaProvider, "available_models", lambda self: installed)
    assert generate.provider_identity() == ("ollama", expected)
