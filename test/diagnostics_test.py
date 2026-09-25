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
from reviewers.reviewer_section import Reviewer_Section
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


def test_only_mat004_is_disabled_by_default() -> None:
    assert [rule.code for rule in RULES if not rule.enabled_by_default] == ["MAT004"]


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


def test_title_casing_correct() -> None:
    reviewer = Reviewer_Casing(Printer())

    reviewer.process_line(0, r"\title{A Study of Digital Systems}")
    reviewer.process_line(1, r"\section*{Analysis of IEEE Results}")

    assert reviewer.get_comments() == []
    assert reviewer.get_status().name == "PASSED"


def test_title_casing_reports_incorrect_minor_word_casing() -> None:
    reviewer = Reviewer_Casing(Printer())

    reviewer.process_line(7, r"\section{A Study Of Digital Systems}")

    comments = reviewer.get_comments()
    assert len(comments) == 1
    assert comments[0].code == "CAS002"
    assert comments[0].line == 8
    assert "A Study of Digital Systems" in comments[0].message
    assert reviewer.get_summary() == "Title casing errors: 1"
    assert reviewer.get_status().name == "FAILED"


def test_title_casing_reports_minor_words_at_title_edges() -> None:
    reviewer = Reviewer_Casing(Printer())

    reviewer.process_line(0, r"\section{of analysis and}")

    comments = reviewer.get_comments()
    assert len(comments) == 1
    assert comments[0].code == "CAS002"
    assert "Of Analysis And" in comments[0].message


def test_title_casing_ignores_math() -> None:
    reviewer = Reviewer_Casing(Printer())

    reviewer.process_line(
        0,
        r"\section{A Study of \textit{Digital} Systems with $x^2$ Results}",
    )

    assert reviewer.get_comments() == []


def test_section_headings_do_not_skip_levels() -> None:
    reviewer = Reviewer_Section(Printer())
    lines = [
        r"\section{Introduction}",
        r"\subsubsection{Skipped subsection}",
        r"\subsection*{Methods}",
        r"\subsubsection{Details}",
        r"\paragraph{Fine detail}",
        r"\subparagraph{More detail}",
        r"\subparagraph{Another detail}",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = reviewer.get_comments()
    assert len(comments) == 1
    assert comments[0].code == "SEC001"
    assert r"\subsection" in comments[0].message
    assert r"\subsubsection" in comments[0].message
    assert reviewer.get_summary() == "Heading hierarchy errors: 1"


def test_section_heading_order_accepts_top_level_and_starred_headings() -> None:
    reviewer = Reviewer_Section(Printer())
    lines = [
        r"\section*{Introduction}",
        r"\subsection{Methods}",
        r"\subsubsection*{Details}",
        r"\section{Results}",
        r"\subsection{Conclusion}",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    assert reviewer.get_comments() == []


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
    reviewer.process_line(2, r"This is still wrong ,}")
    reviewer.process_line(3, "This is correct.")

    comments = reviewer.get_comments()
    assert len(comments) == 3
    assert comments[0].code == "UNS004"
    assert comments[1].code == "UNS004"
    assert comments[2].code == "UNS004"


def test_period_before_closing_brace_does_not_need_a_space() -> None:
    reviewer = Reviewer_Unsure(Printer())

    reviewer.process_line(0, r"This is fine.}")

    assert reviewer.get_comments() == []


def test_double_periods_are_reported_but_relative_paths_are_ignored() -> None:
    reviewer = Reviewer_Unsure(Printer())
    lines = [
        "This sentence ends with two periods..",
        r"\includegraphics{../assets/image.png}",
        r"\input{../../shared.tex}",
        "This uses an ellipsis... correctly.",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = reviewer.get_comments()
    assert len(comments) == 1
    assert comments[0].code == "UNS005"
    assert "two periods" in comments[0].message
    assert reviewer.get_summary() == "Double periods: 1"


def test_double_commas_are_reported_but_latex_spacing_is_ignored() -> None:
    reviewer = Reviewer_Unsure(Printer())
    lines = [
        "This sentence has two commas,,",
        r"This uses thin space\, correctly.",
        "This sentence has a single comma, correctly.",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = reviewer.get_comments()
    assert len(comments) == 1
    assert comments[0].code == "UNS008"
    assert comments[0].line_no == 0
    assert reviewer.get_summary() == "Double commas: 1"


def test_periods_require_following_spaces_except_in_paths_and_abbreviations() -> None:
    reviewer = Reviewer_Unsure(Printer())
    lines = [
        "This sentence has no space.Next sentence.",
        "The author is Ph.D. Smith.",
        r"\includegraphics{../assets/image.png} \input{source/main.tex}",
        "Version 1.2 and an ellipsis... are valid.",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = reviewer.get_comments()
    assert len(comments) == 1
    assert comments[0].code == "UNS006"
    assert "space after periods" in comments[0].message
    assert reviewer.get_summary() == "Periods without following spaces: 1"


def test_dash_length_reports_number_ranges_and_word_en_dashes() -> None:
    reviewer = Reviewer_Unsure(Printer())
    lines = [
        "See pages 5-10 for the proof.",
        "A well--known result.",
        "A correct 5--10 range.",
        "A correct state---of---the-art phrase.",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "UNS007"
    ]
    assert len(comments) == 2
    assert comments[0].line_no == 0
    assert "numbers" in comments[0].message
    assert "unsafe fix" in comments[0].message
    assert comments[1].line_no == 1
    assert "words" in comments[1].message
    assert comments[0].severity == Severity.WARNING


def test_dash_length_reports_text_negative_numbers_but_not_math() -> None:
    reviewer = Reviewer_Unsure(Printer())
    lines = [
        "The value -4 is invalid.",
        r"The math value $-4$ is valid.",
        r"The other math value \(-4\) is valid.",
        "The range 5-10 is a separate issue.",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "UNS007"
    ]
    assert len(comments) == 2
    assert comments[0].line_no == 0
    assert "$-$ 4" in comments[0].message
    assert comments[1].line_no == 3


def test_dash_length_ignores_coordinates_dates_specs_math_and_verbatim() -> None:
    reviewer = Reviewer_Unsure(Printer())
    lines = [
        "Barzilai--Borwein and Newton--Raphson are coordinate names.",
        "Dates 2020-01-15 and ISBN 0-306-40615-2 are opaque.",
        r"\cline{1-3} \cmidrule(lr){2-3} \label{fig:1-3} \cite{smith2020-1}",
        r"\item<1-2> \begin{onlyenv}<2-3>",
        r"Math $5-10$ and \(well--known\).",
        r"\begin{verbatim}",
        "5-10 well--known",
        r"\end{verbatim}",
        "5-10 well-known",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "UNS007"
    ]
    assert len(comments) == 1
    assert comments[0].line_no == 8


def test_disabled_rule_can_be_selected(tmp_path: Path) -> None:
    tex_file = tmp_path / "math.tex"
    tex_file.write_text("$ (x) $\nSee pages 5-10.\n", encoding="utf-8")

    command = [
        sys.executable,
        str(TEST_DIR.parent / "source" / "texact.py"),
        "--no-chktex",
        "-q",
        str(tex_file),
    ]
    disabled = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    assert "MAT004" not in disabled.stdout
    assert "UNS007" in disabled.stdout

    selected_command = [
        *command[:-1],
        "--select",
        "MAT004",
        "--select",
        "UNS007",
        str(tex_file),
    ]
    (tmp_path / ".texact.toml").write_text(
        "[lint]\nselect = ['MAT004']\n",
        encoding="utf-8",
    )
    enabled = subprocess.run(
        selected_command,
        capture_output=True,
        text=True,
        check=False,
        cwd=tmp_path,
    )
    assert enabled.returncode == 1
    assert "MAT004" in enabled.stdout
    assert "UNS007" in enabled.stdout


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


def test_math_operators_inside_labels_are_ignored() -> None:
    reviewer = Reviewer_Math(Printer())

    reviewer.process_line(0, r"$\label{eq:max} + min(x)$")

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "MAT002"
    ]

    assert len(comments) == 1
    assert "min" in comments[0].message


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


def test_ellipsis_uses_context_specific_latex_commands() -> None:
    reviewer = Reviewer_Math(Printer())
    lines = [
        r"Text ... in normal text, but $...$ is math.",
        r"\begin{equation} x ... y \end{equation}",
        r"Text with \dots, $\ldots$ and $\cdots$ is valid.",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "MAT007"
    ]

    assert len(comments) == 3
    assert r"\dots" in comments[0].message
    assert "normal text" in comments[0].message
    assert r"\ldots" in comments[1].message
    assert r"\cdots" in comments[1].message
    assert "math mode" in comments[1].message


def test_ieee_math_uses_ieeeeqnarray() -> None:
    ieee_reviewer = Reviewer_Math(Printer(), Template.IEEE)
    llncs_reviewer = Reviewer_Math(Printer(), Template.LLNCS)

    ieee_reviewer.process_line(0, r"\begin{align}")
    ieee_reviewer.process_line(1, r"\begin{split}")
    ieee_reviewer.process_line(2, r"\begin{IEEEeqnarray}{rCl}")
    ieee_reviewer.process_line(3, r"\end{IEEEeqnarray}")
    ieee_reviewer.process_line(4, r"max in prose")
    llncs_reviewer.process_line(0, r"\begin{align}")

    ieee_comments = [
        comment for comment in ieee_reviewer.get_comments() if comment.code == "MAT005"
    ]

    assert len(ieee_comments) == 2
    assert all("IEEEeqnarray" in comment.message for comment in ieee_comments)
    assert not any(
        comment.code == "MAT005" for comment in llncs_reviewer.get_comments()
    )


def test_delimiters_match_outside_and_inside_math() -> None:
    reviewer = Reviewer_Math(Printer())
    lines = [
        r"Valid [()]{} and escaped \{literal\}.",
        r"Invalid [)",
        r"Invalid (]",
        r"$x + (y$",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "MAT006"
    ]

    assert len(comments) == 3
    assert "expected ]" in comments[0].message
    assert "expected )" in comments[1].message
    assert "unclosed (" in comments[2].message


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


def test_labels_follow_numbering_statements() -> None:
    reviewer = Reviewer_RefLabel(Printer())
    lines = [
        r"\begin{figure*}",
        r"  \label{fig:before}",
        r"  \caption{A plot}",
        r"\end{figure*}",
        r"\begin{table}",
        r"  \label{tab:before}",
        r"  \caption{A table}",
        r"\end{table}",
        r"\begin{minipage}{\textwidth}",
        r"  \label{fig:minipage}",
        r"  \captionof{figure}{A plot}",
        r"\end{minipage}",
        r"\begin{enumerate}",
        r"  \label{item:first}",
        r"  \item<1->[First] An item",
        r"  \label{item:second}",
        r"  \item Second item",
        r"\end{enumerate}",
        r"\begin{itemize}",
        r"  \label{itemize:label}",
        r"  \item An item",
        r"\end{itemize}",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "REF007"
    ]

    assert len(comments) == 4
    assert [comment.line_no for comment in comments] == [1, 5, 9, 13]
    assert "figure caption" in comments[0].message
    assert "table caption" in comments[1].message
    assert r"\captionof" in comments[2].message
    assert "first enumerate item" in comments[3].message
    assert all(comment.severity == Severity.WARNING for comment in comments)


def test_nested_labels_are_not_treated_as_statement_labels() -> None:
    reviewer = Reviewer_RefLabel(Printer())
    lines = [
        r"\begin{figure}",
        r"  \textbf{\label{fig:nested}}",
        r"  \caption{A plot}",
        r"\end{figure}",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    assert not any(comment.code == "REF007" for comment in reviewer.get_comments())


def test_citations_precede_periods() -> None:
    reviewer = Reviewer_RefLabel(Printer())
    lines = [
        r"This is correct \cite{valid}.",
        r"This is wrong. \cite{invalid}.",
        r"This is also wrong.\cite{invalid2}.",
    ]

    for line_no, line in enumerate(lines):
        reviewer.process_line(line_no, line)

    comments = [
        comment for comment in reviewer.get_comments() if comment.code == "REF006"
    ]

    assert len(comments) == 2
    assert [comment.line_no for comment in comments] == [1, 2]
    assert all(r"\cite" in comment.message for comment in comments)


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


def test_vscode_style_formats_diagnostics_from_cli_or_config(tmp_path: Path) -> None:
    tex_file = tmp_path / "main.tex"
    tex_file.write_text("asic\n", encoding="utf-8")

    def run_texact(*arguments: str) -> str:
        result = subprocess.run(
            [
                sys.executable,
                str(TEST_DIR.parent / "source" / "texact.py"),
                "--no-chktex",
                "-q",
                *arguments,
                "./main.tex",
            ],
            capture_output=True,
            text=True,
            check=False,
            cwd=tmp_path,
        )
        assert result.returncode == 1
        return result.stdout

    cli_output = run_texact("--vscode-style")
    assert "main.tex:1: [CAS001] Incorrect casing: asic should be ASIC" in cli_output
    assert "\x1b[" not in cli_output

    (tmp_path / ".texact.toml").write_text(
        "[format]\nvscode-style = true\n",
        encoding="utf-8",
    )
    configured_output = run_texact()
    assert (
        "main.tex:1: [CAS001] Incorrect casing: asic should be ASIC"
        in configured_output
    )


def test_vscode_style_keeps_diagnostic_colors() -> None:
    printer = Printer(vscode_style=True)

    assert printer.dark_red("[CAS001]").startswith(Printer.DARK_RED)
    assert printer.yellow("[CHK001]").startswith(Printer.YELLOW)


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
