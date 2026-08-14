from pathlib import Path
import re
import subprocess

from reviewers.reviewer import Diagnostic
from reviewers.reviewer_casing import Reviewer_Casing
from reviewers.rules import RULES
from printer import Printer


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
        assert rule.documentation_url().startswith("docs/rules/")
        assert rule.documentation_url("https://docs.example.test/texact").endswith(
            f"/rules/{rule.name}.html"
        )

    assert rules_root.joinpath("index.md").is_file()


def test_diagnostic_has_one_based_location() -> None:
    reviewer = Reviewer_Casing(Printer())
    reviewer.process_line(4, "asic")

    diagnostic = reviewer.get_comments()[0].with_source(Path("sample.tex"))

    assert isinstance(diagnostic, Diagnostic)
    assert diagnostic.code == "CAS001"
    assert diagnostic.line == 5
    assert diagnostic.filename == "sample.tex"


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


def test_cli_uses_configured_documentation_base_url() -> None:
    result = subprocess.run(
        [
            "texact",
            "--no-chktex",
            "--docs-base-url",
            "https://docs.example.test/texact",
            str(TEST_DIR / "casing_test.tex"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 1
    assert "[CAS001]" in result.stdout
    assert "https://docs.example.test/texact" not in result.stdout
