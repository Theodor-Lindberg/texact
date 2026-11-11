# math-operator-command (MAT002)

## What it does

Checks that common mathematical operators use their LaTeX commands, such as
`\max`, `\min`, `\log`, and `\sin`.

## Why is this bad?

Unescaped operator names are typeset as products of variables instead of as
mathematical operators.

## Example

```latex
$max(x) = log(x)$
$\max(x) = \log(x)$
```
