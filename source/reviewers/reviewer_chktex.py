import os
import re
import shutil
import subprocess
from importlib import resources
from pathlib import Path

from printer import Printer
from .reviewer import (
    Diagnostic,
    Reviewer,
    Status,
)
from .rules import (
    RULES,
    RULE_CHK901,
    RULE_CHK902,
    RULE_CHK903,
    RULE_CHK904,
    Severity,
)
from template_check import Template


class Reviewer_ChkTeX(Reviewer):
    """Runs ChkTeX and adapts its output for TeXact."""

    _PATTERN_VERSION = re.compile(r"^ChkTeX\s+v(?P<version>[\d.]+)")
    _PATTERN_DIAGNOSTIC = re.compile(
        r"^L(?P<line>\d+):\s+(?P<kind>Warning|Error)\s+(?P<code>\d+)\.\s+(?P<message>.*)$"
    )

    def __init__(
        self, printer: Printer, tex_file_path: Path, template: Template
    ) -> None:
        self.printer = printer
        self.tex_file_path = tex_file_path.resolve()
        self.repo_root = Path(__file__).resolve().parent.parent.parent
        self.template = template

        self.comments: list[Diagnostic] = []
        self.version = "unknown"
        self.warning_count = 0
        self.error_count = 0
        self.execution_failed = False
        self.chktex_not_installed = False
        self._has_run = False

    def process_line(self, line_no: int, line: str) -> None:
        return

    # def suppress_comments(
    #     self, comments: list[tuple[int, str]]
    # ) -> list[tuple[int, str]]:
    #     filtered_comments = []
    #     suppressed_count = 0

    #     for line_no, message in comments:
    #         # The message includes the warning text and source context separated by newlines.
    #         # Because 'Warning' is colorized, we check for '25.' or '8.' in the first line.
    #         first_line = message.split("\n")[0]
    #         if (
    #             "Warning" in first_line
    #             and "25." in first_line
    #             and "\\includegraphics" in message
    #         ):
    #             suppressed_count += 1
    #             continue

    #         filtered_comments.append((line_no, message))

    #     self.warning_count -= suppressed_count
    #     return filtered_comments

    def get_comments(self) -> list[Diagnostic]:
        if self._has_run:
            return self.comments

        self._has_run = True

        # Check if chktex is installed
        if shutil.which("chktex") is None:
            self.execution_failed = True
            self.chktex_not_installed = True
            self.comments.append(
                Diagnostic(
                    0,
                    RULE_CHK901,
                    RULE_CHK901.render_message(),
                )
            )
            return self.comments

        chktexrc_path = self._resolve_chktexrc_path()
        if chktexrc_path is None:
            self.execution_failed = True
            self.comments.append(
                Diagnostic(
                    0,
                    RULE_CHK902,
                    RULE_CHK902.render_message(),
                )
            )
            return self.comments

        command = [
            "chktex",
            "-l",
            str(chktexrc_path),
            "-v7",
            str(self.tex_file_path),
        ]

        if self.template == Template.IEEE or self.template == Template.LLNCS:
            command += [
                "-n12",
                "-n13",
            ]  # French spacing is used so these should be ignored.

        try:
            run_env = os.environ.copy()
            run_env["PATH"] = self._expand_path_entries(run_env.get("PATH", ""))
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=False,
                cwd=self.repo_root,
                env=run_env,
            )
        except FileNotFoundError:
            self.execution_failed = True
            self.comments.append(
                Diagnostic(
                    0,
                    RULE_CHK903,
                    RULE_CHK903.render_message(),
                )
            )
            return self.comments

        output_lines = result.stdout.splitlines() + result.stderr.splitlines()
        index = 0
        while index < len(output_lines):
            output_line = output_lines[index]

            version_match = self._PATTERN_VERSION.match(output_line)
            if version_match:
                self.version = version_match.group("version")
                index += 1
                continue

            diagnostic_match = self._PATTERN_DIAGNOSTIC.match(output_line)
            if diagnostic_match is None:
                index += 1
                continue

            line_no = int(diagnostic_match.group("line")) - 1
            kind = diagnostic_match.group("kind")
            chktex_code = int(diagnostic_match.group("code"))
            if kind == "Warning":
                self.warning_count += 1
            else:
                self.error_count += 1

            detail_text = output_line.split(":", 1)[1].strip()
            colored_kind = self._color_kind_text(kind)
            message = detail_text.replace(kind, colored_kind, 1)
            severity = Severity.WARNING if kind == "Warning" else Severity.ERROR
            rule = RULES.get_or_register_chktex(
                chktex_code,
                severity,
                message,
            )

            context_lines, consumed_lines = self._collect_context_lines(
                output_lines,
                index + 1,
            )
            if context_lines:
                formatted_context = self._format_context_lines(context_lines, kind)
                message = f"{message}\n" + "\n".join(formatted_context)
                index += consumed_lines

            self.comments.append(
                Diagnostic(
                    line_no,
                    rule,
                    rule.render_message(message=message),
                    severity_override=severity,
                )
            )
            index += 1

        if result.returncode != 0 and not self.comments:
            self.execution_failed = True
            stderr_text = result.stderr.strip()
            details = stderr_text or "no diagnostic output"
            self.comments.append(
                Diagnostic(
                    0,
                    RULE_CHK904,
                    RULE_CHK904.render_message(details=details),
                )
            )

        return self.comments

    @staticmethod
    def _is_source_context_line(line: str) -> bool:
        return bool(line) and line[:1].isspace()

    def _collect_context_lines(
        self,
        output_lines: list[str],
        start_index: int,
    ) -> tuple[list[str], int]:
        context_lines: list[str] = []
        consumed_lines = 0
        current_index = start_index

        while current_index < len(output_lines):
            candidate = output_lines[current_index]
            if not self._is_source_context_line(candidate):
                break

            context_lines.append(candidate.rstrip())
            consumed_lines += 1
            current_index += 1

        return context_lines, consumed_lines

    def _color_kind_text(self, kind: str) -> str:
        if kind == "Warning":
            return self.printer.yellow(kind)
        return self.printer.dark_red(kind)

    def _format_context_lines(self, context_lines: list[str], kind: str) -> list[str]:
        formatted_lines: list[str] = []
        for line in context_lines:
            stripped = line.strip()
            if stripped and set(stripped) == {"^"}:
                leading_space_count = len(line) - len(line.lstrip())
                leading_spaces = " " * leading_space_count
                caret = self._color_caret(kind, len(stripped))
                formatted_lines.append(f"{leading_spaces}{caret}")
            else:
                formatted_lines.append(line)

        return formatted_lines

    def _color_caret(self, kind: str, count: int) -> str:
        caret_text = "^" * count
        if kind == "Warning":
            return self.printer.yellow(caret_text)
        return self.printer.dark_red(caret_text)

    def get_summary(self) -> str:
        if not self._has_run:
            self.get_comments()

        return (
            f"v{self.version}, "
            f"warnings: {self.warning_count}, errors: {self.error_count}"
        )

    def get_status(self) -> Status:
        if not self._has_run:
            self.get_comments()

        if self.chktex_not_installed:
            return Status.WARNING

        if self.execution_failed:
            return Status.FAILED

        if self.warning_count > 0 or self.error_count > 0:
            return Status.FAILED

        return Status.PASSED

    def get_name(self) -> str:
        return "ChkTeX"

    @staticmethod
    def _expand_path_entries(path_value: str) -> str:
        if not path_value:
            return path_value

        expanded_entries = [
            os.path.expanduser(entry) if entry.startswith("~") else entry
            for entry in path_value.split(os.pathsep)
        ]
        return os.pathsep.join(expanded_entries)

    def _resolve_chktexrc_path(self) -> Path | None:
        repo_config_path = self.repo_root / "config" / "chktexrc"
        if repo_config_path.is_file():
            return repo_config_path

        try:
            resource_file = resources.files("texact_config").joinpath("chktexrc")
            if resource_file.is_file():
                return Path(str(resource_file))
        except (FileNotFoundError, ModuleNotFoundError):
            return None

        return None
