import re

from printer import Printer

from .reviewer import Diagnostic, Reviewer, Status
from .rules import RULE_UNS001, RULE_UNS002, RULE_UNS003


class Reviewer_Unsure(Reviewer):
    """Checks uncertain wording and repeated use of 'we'."""

    _PATTERN = re.compile(r"\b(?:should|would|could|might|very)\b", re.IGNORECASE)
    _PATTERN_WE = re.compile(r"\bwe\b", re.IGNORECASE)
    _PATTERN_AUTHOR_POSSESSIVE = re.compile(r"\bauthor's\b", re.IGNORECASE)
    _MAX_WE_OCCURRENCES = 5

    def __init__(
        self,
        printer: Printer,
        max_we_occurrences: int | None = None,
    ) -> None:
        self.printer = printer
        self.max_we_occurrences = (
            self._MAX_WE_OCCURRENCES
            if max_we_occurrences is None
            else max_we_occurrences
        )
        self.match_count = 0
        self.we_count = 0
        self.we_limit_comment_added = False
        self.we_last_line: int | None = None
        self.author_possessive_count = 0
        self.comments: list[Diagnostic] = []

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
            self.comments.append(
                Diagnostic(
                    line_no,
                    RULE_UNS001,
                    RULE_UNS001.render_message(line=message),
                )
            )
            self.match_count += len(matches)

        author_possessive_matches = self.find_author_possessive(line)
        if author_possessive_matches:
            self.comments.append(
                Diagnostic(
                    line_no,
                    RULE_UNS003,
                    RULE_UNS003.render_message(),
                )
            )
            self.author_possessive_count += len(author_possessive_matches)

    def get_comments(self) -> list[Diagnostic]:
        if (
            self.we_count > self.max_we_occurrences
            and not self.we_limit_comment_added
            and self.we_last_line is not None
        ):
            self.comments.append(
                Diagnostic(
                    self.we_last_line,
                    RULE_UNS002,
                    RULE_UNS002.render_message(
                        count=self.we_count,
                        limit=self.max_we_occurrences,
                    ),
                )
            )
            self.we_limit_comment_added = True
        return self.comments

    def get_summary(self) -> str:
        issues: list[str] = []
        if self.match_count:
            issues.append(f"Banned words: {self.match_count}")
        if self.we_count > self.max_we_occurrences:
            issues.append(
                f"Exceeded 'we' count: {self.we_count}/{self.max_we_occurrences}"
            )
        if self.author_possessive_count:
            issues.append(f"Author's possessives: {self.author_possessive_count}")

        if not issues:
            return ""
        return ". ".join(issues)

    def get_status(self) -> Status:
        return (
            Status.PASSED
            if (
                self.match_count == 0
                and self.we_count <= self.max_we_occurrences
                and self.author_possessive_count == 0
            )
            else Status.FAILED
        )

    def find_ould(self, line: str) -> list[str]:
        return self._PATTERN.findall(line)

    def find_we(self, line: str) -> list[str]:
        return self._PATTERN_WE.findall(line)

    def find_author_possessive(self, line: str) -> list[str]:
        return self._PATTERN_AUTHOR_POSSESSIVE.findall(line)

    def get_name(self) -> str:
        return "Modal verbs"
