"""Language-model providers. Sovereign mode forbids any provider that leaves the machine."""

from dataclasses import dataclass
from typing import Any, Protocol


class LLMError(RuntimeError):
    """The model could not answer (unreachable, timeout, invalid output)."""


class SovereignModeError(LLMError):
    """An external provider was requested while SOVEREIGN_MODE is on."""


@dataclass(frozen=True)
class LLMResult:
    data: dict[str, Any] | None
    raw: str
    duration_s: float
    output_tokens: int | None


class LLMProvider(Protocol):
    name: str
    model: str
    local: bool

    def generate_json(
        self, system: str, prompt: str, schema: dict[str, Any], temperature: float = 0.2
    ) -> LLMResult: ...
