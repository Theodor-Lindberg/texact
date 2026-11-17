Development
===========

Installation
------------

The latest development version can be installed using pip,
either directly from Git or after cloning the repository.

.. admonition:: Install TeXact from Git

    .. code-block:: console

        $ pip install "git+ssh://git@github.com/Theodor-Lindberg/texact.git"

.. admonition:: Install TeXact after cloning the repository

    .. code-block:: console

        $ pip install .

If TeXact has already been installed from Git via pip, chances are a cached
version will be used instead of the latest. To be sure the latest is installed,
do the following:

.. admonition:: Install TeXact from git, avoiding caches

    .. code-block:: console

        $ pip install --force-reinstall --no-cache-dir "git+ssh://git@github.com/Theodor-Lindberg/texact.git"

Local development
-----------------

Install the project in editable mode, along with the tools used
below:

.. code-block:: console

    $ python -m pip install -e ".[docs,dev]"

Editable installation makes the ``texact`` command available for CLI tests
while picking up source changes. The ``docs`` extra installs Sphinx, the
documentation extensions and theme, and pre-commit. The ``dev`` extra installs
pytest and pre-commit.

Building the documentation
--------------------------

From the repository root, build the current working tree as HTML:

.. code-block:: console

    $ python -m sphinx -b html docs docs/_build/html

Open ``docs/_build/html/index.html`` in a browser. Alternatively, run
``make html`` from ``docs/``. Generated files under ``docs/_build/`` are not
documentation sources and should not be committed.

The documentation CI builds versioned documentation with ``make multiversion``
from ``docs/``. It selects compatible Git tags and branches, so its output is
based on Git refs rather than uncommitted changes. A full checkout with tags
is needed to reproduce the versioned build.

Running tests
-------------

From the repository root, run the regression suite as:

.. code-block:: console

    $ python -m pytest -q test

Installing pre-commit checks
----------------------------

After installing the development dependencies, install the Git hook from the
repository root:

.. code-block:: console

    $ python -m pre_commit install

The hook runs the configured checks on staged files when committing. Some
checks may modify files; review and stage those changes before committing again.

CI also tests TeXact's published hook from the checked-out Git commit. To run
that integration test locally, commit the hook changes first, then run:

.. code-block:: console

    $ python -m pytest -q test/pre_commit_hook.py

Code structure
--------------

The tool is implemented as a set of reviewers, each with its own
focus. The reviewers keep track of their comments as the LaTeX file is
processed line by line.
Once the entire file has passed, all diagnostics are printed to the
console, referencing line numbers.
A summary is also outputted at the end.
As the reviewers are independent of one another, adding new ones
does not break existing features.

Reviewer implementations are located in ``source/reviewers/``. All inherit
from the base class in ``source/reviewers/reviewer.py``, and a central
rule registry is in ``source/reviewers/rules.py``.

Rule identity
-------------

Every diagnostic refers to one immutable ``Rule`` in the central registry.
The registry contains the error code, name, message template, severity,
and documentation path. A ``Diagnostic`` adds the context for one
occurrence: source filename, line, and the rendered message.

Reviewer prefixes:

* ``Reviewer_Inthis`` uses ``INT``.
* ``Reviewer_Casing`` uses ``CAS``.
* ``Reviewer_Unsure`` uses ``UNS``.
* ``Reviewer_RefLabel`` uses ``REF``.
* ``Reviewer_Figure`` uses ``FIG``.
* ``Reviewer_ChkTeX`` uses ``CHK``.

Each reviewer owns the numeric suffixes in its prefix. For example,
``CAS001`` is the casing rule and ``FIG003`` is the missing-figure-label
rule. Native ChkTeX diagnostics use ``CHK001`` through ``CHK899`` with the
Native ChkTeX diagnostics use ``CHK001`` through ``CHK899`` with the
native ChkTeX number preserved. Native numbers at or above 900 are shifted
into a disjoint range. TeXact's ChkTeX lifecycle rules use ``CHK901`` through
``CHK904`` so the two sources cannot collide.

Rule documentation is indexed at ``docs/rules/index.md``. Each TeXact rule
has its own Markdown page under ``docs/rules/`` with sections for what it
detects, why the issue matters, and a LaTeX example. When adding a rule, add
its registry entry, use the returned named rule handle when creating
diagnostics, add its dedicated page to the hidden rule toctree, and add tests.
Never reuse a published code.

Adding features
---------------

All reviewers inherit from the same base class, *Reviewer*, and
implement a set of methods: ``process_line``, ``get_comments``,
``get_summary``, ``get_status``, and ``get_name``. ``get_comments``
returns ``Diagnostic`` objects linked to registry ``Rule`` objects.

Use a named ``Rule`` handle from ``source/reviewers/rules.py`` and
call its ``render_message`` method for dynamic values. Add a test that checks
the registry metadata, the diagnostic location, and the rendered code in CLI
output.
Adding a feature involves either modifying an existing reviewer
or adding a new one.
The easiest way to get started is by studying one of the existing
classes, e.g. ``Reviewer_Unsure``. The main file, ``texact``, must be
updated to include any new reviewer.
Options to the command-line interface and the parsing of the configuration
file can be added as well.
