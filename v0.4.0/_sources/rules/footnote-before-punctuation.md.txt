# Footnote placement (REF013)

## What it does

Checks that `\footnote{...}` appears after punctuation and without a preceding
space, line break, or `~`, including when the command has an optional mark argument.
Footnotes within a sentence do not need punctuation.

## Why is this bad?

Footnote markers are conventionally placed immediately after punctuation.

## Example

```latex
This is a sentence\footnote{Note}.
This is a sentence. \footnote{Note}
This is a sentence.\footnote{Note}
```
