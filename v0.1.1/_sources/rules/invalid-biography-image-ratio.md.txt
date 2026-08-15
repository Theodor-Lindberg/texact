# invalid-biography-image-ratio (FIG008)

## What it does

Checks that an IEEE biography image has the expected height-to-width ratio of
1.25 within the configured tolerance.

## Why is this bad?

Incorrectly proportioned biography image can produce a visibly stretched portrait.

## Example

```latex
\includegraphics{images/author.png}
```
