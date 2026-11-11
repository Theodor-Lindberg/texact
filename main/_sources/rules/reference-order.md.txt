# reference-order (REF014)

## What it does

Checks adjacent `\ref` and `\eqref` references in a list against the source
order of their definitions. Only labels with a known matching context, such as
two tables or two figures, are compared. Undefined labels are skipped.

## Why is this bad?

References listed out of order can be confusing, such as Tables 1, 3, and 2.

## Example

```latex
% When the tables are defined in the order first, second, third:
Tables~\ref{tab:first}, \ref{tab:third}, and~\ref{tab:second}.
Tables~\ref{tab:first}, \ref{tab:second}, and~\ref{tab:third}.
```

The check uses source order as an approximation of numbering; custom counters,
included files, and labels outside recognized contexts are not resolved.
