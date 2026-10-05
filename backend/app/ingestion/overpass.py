"""Overpass API client with a local cache.

Every response is saved under `data/raw/<territory>/` with its query and retrieval date, so
the imports can be replayed offline and traced to a dated extraction.
"""

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx

from app.settings import get_settings

USER_AGENT = "MAJAL-demonstrateur/0.1 (diagnostic territorial, usage non commercial)"


@dataclass(frozen=True)
class RawResponse:
    data: dict[str, Any]
    path: Path
    retrieved_at: datetime
    from_cache: bool

    @property
    def osm_base(self) -> datetime | None:
        """Date of the OpenStreetMap data served by the Overpass server."""
        stamp = self.data.get("osm3s", {}).get("timestamp_osm_base")
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")) if stamp else None


class OverpassError(RuntimeError):
    pass


RETRY_STATUSES = {429, 502, 503, 504}


def _post_with_retries(query: str, attempts: int = 4) -> dict[str, Any]:
    """The public Overpass servers are often busy: wait and retry before giving up."""
    detail = ""
    servers = get_settings().overpass_urls
    for attempt in range(attempts):
        if attempt >= len(servers):
            time.sleep(15 * attempt)
        url = servers[attempt % len(servers)]
        try:
            response = httpx.post(
                url,
                data={"data": query},
                headers={"User-Agent": USER_AGENT},
                timeout=httpx.Timeout(600.0, connect=20.0),
            )
        except httpx.HTTPError as exc:
            detail = exc.__class__.__name__
            continue
        if response.status_code in RETRY_STATUSES or "too busy" in response.text[:2000]:
            detail = f"HTTP {response.status_code}, serveur occupé"
            continue
        if response.status_code != 200:
            raise OverpassError(
                f"Overpass a refusé la requête (HTTP {response.status_code}) : "
                f"{response.text[:300]}"
            )
        try:
            data: dict[str, Any] = response.json()
        except ValueError:
            detail = "réponse illisible"
            continue
        return data
    raise OverpassError(
        f"Le service OpenStreetMap (Overpass) n'a pas répondu ({detail}) après {attempts} "
        "tentatives. Vérifiez la connexion internet et relancez `make data` un peu plus tard."
    )


def fetch(query: str, cache_path: Path, refresh: bool = False) -> RawResponse:
    if cache_path.exists() and not refresh:
        cached = json.loads(cache_path.read_text(encoding="utf-8"))
        if cached.get("query") == query:
            return RawResponse(
                cached["response"],
                cache_path,
                datetime.fromisoformat(cached["retrieved_at"]),
                from_cache=True,
            )
    data = _post_with_retries(query)
    if data.get("remark", "").startswith("runtime error"):
        raise OverpassError(f"Overpass a refusé la requête : {data['remark']}")
    retrieved_at = datetime.now(UTC)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(
        json.dumps(
            {"retrieved_at": retrieved_at.isoformat(), "query": query, "response": data},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return RawResponse(data, cache_path, retrieved_at, from_cache=False)
