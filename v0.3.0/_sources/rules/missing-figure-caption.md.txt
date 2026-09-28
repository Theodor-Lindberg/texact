# missing-figure-caption (FIG004)

## What it does

Reports a figure containing graphics but no `\caption{...}` command.

## Why is this bad?

Every figure should have a caption.
Having a title in the figure does not replace the caption, rather the opposite.

## Example

```latex
\begin{figure}
\includegraphics{architecture.png}
\label{fig-architecture}
\end{figure}
```
