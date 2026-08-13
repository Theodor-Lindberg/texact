from abc import ABC, abstractmethod
from enum import Enum, auto

from printer import Printer


class Status(Enum):
    PASSED = auto()
    FAILED = auto()
    WARNING = auto()
    UNCHECKED = auto()


class Reviewer(ABC):
    @abstractmethod
    def __init__(self, printer: Printer) -> None:
        raise NotImplementedError

    @abstractmethod
    def process_line(self, line_no: int, line: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_comments(self) -> list[tuple[int, str]]:
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
