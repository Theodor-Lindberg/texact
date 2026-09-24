import re
from typing import ClassVar

from printer import Printer

from .reviewer import Diagnostic, Reviewer, Status
from .rules import RULE_SEC001


class Reviewer_Section(Reviewer):
    """Checks that section headings follow the document hierarchy."""

    _PATTERN_HEADING = re.compile(
        r"\\(?P<heading>section|subsection|subsubsection|paragraph|subparagraph)"
        r"\*?(?![A-Za-z@])"
    )
    _LEVELS: ClassVar[dict[str, int]] = {
        "section": 0,
        "subsection": 1,
        "subsubsection": 2,
        "paragraph": 3,
        "subparagraph": 4,
    }

    def __init__(self, printer: Printer) -> None:
        self.printer = printer
        self.comments: list[Diagnostic] = []
        self.last_level = 0
        self.heading_count = 0

    def process_line(self, line_no: int, line: str) -> None:
        for match in self._PATTERN_HEADING.finditer(line):
            heading = match.group("heading")
            level = self._LEVELS[heading]
            if level > self.last_level + 1:
                parent = next(
                    name
                    for name, parent_level in self._LEVELS.items()
                    if parent_level == level - 1
                )
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_SEC001,
                        RULE_SEC001.render_message(
                            parent=self.printer.yellow(rf"\{parent}"),
                            heading=self.printer.dark_red(rf"\{heading}"),
                        ),
                    )
                )
            self.last_level = level
            self.heading_count += 1

    def get_comments(self) -> list[Diagnostic]:
        return self.comments

    def get_summary(self) -> str:
        if not self.comments:
            return ""
        return f"Heading hierarchy errors: {len(self.comments)}"

    def get_status(self) -> Status:
        return Status.PASSED if not self.comments else Status.FAILED

    def get_name(self) -> str:
        return "Section"
