# eqref-non-equation-label (REF012)

## What it does

Checks that `\eqref` is used only with equation labels. It flags labels with
the `fig:`, `tab:`, or `sec:` prefixes.

## Why is this bad?

`\eqref` adds parentheses around the referenced number, which is intended for
equations rather than figures, tables, or sections.

## Example

```latex
\eqref{fig:plot}
\ref{fig:plot}
```
