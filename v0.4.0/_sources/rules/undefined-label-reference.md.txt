# undefined-label-reference (REF002)

## What it does

Reports a `\ref{...}` whose label is not defined anywhere in the scanned
source file.

## Why is this bad?

The document will not compile correctly.

## Example

```latex
See Figure~\ref{fig-architecture}.
```
