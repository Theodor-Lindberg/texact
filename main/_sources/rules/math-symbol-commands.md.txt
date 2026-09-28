# math-symbol-commands (MAT001)

## What it does

Checks for `+-` and `-+` notation, and plain-text assignment, comparison, and
arrow symbols in mathematical expressions that have corresponding LaTeX
commands.

## Why is this bad?

LaTeX commands produce consistent mathematical symbols and avoid ambiguous
sequences of text characters.

## Example

| Instead of | Use |
| --- | --- |
| `+-` or `-+` | `\pm` |
| `:=` | `\coloneqq` |
| `>=` | `\geq` |
| `<=` | `\leq` |
| `<<` | `\ll` |
| `>>` | `\gg` |
| `->` | `\rightarrow` |
| `<-` | `\leftarrow` |
| `<=>` | `\Leftrightarrow` |
