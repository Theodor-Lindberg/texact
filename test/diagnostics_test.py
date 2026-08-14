from pathlib import Path
import re
import subprocess
from unittest.mock import patch

from reviewers.reviewer import Diagnostic, Severity
from reviewers.reviewer_casing import Reviewer_Casing
from reviewers.reviewer_chktex import Reviewer_ChkTeX
from reviewers.rules import RULES
from printer import Printer
from template_check import Template


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
