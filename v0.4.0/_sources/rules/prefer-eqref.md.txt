# prefer-eqref (REF008)

## What it does

Checks that equation labels are referenced with `\eqref` instead of `\ref`.
This rule is disabled by default. Enable it with `--select REF008` or add
`REF008` to `lint.select` in the TeXact configuration.

## Why is this bad?

The `\ref` command sometimes does not always resolve correctly for equations.

## Example

```latex
See (\ref{eq:energy}).
See \eqref{eq:energy}.
```
