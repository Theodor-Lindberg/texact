import re
from pathlib import Path
from typing import ClassVar

from PIL import Image
from printer import Printer

from .reviewer import Diagnostic, Reviewer, Status
from .rules import (
    RULE_FIG001,
    RULE_FIG002,
    RULE_FIG003,
    RULE_FIG004,
    RULE_FIG005,
    RULE_FIG006,
    RULE_FIG007,
    RULE_FIG008,
)


class Reviewer_Figure(Reviewer):
    """Checks figure structure and biography images."""

    _PATTERN_BEGIN_FIGURE = re.compile(
        r"\\begin\{figure\*?\}(?:\[(?P<position>[^\]]+)\])?"
    )
    _PATTERN_END_FIGURE = re.compile(r"\\end\{figure\*?\}")
    _PATTERN_INCLUDEGRAPHICS = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?")
    _PATTERN_SCALE = re.compile(r"(?:scale|width|height)\s*=", re.IGNORECASE)
    _PATTERN_LABEL = re.compile(r"\\label\{")
    _PATTERN_CAPTION = re.compile(r"\\caption(?:\[[^\]]*\])?\{")
    _PATTERN_CAPTION_START = re.compile(r"\\caption(?:\[[^\]]*\])?\{")
    _PATTERN_BEGIN_IEEE_BIOGRAPHY = re.compile(r"\\begin\{IEEEbiography\}")
    _PATTERN_END_IEEE_BIOGRAPHY = re.compile(r"\\end\{IEEE(?:biography|bibliography)\}")
    _PATTERN_INCLUDEGRAPHICS_PATH = re.compile(
        r"\\includegraphics(?:\[(?P<options>[^\]]*)\])?\{(?P<path>[^}]+)\}"
    )
    _ALLOWED_POSITIONS: ClassVar[set[str]] = {"bt", "t", "b", "tb"}
    _IEEE_BIO_REQUIRED_RATIO = 1.25
    _IEEE_BIO_RATIO_TOLERANCE = 0.01

    @staticmethod
    def _extract_caption_content(line: str) -> str | None:
        r"""Extract caption content handling nested braces.

        This properly handles captions with nested braces like:
        \caption{...with $2^{(\cdot)}$ math...}

        Returns the caption text (without the \caption{} wrapper) or None if not found.
        """
        match = Reviewer_Figure._PATTERN_CAPTION_START.search(line)
        if not match:
            return None

        # Find the start of the caption content (after the opening brace)
        start_pos = match.end()
        brace_count = 1
        pos = start_pos

        # Iterate through the line counting braces to find the matching closing brace
        while pos < len(line) and brace_count > 0:
            if line[pos] == "\\" and pos + 1 < len(line):
                # Skip escaped characters
                pos += 2
            elif line[pos] == "{":
                brace_count += 1
                pos += 1
            elif line[pos] == "}":
                brace_count -= 1
                if brace_count == 0:
                    # Found the closing brace
                    return line[start_pos:pos].strip()
                pos += 1
            else:
                pos += 1

        # If we get here, the closing brace wasn't on this line (shouldn't happen for single-line captions)
        return None

    def __init__(self, printer: Printer, tex_file_path: Path) -> None:
        self.printer = printer
        self.tex_dir = tex_file_path.parent
        self.comments: list[Diagnostic] = []
        self.error_count = 0

        # Track figure environment state
        self.in_figure = False
        self.figure_start_line = -1
        self.has_label_in_figure = False
        self.has_caption_in_figure = False
        self.has_scaled_image_in_figure = False
        self.first_caption_line: int | None = None
        self.first_includegraphics_line: int | None = None
        self.includegraphics_lines: list[int] = []
        self.caption_period_style: bool | None = None
        self.caption_period_style_line: int | None = None
        self.caption_period_all_same = True
        self.caption_period_issue_line: int | None = None
        self.caption_period_other_line: int | None = None
        self.caption_period_issue_added = False

        # Track IEEEbiography context (can span multiple lines)
        self.in_ieee_biography = False
        self.ieee_biography_start_line = -1
        self.ieee_biography_lines: list[str] = []

    def process_line(self, line_no: int, line: str) -> None:
        # Remove comments (everything after %)
        if "%" in line:
            line = line[: line.index("%")]

        # Check for figure environment start
        begin_match = self._PATTERN_BEGIN_FIGURE.search(line)
        if begin_match:
            self.in_figure = True
            self.figure_start_line = line_no
            self.has_label_in_figure = False
            self.has_caption_in_figure = False
            self.has_scaled_image_in_figure = False
            self.first_caption_line = None
            self.first_includegraphics_line = None
            self.includegraphics_lines = []

            position = begin_match.group("position")
            if position is not None and position not in self._ALLOWED_POSITIONS:
                self.comments.append(
                    Diagnostic(
                        line_no,
                        RULE_FIG001,
                        RULE_FIG001.render_message(),
                    )
                )
                self.error_count += 1

        if self.in_figure:
            # Check for label
            if self._PATTERN_LABEL.search(line):
                self.has_label_in_figure = True

            if self._PATTERN_CAPTION.search(line):
                self.has_caption_in_figure = True
                if self.first_caption_line is None:
                    self.first_caption_line = line_no
                caption_text = self._extract_caption_content(line)
                if caption_text:
                    caption_has_period = caption_text.endswith(".")
                    if self.caption_period_style is None:
                        self.caption_period_style = caption_has_period
                        self.caption_period_style_line = line_no
                    elif caption_has_period != self.caption_period_style:
                        self.caption_period_all_same = False
                        if self.caption_period_issue_line is None:
                            self.caption_period_issue_line = line_no
                            self.caption_period_other_line = (
                                self.caption_period_style_line
                            )

            # Check for includegraphics
            if self._PATTERN_INCLUDEGRAPHICS.search(line):
                self.includegraphics_lines.append(line_no)
                if self.first_includegraphics_line is None:
                    self.first_includegraphics_line = line_no
                # Check if image is scaled
                if self._PATTERN_SCALE.search(line):
                    self.has_scaled_image_in_figure = True
                    self.comments.append(
                        Diagnostic(
                            line_no,
                            RULE_FIG002,
                            RULE_FIG002.render_message(),
                        )
                    )
                    self.error_count += 1

        self._process_ieee_biography_context(line_no, line)

        # Check for figure environment end
        if self._PATTERN_END_FIGURE.search(line):
            if self.in_figure:
                # Report missing label if there's an image
                if self.includegraphics_lines and not self.has_label_in_figure:
                    self.comments.append(
                        Diagnostic(
                            self.figure_start_line,
                            RULE_FIG003,
                            RULE_FIG003.render_message(),
                        )
                    )
                    self.error_count += 1

                if self.includegraphics_lines and not self.has_caption_in_figure:
                    self.comments.append(
                        Diagnostic(
                            self.figure_start_line,
                            RULE_FIG004,
                            RULE_FIG004.render_message(),
                        )
                    )
                    self.error_count += 1

                if (
                    self.first_caption_line is not None
                    and self.first_includegraphics_line is not None
                    and self.first_caption_line < self.first_includegraphics_line
                ):
                    self.comments.append(
                        Diagnostic(
                            self.first_caption_line,
                            RULE_FIG005,
                            RULE_FIG005.render_message(),
                        )
                    )
                    self.error_count += 1

            self.in_figure = False
            self.figure_start_line = -1
            self.has_label_in_figure = False
            self.has_caption_in_figure = False
            self.has_scaled_image_in_figure = False
            self.first_caption_line = None
            self.first_includegraphics_line = None
            self.includegraphics_lines = []

    def get_comments(self) -> list[Diagnostic]:
        if self.in_ieee_biography and self.ieee_biography_lines:
            self._finalize_ieee_biography_context()
        self._add_caption_period_consistency_issue()
        return self.comments

    def _add_caption_period_consistency_issue(self) -> None:
        if self.caption_period_issue_added:
            return

        if self.caption_period_all_same:
            return

        issue_line = (
            self.caption_period_issue_line
            if self.caption_period_issue_line is not None
            else 0
        )
        details = (
            f"line {issue_line + 1} conflicts with line "
            f"{self.caption_period_other_line + 1}; all figure captions should use "
            "the same period style."
            if self.caption_period_other_line is not None
            else "all figure captions should use the same period style."
        )
        self.comments.append(
            Diagnostic(
                issue_line,
                RULE_FIG006,
                RULE_FIG006.render_message(details=details),
            )
        )
        self.error_count += 1
        self.caption_period_issue_added = True

    def _process_ieee_biography_context(self, line_no: int, line: str) -> None:
        if self._PATTERN_BEGIN_IEEE_BIOGRAPHY.search(line):
            self.in_ieee_biography = True
            self.ieee_biography_start_line = line_no
            self.ieee_biography_lines = [line]
            if self._PATTERN_END_IEEE_BIOGRAPHY.search(line):
                self._finalize_ieee_biography_context()
            return

        if not self.in_ieee_biography:
            return

        self.ieee_biography_lines.append(line)
        if self._PATTERN_END_IEEE_BIOGRAPHY.search(line):
            self._finalize_ieee_biography_context()

    def _finalize_ieee_biography_context(self) -> None:
        block_text = "\n".join(self.ieee_biography_lines)
        self._check_ieee_biography(self.ieee_biography_start_line, block_text)
        self.in_ieee_biography = False
        self.ieee_biography_start_line = -1
        self.ieee_biography_lines = []

    def _check_ieee_biography(self, line_no: int, biography_block: str) -> None:
        includegraphics_match = self._PATTERN_INCLUDEGRAPHICS_PATH.search(
            biography_block
        )
        if includegraphics_match is None:
            return

        graphics_path = includegraphics_match.group("path")
        resolved_path = self._resolve_graphics_path(graphics_path)
        if resolved_path is None:
            self.comments.append(
                Diagnostic(
                    line_no,
                    RULE_FIG007,
                    RULE_FIG007.render_message(path=graphics_path),
                )
            )
            self.error_count += 1
            return

        is_valid_size, size_message = self._is_ieee_biography_image_size_valid(
            resolved_path
        )
        if not is_valid_size:
            self.comments.append(
                Diagnostic(
                    line_no,
                    RULE_FIG008,
                    RULE_FIG008.render_message(details=size_message),
                )
            )
            self.error_count += 1

    def _is_ieee_biography_image_size_valid(self, image_path: Path) -> tuple[bool, str]:
        with Image.open(image_path) as image:
            width_px, height_px = image.size

        if width_px <= 0:
            return False, "image width is invalid"

        actual_ratio = height_px / width_px
        ratio_ok = (
            abs(actual_ratio - self._IEEE_BIO_REQUIRED_RATIO)
            <= self._IEEE_BIO_RATIO_TOLERANCE
        )
        if ratio_ok:
            return True, ""

        return (
            False,
            (f"actual ratio is {actual_ratio:.3f} (from {width_px}x{height_px}px)"),
        )

    def _resolve_graphics_path(self, graphics_path: str) -> Path | None:
        candidate = self.tex_dir / graphics_path
        if candidate.is_file():
            return candidate
        return None

    def get_summary(self) -> str:
        if self.error_count == 0:
            return ""
        return f"Figure errors: {self.error_count}"

    def get_status(self) -> Status:
        return Status.PASSED if self.error_count == 0 else Status.FAILED

    def get_name(self) -> str:
        return "Figure"
