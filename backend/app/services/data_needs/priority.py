"""Priority of a data request: COMPUTED from what the data would change, never chosen by hand
(rule of the project owner, 2026-10-07).

- essential: it makes indicators computable that are « non disponible » today, or it concerns
  the official boundaries;
- useful: it improves indicators that are only estimated or open, or it gives a measure to a
  citizen theme;
- context: programmed projects (to tell, later, a need not covered from a need already covered
  by a programmed project); a request for programmed projects stays « context » even when it
  also improves an indicator (Bouregreg: its public spaces complete the green spaces).
"""

from typing import Literal

from app.config_loader.data_holders import DataHolders, DataRequest

Priority = Literal["essential", "useful", "context"]
ORDER: dict[Priority, int] = {"essential": 0, "useful": 1, "context": 2}
LABELS: dict[Priority, dict[str, str]] = {
    "essential": {"fr": "Essentielle", "ar": "أساسية"},
    "useful": {"fr": "Utile", "ar": "مفيدة"},
    "context": {"fr": "Contexte", "ar": "سياق"},
}


def priority(request: DataRequest) -> Priority:
    if request.enables or request.boundaries:
        return "essential"
    if request.context:
        return "context"
    if request.improves or request.themes:
        return "useful"
    return "context"


def sort_key(request: DataRequest) -> tuple[int, int, int, int, str]:
    """Priority first, then the number of indicators made computable, then improved, then
    themes given a measure."""
    return (
        ORDER[priority(request)],
        -len(request.enables),
        -len(request.improves),
        -len(request.themes),
        request.code,
    )


def ranked(holders: DataHolders) -> list[DataRequest]:
    return sorted(holders.requests, key=sort_key)
