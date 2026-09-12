import re

from printer import Printer

from .reviewer import Diagnostic, Reviewer, Status
from .rules import RULE_CAS001, RULE_CAS002


class Reviewer_Casing(Reviewer):
    """Checks the casing of known terms."""

    # Canonical spellings to enforce
    CORRECT_SPELLINGS = (
        "ASIC",
        "CMOS",
        "CORDIC",
        "FPGA",
        "VLSI",
        "FloPoCo",
        "RTL",
        "HDL",
        "FSM",
        "DNN",
        "CNN",
        "ReLU",
        "PWL",
        "RAM",
        "RMS",
        "Verilog",
        "SystemVerilog",
        "VHDL",
        "FIR",
        "IIR",
        "LWDF",
        # "AXI", # collides with the word axis
        "SRAM",
        "DSP",
        "FIFO",
        "ALU",
        "PDK",
        "PLL",
        "HLS",
        "AI",
        "ML",
        "AMD",
        "Intel",
        "Xilinx",
        "Altera",
        "Lattice",
        "LSTM",
        "TSMC",
        "FD-SOI",
        "Synopsys",
        "Cadence",
        "Vivado",
        "Quartus",
        "APyTypes",
        "NumPy",
        "Matplotlib",
        "URL",
        "DNS",
        "BRAM",
        "DRAM",
        "NaN",
        "LUT",
        "LNS",
        "MNIST",
        "MHz",
        "kHz",
        "GHz",
        "GiB",
        "MiB",
        "Basys",
        "Virtex",
        "Spartan",
        "MIPS",
        "TOML",
        "CSV",
        "RISC",
        "CISC",
        "EDA",
        "Python",
        "GitHub",
        "GitLab",
        "VSCode",
        "IEE",
        "IEEE",
        "FOSSi",
        "ELLIIT",
        "VCD",
        "FST",
        "GHW",
        "WASM",
        "HTML",
        "VLIW",
        "FP4",
        "FP8",
        "FP16",
        "FP32",
        "FP64",
        "MILP",
        "ILP",
        "SNR",
        "SQNR",
        "MIMO",
        "CPU",
    )
    _PATTERN_LATEX_IGNORED_COMMANDS = re.compile(
        r"\\(?:cite|ref|label|url|usepackage)\{[^}]*\}"
    )
    _PATTERN_TITLE_COMMAND = re.compile(
        r"\\(?:title|part|chapter|section|subsection|subsubsection|"
        r"paragraph|subparagraph)\*?(?![A-Za-z@])"
    )
    _PATTERN_TITLE_WORD = re.compile(
        r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?"
        r"(?:-[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?)*"
    )
    _PATTERN_TITLE_MATH = re.compile(
        r"\$(?:\\.|[^$])*?\$|\\\(.*?\\\)|\\\[.*?\\\]",
        re.DOTALL,
    )
    _TITLE_MINOR_WORDS = frozenset(
        {
            "a",
            "an",
            "and",
            "as",
            "at",
            "but",
            "by",
            "for",
            "if",
            "in",
            "nor",
            "of",
            "on",
            "or",
            "the",
            "to",
            "via",
            "with",
        }
    )
    _TITLE_IGNORED_COMMANDS = frozenset(
        {
            "acrshort",
            "cite",
            "citealp",
            "citealt",
            "citeauthor",
            "citet",
            "eqref",
            "gls",
            "href",
            "includegraphics",
            "index",
            "label",
            "pageref",
            "parencite",
            "ref",
            "textcite",
            "url",
            "usepackage",
        }
    )

    def __init__(
        self,
        printer: Printer,
        additional_spellings: tuple[str, ...] = (),
    ) -> None:
        self.printer = printer
        self.correct_spellings = tuple(
            dict.fromkeys((*self.CORRECT_SPELLINGS, *additional_spellings))
        )
        self.canonical_spellings = {
            spelling.casefold(): spelling for spelling in self.correct_spellings
        }
        self.comments: list[Diagnostic] = []
        self.mismatch_count = 0
        self.title_mismatch_count = 0

    def process_line(self, line_no: int, line: str) -> None:
        # Ignore casing checks inside \cite{...}, \ref{...}, \label{...}, and \url{...}
        line = self._PATTERN_LATEX_IGNORED_COMMANDS.sub(
            lambda match: " " * len(match.group(0)),
            line,
        )

        # Check each word in the line
        for correct_spelling in self.correct_spellings:
            word_lower = correct_spelling.lower()
            # Create regex pattern to match the word with optional suffixes:
            # - plural 's': fpgas
            # - possessive 's: fpga's
            # - colon suffix: fpga:s
            # - hyphenated compounds: fpga-design
            pattern = re.compile(
                r"(?<![a-zA-Z])(?P<base>"
                + re.escape(word_lower)
                + r")(?P<suffix>s|'s|:s)?(?=\W|$)",
                re.IGNORECASE,
            )

            for match in pattern.finditer(line):
                matched_text = match.group(0)
                matched_base = match.group("base")
                matched_suffix = match.group("suffix") or ""
                normalized_suffix = matched_suffix.lower()
                expected_text = f"{correct_spelling}{normalized_suffix}"
                if matched_base != correct_spelling:
                    self.comments.append(
                        Diagnostic(
                            line_no,
                            RULE_CAS001,
                            RULE_CAS001.render_message(
                                actual=self.printer.dark_red(matched_text),
                                expected=self.printer.yellow(expected_text),
                            ),
                        )
                    )
                    self.mismatch_count += 1

        self._process_title_casing(line_no, line)

    def _process_title_casing(self, line_no: int, line: str) -> None:
        position = 0
        while match := self._PATTERN_TITLE_COMMAND.search(line, position):
            argument_start = self._find_title_argument_start(line, match.end())
            if argument_start is None:
                position = match.end()
                continue

            argument = self._extract_title_group(line, argument_start)
            if argument is None:
                position = match.end()
                continue

            title, position = argument
            self._check_title_casing(line_no, title)

    def _check_title_casing(self, line_no: int, title: str) -> None:
        visible_title = self._visible_title_text(title)
        words = list(self._PATTERN_TITLE_WORD.finditer(visible_title))
        if not words:
            return

        expected_title = self._format_title(visible_title, words)
        actual_display = " ".join(visible_title.split())
        expected_display = " ".join(expected_title.split())
        if actual_display == expected_display:
            return

        self.comments.append(
            Diagnostic(
                line_no,
                RULE_CAS002,
                RULE_CAS002.render_message(
                    actual=self.printer.dark_red(actual_display),
                    expected=self.printer.yellow(expected_display),
                ),
            )
        )
        self.title_mismatch_count += 1

    def _format_title(self, title: str, words: list[re.Match[str]]) -> str:
        formatted: list[str] = []
        previous_end = 0
        for index, match in enumerate(words):
            formatted.append(title[previous_end : match.start()])
            separator = title[previous_end : match.start()]
            is_edge = index == 0 or index == len(words) - 1
            after_colon = bool(re.search(r"[:!?]\s*$", separator))
            formatted.append(
                self._format_title_word(
                    match.group(0),
                    is_edge=is_edge or after_colon,
                )
            )
            previous_end = match.end()
        formatted.append(title[previous_end:])
        return "".join(formatted)

    def _format_title_word(self, word: str, *, is_edge: bool) -> str:
        base, suffix = self._split_title_possessive(word)
        canonical = self._canonical_spelling(base)
        if canonical is not None:
            return canonical + suffix

        parts = base.split("-")
        formatted_parts = []
        for index, part in enumerate(parts):
            part_is_edge = (is_edge and index == 0) or (
                is_edge and index == len(parts) - 1
            )
            formatted_parts.append(self._format_title_component(part, part_is_edge))
        return "-".join(formatted_parts) + suffix

    def _format_title_component(self, component: str, is_edge: bool) -> str:
        canonical = self._canonical_spelling(component)
        if canonical is not None:
            return canonical
        if not is_edge and component.casefold() in self._TITLE_MINOR_WORDS:
            return component.casefold()
        if component.isupper() and any(character.isalpha() for character in component):
            return component
        if any(character.islower() for character in component) and any(
            character.isupper() for character in component
        ):
            return component
        return self._capitalize_title_word(component)

    def _canonical_spelling(self, word: str) -> str | None:
        return self.canonical_spellings.get(word.casefold())

    @staticmethod
    def _split_title_possessive(word: str) -> tuple[str, str]:
        if word.casefold().endswith("'s"):
            return word[:-2], "'s"
        return word, ""

    @staticmethod
    def _capitalize_title_word(word: str) -> str:
        lowercase_word = word.lower()
        for index, character in enumerate(lowercase_word):
            if character.isalpha():
                return (
                    lowercase_word[:index]
                    + character.upper()
                    + lowercase_word[index + 1 :]
                )
        return lowercase_word

    @classmethod
    def _visible_title_text(cls, text: str) -> str:
        text = cls._PATTERN_TITLE_MATH.sub(
            lambda match: " " * len(match.group(0)),
            text,
        )

        visible: list[str] = []
        position = 0
        while position < len(text):
            character = text[position]
            if character != "\\":
                visible.append(" " if character in "{}" else character)
                position += 1
                continue

            if position + 1 >= len(text):
                visible.append(" ")
                position += 1
                continue

            next_character = text[position + 1]
            if next_character.isalpha() or next_character == "@":
                command_start = position + 1
                position = command_start
                while position < len(text) and (
                    text[position].isalpha() or text[position] == "@"
                ):
                    position += 1
                command = text[command_start:position].casefold()
                if position < len(text) and text[position] == "*":
                    position += 1

                if command in cls._TITLE_IGNORED_COMMANDS:
                    position = cls._skip_title_command_argument(text, position)
                visible.append(" ")
                continue

            visible.append(next_character)
            position += 2

        return re.sub(r"\s+", " ", "".join(visible)).strip()

    @classmethod
    def _skip_title_command_argument(cls, text: str, position: int) -> int:
        while position < len(text) and text[position].isspace():
            position += 1

        if position < len(text) and text[position] == "[":
            optional_argument = cls._extract_title_group(
                text,
                position,
                opening="[",
                closing="]",
            )
            if optional_argument is None:
                return len(text)
            _, position = optional_argument

        while position < len(text) and text[position].isspace():
            position += 1

        if position < len(text) and text[position] == "{":
            argument = cls._extract_title_group(text, position)
            if argument is None:
                return len(text)
            _, position = argument
        return position

    @classmethod
    def _find_title_argument_start(cls, text: str, position: int) -> int | None:
        while position < len(text) and text[position].isspace():
            position += 1

        if position < len(text) and text[position] == "[":
            optional_argument = cls._extract_title_group(
                text,
                position,
                opening="[",
                closing="]",
            )
            if optional_argument is None:
                return None
            _, position = optional_argument
            while position < len(text) and text[position].isspace():
                position += 1

        if position >= len(text) or text[position] != "{":
            return None
        return position

    @staticmethod
    def _extract_title_group(
        text: str,
        opening_index: int,
        *,
        opening: str = "{",
        closing: str = "}",
    ) -> tuple[str, int] | None:
        if opening_index >= len(text) or text[opening_index] != opening:
            return None

        depth = 1
        position = opening_index + 1
        while position < len(text):
            character = text[position]
            if character == "\\":
                position += 2
                continue
            if character == opening:
                depth += 1
            elif character == closing:
                depth -= 1
                if depth == 0:
                    return text[opening_index + 1 : position], position + 1
            position += 1
        return None

    def get_comments(self) -> list[Diagnostic]:
        return self.comments

    def get_summary(self) -> str:
        issues: list[str] = []
        if self.mismatch_count:
            issues.append(f"Casing errors: {self.mismatch_count}")
        if self.title_mismatch_count:
            issues.append(f"Title casing errors: {self.title_mismatch_count}")
        return ". ".join(issues)

    def get_status(self) -> Status:
        return (
            Status.PASSED
            if self.mismatch_count == 0 and self.title_mismatch_count == 0
            else Status.FAILED
        )

    def get_name(self) -> str:
        return "Casing"
