import re
from dataclasses import dataclass
from typing import ClassVar

from printer import Printer

from .reviewer import Diagnostic, Reviewer, Status
from .rules import (
    RULE_REF001,
    RULE_REF002,
    RULE_REF003,
    RULE_REF004,
    RULE_REF005,
    RULE_REF006,
    RULE_REF007,
    RULE_REF008,
    RULE_REF009,
    RULE_REF010,
    RULE_REF011,
    RULE_REF012,
    RULE_REF013,
    RULE_REF014,
)


@dataclass
class _EnvironmentFrame:
    name: str
    base_depth: int
    counter_established: bool = False


class Reviewer_RefLabel(Reviewer):
    """Checks label names and references."""

    _PATTERN_LABEL = re.compile(r"\\label\{([^}]+)\}")
    _PATTERN_REF = re.compile(r"\\(?P<command>eqref|ref)\{(?P<label>[^}]+)\}")
    _PATTERN_REFERENCE_LIST_SEPARATOR = re.compile(
        r"[\s~]*(?:,[\s~]*(?:(?:and|or)[\s~]+)?|(?:and|or)[\s~]+)"
    )
    _PATTERN_REFERENCE_LIST_PREFIX = re.compile(
        r"[\s~]*(?:,[\s~]*(?:a(?:n(?:d)?)?|o(?:r)?)?[\s~]*"
        r"|(?:a(?:n(?:d)?)?|o(?:r)?)[\s~]*)?"
    )
    _PATTERN_REF_WITHOUT_HARD_SPACE = re.compile(r"(?<!~)\\ref\{[^}]+\}")
    _PATTERN_CITE = re.compile(r"\\cite\s*\{[^}]+\}")
    _PATTERN_CITE_PACKAGE = re.compile(
        r"\\(?:usepackage|RequirePackage)\s*"
        r"(?:\[(?P<options>[^\]]*)\])?\s*"
        r"\{(?P<packages>[^}]+)\}"
    )
    _PATTERN_LOWERCASE_REFERENCE_TYPE = re.compile(
        r"(?<![A-Za-z])(?P<reference>(?:tables|table|section|figure|figs?\.|listing)~\\ref\{[^}]+\})"
    )
    _PATTERN_PARENTHESIZED_EQREF = re.compile(r"\(\s*\\eqref\{[^}]+\}\s*\)")
    _PATTERN_CITE_AFTER_PUNCTUATION = re.compile(r"[.,;:!?][ \t~]*\\cite\{[^}]+\}")
    _PATTERN_FOOTNOTE_START = re.compile(r"\\footnote\s*(?:\[[^\]]*\]\s*)?\{")
    _PATTERN_FOOTNOTE_BRACE = re.compile(r"\\[{}\\]|[{}]")
    _PATTERN_TOKEN = re.compile(
        r"\\(?P<environment_command>begin|end)\s*\{(?P<environment>[^}]+)\}"
        r"|\\(?P<command>label|captionof|caption|item)\b"
        r"|(?P<brace>[{}])"
    )
    _PATTERN_BEGIN_CONTEXT = re.compile(
        r"\\begin\{(?P<context>figure|table|equation|align|alignat|gather|multline|flalign|displaymath|math)\*?\}"
    )
    _PATTERN_END_CONTEXT = re.compile(
        r"\\end\{(?P<context>figure|table|equation|align|alignat|gather|multline|flalign|displaymath|math)\*?\}"
    )
    _PATTERN_SECTION = re.compile(r"\\(?:sub)*section\*?(?=\s*(?:\[|\{))")
    _NON_EQUATION_LABEL_PREFIXES: ClassVar[tuple[str, ...]] = (
        "fig:",
        "tab:",
        "sec:",
    )
    _CONTEXT_PREFIXES: ClassVar[dict[str, tuple[str, str]]] = {
        "figure": ("fig:", "figure"),
        "equation": ("eq:", "equation"),
        "align": ("eq:", "equation"),
        "alignat": ("eq:", "equation"),
        "gather": ("eq:", "equation"),
        "multline": ("eq:", "equation"),
        "flalign": ("eq:", "equation"),
        "displaymath": ("eq:", "equation"),
        "math": ("eq:", "equation"),
        "section": ("sec:", "section"),
        "table": ("tab:", "table"),
    }

    def __init__(self, printer: Printer) -> None:
        self.printer = printer
        self.defined_labels = set()
        self.referenced_labels = set()
        self.label_line_map = {}  # Maps label name to first line number it was defined
        self.ref_line_map = {}  # Maps reference name to first line number it was referenced
        self.label_order: dict[str, tuple[str, int, int]] = {}
        self.reference_pairs: list[tuple[str, str, int]] = []
        self.previous_reference: str | None = None
        self.reference_gap = ""
        self.underscore_comments: list[Diagnostic] = []
        self.prefix_comments: list[Diagnostic] = []
        self.ref_space_comments: list[Diagnostic] = []
        self.cite_lines: list[int] = []
        self.cite_package_lines: list[int] = []
        self.cite_package_nobreak = False
        self.cite_period_comments: list[Diagnostic] = []
        self.footnote_period_comments: list[Diagnostic] = []
        self.footnote_depth = 0
        self.footnote_line: int | None = None
        self.footnote_awaiting_punctuation = False
        self.footnote_reported = False
        self.previous_line_ends_with_space = False
        self.eqref_preference_comments: list[Diagnostic] = []
        self.eqref_parentheses_comments: list[Diagnostic] = []
        self.eqref_misuse_comments: list[Diagnostic] = []
        self.reference_type_comments: list[Diagnostic] = []
        self.label_before_counter_comments: list[Diagnostic] = []
        self.context_stack: list[str] = []
        self.pending_section_context = False
        self.environment_stack: list[_EnvironmentFrame] = []
        self.brace_depth = 0

    def process_line(self, line_no: int, line: str) -> None:
        # Remove comments (everything after %)
        if "%" in line:
            line = line[: line.index("%")]

        for package_match in self._PATTERN_CITE_PACKAGE.finditer(line):
            packages = {
                package.strip()
                for package in package_match.group("packages").split(",")
            }
            options = {
                option.strip()
                for option in (package_match.group("options") or "").split(",")
            }
            if "cite" in packages:
                if "nobreak" in options:
                    self.cite_package_nobreak = True
                else:
                    self.cite_package_lines.append(line_no)

        for begin_match in self._PATTERN_BEGIN_CONTEXT.finditer(line):
            self.context_stack.append(begin_match.group("context"))

        section_context = self._PATTERN_SECTION.search(line) is not None
        pending_section_context = self.pending_section_context
        self.pending_section_context = section_context and (
            self._PATTERN_LABEL.search(line) is None
        )
        active_context = self.context_stack[-1] if self.context_stack else None

        # Extract all \label{...} patterns
        label_matches = self._PATTERN_LABEL.finditer(line)
        for label_match in label_matches:
            label_name = label_match.group(1)
            label_context = active_context
            if label_context is None and (section_context or pending_section_context):
                label_context = "section"
            if label_context is not None:
                expected_prefix, context_name = self._CONTEXT_PREFIXES[label_context]
                if not label_name.startswith(expected_prefix):
                    self.prefix_comments.append(
                        Diagnostic(
                            line_no,
                            RULE_REF004,
                            RULE_REF004.render_message(
                                expected_prefix=self.printer.dark_red(expected_prefix),
                                context=context_name,
                                label=self.printer.dark_red(label_name),
                            ),
                        )
                    )
            if "_" in label_name:
                self.underscore_comments.append(
                    Diagnostic(
                        line_no,
                        RULE_REF001,
                        RULE_REF001.render_message(
                            label=self.printer.dark_red(label_name)
                        ),
                    )
                )
            if label_name not in self.defined_labels:
                self.defined_labels.add(label_name)
                self.label_line_map[label_name] = line_no
                if label_context is not None:
                    self.label_order[label_name] = (
                        self._CONTEXT_PREFIXES[label_context][1],
                        line_no,
                        label_match.start(),
                    )

        self._check_label_counter_order(line_no, line)

        # Extract all \ref{...} patterns
        for _ in self._PATTERN_CITE_AFTER_PUNCTUATION.finditer(line):
            self.cite_period_comments.append(
                Diagnostic(
                    line_no,
                    RULE_REF006,
                    RULE_REF006.render_message(),
                )
            )

        self._check_footnote_punctuation(line_no, line)
        self.previous_line_ends_with_space = bool(line) and (
            line[-1].isspace() or line[-1] == "~"
        )

        for _ in self._PATTERN_CITE.finditer(line):
            self.cite_lines.append(line_no)

        for _ in self._PATTERN_PARENTHESIZED_EQREF.finditer(line):
            self.eqref_parentheses_comments.append(
                Diagnostic(
                    line_no,
                    RULE_REF009,
                    RULE_REF009.render_message(),
                )
            )

        for reference_match in self._PATTERN_LOWERCASE_REFERENCE_TYPE.finditer(line):
            self.reference_type_comments.append(
                Diagnostic(
                    line_no,
                    RULE_REF010,
                    RULE_REF010.render_message(
                        reference=self.printer.dark_red(
                            reference_match.group("reference")
                        ),
                    ),
                )
            )

        for ref_match in self._PATTERN_REF_WITHOUT_HARD_SPACE.finditer(line):
            if line[: ref_match.start()].rstrip().endswith("("):
                continue
            self.ref_space_comments.append(
                Diagnostic(
                    line_no,
                    RULE_REF005,
                    RULE_REF005.render_message(),
                )
            )

        reference_cursor = 0
        for ref_match in self._PATTERN_REF.finditer(line):
            ref_name = ref_match.group("label")
            gap = self.reference_gap + line[reference_cursor : ref_match.start()]
            if self.previous_reference is not None and (
                self._PATTERN_REFERENCE_LIST_SEPARATOR.fullmatch(gap)
            ):
                self.reference_pairs.append(
                    (self.previous_reference, ref_name, line_no)
                )
            self.previous_reference = ref_name
            self.reference_gap = ""
            reference_cursor = ref_match.end()
            command = ref_match.group("command")
            if command == "eqref" and ref_name.startswith(
                self._NON_EQUATION_LABEL_PREFIXES
            ):
                self.eqref_misuse_comments.append(
                    Diagnostic(
                        line_no,
                        RULE_REF012,
                        RULE_REF012.render_message(
                            label=self.printer.dark_red(ref_name),
                        ),
                    )
                )
            if command == "ref" and ref_name.startswith("eq:"):
                self.eqref_preference_comments.append(
                    Diagnostic(
                        line_no,
                        RULE_REF008,
                        RULE_REF008.render_message(),
                    )
                )
            if ref_name not in self.referenced_labels:
                self.referenced_labels.add(ref_name)
                self.ref_line_map[ref_name] = line_no

        if self.previous_reference is not None:
            self.reference_gap += line[reference_cursor:] + "\n"
            if not self._PATTERN_REFERENCE_LIST_PREFIX.fullmatch(self.reference_gap):
                self.previous_reference = None
                self.reference_gap = ""

        for end_match in self._PATTERN_END_CONTEXT.finditer(line):
            context = end_match.group("context")
            for index in range(len(self.context_stack) - 1, -1, -1):
                if self.context_stack[index] == context:
                    del self.context_stack[index:]
                    break

    def _check_footnote_punctuation(self, line_no: int, line: str) -> None:
        position = 0
        while position < len(line):
            if self.footnote_awaiting_punctuation:
                next_character = re.search(r"[^\s~]", line[position:])
                if next_character is None:
                    return
                position += next_character.start()
                if line[position] in ".,;:!?" and not self.footnote_reported:
                    assert self.footnote_line is not None
                    self.footnote_period_comments.append(
                        Diagnostic(
                            self.footnote_line,
                            RULE_REF013,
                            RULE_REF013.render_message(),
                        )
                    )
                self.footnote_awaiting_punctuation = False
                self.footnote_line = None

            if self.footnote_depth == 0:
                start = self._PATTERN_FOOTNOTE_START.search(line, position)
                if start is None:
                    return
                self.footnote_line = line_no
                self.footnote_depth = 1
                self.footnote_reported = (
                    start.start() > 0
                    and (
                        line[start.start() - 1].isspace()
                        or line[start.start() - 1] == "~"
                    )
                    or start.start() == 0
                    and self.previous_line_ends_with_space
                )
                if self.footnote_reported:
                    self.footnote_period_comments.append(
                        Diagnostic(line_no, RULE_REF013, RULE_REF013.render_message())
                    )
                position = start.end()

            brace = self._PATTERN_FOOTNOTE_BRACE.search(line, position)
            if brace is None:
                return
            if brace.group() == "{":
                self.footnote_depth += 1
            elif brace.group() == "}":
                self.footnote_depth -= 1
                if self.footnote_depth == 0:
                    self.footnote_awaiting_punctuation = True
            position = brace.end()

    def _check_label_counter_order(self, line_no: int, line: str) -> None:
        for token_match in self._PATTERN_TOKEN.finditer(line):
            environment_command = token_match.group("environment_command")
            if environment_command is not None:
                environment = token_match.group("environment").strip().rstrip("*")
                if environment_command == "begin":
                    self.environment_stack.append(
                        _EnvironmentFrame(environment, self.brace_depth)
                    )
                else:
                    for index in range(len(self.environment_stack) - 1, -1, -1):
                        if self.environment_stack[index].name == environment:
                            del self.environment_stack[index:]
                            break
                continue

            brace = token_match.group("brace")
            if brace is not None:
                if brace == "{":
                    self.brace_depth += 1
                elif self.brace_depth:
                    self.brace_depth -= 1
                continue

            command = token_match.group("command")
            frame = self.environment_stack[-1] if self.environment_stack else None
            if frame is None or self.brace_depth != frame.base_depth:
                continue

            if command == "label" and not frame.counter_established:
                target = self._label_counter_target(frame.name)
                if target is not None:
                    self.label_before_counter_comments.append(
                        Diagnostic(
                            line_no,
                            RULE_REF007,
                            RULE_REF007.render_message(target=target),
                        )
                    )
            elif (
                command == "caption"
                and frame.name in {"figure", "table"}
                or command == "captionof"
                and frame.name == "minipage"
                or command == "item"
                and frame.name == "enumerate"
            ):
                frame.counter_established = True

    @staticmethod
    def _label_counter_target(environment: str) -> str | None:
        if environment == "figure":
            return "figure caption"
        if environment == "table":
            return "table caption"
        if environment == "minipage":
            return r"\captionof"
        if environment == "enumerate":
            return "first enumerate item"
        return None

    def _get_reference_order_comments(self) -> list[Diagnostic]:
        comments = []
        for previous_label, label, line_no in self.reference_pairs:
            previous_order = self.label_order.get(previous_label)
            order = self.label_order.get(label)
            if (
                previous_order is not None
                and order is not None
                and previous_order[0] == order[0]
                and order[1:] < previous_order[1:]
            ):
                comments.append(
                    Diagnostic(
                        line_no,
                        RULE_REF014,
                        RULE_REF014.render_message(
                            label=self.printer.dark_red(label),
                            previous_label=self.printer.dark_red(previous_label),
                        ),
                    )
                )
        return comments

    def _get_cite_comments(self) -> list[Diagnostic]:
        if self.cite_package_nobreak or not self.cite_lines:
            return []
        line_no = (
            self.cite_package_lines[0]
            if self.cite_package_lines
            else self.cite_lines[0]
        )
        return [
            Diagnostic(
                line_no,
                RULE_REF011,
                RULE_REF011.render_message(),
            )
        ]

    def get_summary(self) -> str:
        missing_labels = self.referenced_labels - self.defined_labels
        orphaned_labels = self.defined_labels - self.referenced_labels

        messages = []

        if missing_labels:
            messages.append(f"Missing labels: {len(missing_labels)}")

        if orphaned_labels:
            messages.append(f"Orphaned labels: {len(orphaned_labels)}")

        if self.underscore_comments:
            messages.append(f"Labels with underscores: {len(self.underscore_comments)}")

        if self.prefix_comments:
            messages.append(
                f"Labels with invalid prefixes: {len(self.prefix_comments)}"
            )

        if self.ref_space_comments:
            messages.append(
                f"References without hard spaces: {len(self.ref_space_comments)}"
            )

        if self.eqref_preference_comments:
            messages.append(
                "Equation references not using \\eqref: "
                f"{len(self.eqref_preference_comments)}"
            )

        if self.eqref_parentheses_comments:
            messages.append(
                f"Parentheses around \\eqref: {len(self.eqref_parentheses_comments)}"
            )

        if self.eqref_misuse_comments:
            messages.append(
                f"\\eqref used for non-equation labels: {len(self.eqref_misuse_comments)}"
            )

        if self.reference_type_comments:
            messages.append(
                f"Lowercase reference types: {len(self.reference_type_comments)}"
            )

        if self.cite_period_comments:
            messages.append(
                f"Citations after periods: {len(self.cite_period_comments)}"
            )

        if self.footnote_period_comments:
            messages.append(
                f"Footnote placement issues: {len(self.footnote_period_comments)}"
            )

        if self.label_before_counter_comments:
            messages.append(
                f"Labels before counters: {len(self.label_before_counter_comments)}"
            )

        return " | ".join(messages) if messages else ""

    def get_comments(self) -> list[Diagnostic]:
        missing_labels = self.referenced_labels - self.defined_labels
        orphaned_labels = self.defined_labels - self.referenced_labels
        cite_comments = self._get_cite_comments()

        comments: list[Diagnostic] = []
        comments.extend(self.underscore_comments)
        comments.extend(self.prefix_comments)
        comments.extend(self.ref_space_comments)
        comments.extend(cite_comments)
        comments.extend(self.eqref_preference_comments)
        comments.extend(self.eqref_parentheses_comments)
        comments.extend(self.eqref_misuse_comments)
        comments.extend(self.reference_type_comments)
        comments.extend(self.cite_period_comments)
        comments.extend(self.footnote_period_comments)
        comments.extend(self.label_before_counter_comments)
        comments.extend(self._get_reference_order_comments())

        for label in missing_labels:
            comments.append(
                Diagnostic(
                    self.ref_line_map[label],
                    RULE_REF002,
                    RULE_REF002.render_message(label=self.printer.dark_red(label)),
                )
            )

        for label in orphaned_labels:
            comments.append(
                Diagnostic(
                    self.label_line_map[label],
                    RULE_REF003,
                    RULE_REF003.render_message(label=self.printer.dark_red(label)),
                )
            )

        return comments

    def get_status(self) -> Status:
        missing_labels = self.referenced_labels - self.defined_labels
        orphaned_labels = self.defined_labels - self.referenced_labels
        cite_comments = self._get_cite_comments()

        if (
            missing_labels
            or orphaned_labels
            or self.underscore_comments
            or self.prefix_comments
            or self.ref_space_comments
            or cite_comments
            or self.eqref_misuse_comments
            or self.reference_type_comments
            or self.cite_period_comments
            or self.footnote_period_comments
            or self.label_before_counter_comments
        ):
            return Status.FAILED
        if self._get_reference_order_comments():
            return Status.WARNING
        return Status.PASSED

    def get_name(self) -> str:
        return "RefLabel"
