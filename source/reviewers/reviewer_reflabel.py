import re

from .reviewer import Reviewer, Status
from printer import Printer


class Reviewer_RefLabel(Reviewer):
    _PATTERN_LABEL = re.compile(r"\\label\{([^}]+)\}")
    _PATTERN_REF = re.compile(r"\\ref\{([^}]+)\}")

    def __init__(self, printer: Printer) -> None:
        self.printer = printer
        self.defined_labels = set()
        self.referenced_labels = set()
        self.label_line_map = {}  # Maps label name to first line number it was defined
        self.ref_line_map = {}  # Maps reference name to first line number it was referenced
        self.underscore_comments = []

    def process_line(self, line_no: int, line: str) -> None:
        # Remove comments (everything after %)
        if "%" in line:
            line = line[: line.index("%")]

        # Extract all \label{...} patterns
        label_matches = self._PATTERN_LABEL.findall(line)
        for label_name in label_matches:
            if "_" in label_name:
                self.underscore_comments.append(
                    (
                        line_no,
                        f"Label '{self.printer.dark_red(label_name)}' should use hyphens (-) instead of underscores (_).",
                    )
                )
            if label_name not in self.defined_labels:
                self.defined_labels.add(label_name)
                self.label_line_map[label_name] = line_no

        # Extract all \ref{...} patterns
        ref_matches = self._PATTERN_REF.findall(line)
        for ref_name in ref_matches:
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

    def get_comments(self) -> list[tuple[int, str]]:
        missing_labels = self.referenced_labels - self.defined_labels
        orphaned_labels = self.defined_labels - self.referenced_labels

        comments: list[tuple[int, str]] = []
        comments.extend(self.underscore_comments)

        for label in missing_labels:
            line_no = self.ref_line_map[label]
            comments.append(
                (
                    line_no,
                    f"Reference to undefined label: {self.printer.dark_red(label)}",
                )
            )

        for label in orphaned_labels:
            line_no = self.label_line_map[label]
            comments.append(
                (line_no, f"Label never referenced: {self.printer.dark_red(label)}")
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
