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
)


@dataclass
class _EnvironmentFrame:
    name: str
    base_depth: int
    counter_established: bool = False


class Reviewer_RefLabel(Reviewer):
    """Checks label names and references."""

    _PATTERN_LABEL = re.compile(r"\\label\{([^}]+)\}")
    _PATTERN_REF = re.compile(r"\\ref\{([^}]+)\}")
    _PATTERN_REF_WITHOUT_HARD_SPACE = re.compile(r"(?<!~)\\ref\{[^}]+\}")
    _PATTERN_CITE_AFTER_PERIOD = re.compile(r"\.\s*\\cite\{[^}]+\}")
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
        self.underscore_comments: list[Diagnostic] = []
        self.prefix_comments: list[Diagnostic] = []
        self.ref_space_comments: list[Diagnostic] = []
        self.cite_period_comments: list[Diagnostic] = []
        self.label_before_counter_comments: list[Diagnostic] = []
        self.context_stack: list[str] = []
        self.pending_section_context = False
        self.environment_stack: list[_EnvironmentFrame] = []
        self.brace_depth = 0

    def process_line(self, line_no: int, line: str) -> None:
        # Remove comments (everything after %)
        if "%" in line:
            line = line[: line.index("%")]

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

        self._check_label_counter_order(line_no, line)

        # Extract all \ref{...} patterns
        for _ in self._PATTERN_CITE_AFTER_PERIOD.finditer(line):
            self.cite_period_comments.append(
                Diagnostic(
                    line_no,
                    RULE_REF006,
                    RULE_REF006.render_message(),
                )
            )

        for ref_match in self._PATTERN_REF_WITHOUT_HARD_SPACE.finditer(line):
            self.ref_space_comments.append(
                Diagnostic(
                    line_no,
                    RULE_REF005,
                    RULE_REF005.render_message(),
                )
            )

        ref_matches = self._PATTERN_REF.finditer(line)
        for ref_match in ref_matches:
            ref_name = ref_match.group(1)
            if ref_name not in self.referenced_labels:
                self.referenced_labels.add(ref_name)
                self.ref_line_map[ref_name] = line_no

        for end_match in self._PATTERN_END_CONTEXT.finditer(line):
            context = end_match.group("context")
            for index in range(len(self.context_stack) - 1, -1, -1):
                if self.context_stack[index] == context:
                    del self.context_stack[index:]
                    break

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

        if self.cite_period_comments:
            messages.append(
                f"Citations after periods: {len(self.cite_period_comments)}"
            )

        if self.label_before_counter_comments:
            messages.append(
                f"Labels before counters: {len(self.label_before_counter_comments)}"
            )

        return " | ".join(messages) if messages else ""

    def get_comments(self) -> list[Diagnostic]:
        missing_labels = self.referenced_labels - self.defined_labels
        orphaned_labels = self.defined_labels - self.referenced_labels

        comments: list[Diagnostic] = []
        comments.extend(self.underscore_comments)
        comments.extend(self.prefix_comments)
        comments.extend(self.ref_space_comments)
        comments.extend(self.cite_period_comments)
        comments.extend(self.label_before_counter_comments)

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

        if (
            missing_labels
            or orphaned_labels
            or self.underscore_comments
            or self.prefix_comments
            or self.ref_space_comments
            or self.cite_period_comments
            or self.label_before_counter_comments
        ):
            return Status.FAILED
        return Status.PASSED

    def get_name(self) -> str:
        return "RefLabel"
