"""Per-run state contains observed facts, never shared conversation state."""

from dataclasses import dataclass, field
from typing import Any

TASKS = {"workflow", "classify", "summarize", "review", "revisions"}


@dataclass(frozen=True)
class Document:
    filename: str
    text: str
    sha256: str
    pages: int

    @property
    def lines(self):
        return list(enumerate(self.text.splitlines(), start=1))


@dataclass
class State:
    document: Document
    task: str
    instruction: str = ""
    results: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Decision:
    tool: str
    reason: str
    arguments: dict[str, Any] = field(default_factory=dict)


class InputError(ValueError):
    """A submission that cannot be processed."""


class PlannerError(RuntimeError):
    """Provider failure or invalid proposed action."""
