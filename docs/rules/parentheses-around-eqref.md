# parentheses-around-eqref (REF009)

## What it does

Warns when ordinary parentheses are placed around an `\eqref` command.

## Why is this bad?

The `\eqref` command adds parentheses around the equation number automatically.
Wrapping the command in another pair produces redundant parentheses.

## Example

```latex
(\eqref{eq:energy})
\eqref{eq:energy}
```
