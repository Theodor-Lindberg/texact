# dash-length (UNS007)

## What it does

Checks dash runs in compact words such as number ranges and compounds.

## Why is this bad?

LaTeX uses `-`, `--`, and `---` for hyphens, en dashes, and em dashes.
Number ranges should use `--`; between words, `--` is ambiguous and needs a
manual choice. Coordinate names such as `Newton--Raphson` are allowed.

## Example

```latex
See pages 5-10 for the proof.
A well--known result.
The value -4 has the incorrect sign for minus.
```

The first line should use `5--10`. The second needs either a hyphen or an em
dash, depending on the intended meaning. For a negative number in text, use
math mode, such as `$-$ 4`.
