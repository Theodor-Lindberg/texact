import re
from typing import ClassVar

from printer import Printer
from template_check import Template

from .reviewer import Diagnostic, Reviewer, Status
from .rules import (
    RULE_MAT001,
    RULE_MAT002,
    RULE_MAT003,
    RULE_MAT004,
    RULE_MAT005,
    RULE_MAT006,
)


class Reviewer_Math(Reviewer):
    """Checks mathematical notation."""

    _PATTERN_PLUS_MINUS = re.compile(r"\+\-|\-\+")
    _MATH_OPERATORS = (
        "arccos",
        "arcsin",
        "arctan",
        "arg",
        "cos",
        "cosh",
        "cot",
        "coth",
        "csc",
        "deg",
        "det",
        "dim",
        "exp",
        "gcd",
        "hom",
        "inf",
        "ker",
        "lg",
        "lim",
        "liminf",
        "limsup",
        "ln",
        "log",
        "max",
        "min",
        "Pr",
        "sec",
        "sin",
        "sinh",
        "sup",
        "tan",
        "tanh",
    )
    _PATTERN_MATH_OPERATOR = re.compile(
        r"(?<![A-Za-z\\])(?P<operator>"
        + "|".join(sorted(_MATH_OPERATORS, key=len, reverse=True))
        + r")(?![A-Za-z])"
    )
    _PATTERN_MU = re.compile(r"(?<![A-Za-z])\\mu(?![A-Za-z])")
    _PATTERN_PARENTHESIS = re.compile(r"(?P<delimiter>\(|\))")
    _PATTERN_DELIMITER = re.compile(r"(?<!\\)(?P<delimiter>[\[\]{}()])")
    _DELIMITER_PAIRS: ClassVar[dict[str, str]] = {
        "(": ")",
        "[": "]",
        "{": "}",
    }
    _PATTERN_UNSUPPORTED_IEEE_ENVIRONMENT = re.compile(
        r"\\begin\{(?P<environment>"
        r"align\*?|alignat\*?|gather\*?|multline\*?|flalign\*?|"
        r"split\*?|aligned\*?|alignedat\*?|gathered\*?)\}"
    )
    _PATTERN_MATH_TOKEN = re.compile(
        r"\\begin\{(?:equation|IEEEeqnarray|align|alignat|gather|multline|flalign|displaymath|math)\*?\}"
        r"|\\end\{(?:equation|IEEEeqnarray|align|alignat|gather|multline|flalign|displaymath|math)\*?\}"
        r"|\\\(|\\\)|\\\[|\\\]|(?<!\\)\$\$?"
    )
    _PATTERN_LABEL = re.compile(r"\\label\{[^}]*\}")

    def __init__(
        self,
        printer: Printer,
        template: Template = Template.UNKNOWN,
    ) -> None:
        self.printer = printer
        self.template = template
        self.comments: list[Diagnostic] = []
        self._in_math_mode = False
        self._delimiter_stack: list[tuple[str, int]] = []
        self._unclosed_delimiters_added = False

    def process_line(self, line_no: int, line: str) -> None:
        for match in self._PATTERN_DELIMITER.finditer(line):
            delimiter = match.group("delimiter")
            if delimiter in self._DELIMITER_PAIRS:
                self._delimiter_stack.append((delimiter, line_no))
                continue

            if not self._delimiter_stack:
                details = f"unmatched closing {delimiter}"
            else:
                opening, opening_line = self._delimiter_stack.pop()
                expected = self._DELIMITER_PAIRS[opening]
                if expected == delimiter:
                    continue
                details = (
                    f"{opening} from line {opening_line + 1} is closed by {delimiter}; "
                    f"expected {expected}"
                )

            self.comments.append(
                Diagnostic(
                    line_no,
                    RULE_MAT006,
                    RULE_MAT006.render_message(
                        details=self.printer.dark_red(details),
                    ),
                )
            )

        if self.template == Template.IEEE:
            for match in self._PATTERN_UNSUPPORTED_IEEE_ENVIRONMENT.finditer(line):
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_MAT005,
                        RULE_MAT005.render_message(
                            environment=self.printer.dark_red(
                                match.group("environment")
                            ),
                        ),
                    )
                )

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

        math_segments: list[str] = []
        cursor = 0
        for token_match in self._PATTERN_MATH_TOKEN.finditer(line):
            if self._in_math_mode:
                math_segments.append(line[cursor : token_match.start()])

            token = token_match.group(0)
            is_begin_environment = token.startswith(r"\begin")
            is_end_environment = token.startswith(r"\end")
            is_opening_delimiter = token in (r"\(", r"\[", "$$", "$")

            if is_begin_environment or (
                not self._in_math_mode and is_opening_delimiter
            ):
                self._in_math_mode = True
            elif is_end_environment or token in (r"\)", r"\]", "$$", "$"):
                self._in_math_mode = False

            cursor = token_match.end()

        if self._in_math_mode:
            math_segments.append(line[cursor:])

        for math_segment in math_segments:
            operator_segment = self._PATTERN_LABEL.sub("", math_segment)
            for match in self._PATTERN_MATH_OPERATOR.finditer(operator_segment):
                operator = match.group("operator")
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_MAT002,
                        RULE_MAT002.render_message(
                            operator=self.printer.dark_red(operator),
                            command=self.printer.yellow(f"\\{operator}"),
                        ),
                    )
                )
            for match in self._PATTERN_MU.finditer(math_segment):
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_MAT003,
                        RULE_MAT003.render_message(
                            command=self.printer.yellow(r"\textmu"),
                        ),
                    )
                )
            for match in self._PATTERN_PARENTHESIS.finditer(math_segment):
                delimiter = match.group("delimiter")
                required_command = r"\left" if delimiter == "(" else r"\right"
                preceding_text = math_segment[: match.start()]
                if preceding_text.endswith(required_command):
                    continue
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_MAT004,
                        RULE_MAT004.render_message(
                            command=self.printer.yellow(required_command),
                            delimiter=self.printer.dark_red(delimiter),
                        ),
                    )
                )

    def get_comments(self) -> list[Diagnostic]:
        if not self._unclosed_delimiters_added:
            for delimiter, opening_line in self._delimiter_stack:
                details = f"unclosed {delimiter} from line {opening_line + 1}"
                self.comments.append(
                    Diagnostic(
                        opening_line,
                        RULE_MAT006,
                        RULE_MAT006.render_message(
                            details=self.printer.dark_red(details),
                        ),
                    )
                )
            self._unclosed_delimiters_added = True
        return self.comments

    def get_summary(self) -> str:
        if not self.comments:
            return ""
        plus_minus_count = sum(
            comment.code == RULE_MAT001.code for comment in self.comments
        )
        operator_count = sum(
            comment.code == RULE_MAT002.code for comment in self.comments
        )
        mu_count = sum(comment.code == RULE_MAT003.code for comment in self.comments)
        parenthesis_count = sum(
            comment.code == RULE_MAT004.code for comment in self.comments
        )
        ieee_environment_count = sum(
            comment.code == RULE_MAT005.code for comment in self.comments
        )
        delimiter_count = sum(
            comment.code == RULE_MAT006.code for comment in self.comments
        )
        summaries = []
        if plus_minus_count:
            summaries.append(f"Plus-minus notation: {plus_minus_count}")
        if operator_count:
            summaries.append(f"Unescaped math operators: {operator_count}")
        if mu_count:
            summaries.append(f"Mu commands: {mu_count}")
        if parenthesis_count:
            summaries.append(f"Unscaled parentheses: {parenthesis_count}")
        if ieee_environment_count:
            summaries.append(
                f"Non-IEEE alignment environments: {ieee_environment_count}"
            )
        if delimiter_count:
            summaries.append(f"Mismatched delimiters: {delimiter_count}")
        return " | ".join(summaries)

    def get_status(self) -> Status:
        return Status.PASSED if not self.comments else Status.FAILED

    def get_name(self) -> str:
        return "Math"
