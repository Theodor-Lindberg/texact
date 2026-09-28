# space-before-reference (REF005)

## What it does

Checks that references have a hard space (`~`) before `\ref`.

## Why is this bad?

A normal space can leave a reference number at the beginning of a line. A hard
space keeps the preceding text and reference together.

## Example

```latex
See \ref{fig:example}.
See~\ref{fig:example}.
```
