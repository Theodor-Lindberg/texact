# missing-figure-label (FIG003)

## What it does

Reports a figure containing graphics but no `\label{...}` command.

## Why is this bad?

Without a label, the figure cannot be referenced reliably from the surrounding
text.

## Example

```latex
\begin{figure}
\includegraphics{architecture.png}
\caption{System architecture.}
\end{figure}
```
