# textmu-command (MAT003)

## What it does

Checks that the Greek letter mu uses the `\textmu` command instead of `\mu`.

## Why is this bad?

The text mu symbol is preferred for units and other quantities that represent
the micro prefix.

## Example

```latex
$10\mu\mathrm{m}$
$10\textmu\mathrm{m}$
```
