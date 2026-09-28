# space-before-citation (REF011)

## What it does

Checks that a hard space (`~`) precedes each `\cite` command. This rule is
disabled by default. Enable it with `--select REF011` or add `REF011` to
`lint.select` in the TeXact configuration.

## Why is this bad?

A hard space keeps the citation attached to the preceding word and prevents a
line break before the citation.

## Example

```latex
See \cite{source}.
See~\cite{source}.
```
