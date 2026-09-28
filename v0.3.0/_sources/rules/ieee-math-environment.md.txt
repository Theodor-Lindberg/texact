# ieee-math-environment (MAT005)

## What it does

Checks that IEEE papers use `IEEEeqnarray` instead of `align`, `split`, or
similar alignment environments.

## Why is this bad?

The IEEE template provides a dedicated command for multi-line equations,
`IEEEeqnarray`.

## Example

```latex
\begin{align}
  a &= b
\end{align}

\begin{IEEEeqnarray}{rCl}
  a & = & b
\end{IEEEeqnarray}
```
