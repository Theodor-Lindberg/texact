import re

from printer import Printer

from .reviewer import Diagnostic, Reviewer, Status
from .rules import RULE_MAT001


class Reviewer_Math(Reviewer):
    """Checks mathematical notation."""

    _PATTERN_PLUS_MINUS = re.compile(r"\+\-|\-\+")

    def __init__(self, printer: Printer) -> None:
        self.printer = printer
        self.comments: list[Diagnostic] = []

    def process_line(self, line_no: int, line: str) -> None:
        for match in self._PATTERN_PLUS_MINUS.finditer(line):
            self.comments.append(
                Diagnostic(
                    line_no,
                    RULE_MAT001,
                    RULE_MAT001.render_message(
                        notation=self.printer.dark_red(match.group(0)),
                    ),
                )
            )

    def get_comments(self) -> list[Diagnostic]:
        return self.comments

    def get_summary(self) -> str:
        if not self.comments:
            return ""
        return f"Plus-minus notation: {len(self.comments)}"

    def get_status(self) -> Status:
        return Status.PASSED if not self.comments else Status.FAILED

    def get_name(self) -> str:
        return "Math"
