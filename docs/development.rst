Development
===========

Code structure
--------------

The tool is implemented as a set of reviewers, each with its own
focus. The reviewers keep track of their comments as the LaTeX file is
processed line by line.
Once the entire file has passed, all diagnostics are printed to the
console, referencing the line number.
A summary is also outputted at the end.
As the reviewers are independent of one another, adding new ones
does not break existing features.

Reviewer implementations live in ``source/reviewers/``. The shared
reviewer contract is in ``source/reviewers/reviewer.py`` and the central
rule registry is in ``source/reviewers/rules.py``.

Rule identity
-------------

Every diagnostic refers to one immutable ``Rule`` in the central registry.
The registry owns the stable code, kebab-case name, canonical message
template, severity, and documentation path. A ``Diagnostic`` adds the
context for one occurrence: source filename, line, and the rendered message.

The command-line output follows this general shape::

	path/to/file.tex:12:4: error: CAS001 incorrect-casing: Use the canonical casing for this technical term. [docs: docs/rules/incorrect-casing.md]

The default documentation link is repository-relative. Pass
``--docs-base-url`` to generate links to a documentation website, for
example ``https://example.org/texact/rules/incorrect-casing.html``.

Reviewer prefixes and rule ranges are stable:

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
Command-line arguments can be added as well, if necessary.
