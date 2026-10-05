"""Provider selection. In sovereign mode only local providers are allowed."""

from app.services.llm.anthropic import AnthropicProvider
from app.services.llm.base import LLMError, LLMProvider, LLMResult, SovereignModeError
from app.services.llm.ollama import OllamaProvider
from app.settings import Settings, get_settings

__all__ = ["LLMError", "LLMProvider", "LLMResult", "SovereignModeError", "get_provider"]


def get_provider(settings: Settings | None = None, model: str | None = None) -> LLMProvider | None:
    """Return the configured provider, or None when the AI is switched off (LLM_PROVIDER=none)."""
    settings = settings or get_settings()
    name = settings.llm_provider
    if name == "none":
        return None
    if name == "ollama":
        return OllamaProvider(
            settings.ollama_url, model or settings.ollama_model, settings.llm_timeout_s
        )
    if name == "anthropic":
        if settings.sovereign_mode:
            raise SovereignModeError(
                "Mode souverain actif (SOVEREIGN_MODE=true) : aucun service d'IA extérieur ne peut "
                "être utilisé. Pour activer Claude, mettez SOVEREIGN_MODE=false et une clé "
                "ANTHROPIC_API_KEY dans .env."
            )
        return AnthropicProvider(settings.anthropic_api_key, model or settings.anthropic_model)
    raise LLMError(
        f"Fournisseur d'IA inconnu : {name} (valeurs possibles : ollama, anthropic, none)."
    )
