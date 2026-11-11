# invalid-figure-position (FIG001)

## What it does

Checks optional LaTeX figure placement arguments and permits only the empty
argument or `[bt]`, `[t]`, `[b]`, and `[tb]`.

## Why is this bad?

Forcing the placement of a figure makes the spacing look wrong.
If the figure must be moved, in the can be moved by changing the location
of the source code.

## Example

```latex
\begin{figure}[h]
```
