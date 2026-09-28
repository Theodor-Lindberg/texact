# double-period-sentence (UNS005)

## What it does

Checks for consecutive periods in prose, excluding ellipses and relative paths.

## Why is this bad?

Two consecutive periods can accidentally leave a sentence or abbreviation with
incorrect punctuation.

## Example

```latex
This sentence ends with two periods..
The list includes apples, etc.., and pears.
\includegraphics{../assets/image.png}
This uses an ellipsis... correctly.
```
