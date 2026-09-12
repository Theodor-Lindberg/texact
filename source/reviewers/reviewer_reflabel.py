import re
from typing import ClassVar

from printer import Printer

from .reviewer import Diagnostic, Reviewer, Status
from .rules import (
    RULE_REF001,
    RULE_REF002,
    RULE_REF003,
    RULE_REF004,
    RULE_REF005,
)


class Reviewer_RefLabel(Reviewer):
    """Checks label names and references."""

    _PATTERN_LABEL = re.compile(r"\\label\{([^}]+)\}")
    _PATTERN_REF = re.compile(r"\\ref\{([^}]+)\}")
    _PATTERN_REF_WITHOUT_HARD_SPACE = re.compile(r"(?<!~)\\ref\{[^}]+\}")
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
        self.context_stack: list[str] = []
        self.pending_section_context = False

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

        # Extract all \ref{...} patterns
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

        return " | ".join(messages) if messages else ""

    def get_comments(self) -> list[Diagnostic]:
        missing_labels = self.referenced_labels - self.defined_labels
        orphaned_labels = self.defined_labels - self.referenced_labels

        comments: list[Diagnostic] = []
        comments.extend(self.underscore_comments)
        comments.extend(self.prefix_comments)
        comments.extend(self.ref_space_comments)

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
        ):
            return Status.FAILED
        return Status.PASSED

    def get_name(self) -> str:
        return "RefLabel"
