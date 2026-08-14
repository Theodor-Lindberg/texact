from abc import ABC, abstractmethod
from dataclasses import dataclass, replace
from pathlib import Path
from enum import Enum, auto

from printer import Printer
from .rules import Rule, Severity


class Status(Enum):
    """Result states for reviewers."""

    PASSED = auto()
    FAILED = auto()
    WARNING = auto()
    UNCHECKED = auto()


@dataclass(frozen=True)
class Diagnostic:
    """One rule finding and its source location."""

    line_no: int
    rule: Rule
    message: str
    source_path: Path | None = None
    severity_override: Severity | None = None

    @property
    def code(self) -> str:
        return self.rule.code

    @property
    def severity(self) -> Severity:
        return self.severity_override or self.rule.severity

    @property
    def line(self) -> int:
        return self.line_no + 1

    @property
    def filename(self) -> str | None:
        if self.source_path is None:
            return None
        return str(self.source_path)

    def documentation_url(self, base_url: str | None = None) -> str:
        return self.rule.documentation_url(base_url)

    def with_source(self, source_path: Path) -> "Diagnostic":
        return replace(self, source_path=source_path)


class Reviewer(ABC):
    """Base interface for reviewers."""

    @abstractmethod
    def __init__(self, printer: Printer) -> None:
        raise NotImplementedError

    @abstractmethod
    def process_line(self, line_no: int, line: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_comments(self) -> list[Diagnostic]:
        raise NotImplementedError

    @abstractmethod
    def get_summary(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_status(self) -> Status:
        raise NotImplementedError

    @abstractmethod
    def get_name(self) -> str:
        raise NotImplementedError
