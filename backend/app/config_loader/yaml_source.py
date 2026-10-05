"""YAML reading that keeps line numbers, so errors can point to the exact line."""

from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode, Node, SequenceNode

from app.config_loader.errors import ConfigIssue


def read_yaml(path: Path) -> tuple[Any, Node | None, list[ConfigIssue]]:
    """Return (data, root node, issues). Syntax errors and duplicate keys become issues."""
    text = path.read_text(encoding="utf-8")
    try:
        root = yaml.compose(text, Loader=yaml.SafeLoader)
        data = yaml.safe_load(text)
    except yaml.MarkedYAMLError as exc:
        mark = exc.problem_mark
        return (
            None,
            None,
            [
                ConfigIssue(
                    file=path.name,
                    line=mark.line + 1 if mark else None,
                    field="",
                    problem=(
                        "Le fichier n'est pas un YAML valide (indentation, deux-points ou "
                        f"guillemets à vérifier). Détail technique : {exc.problem}"
                    ),
                )
            ],
        )
    return data, root, _duplicate_keys(path.name, root, ())


def _duplicate_keys(file: str, node: Node | None, loc: tuple[str, ...]) -> list[ConfigIssue]:
    issues: list[ConfigIssue] = []
    if isinstance(node, MappingNode):
        seen: set[str] = set()
        for key_node, value_node in node.value:
            key = str(key_node.value)
            if key in seen:
                issues.append(
                    ConfigIssue(
                        file=file,
                        line=key_node.start_mark.line + 1,
                        field=" > ".join((*loc, key)),
                        problem="Ce champ apparaît deux fois au même niveau ; gardez-en un seul.",
                    )
                )
            seen.add(key)
            issues.extend(_duplicate_keys(file, value_node, (*loc, key)))
    elif isinstance(node, SequenceNode):
        for index, item in enumerate(node.value):
            issues.extend(_duplicate_keys(file, item, (*loc, str(index))))
    return issues


def locate_line(root: Node | None, loc: tuple[int | str, ...]) -> int | None:
    """Line (1-based) of the deepest node reachable along `loc`."""
    node = root
    line = node.start_mark.line + 1 if node else None
    for part in loc:
        child: Node | None = None
        if isinstance(node, MappingNode):
            for key_node, value_node in node.value:
                if str(key_node.value) == str(part):
                    child = value_node
                    line = key_node.start_mark.line + 1
                    break
        elif isinstance(node, SequenceNode) and isinstance(part, int) and part < len(node.value):
            child = node.value[part]
            line = child.start_mark.line + 1
        if child is None:
            break
        node = child
    return line
