# capitalize-reference-type (REF010)

## What it does

Checks that `table`, `section`, `figure`, `fig.`, `figs.`, `tables`, and
`listing` are capitalized when followed by `~\ref`.

## Why is this bad?

Capitalizing these reference types keeps cross-references consistent and easy
to identify in the text.

## Example

```latex
See table~\ref{tab:results}.
See Table~\ref{tab:results}.
```
