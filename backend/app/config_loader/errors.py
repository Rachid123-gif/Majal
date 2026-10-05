"""Configuration errors, written for a non-developer reader (the scientific referent)."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfigIssue:
    file: str
    line: int | None
    field: str
    problem: str
    example: str | None = None

    def format(self) -> str:
        where = f"{self.file}, ligne {self.line}" if self.line else self.file
        parts = [
            f"• {where}",
            f"  Champ : {self.field or '(fichier entier)'}",
            f"  Problème : {self.problem}",
        ]
        if self.example:
            parts.append(f"  Exemple correct : {self.example}")
        return "\n".join(parts)


class ConfigError(Exception):
    def __init__(self, issues: list[ConfigIssue]) -> None:
        self.issues = issues
        super().__init__(self.format())

    def format(self) -> str:
        count = len(self.issues)
        header = f"{count} erreur{'s' if count > 1 else ''} dans la configuration :"
        return "\n".join([header, *(issue.format() for issue in self.issues)])
