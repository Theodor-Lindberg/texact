import re

from printer import Printer

from .reviewer import Diagnostic, Reviewer, Status
from .rules import RULE_INT001


class Reviewer_Inthis(Reviewer):
    """Checks the opening wording of an abstract."""

    _PATTERN_ABSTRACT_START = re.compile(r"\\begin\{abstract\}")
    _PATTERN_THIS_WORK = re.compile(
        r"\bthis\s+(?:\w+\s+)*(work|brief|paper|manuscript)s?\b",
        re.IGNORECASE,
    )

    def __init__(self, printer: Printer) -> None:
        self.printer = printer
        self.abstract_context_start = False
        self.check_abstract_first_line = False
        self.abstract_check = Status.UNCHECKED
        self.comments: list[Diagnostic] = []

    def process_line(self, line_no: int, line: str) -> None:
        if (
            self.abstract_check == Status.UNCHECKED
            and self._PATTERN_ABSTRACT_START.search(line)
        ):
            self.check_abstract_first_line = True
            return

        if self.check_abstract_first_line and line and line[0] != "%":
            self.check_abstract_first_line = False
            match = self._PATTERN_THIS_WORK.search(line)
            if match:
                self.abstract_check = Status.FAILED
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_INT001,
                        RULE_INT001.render_message(),
                    )
                )
            else:
                self.abstract_check = Status.PASSED

    def get_comments(self) -> list[Diagnostic]:
        return self.comments

    def get_summary(self) -> str:
        return ""

    def get_status(self) -> Status:
        return self.abstract_check

    def get_name(self) -> str:
        return "InThisWork"
