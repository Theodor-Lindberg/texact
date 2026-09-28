# matching-delimiters (MAT006)

## What it does

Checks that square brackets, parentheses, and braces are opened and closed in
matching pairs throughout the LaTeX document.

## Why is this bad?

Mismatched or unclosed delimiters can break LaTeX parsing or change the
structure of the document and its mathematical expressions.

## Example

```latex
[x + (y)]
[x + (y]
```
