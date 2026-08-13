import argparse
import sys

from pathlib import Path
from printer import Printer
from reviewer import Status
from reviewer_unsure import Reviewer_Unsure
from reviewer_inthis import Reviewer_Inthis
from reviewer_reflabel import Reviewer_RefLabel
from reviewer_casing import Reviewer_Casing
from reviewer_figure import Reviewer_Figure
from reviewer_chktex import Reviewer_ChkTeX
from template_check import get_template


def set_up_arg_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automated LaTeX and article reviewer(s). Can you pass the judgement?"
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Path(s) to LaTeX files",
    )
    parser.add_argument(
        "--unsure",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Find should|would|could|might",
    )
    parser.add_argument(
        "--chktex",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="Run chktex with config/chktexrc",
    )
    parser.add_argument(
        "--html-style",
        action="store_true",
        help="Output colors using HTML spans instead of ANSI escape codes",
    )
    return parser.parse_args()


def process_file(file_path: Path, reviewers: tuple, printer: Printer) -> int:
    with file_path.open("r", encoding="utf-8") as input_file:
        for line_no, line in enumerate(input_file):
            if "% texact *" in line:
                continue
            for reviewer in reviewers:
                reviewer.process_line(line_no, line)

    all_comments: list[tuple[int, str]] = []
    for reviewer in reviewers:
        all_comments.extend(reviewer.get_comments())

    for line_no, message in sorted(all_comments, key=lambda comment: comment[0]):
        printer.print_no(line_no, message)

    printer.print("=== Summary ===")
    for reviewer in reviewers:
        name = reviewer.get_name()
        status = printer.status_str(reviewer.get_status())
        summary = reviewer.get_summary()
        printer.print(f"Reviewer {name}: {status}. {summary}")

    any_failed = any(reviewer.get_status() == Status.FAILED for reviewer in reviewers)
    return 1 if any_failed else 0


def main():
    args = set_up_arg_parser()
    printer = Printer(html_style=args.html_style)

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
            Reviewer_Casing(printer),
            Reviewer_Figure(printer, file_path),
        ]
        if args.unsure:
            reviewers.append(Reviewer_Unsure(printer))
        if args.chktex:
            reviewers.append(Reviewer_ChkTeX(printer, file_path, template))

        ret_code = process_file(file_path, tuple(reviewers), printer)
        max_ret_code = max(max_ret_code, ret_code)

    sys.exit(max_ret_code)


if __name__ == "__main__":
    main()
