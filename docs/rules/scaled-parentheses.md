# scaled-parentheses (MAT004)

## What it does

Checks that parentheses in math mode use `\left` and `\right`.

## Why is this bad?

Fixed-size parentheses can be too small for the expression they enclose and
make mathematical expressions harder to read.

## Example

```latex
$(x + 1)$
$\left(x + 1\right)$
```
