# chktex-execution-failed (CHK904)

## What it does

Reports a ChkTeX invocation that failed without producing a parseable
diagnostic.

## Why is this bad?

A failed external check leaves the document review incomplete and should be
fixed or explicitly disabled.

## Example

```text
ChkTeX execution failed
```
