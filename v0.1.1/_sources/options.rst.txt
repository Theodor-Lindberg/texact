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
    casing = ["LaTeX"]
    we_count = 7

    [format]
    html-style = true

    [tools]
    chktex_path = "/usr/bin"

``lint.ignore`` accepts rule codes to suppress. ``lint.casing`` adds
spellings to the built-in casing list. ``lint.we_count`` changes the maximum
allowed number of ``we`` occurrences. ``format.html-style`` enables HTML
output by default, and ``tools.chktex_path`` points to a ChkTeX executable
or directory.

When no configuration file exists, TeXact uses its normal built-in defaults.
