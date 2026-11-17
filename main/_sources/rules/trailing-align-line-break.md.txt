# trailing-align-line-break (MAT011)

## What it does

Warns when the final row in an `align` or `align*` environment ends with
`\\`, including its starred or optional-spacing forms.

## Why is this bad?

A trailing line break can introduce an unwanted empty row or extra vertical
space. Line breaks between rows are still needed.

## Example

```latex
% Avoid the final line break:
\begin{align}
  a &= b \\
  c &= d \\
\end{align}

% End the final row without a line break:
\begin{align}
  a &= b \\
  c &= d
\end{align}
```
