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
    RULE_MAT007,
    RULE_MAT009,
    RULE_MAT010,
)


class Reviewer_Math(Reviewer):
    """Checks mathematical notation."""

    _PATTERN_PLUS_MINUS = re.compile(r"\+\-|\-\+")
    _MATH_SYMBOL_COMMANDS: ClassVar[dict[str, str]] = {
        "<=>": r"\Leftrightarrow",
        ">=": r"\geq",
        "<=": r"\leq",
        "<<": r"\ll",
        ">>": r"\gg",
        "->": r"\rightarrow",
        "<-": r"\leftarrow",
        "::=": r"\Coloneqq",
        ":=": r"\coloneqq",
    }
    _PATTERN_MATH_SYMBOL = re.compile(
        "|".join(re.escape(symbol) for symbol in _MATH_SYMBOL_COMMANDS)
    )
    _PATTERN_UNBRACED_SCRIPT = re.compile(
        r"(?<!\\)(?P<operator>[\^_])(?P<argument>[A-Za-z0-9]{2,})"
    )
    _PATTERN_UNBRACED_SQRT = re.compile(
        r"(?<!\\)\\sqrt(?![A-Za-z@])"
        r"(?:(?P<index>\s*\[[^\]]*\])|(?!\s*\[))"
        r"(?!\s*\{)\s*"
        r"(?P<argument>\\[A-Za-z@]+|\S)"
    )
    _PATTERN_ELLIPSIS = re.compile(r"\.\.\.")
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
            self._add_symbol_command_comment(line_no, match.group(0), r"\pm")

        text_segments: list[str] = []
        math_segments: list[str] = []
        cursor = 0
        for token_match in self._PATTERN_MATH_TOKEN.finditer(line):
            if self._in_math_mode:
                math_segments.append(line[cursor : token_match.start()])
            else:
                text_segments.append(line[cursor : token_match.start()])

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
        else:
            text_segments.append(line[cursor:])

        for text_segment in text_segments:
            for match in self._PATTERN_ELLIPSIS.finditer(text_segment):
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_MAT007,
                        RULE_MAT007.render_message(
                            command=self.printer.yellow(r"\dots"),
                            context=" in normal text",
                        ),
                    )
                )

        for math_segment in math_segments:
            for match in self._PATTERN_UNBRACED_SQRT.finditer(math_segment):
                index = (match.group("index") or "").strip()
                braced_sqrt = f"\\sqrt{index}{{...}}"
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_MAT010,
                        RULE_MAT010.render_message(
                            braced_sqrt=self.printer.yellow(braced_sqrt),
                            expression=self.printer.dark_red(match.group(0)),
                        ),
                    )
                )

            for match in self._PATTERN_UNBRACED_SCRIPT.finditer(math_segment):
                script = match.group(0)
                operator = match.group("operator")
                argument = match.group("argument")
                braced_script = f"{operator}{{{argument}}}"
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_MAT009,
                        RULE_MAT009.render_message(
                            script=self.printer.dark_red(script),
                            braced_script=self.printer.yellow(braced_script),
                        ),
                    )
                )

            for match in self._PATTERN_MATH_SYMBOL.finditer(math_segment):
                operator = match.group(0)
                self._add_symbol_command_comment(
                    line_no,
                    operator,
                    self._MATH_SYMBOL_COMMANDS[operator],
                )

            for _match in self._PATTERN_ELLIPSIS.finditer(math_segment):
                baseline_ellipsis = self.printer.yellow(r"\ldots")
                centered_ellipsis = self.printer.yellow(r"\cdots")
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_MAT007,
                        RULE_MAT007.render_message(
                            command=(
                                f"{baseline_ellipsis} (baseline, for comma lists) "
                                f"or {centered_ellipsis} (centered, for operator chains)"
                            ),
                            context=" in math mode",
                        ),
                    )
                )
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

    def _add_symbol_command_comment(
        self,
        line_no: int,
        operator: str,
        command: str,
    ) -> None:
        self.comments.append(
            Diagnostic(
                line_no,
                RULE_MAT001,
                RULE_MAT001.render_message(
                    command=self.printer.yellow(command),
                    operator=self.printer.dark_red(operator),
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
        symbol_command_count = sum(
            comment.code == RULE_MAT001.code for comment in self.comments
        )
        unbraced_sqrt_count = sum(
            comment.code == RULE_MAT010.code for comment in self.comments
        )
        unbraced_script_count = sum(
            comment.code == RULE_MAT009.code for comment in self.comments
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
        ellipsis_count = sum(
            comment.code == RULE_MAT007.code for comment in self.comments
        )
        summaries = []
        if symbol_command_count:
            summaries.append(f"Math symbol command issues: {symbol_command_count}")
        if unbraced_sqrt_count:
            summaries.append(f"Unbraced square roots: {unbraced_sqrt_count}")
        if unbraced_script_count:
            summaries.append(
                f"Unbraced multi-character scripts: {unbraced_script_count}"
            )
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
        if ellipsis_count:
            summaries.append(f"Ellipsis notation: {ellipsis_count}")
        return " | ".join(summaries)

    def get_status(self) -> Status:
        return Status.PASSED if not self.comments else Status.FAILED

    def get_name(self) -> str:
        return "Math"
