"""Priority of a data request: COMPUTED from what the data would change, never chosen by hand
(rule of the project owner, 2026-10-07). The rules, their order and the sort order are in
config/data_holders/regles.yaml (TODO_REFERENT); the first rule that applies wins.
"""

from app.config_loader.data_holders import DataHolders, DataRequest, ModuleRules, PriorityCode


def _criterion(request: DataRequest, name: str) -> bool:
    return bool(getattr(request, name))


def priority(request: DataRequest, rules: ModuleRules) -> PriorityCode:
    for rule in rules.priority_rules:
        if any(_criterion(request, name) for name in rule.when_any):
            return rule.priority
    return rules.priority_rules[-1].priority


def sort_key(request: DataRequest, rules: ModuleRules) -> tuple[int | str, ...]:
    """By default: priority, then the total number of indicators concerned (computable +
    improved), then the number of citizen themes; the code last, for a stable order."""
    order = list(rules.priorities)
    values: dict[str, int] = {
        "priority": order.index(priority(request, rules)),
        "indicators": -len(set(request.enables) | set(request.improves)),
        "themes": -len(request.themes),
    }
    return (*(values[name] for name in rules.sort_by), request.code)


def ranked(holders: DataHolders, rules: ModuleRules) -> list[DataRequest]:
    return sorted(holders.requests, key=lambda r: sort_key(r, rules))
