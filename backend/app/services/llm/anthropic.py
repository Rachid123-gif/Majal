"""Anthropic Claude API. Ready but disabled: only usable with SOVEREIGN_MODE=false and a key."""

import json
import re
import time
from typing import Any

import httpx

from app.services.llm.base import LLMError, LLMResult

API_URL = "https://api.anthropic.com/v1/messages"


class AnthropicProvider:
    name = "anthropic"
    local = False

    def __init__(self, api_key: str, model: str, timeout_s: float = 120.0) -> None:
        if not api_key:
            raise LLMError("Clé ANTHROPIC_API_KEY absente du fichier .env.")
        self.api_key = api_key
        self.model = model
        self.timeout_s = timeout_s

    def generate_json(
        self, system: str, prompt: str, schema: dict[str, Any], temperature: float = 0.2
    ) -> LLMResult:
        instruction = (
            f"{prompt}\n\nRéponds uniquement par un objet JSON conforme à ce schéma :\n"
            f"{json.dumps(schema, ensure_ascii=False)}"
        )
        started = time.perf_counter()
        try:
            response = httpx.post(
                API_URL,
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": 2000,
                    "temperature": temperature,
                    "system": system,
                    "messages": [{"role": "user", "content": instruction}],
                },
                timeout=self.timeout_s,
            )
        except httpx.HTTPError as exc:
            raise LLMError(f"API Anthropic injoignable ({exc.__class__.__name__}).") from exc
        if response.status_code != 200:
            raise LLMError(f"API Anthropic : HTTP {response.status_code}.")
        payload = response.json()
        raw = "".join(b.get("text", "") for b in payload.get("content", []))
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        try:
            data = json.loads(match.group(0)) if match else None
        except json.JSONDecodeError:
            data = None
        return LLMResult(
            data if isinstance(data, dict) else None,
            raw,
            time.perf_counter() - started,
            payload.get("usage", {}).get("output_tokens"),
        )
