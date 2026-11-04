# space-before-citation (REF011)

## What it does

Checks that documents using `\cite` load the `cite` package with the
`nobreak` option.

## Why is this bad?

A hard space keeps the citation attached to the preceding word and prevents a
The `nobreak` option prevents a line break before a citation without requiring
each citation to use a hard space.

## Example

```latex
\usepackage{cite}
See~\cite{source}.

\usepackage[nobreak]{cite}
See\cite{source}.
```
