# braced-math-scripts (MAT009)

## What it does

Warns when a multi-character subscript or superscript is not enclosed in
braces. This warning is disabled by default. Enable it with `--select MAT009`
or add `MAT009` to `lint.select` in the TeXact configuration.

## Why is this bad?

In LaTeX, an unbraced script applies only to the next token. For example,
`x^23` applies `2` as the superscript and leaves `3` on the baseline. Braces
make the intended multi-character script explicit.

## Example

```latex
x^23 + y_ij
x^{23} + y_{ij}
```
