import re
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from printer import Printer
from reviewers.reviewer import Diagnostic, Severity
from reviewers.reviewer_casing import Reviewer_Casing
from reviewers.reviewer_chktex import Reviewer_ChkTeX
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
