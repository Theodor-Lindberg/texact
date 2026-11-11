# chktex-diagnostic (CHK###)

## What it does

Represents a native ChkTeX warning or error emitted by the optional ChkTeX
reviewer. TeXact preserves native numbers below 900 after the `CHK` prefix, so
native code 25 is reported as `CHK025`.

## Why is this bad?

The exact issue depends on the native ChkTeX rule. ChkTeX diagnostics identify
LaTeX constructs that are commonly ambiguous, fragile, or inconsistent, and
should be reviewed in the context of the document. For further motivation,
consult the documentation for ChkTeX.

## Example

```text
CHK025: ChkTeX's native diagnostic message
```
