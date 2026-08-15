import argparse
import sys
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from configuration import ConfigurationError, TexactConfig, load_config
from printer import Printer
from reviewers.reviewer import Diagnostic, Reviewer, Severity, Status
from reviewers.reviewer_casing import Reviewer_Casing
from reviewers.reviewer_chktex import Reviewer_ChkTeX
from reviewers.reviewer_figure import Reviewer_Figure
from reviewers.reviewer_inthis import Reviewer_Inthis
from reviewers.reviewer_reflabel import Reviewer_RefLabel
from reviewers.reviewer_unsure import Reviewer_Unsure
from template_check import get_template


def get_version() -> str:
    try:
        return version("texact")
    except PackageNotFoundError:
        return "unknown"


def _strip_latex_comment(line: str) -> str:
    for index, character in enumerate(line):
        if character != "%":
            continue
        backslashes = 0
        preceding = index - 1
        while preceding >= 0 and line[preceding] == "\\":
            backslashes += 1
            preceding -= 1
        if backslashes % 2 == 0:
            return line[:index]
    return line


def set_up_arg_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automated LaTeX and article review. Can you pass the judgement?"
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Path(s) to LaTeX files",
    )
    parser.add_argument(
        "--config",
        type=Path,
        metavar="PATH",
        help="Path to a TeXact TOML configuration file",
    )
    parser.add_argument(
        "--chktex",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="Run chktex with config/chktexrc",
    )
    parser.add_argument(
        "--html-style",
        default=None,
        action=argparse.BooleanOptionalAction,
        help="Output colors using HTML spans instead of ANSI escape codes",
    )
    return parser.parse_args()


def process_file(
    file_path: Path,
    display_name: str,
    reviewers: tuple[Reviewer, ...],
    printer: Printer,
    config: TexactConfig,
) -> int:
    with file_path.open("r", encoding="utf-8") as input_file:
        for line_no, line in enumerate(input_file):
            if "% texact *" in line:
                continue
            line = _strip_latex_comment(line)
            for reviewer in reviewers:
                reviewer.process_line(line_no, line)

    reviewer_comments: list[tuple[Reviewer, list[Diagnostic]]] = []
    all_comments: list[Diagnostic] = []
    for reviewer in reviewers:
        comments = reviewer.get_comments()
        reviewer_comments.append((reviewer, comments))
        all_comments.extend(comments)

    visible_comments = [
        comment for comment in all_comments if comment.code not in config.lint.ignore
    ]
    sourced_comments = [comment.with_source(file_path) for comment in visible_comments]
    for comment in sorted(
        sourced_comments,
        key=lambda diagnostic: (
            diagnostic.line_no,
            diagnostic.code,
        ),
    ):
        printer.print_diagnostic(comment)

    printer.print(f"=== Summary of {display_name} ===")
    configuration_path = (
        str(config.source_path.resolve())
        if config.source_path is not None
        else "none (built-in defaults)"
    )
    printer.print(f"Configuration file: {configuration_path}")
    for reviewer, comments in reviewer_comments:
        visible_reviewer_comments = [
            comment for comment in comments if comment.code not in config.lint.ignore
        ]
        status = _status_for_diagnostics(
            reviewer,
            comments,
            visible_reviewer_comments,
        )
        name = reviewer.get_name()
        summary = reviewer.get_summary() if visible_reviewer_comments else ""
        printer.print(f"Reviewer {name}: {printer.status_str(status)}. {summary}")

    any_failed = any(comment.severity == Severity.ERROR for comment in visible_comments)
    return 1 if any_failed else 0


def _status_for_diagnostics(
    reviewer: Reviewer,
    all_comments: list[Diagnostic],
    visible_comments: list[Diagnostic],
) -> Status:
    original_status = reviewer.get_status()
    if not visible_comments and all_comments:
        return Status.PASSED
    if any(comment.severity == Severity.ERROR for comment in visible_comments):
        return Status.FAILED
    if any(comment.severity == Severity.WARNING for comment in visible_comments):
        return Status.WARNING
    return original_status


def main():
    args = set_up_arg_parser()
    try:
        config = load_config(args.config)
    except ConfigurationError as error:
        raise SystemExit(f"Configuration error: {error}") from error

    html_style = (
        config.format.html_style if args.html_style is None else args.html_style
    )
    printer = Printer(html_style=html_style)

    if not args.files:
        raise SystemExit("Error: provide at least one LaTeX file.")

    max_ret_code = 0

    for file_name in args.files:
        name, extension = file_name[:-4], file_name[-3:]
        printer.print(f"=== Reviewing {name}(.){extension} ===")
        file_path = Path(file_name)

        if not file_path.is_file():
            raise SystemExit(
                f"Error: '{file_path}' does not exist or is not a regular file."
            )

        template = get_template(file_path)

        # Add reviewers
        reviewers = [
            Reviewer_Inthis(printer),
            Reviewer_RefLabel(printer),
            Reviewer_Casing(printer, config.lint.casing),
            Reviewer_Figure(printer, file_path),
            Reviewer_Unsure(printer, config.lint.we_count),
        ]
        if args.chktex is not False:
            reviewers.append(
                Reviewer_ChkTeX(
                    printer,
                    file_path,
                    template,
                    config.tools.chktex_path,
                    required=args.chktex is True,
                )
            )

        ret_code = process_file(
            file_path,
            f"{name}(.){extension}",
            tuple(reviewers),
            printer,
            config,
        )
        max_ret_code = max(max_ret_code, ret_code)

    sys.exit(max_ret_code)


if __name__ == "__main__":
    main()
