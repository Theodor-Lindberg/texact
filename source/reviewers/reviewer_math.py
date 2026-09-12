import re

from printer import Printer

from .reviewer import Diagnostic, Reviewer, Status
from .rules import RULE_MAT001, RULE_MAT002, RULE_MAT003


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
    _PATTERN_MATH_TOKEN = re.compile(
        r"\\begin\{(?:equation|align|alignat|gather|multline|flalign|displaymath|math)\*?\}"
        r"|\\end\{(?:equation|align|alignat|gather|multline|flalign|displaymath|math)\*?\}"
        r"|\\\(|\\\)|\\\[|\\\]|(?<!\\)\$\$?"
    )

    def __init__(self, printer: Printer) -> None:
        self.printer = printer
        self.comments: list[Diagnostic] = []
        self._in_math_mode = False

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
            for match in self._PATTERN_MATH_OPERATOR.finditer(math_segment):
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

    def get_comments(self) -> list[Diagnostic]:
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
        summaries = []
        if plus_minus_count:
            summaries.append(f"Plus-minus notation: {plus_minus_count}")
        if operator_count:
            summaries.append(f"Unescaped math operators: {operator_count}")
        if mu_count:
            summaries.append(f"Mu commands: {mu_count}")
        return " | ".join(summaries)

    def get_status(self) -> Status:
        return Status.PASSED if not self.comments else Status.FAILED

    def get_name(self) -> str:
        return "Math"
