# scaled-figure-image (FIG002)

## What it does

Reports `\includegraphics` commands inside figures that specify `scale`,
`width`, or `height` options.

## Why is this bad?

Scaling can make figures look distorted.
Also, many article templates recommends using a specific font size inside figures.

## Example

```latex
\includegraphics[width=0.8\textwidth]{architecture.png}
```
