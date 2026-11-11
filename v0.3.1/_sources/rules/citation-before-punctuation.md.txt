# citation-before-punctuation (REF006)

## What it does

Checks that `\cite{...}` comes before sentence punctuation, including when
spaces or a hard space (`~`) separate the punctuation from the citation.

## Why is this bad?

Putting the citation after punctuation makes it appear detached from the text
it documents.

## Example

```latex
This is a sentence.~\cite{reference}
This is a sentence\cite{reference}.
```
