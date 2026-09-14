# label-prefix (REF004)

## What it does

Reports labels whose prefixes do not match the LaTeX structure they belong to.
Figure labels should start with `fig:`, equation labels with `eq:`, section
labels with `sec:`, and table labels with `tab:`.

## Why is this bad?

Inconsistent label prefixes make references more difficult to
understand and labels harder to find.

## Example

```latex
\begin{figure}
  \caption{System overview}
  \label{system-overview}
\end{figure}
```
