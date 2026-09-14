# caption-before-graphics (FIG005)

## What it does

Reports figures whose caption appears before the graphics command.

## Why is this bad?

The document templates supported by TeXact expect the visual content before
its caption.

## Example

```latex
\caption{System architecture.}
\includegraphics{architecture.png}
```
