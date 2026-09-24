import re

from printer import Printer

from .reviewer import Diagnostic, Reviewer, Status
from .rules import (
    RULE_UNS001,
    RULE_UNS002,
    RULE_UNS003,
    RULE_UNS004,
    RULE_UNS005,
    RULE_UNS006,
)


class Reviewer_Unsure(Reviewer):
    """Checks uncertain wording and repeated use of 'we'."""

    _PATTERN = re.compile(r"\b(?:should|would|could|might|very)\b", re.IGNORECASE)
    _PATTERN_WE = re.compile(r"\bwe\b", re.IGNORECASE)
    _PATTERN_AUTHOR_POSSESSIVE = re.compile(r"\bauthor's\b", re.IGNORECASE)
    _PATTERN_SPACE_BEFORE_PUNCTUATION = re.compile(r"[ \t]+[.,;:!?]")
    _PATTERN_DOUBLE_PERIOD = re.compile(r"(?<![./])\.\.(?![./])(?=\s|$)")
    _PATTERN_PERIOD_WITHOUT_SPACE = re.compile(r"(?<![.\d/])\.(?=\S)(?![.\d/])")
    _PATTERN_PATH = re.compile(r"[^\s{}]*\/[^\s{}]*")
    _PATTERN_ABBREVIATION = re.compile(r"\b(?:[A-Za-z]{1,3}\.){2,}")
    _PATTERN_FILENAME = re.compile(
        r"\b[\w-]+\.(?:aux|bib|cfg|class|cls|css|csv|gif|html|jpg|jpeg|js|json|md|pdf|png|py|svg|tex|txt|webp|xml|yaml|yml)\b"
    )
    _PATTERN_MARKBOTH_START = re.compile(r"\\markboth\b")
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
        self.space_before_punctuation_count = 0
        self.double_period_count = 0
        self.period_without_space_count = 0
        self.comments: list[Diagnostic] = []
        # State for masking \markboth{...}{...}, which may span multiple lines
        self._markboth_awaiting_brace = False
        self._markboth_depth = 0
        self._markboth_groups_remaining = 0

    def _mask_markboth(self, line: str) -> str:
        chars = list(line)
        i = 0
        while i < len(chars):
            if self._markboth_depth == 0 and not self._markboth_awaiting_brace:
                match = self._PATTERN_MARKBOTH_START.search(line, i)
                if not match:
                    break
                for j in range(match.start(), match.end()):
                    chars[j] = " "
                i = match.end()
                self._markboth_awaiting_brace = True
                self._markboth_groups_remaining = 2
                continue

            char = chars[i]
            if self._markboth_awaiting_brace:
                if char == "{":
                    self._markboth_awaiting_brace = False
                    self._markboth_depth = 1
                    chars[i] = " "
                elif not char.isspace():
                    # Not the expected argument; stop masking.
                    self._markboth_awaiting_brace = False
                    self._markboth_groups_remaining = 0
                    continue
                i += 1
                continue

            if char == "{":
                self._markboth_depth += 1
            elif char == "}":
                self._markboth_depth -= 1
                if self._markboth_depth == 0:
                    self._markboth_groups_remaining -= 1
                    if self._markboth_groups_remaining > 0:
                        self._markboth_awaiting_brace = True
            chars[i] = " "
            i += 1

        return "".join(chars)

    def process_line(self, line_no: int, line: str) -> None:
        # Ignore the boilerplate running header set via \markboth{...}{...},
        # which may span multiple lines.
        line = self._mask_markboth(line)

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

        space_before_punctuation_matches = self.find_space_before_punctuation(line)
        if space_before_punctuation_matches:
            self.comments.append(
                Diagnostic(
                    line_no,
                    RULE_UNS004,
                    RULE_UNS004.render_message(),
                )
            )
            self.space_before_punctuation_count += len(space_before_punctuation_matches)

        double_period_matches = self.find_double_periods(line)
        if double_period_matches:
            self.comments.append(
                Diagnostic(
                    line_no,
                    RULE_UNS005,
                    RULE_UNS005.render_message(),
                )
            )
            self.double_period_count += len(double_period_matches)

        period_without_space_matches = self.find_periods_without_space(line)
        if period_without_space_matches:
            self.comments.append(
                Diagnostic(
                    line_no,
                    RULE_UNS006,
                    RULE_UNS006.render_message(),
                )
            )
            self.period_without_space_count += len(period_without_space_matches)

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
        if self.space_before_punctuation_count:
            issues.append(
                f"Spaces before punctuation: {self.space_before_punctuation_count}"
            )
        if self.double_period_count:
            issues.append(f"Double periods: {self.double_period_count}")
        if self.period_without_space_count:
            issues.append(
                f"Periods without following spaces: {self.period_without_space_count}"
            )

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
                and self.space_before_punctuation_count == 0
                and self.double_period_count == 0
                and self.period_without_space_count == 0
            )
            else Status.FAILED
        )

    def find_ould(self, line: str) -> list[str]:
        return self._PATTERN.findall(line)

    def find_we(self, line: str) -> list[str]:
        return self._PATTERN_WE.findall(line)

    def find_author_possessive(self, line: str) -> list[str]:
        return self._PATTERN_AUTHOR_POSSESSIVE.findall(line)

    def find_space_before_punctuation(self, line: str) -> list[str]:
        return self._PATTERN_SPACE_BEFORE_PUNCTUATION.findall(line)

    def find_double_periods(self, line: str) -> list[str]:
        return self._PATTERN_DOUBLE_PERIOD.findall(line)

    def find_periods_without_space(self, line: str) -> list[str]:
        masked_line = list(line)
        for pattern in (
            self._PATTERN_PATH,
            self._PATTERN_ABBREVIATION,
            self._PATTERN_FILENAME,
        ):
            for match in pattern.finditer(line):
                for index in range(match.start(), match.end()):
                    masked_line[index] = " "
        return self._PATTERN_PERIOD_WITHOUT_SPACE.findall("".join(masked_line))

    def get_name(self) -> str:
        return "Modal verbs"
