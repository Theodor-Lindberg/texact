# citation-before-period (REF006)

## What it does

Checks that a `\cite{...}` tag comes before the period that ends a sentence.

## Why is this bad?

Putting the citation after the period makes it appear detached from the
sentence it documents.

## Example

```latex
This is a sentence.\cite{reference}
This is a sentence\cite{reference}.
```
