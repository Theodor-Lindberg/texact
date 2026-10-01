---
name: texact
description: 'Use when working on TeXact, the Python CLI for reviewing LaTeX documents: adding or fixing reviewers, rule codes, math or reference checks, template-specific behavior, diagnostics, tests, documentation, packaging, or the CLI.'
user-invocable: true
---

# TeXact Repository Guide

## What TeXact Is

TeXact is a Python command-line tool that reviews LaTeX source files. It
reports diagnostics but does not edit the input document. It complements
ChkTeX and lacheck with project-specific writing, LaTeX, math, figure, label,
and template checks. Read `pyproject.toml` for the current Python requirement
and packaging configuration.

The CLI is installed as `texact` and implemented by `source/texact.py`.

## Repository Map

- `source/texact.py`: CLI parsing, template detection, reviewer construction,
  file processing, inline-ignore handling, diagnostic filtering, and output.
- `source/reviewers/reviewer.py`: abstract reviewer interface plus `Diagnostic`,
  `Status`, and shared severity behavior.
- `source/reviewers/`: concrete reviewer implementations. Discover current
  reviewer classes here and check `source/texact.py` to see which are active.
- `source/reviewers/rules.py`: `Rule` metadata, `RuleRegistry`, all built-in
  rule definitions, and exported `RULE_*` constants. This is the source of
  truth for rule codes and messages.
- `source/template_check.py`: detects `Template.IEEE`, `Template.LLNCS`, or
  `Template.UNKNOWN` from `\\documentclass`.
- `source/configuration.py`: TOML configuration discovery and validation.
- `source/printer.py`: terminal, HTML, and VS Code diagnostic formatting.
- `source/texact_config/chktexrc`: packaged ChkTeX configuration.
- `test/diagnostics_test.py`: focused unit tests for reviewers, rules, and
  diagnostic behavior.
- `test/test.py`: CLI smoke tests over the `.tex` fixtures in `test/`.
- `test/*.tex`: LaTeX fixtures used by CLI smoke tests.
- `docs/rules/`: one Markdown page per built-in rule.
- `docs/rules/index.md`: rule table and hidden documentation toctree.
- `docs/conf.py`, `docs/Makefile`, and `docs/_templates/`: Sphinx docs and
  versioned documentation presentation.
- `CHANGELOG.md`: Keep a Changelog-style Unreleased and release history.
- `pyproject.toml`: packaging, entry point, dependencies, pytest path, and
  optional docs dependencies.

`build/` and `source/texact.egg-info/` are generated/package artifacts. Prefer
editing `source/`, `docs/`, `test/`, `CHANGELOG.md`, and `pyproject.toml`, not
copies under `build/` or generated metadata.

## Runtime Flow

1. `main()` parses CLI options and loads configuration.
2. `get_template()` identifies the document template.
3. `main()` constructs the reviewer tuple. A reviewer is not active unless it
   is instantiated here, except for ChkTeX's conditional construction.
4. `process_file()` reads lines, records inline ignores, strips LaTeX comments,
   and calls `process_line(line_no, line)` on every reviewer.
5. Reviewers return `Diagnostic` objects from `get_comments()`.
6. TeXact filters ignored rule codes, attaches the source path, sorts by line
   and rule code, prints diagnostics, and computes the exit status.

`line_no` is zero-based internally. `Diagnostic.line` exposes the one-based
line number users see.

## Rule Source Of Truth

Rule codes, names, ownership, defaults, and messages change as TeXact evolves.
Do not keep a copied rule inventory in this skill. Inspect
`source/reviewers/rules.py` for current metadata and `docs/rules/index.md` for
the documented rule list. Reviewer behavior and tests are authoritative for
what each check actually detects.

## Adding A Reviewer Rule

Use this sequence for a new rule:

1. Find the reviewer that owns the behavior and inspect its current rules in
  `source/reviewers/rules.py`. Choose an unused code consistent with that
  reviewer; the registry validates code and reviewer-number uniqueness.
2. Add the rule metadata and exported constant in `rules.py`, then emit its
  `Diagnostic` from the owning reviewer with the zero-based source line.
3. If the reviewer is new, register it in `source/texact.py`. Pass template
  information only when the behavior is template-specific.
4. Add `docs/rules/<rule-name>.md` with sections for what the rule does, why
  the behavior is undesirable, and examples.
5. Add the rule to the matching table and hidden toctree in
  `docs/rules/index.md`, and add a concise `Unreleased` entry to
  `CHANGELOG.md`.
6. Add focused tests for invalid and valid cases, false-positive boundaries,
  and default/selection behavior when the rule is opt-in.

Rule messages are Python format strings. Escape literal braces as `{{` and
`}}`. Use `Rule.render_message()` at the diagnostic site, and use `Printer`
color helpers for values that should be highlighted.

## Math Reviewer Guidance

Before changing math checks, inspect the current tokenizer, math-mode state,
reviewer implementation, and nearby tests; do not assume a fixed list of
supported delimiters, environments, or rules. Test the relevant inline and
display forms, multiline/environment transitions, prose boundaries, and
already-correct commands. Keep opening and closing token handling consistent.

## Reference And Template Notes

- For label and reference behavior, inspect the current `Reviewer_RefLabel`
  implementation and its rule tests. Read its label-context mapping rather
  than duplicating prefix assumptions here.
- Template detection is based on the first relevant `\\documentclass`.
- IEEE-specific behavior should be gated by `Template.IEEE`; do not apply it
  to LLNCS or unknown templates without an explicit requirement.
- ChkTeX receives the detected template and may have template-specific config
  behavior of its own.
- Comments are stripped by the main processing path before reviewers see them.
  Reviewer-level direct tests should pass already-normalized lines unless the
  reviewer intentionally owns comment handling.

## Validation Workflow

Read `pyproject.toml` and the CI workflow to find the current test, lint, and
documentation commands. Run the narrowest relevant test first, then broaden
validation to the full suite when the change warrants it. For source-tree CLI
tests, use the repository's configured import path or install the local
package if required.

Use `git diff --check` for whitespace validation. Follow current CI for
formatting, linting, packaging, and documentation checks rather than assuming
particular tools or commands. Never treat generated documentation output as
source content.

## Editing Rules

- Make the smallest change that preserves existing public APIs and patterns.
- Never edit generated files under `build/` or `docs/_build/` to fix source
  behavior.
- Do not commit or create branches unless explicitly requested.
- Preserve unrelated user changes in a dirty worktree.
- Prefer ASCII in source and documentation unless the existing file clearly
  requires another character set.
