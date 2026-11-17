# braced-square-root (MAT010)

## What it does

Warns when a square-root argument is not enclosed in braces, including roots
with an optional index.

## Why is this bad?

Braces make the extent of the radicand explicit and avoid ambiguity when the
expression changes.

## Example

```latex
\sqrt x
\sqrt{x}
\sqrt[3]y
\sqrt[3]{y}
```
