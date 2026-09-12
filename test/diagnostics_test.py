import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from printer import Printer
from reviewers.reviewer import Diagnostic, Severity
from reviewers.reviewer_casing import Reviewer_Casing
from reviewers.reviewer_chktex import Reviewer_ChkTeX
from reviewers.reviewer_math import Reviewer_Math
from reviewers.reviewer_reflabel import Reviewer_RefLabel
from reviewers.reviewer_unsure import Reviewer_Unsure
from reviewers.rules import RULES
from template_check import Template
from texact import _strip_latex_comment

TEST_DIR = Path(__file__).resolve().parent


def test_rule_codes_and_reviewer_numbers_are_unique() -> None:
    rules = list(RULES)
    codes = [rule.code for rule in rules]
    reviewer_numbers = [(rule.reviewer_class, rule.number) for rule in rules]

    assert len(codes) == len(set(codes))
    assert len(reviewer_numbers) == len(set(reviewer_numbers))
    assert len(RULES.prefixes) == len(set(RULES.prefixes.values()))


def test_rule_metadata_has_kebab_names_and_documentation() -> None:
    rules_root = TEST_DIR.parent / "docs" / "rules"

    for rule in RULES:
        assert re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", rule.name)
        documentation_file = rule.documentation_path.split("#", 1)[0]
        assert (TEST_DIR.parent / documentation_file).is_file()

    assert rules_root.joinpath("index.md").is_file()


def test_diagnostic_has_one_based_location() -> None:
    reviewer = Reviewer_Casing(Printer())
    reviewer.process_line(4, "asic")

    diagnostic = reviewer.get_comments()[0].with_source(Path("sample.tex"))

    assert isinstance(diagnostic, Diagnostic)
    assert diagnostic.code == "CAS001"
    assert diagnostic.line == 5
    assert diagnostic.filename == "sample.tex"


def test_strip_latex_comment_preserves_escaped_percent() -> None:
    escaped_percent = r"\%"
    even_backslashes = "\\" * 2
    cases = [
        ("text % comment\n", "text "),
        (
            f"text {escaped_percent} literal % comment\n",
            f"text {escaped_percent} literal ",
        ),
        (f"text {even_backslashes}% comment\n", f"text {even_backslashes}"),
        ("text % comment", "text "),
    ]

    for line, expected in cases:
        assert _strip_latex_comment(line) == expected


def test_casing_checks_text_after_escaped_percent() -> None:
    reviewer = Reviewer_Casing(Printer())

    reviewer.process_line(13, r"The \% is not be ignore, so trigger on FPgA")

    comments = reviewer.get_comments()
    assert len(comments) == 1
    assert comments[0].code == "CAS001"


def test_author_possessive_prefers_plural_form() -> None:
    reviewer = Reviewer_Unsure(Printer())

    reviewer.process_line(0, "The author's contributions are listed.")
    reviewer.process_line(1, "The authors' contributions are listed.")

    reviewer.process_line(2, "Author's contributions are listed.")
    reviewer.process_line(3, "Authors' contributions are listed.")

    comments = reviewer.get_comments()
    assert len(comments) == 2
    assert comments[0].code == "UNS003"
    assert comments[1].code == "UNS003"


def test_spaces_before_punctuation_are_reported() -> None:
    reviewer = Reviewer_Unsure(Printer())

    reviewer.process_line(0, "This is wrong .")
    reviewer.process_line(1, "This is also wrong ,")
    reviewer.process_line(2, "This is correct.")

    comments = reviewer.get_comments()
    assert len(comments) == 2
    assert comments[0].code == "UNS004"
    assert comments[1].code == "UNS004"


def test_plus_minus_notation_is_reported() -> None:
    reviewer = Reviewer_Math(Printer())

    reviewer.process_line(0, r"The values are +-1 and -+2, but + 3 is valid.")

    comments = reviewer.get_comments()
    assert len(comments) == 2
    assert [comment.code for comment in comments] == ["MAT001", "MAT001"]
    assert all(r"\pm" in comment.message for comment in comments)


def test_math_operators_use_latex_commands() -> None:
    reviewer = Reviewer_Math(Printer())
    lines = [
        "The maximum is max in prose.",
        r"$max(x) + min(x)$",
        r"\[\max(x) + \log(x)\]",
        r"\begin{equation} exp(x) \end{equation}",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "MAT002"
    ]

    assert len(comments) == 3
    assert all("Use" in comment.message for comment in comments)


def test_mu_uses_textmu_command() -> None:
    reviewer = Reviewer_Math(Printer())
    lines = [
        r"The word \mu in prose is not checked.",
        r"$\mu + \textmu$",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "MAT003"
    ]

    assert len(comments) == 1
    assert r"\textmu" in comments[0].message


def test_math_parentheses_use_left_and_right() -> None:
    reviewer = Reviewer_Math(Printer())
    lines = [
        r"Text (outside math) is not checked.",
        r"$f(x) + \left(x + 1\right)$",
        r"\[\left( x + 1 \right)\]",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "MAT004"
    ]

    assert len(comments) == 2
    assert r"\left" in comments[0].message
    assert r"\right" in comments[1].message


def test_label_prefixes_match_latex_context() -> None:
    reviewer = Reviewer_RefLabel(Printer())
    lines = [
        r"\section{Introduction}",
        r"\label{intro}",
        r"\section{Conclusion}\label{sec:conclusion}",
        r"\label{standalone}",
        r"\begin{figure}",
        r"\label{figure:overview}",
        r"\end{figure}",
        r"\begin{equation}",
        r"\label{eq:energy}",
        r"\end{equation}",
        r"\begin{table}",
        r"\label{table:results}",
        r"\end{table}",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "REF004"
    ]

    assert [comment.code for comment in comments] == ["REF004", "REF004", "REF004"]
    assert [comment.line_no for comment in comments] == [1, 5, 11]
    assert "sec:" in comments[0].message
    assert "fig:" in comments[1].message
    assert "tab:" in comments[2].message


def test_references_require_hard_spaces() -> None:
    reviewer = Reviewer_RefLabel(Printer())
    lines = [
        r"See~\ref{fig:valid}.",
        r"See \ref{fig:invalid}.",
        r"\ref{fig:at-start}.",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "REF005"
    ]

    assert len(comments) == 2
    assert [comment.line_no for comment in comments] == [1, 2]
    assert all("hard space" in comment.message for comment in comments)


def test_markboth_spanning_multiple_lines_is_ignored() -> None:
    reviewer = Reviewer_Unsure(Printer())

    lines = [
        r"\markboth{",
        r"    IEEE TRANSACTIONS ON VERY LARGE SCALE INTEGRATION (VLSI) SYSTEMS,",
        r"}{Author \MakeLowercase{\textit{et al.}}: Title}",
        r"This should be flagged normally.",
    ]
    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line + "\n")

    comments = reviewer.get_comments()
    assert len(comments) == 1
    assert comments[0].line_no == 3


def test_texact_file_marker_stops_processing(tmp_path: Path) -> None:
    tex_file = tmp_path / "marker.tex"
    tex_file.write_text(
        "Before the marker.\n% texact-file ##\nasics after the marker.\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(TEST_DIR.parent / "source" / "texact.py"),
            "--no-chktex",
            str(tex_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert "asics" not in result.stdout


def test_inline_rule_ignore_applies_to_the_same_line(tmp_path: Path) -> None:
    tex_file = tmp_path / "inline-ignore.tex"
    tex_file.write_text(
        "\\begin{figure}[x] asics % texact FIG001 texact CAS001\n"
        "asics\n"
        "\\end{figure}\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(TEST_DIR.parent / "source" / "texact.py"),
            "--no-chktex",
            str(tex_file),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "[FIG001]" not in result.stdout
    assert result.stdout.count("[CAS001]") == 1


def test_output_controls_can_be_set_from_cli_or_config(tmp_path: Path) -> None:
    tex_file = tmp_path / "empty.tex"
    tex_file.write_text("\\documentclass{article}\n", encoding="utf-8")

    def run_texact(*arguments: str) -> str:
        result = subprocess.run(
            [
                sys.executable,
                str(TEST_DIR.parent / "source" / "texact.py"),
                "--no-chktex",
                *arguments,
                str(tex_file),
            ],
            capture_output=True,
            text=True,
            check=True,
            cwd=tmp_path,
        )
        return result.stdout

    normal_output = run_texact()
    assert "=== Reviewing" in normal_output
    assert "=== Summary" in normal_output

    quiet_output = run_texact("-q")
    assert "=== Reviewing" in quiet_output
    assert "=== Summary" not in quiet_output

    very_quiet_output = run_texact("-qq")
    assert "=== Reviewing" not in very_quiet_output
    assert "=== Summary" not in very_quiet_output

    (tmp_path / ".texact.toml").write_text(
        "[format]\nquiet = 2\n",
        encoding="utf-8",
    )
    configured_output = run_texact()
    assert "=== Reviewing" not in configured_output
    assert "=== Summary" not in configured_output


def test_missing_chktex_is_warning_unless_explicitly_enabled() -> None:
    for required, expected_severity in (
        (False, Severity.WARNING),
        (True, Severity.ERROR),
    ):
        reviewer = Reviewer_ChkTeX(
            Printer(),
            Path("missing.tex"),
            Template.UNKNOWN,
            required=required,
        )
        with patch.object(reviewer, "_resolve_chktex_command", return_value=None):
            diagnostic = reviewer.get_comments()[0]

        assert diagnostic.code == "CHK901"
        assert diagnostic.severity == expected_severity


def test_chktex_lookup_expands_tilde_in_path(
    tmp_path: Path,
    monkeypatch,
) -> None:
    chktex_directory = tmp_path / "bin"
    chktex_directory.mkdir()
    chktex_executable = chktex_directory / "chktex"
    chktex_executable.write_text("#!/bin/sh\n", encoding="utf-8")
    chktex_executable.chmod(0o755)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", "~/bin")

    reviewer = Reviewer_ChkTeX(
        Printer(),
        Path("missing.tex"),
        Template.UNKNOWN,
    )

    assert reviewer._resolve_chktex_command() == str(chktex_executable)


def test_cli_prints_warning_number() -> None:
    result = subprocess.run(
        ["texact", "--no-chktex", str(TEST_DIR / "casing_test.tex")],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert re.search(
        r"L\d+ \[CAS001\]: Incorrect casing: .* should be .*",
        result.stdout,
    )
