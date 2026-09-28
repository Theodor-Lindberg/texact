# unreferenced-label (REF003)

## What it does

Reports a label that is defined but never referenced in the scanned source
file.

## Why is this bad?

Unused labels add maintenance noise and can hide a misspelled reference that
was intended to point to the labeled object.

## Example

```latex
\label{fig-architecture}
```
