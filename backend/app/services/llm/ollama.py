"""Local model served by Ollama on the Mac (outside Docker, to use the Apple GPU)."""

import json
import time
from typing import Any

import httpx

from app.services.llm.base import LLMError, LLMResult


class OllamaProvider:
    name = "ollama"
    local = True

    def __init__(self, url: str, model: str, timeout_s: float = 300.0) -> None:
        self.url = url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def generate_json(
        self, system: str, prompt: str, schema: dict[str, Any], temperature: float = 0.2
    ) -> LLMResult:
        body: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "format": schema,  # structured output, constrained by the JSON schema
            "stream": False,
            "options": {"temperature": temperature, "num_ctx": 8192},
            "keep_alive": "30m",
        }
        if self.model.startswith("qwen3"):
            body["think"] = False  # no hidden reasoning: faster, and the output is the answer
        started = time.perf_counter()
        try:
            response = httpx.post(f"{self.url}/api/chat", json=body, timeout=self.timeout_s)
        except httpx.HTTPError as exc:
            raise LLMError(
                f"Ollama injoignable ({exc.__class__.__name__}) : vérifiez que l'application "
                "Ollama est ouverte sur le Mac."
            ) from exc
        if response.status_code != 200:
            raise LLMError(f"Ollama a répondu HTTP {response.status_code} : {response.text[:200]}")
        payload = response.json()
        raw = payload.get("message", {}).get("content", "")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            data = None
        return LLMResult(
            data if isinstance(data, dict) else None,
            raw,
            time.perf_counter() - started,
            payload.get("eval_count"),
        )

    def available_models(self) -> list[str]:
        try:
            response = httpx.get(f"{self.url}/api/tags", timeout=5)
            return [m["name"] for m in response.json().get("models", [])]
        except (httpx.HTTPError, ValueError, KeyError):
            return []
