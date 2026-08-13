import re

from .reviewer import Reviewer, Status
from printer import Printer


class Reviewer_Unsure(Reviewer):
    _PATTERN = re.compile(r"\b(?:should|would|could|might|very)\b", re.IGNORECASE)
    _PATTERN_WE = re.compile(r"\bwe\b", re.IGNORECASE)
    _MAX_WE_OCCURRENCES = 5

    def __init__(self, printer: Printer) -> None:
        self.printer = printer
        self.match_count = 0
        self.we_count = 0
        self.we_limit_comment_added = False
        self.we_last_line: int | None = None
        self.comments: list[tuple[int, str]] = []

    def process_line(self, line_no: int, line: str) -> None:
        we_matches = self.find_we(line)
        if we_matches:
            self.we_count += len(we_matches)
            self.we_last_line = line_no

        matches = self.find_ould(line)
        if matches:
            message = self._PATTERN.sub(
                lambda match: self.printer.dark_red(match.group(0)),
                line.rstrip("\n"),
            )
            self.comments.append((line_no, message))
            self.match_count += len(matches)

    def get_comments(self) -> list[tuple[int, str]]:
        if (
            self.we_count > self._MAX_WE_OCCURRENCES
            and not self.we_limit_comment_added
            and self.we_last_line is not None
        ):
            self.comments.append(
                (
                    self.we_last_line,
                    (
                        f"Word {self.printer.dark_red('we')} occurs "
                        f"{self.we_count} times; maximum allowed is "
                        f"{self._MAX_WE_OCCURRENCES}."
                    ),
                )
            )
            self.we_limit_comment_added = True
        return self.comments

    def get_summary(self) -> str:
        issues: list[str] = []
        if self.match_count:
            issues.append(f"Banned words: {self.match_count}")
        if self.we_count > self._MAX_WE_OCCURRENCES:
            issues.append(
                f"Exceeded 'we' count: {self.we_count}/{self._MAX_WE_OCCURRENCES}"
            )

        if not issues:
            return ""
        return ". ".join(issues)

    def get_status(self) -> Status:
        return (
            Status.PASSED
            if self.match_count == 0 and self.we_count <= self._MAX_WE_OCCURRENCES
            else Status.FAILED
        )

    def find_ould(self, line: str) -> list[str]:
        return self._PATTERN.findall(line)

    def find_we(self, line: str) -> list[str]:
        return self._PATTERN_WE.findall(line)

    def get_name(self) -> str:
        return "Modal verbs"
