---
tocdepth: 2
---

# TeXact Rules

Some of these rules can seem like nitpicking, but users are free to disable
them per their liking and, if supported, configure them.

## Inthis (`INT`)

| Code | Name | Message | Severity |
| --- | --- | --- | --- |
| INT001 | [abstract-first-line-this-work](abstract-first-line-this-work.md) | Avoid 'this work' in the first line of the abstract. | error |

## Casing (`CAS`)

| Code | Name | Message | Severity |
| --- | --- | --- | --- |
| CAS001 | [incorrect-casing](incorrect-casing.md) | Incorrect casing. | error |

## Math (`MAT`)

| Code | Name | Message | Severity |
| --- | --- | --- | --- |
| MAT001 | [plus-minus-notation](plus-minus-notation.md) | Use `\pm` instead of `+-` or `-+`. | error |
| MAT002 | [math-operator-command](math-operator-command.md) | Use LaTeX commands for common math operators. | error |
| MAT003 | [textmu-command](textmu-command.md) | Use `\textmu` instead of `\mu`. | error |

## Unsure (`UNS`)

| Code | Name | Message | Severity |
| --- | --- | --- | --- |
| UNS001 | [modal-or-uncertain-word](modal-or-uncertain-word.md) | Avoid modal or uncertain wording. | error |
| UNS002 | [excessive-we-usage](excessive-we-usage.md) | Reduce use of 'we' when it exceeds the configured maximum. | error |
| UNS003 | [singular-author-possessive](singular-author-possessive.md) | Use authors' to author's in papers. | error |
| UNS004 | [space-before-punctuation](space-before-punctuation.md) | Avoid spaces before punctuation. | error |

## RefLabel (`REF`)

| Code | Name | Message | Severity |
| --- | --- | --- | --- |
| REF001 | [underscore-in-label](underscore-in-label.md) | Use hyphens in label names. | error |
| REF002 | [undefined-label-reference](undefined-label-reference.md) | Undefined label. | error |
| REF003 | [unreferenced-label](unreferenced-label.md) | Unreferenced label. | error |
| REF004 | [label-prefix](label-prefix.md) | Use the matching prefix for the label context. | error |
| REF005 | [space-before-reference](space-before-reference.md) | Use a hard space (`~`) before `\ref`. | error |

## Figure (`FIG`)

| Code | Name | Message | Severity |
| --- | --- | --- | --- |
| FIG001 | [invalid-figure-position](invalid-figure-position.md) | Use an empty figure position or one of `[bt]`, `[t]`, `[b]`, `[tb]`. | error |
| FIG002 | [scaled-figure-image](scaled-figure-image.md) | Avoid scaling figure images. | error |
| FIG003 | [missing-figure-label](missing-figure-label.md) | Add a `\label{...}` to the figure. | error |
| FIG004 | [missing-figure-caption](missing-figure-caption.md) | Add a `\caption{...}` to the figure. | error |
| FIG005 | [caption-before-graphics](caption-before-graphics.md) | Place the figure caption below the graphics. | error |
| FIG006 | [inconsistent-caption-period](inconsistent-caption-period.md) | Use one consistent period style for all figure captions. | error |
| FIG007 | [biography-image-not-found](biography-image-not-found.md) | Add the IEEEbiography image relative to the TeX file. | error |
| FIG008 | [invalid-biography-image-ratio](invalid-biography-image-ratio.md) | Use an IEEEbiography image with a height/width ratio of 1.25. | error |

## ChkTeX (`CHK`)

`CHK001` through `CHK899` are reserved for native ChkTeX diagnostics with
native numbers 1 through 899. Native numbers at or above 900 are mapped into
a disjoint numeric range beginning at `CHK1900`. Their metadata and message
come from ChkTeX, and they link to the shared
[chktex-diagnostic](chktex-diagnostic.md) page.

| Code | Name | Message | Severity |
| --- | --- | --- | --- |
| CHK901 | [chktex-not-installed](chktex-not-installed.md) | ChkTeX not installed. | warning |
| CHK902 | [chktex-config-not-found](chktex-config-not-found.md) | Provide `config/chktexrc` or a packaged ChkTeX configuration. | error |
| CHK903 | [chktex-command-not-found](chktex-command-not-found.md) | Make the ChkTeX executable available on `PATH`. | error |
| CHK904 | [chktex-execution-failed](chktex-execution-failed.md) | Fix the ChkTeX execution failure. | error |

```{toctree}
:maxdepth: 1
:hidden:

abstract-first-line-this-work
incorrect-casing
plus-minus-notation
math-operator-command
textmu-command
modal-or-uncertain-word
excessive-we-usage
singular-author-possessive
space-before-punctuation
underscore-in-label
undefined-label-reference
unreferenced-label
label-prefix
space-before-reference
invalid-figure-position
scaled-figure-image
missing-figure-label
missing-figure-caption
caption-before-graphics
inconsistent-caption-period
biography-image-not-found
invalid-biography-image-ratio
chktex-not-installed
chktex-config-not-found
chktex-command-not-found
chktex-execution-failed
chktex-diagnostic
```
