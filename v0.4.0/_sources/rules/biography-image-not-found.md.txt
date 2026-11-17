# biography-image-not-found (FIG007)

## What it does

Checks that an image referenced by an `IEEEbiography` environment exists
relative to the TeX source file.

## Why is this bad?

A missing biography image prevents the document from compiling.

## Example

```latex
\begin{IEEEbiography}{Author}
\includegraphics{images/author.png}
\end{IEEEbiography}
```
