Options
=======


Inline suppressions
---------------------

To make TeXact ignore certain lines add the following as a LaTeX comment in your source file:

.. code-block:: tex

    % texact *


To ignore specific rules only on the current line, list their codes using
repeated ``texact`` markers:

.. code-block:: tex

    \begin{figure}[x] % texact FIG001 texact CAS001


The ignore the rest of the file, use:

.. code-block:: tex

    % texact-file ##


Quiet output
------------

Use ``-q`` or ``--quiet`` to remove per-file summaries. Repeat the short
option as ``-qq`` to remove both summaries and title lines.


Rule selection
--------------

Enable a disabled rule with ``--select``. Repeat the option to select multiple
rules::

    texact --select MAT004 --select UNS007 paper.tex


Configuration file
------------------

TeXact can load optional settings from a TOML file. It searches the current
directory in this order and stops at the first TeXact configuration it finds:

1. ``.texact.toml``
2. ``texact.toml``
3. ``pyproject.toml`` under ``[tool.texact]``

Use ``--config PATH`` to select a configuration file explicitly. An explicit
file takes precedence over automatic discovery. Command-line options take
precedence over values loaded from TOML.

The supported structure is::

    [lint]
    ignore = ["FIG002", "UNS001"]
    select = ["MAT004"]
    casing = ["LaTeX"]
    we_count = 7

    [format]
    html-style = true
    vscode-style = true
    quiet = 2

    [tools]
    chktex_path = "/usr/bin"

``lint.ignore`` accepts rule codes to suppress. ``lint.casing`` adds
spellings to the built-in casing list. ``lint.select`` enables rules that are
disabled by default. ``lint.we_count`` changes the maximum allowed number of
``we`` occurrences. ``format.html-style`` enables HTML
output by default. ``format.quiet`` controls non-diagnostic output: ``0``
prints titles and summaries, ``1`` removes summaries, and ``2`` removes both
titles and summaries. ``format.vscode-style`` enables VS Code-compatible
diagnostic output. ``tools.chktex_path`` points to a ChkTeX executable or
directory.

When no configuration file exists, TeXact uses its normal built-in defaults.
