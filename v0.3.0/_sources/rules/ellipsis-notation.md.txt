# ellipsis-notation (MAT007)

## What it does

Checks for three periods used as an ellipsis in normal text or math mode.

## Why is this bad?

Use `\dots` in normal text. In math mode, use `\ldots` for baseline ellipses
in comma lists and `\cdots` for centered ellipses in operator chains.

## Example

```latex
Text \dots continues.
$x_1, \ldots, x_n$
$A_1 + \cdots + A_n$
```
