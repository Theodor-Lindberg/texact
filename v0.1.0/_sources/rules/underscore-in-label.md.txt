# underscore-in-label (REF001)

## What it does

Reports LaTeX labels whose names contain underscores.

## Why is this bad?

It is not per se but it avoids warnings from ChkTeX reporting false positives.
It is also good to be consistent.

## Example

```latex
\label{fig_system_overview}
```
