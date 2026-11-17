# heading-order (SEC001)

## What it does

Checks that section headings do not skip a level.

## Example

```latex
\section{Methods}
\subsection{Setup}
\subsubsection{Details}
```

A `\subsubsection` should not appear directly under a `\section`; add the
missing `\subsection` first.
