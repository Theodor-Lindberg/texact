import re
from collections.abc import Iterator
from dataclasses import dataclass
from enum import StrEnum


class Severity(StrEnum):
    """Severity levels used by rule diagnostics."""

    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True)
class Rule:
    """Metadata and message template for one TeXact rule."""

    code: str
    name: str
    reviewer_class: str
    message: str
    severity: Severity = Severity.ERROR
    documentation_path: str = ""

    def __post_init__(self) -> None:
        if not self.documentation_path:
            object.__setattr__(
                self,
                "documentation_path",
                f"docs/rules/{self.name}.md",
            )

    @property
    def prefix(self) -> str:
        match = re.fullmatch(r"([A-Z]{2,3})\d+", self.code)
        if match is None:
            raise ValueError(f"Invalid TeXact rule code: {self.code}")
        return match.group(1)

    @property
    def number(self) -> int:
        match = re.fullmatch(r"[A-Z]{2,3}(\d+)", self.code)
        if match is None:
            raise ValueError(f"Invalid TeXact rule code: {self.code}")
        return int(match.group(1))

    def render_message(self, **values: object) -> str:
        return self.message.format(**values)


class RuleRegistry:
    """Registry that validates and resolves TeXact rules."""

    def __init__(self, rules: tuple[Rule, ...]) -> None:
        self._rules_by_code: dict[str, Rule] = {}
        self._prefix_reviewers: dict[str, str] = {}
        self._reviewer_prefixes: dict[str, str] = {}
        self._reviewer_numbers: dict[str, set[int]] = {}
        for rule in rules:
            self.register(rule)

    def register(self, rule: Rule) -> Rule:
        if rule.code in self._rules_by_code:
            raise ValueError(f"Duplicate TeXact rule code: {rule.code}")

        prefix = rule.prefix
        existing_reviewer = self._prefix_reviewers.get(prefix)
        if existing_reviewer is not None and existing_reviewer != rule.reviewer_class:
            raise ValueError(
                f"Rule prefix {prefix} is used by both "
                f"{existing_reviewer} and {rule.reviewer_class}"
            )

        existing_prefix = self._reviewer_prefixes.get(rule.reviewer_class)
        if existing_prefix is not None and existing_prefix != prefix:
            raise ValueError(
                f"{rule.reviewer_class} uses both {existing_prefix} and {prefix}"
            )

        reviewer_numbers = self._reviewer_numbers.setdefault(rule.reviewer_class, set())
        if rule.number in reviewer_numbers:
            raise ValueError(
                f"Rule number {rule.number} is duplicated for {rule.reviewer_class}"
            )

        self._rules_by_code[rule.code] = rule
        self._prefix_reviewers[prefix] = rule.reviewer_class
        self._reviewer_prefixes[rule.reviewer_class] = prefix
        reviewer_numbers.add(rule.number)
        return rule

    def get(self, code: str) -> Rule:
        return self._rules_by_code[code]

    def get_or_register_chktex(
        self,
        chktex_code: int,
        severity: Severity,
        message: str,
    ) -> Rule:
        native_number = chktex_code if chktex_code < 900 else 1000 + chktex_code
        code = f"CHK{native_number:03d}"
        existing_rule = self._rules_by_code.get(code)
        if existing_rule is not None:
            return existing_rule

        return self.register(
            Rule(
                code=code,
                name=f"chktex-{chktex_code}",
                reviewer_class="Reviewer_ChkTeX",
                message="{message}",
                severity=severity,
                documentation_path="docs/rules/chktex-diagnostic.md",
            )
        )

    def __iter__(self) -> Iterator[Rule]:
        return iter(self._rules_by_code.values())

    @property
    def prefixes(self) -> dict[str, str]:
        return self._prefix_reviewers.copy()


RULES = RuleRegistry(
    (
        Rule(
            "INT001",
            "abstract-first-line-this-work",
            "Reviewer_Inthis",
            "Avoid using 'this work' in the first line of the abstract.",
        ),
        Rule(
            "CAS001",
            "incorrect-casing",
            "Reviewer_Casing",
            "Incorrect casing: {actual} should be {expected}",
        ),
        Rule(
            "UNS001",
            "modal-or-uncertain-word",
            "Reviewer_Unsure",
            "Avoid wording: {line}",
        ),
        Rule(
            "UNS002",
            "excessive-we-usage",
            "Reviewer_Unsure",
            "Reduce use of 'we': found {count} occurrences; maximum is {limit}.",
        ),
        Rule(
            "UNS003",
            "singular-author-possessive",
            "Reviewer_Unsure",
            "Prefer authors' to author's in papers.",
        ),
        Rule(
            "REF001",
            "underscore-in-label",
            "Reviewer_RefLabel",
            "Use hyphens in label names instead of underscores: {label}.",
        ),
        Rule(
            "REF002",
            "undefined-label-reference",
            "Reviewer_RefLabel",
            "Undefined label: {label}.",
        ),
        Rule(
            "REF003",
            "unreferenced-label",
            "Reviewer_RefLabel",
            "Unused label: {label}.",
        ),
        Rule(
            "FIG001",
            "invalid-figure-position",
            "Reviewer_Figure",
            "Use an empty figure position or one of [bt], [t], [b], [tb].",
        ),
        Rule(
            "FIG002",
            "scaled-figure-image",
            "Reviewer_Figure",
            "Avoid scaling figure images; remove scale, width, or height.",
        ),
        Rule(
            "FIG003",
            "missing-figure-label",
            "Reviewer_Figure",
            "Add a \\label{{...}} to this figure.",
        ),
        Rule(
            "FIG004",
            "missing-figure-caption",
            "Reviewer_Figure",
            "Add a \\caption{{...}} to this figure.",
        ),
        Rule(
            "FIG005",
            "caption-before-graphics",
            "Reviewer_Figure",
            "Place the figure caption below the graphics.",
        ),
        Rule(
            "FIG006",
            "inconsistent-caption-period",
            "Reviewer_Figure",
            "Use one consistent period style for all figure captions: {details}",
        ),
        Rule(
            "FIG007",
            "biography-image-not-found",
            "Reviewer_Figure",
            "Add the IEEEbiography image relative to the TeX file: {path}.",
        ),
        Rule(
            "FIG008",
            "invalid-biography-image-ratio",
            "Reviewer_Figure",
            "Use an IEEEbiography image with a height/width ratio of 1.25: {details}.",
        ),
        Rule(
            "CHK901",
            "chktex-not-installed",
            "Reviewer_ChkTeX",
            "ChkTeX not installed.",
            Severity.WARNING,
        ),
        Rule(
            "CHK902",
            "chktex-config-not-found",
            "Reviewer_ChkTeX",
            "Provide config/chktexrc or a packaged ChkTeX configuration.",
        ),
        Rule(
            "CHK903",
            "chktex-command-not-found",
            "Reviewer_ChkTeX",
            "ChkTeX executable not found.",
        ),
        Rule(
            "CHK904",
            "chktex-execution-failed",
            "Reviewer_ChkTeX",
            "Fix the ChkTeX execution failure: {details}",
        ),
    )
)

RULE_INT001 = RULES.get("INT001")
RULE_CAS001 = RULES.get("CAS001")
RULE_UNS001 = RULES.get("UNS001")
RULE_UNS002 = RULES.get("UNS002")
RULE_UNS003 = RULES.get("UNS003")
RULE_REF001 = RULES.get("REF001")
RULE_REF002 = RULES.get("REF002")
RULE_REF003 = RULES.get("REF003")
RULE_FIG001 = RULES.get("FIG001")
RULE_FIG002 = RULES.get("FIG002")
RULE_FIG003 = RULES.get("FIG003")
RULE_FIG004 = RULES.get("FIG004")
RULE_FIG005 = RULES.get("FIG005")
RULE_FIG006 = RULES.get("FIG006")
RULE_FIG007 = RULES.get("FIG007")
RULE_FIG008 = RULES.get("FIG008")
RULE_CHK901 = RULES.get("CHK901")
RULE_CHK902 = RULES.get("CHK902")
RULE_CHK903 = RULES.get("CHK903")
RULE_CHK904 = RULES.get("CHK904")
