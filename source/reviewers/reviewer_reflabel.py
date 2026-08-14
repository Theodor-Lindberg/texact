import re

from .reviewer import Diagnostic, Reviewer, Status
from .rules import RULE_REF001, RULE_REF002, RULE_REF003
from printer import Printer


class Reviewer_RefLabel(Reviewer):
    """Checks label names and references."""

    _PATTERN_LABEL = re.compile(r"\\label\{([^}]+)\}")
    _PATTERN_REF = re.compile(r"\\ref\{([^}]+)\}")

    def __init__(self, printer: Printer) -> None:
        self.printer = printer
        self.defined_labels = set()
        self.referenced_labels = set()
        self.label_line_map = {}  # Maps label name to first line number it was defined
        self.ref_line_map = {}  # Maps reference name to first line number it was referenced
        self.underscore_comments: list[Diagnostic] = []

    def process_line(self, line_no: int, line: str) -> None:
        # Remove comments (everything after %)
        if "%" in line:
            line = line[: line.index("%")]

        # Extract all \label{...} patterns
        label_matches = self._PATTERN_LABEL.finditer(line)
        for label_match in label_matches:
            label_name = label_match.group(1)
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
        ref_matches = self._PATTERN_REF.finditer(line)
        for ref_match in ref_matches:
            ref_name = ref_match.group(1)
            if ref_name not in self.referenced_labels:
                self.referenced_labels.add(ref_name)
                self.ref_line_map[ref_name] = line_no

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

        return " | ".join(messages) if messages else ""

    def get_comments(self) -> list[Diagnostic]:
        missing_labels = self.referenced_labels - self.defined_labels
        orphaned_labels = self.defined_labels - self.referenced_labels

        comments: list[Diagnostic] = []
        comments.extend(self.underscore_comments)

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

        if missing_labels or orphaned_labels or self.underscore_comments:
            return Status.FAILED
        return Status.PASSED

    def get_name(self) -> str:
        return "RefLabel"
