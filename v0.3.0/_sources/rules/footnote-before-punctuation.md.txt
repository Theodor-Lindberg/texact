# footnote-before-punctuation (REF013)

## What it does

Checks that `\footnote{...}` appears before punctuation, including when the
command has an optional mark argument.

## Why is this bad?

Placing the footnote after sentence punctuation can make the marker look
detached from the text it annotates.

## Example

```latex
This is a sentence\footnote{Note}.
This is a sentence.\footnote{Note}
```
