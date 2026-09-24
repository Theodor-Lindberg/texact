# label-before-caption (REF007)

## What it does

Warns when a label appears before the caption or first numbered list item it
should refer to.

## Why is this bad?

LaTeX may save the previous counter value, so a reference can show the wrong
number. Put the label after the caption or item.

## Example

```latex
\begin{figure}
  \label{fig:plot}
  \caption{A plot.}
\end{figure}
```
