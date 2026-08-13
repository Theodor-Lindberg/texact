Integration
===========

TeXact can be integrated easily into existing workflows.

Pre-commit hook
---------------

Add the following to your ``.pre-commit-config.yaml`` to run TeXact automatically before commits:

.. code-block:: yaml

    repos:
    - repo: https://github.com/Theodor-Lindberg/TeXact
        rev: main
        hooks:
        - id: texact-check

To avoid running ChkTeX, add the additional flag:

.. code-block:: yaml

    repos:
    - repo: https://github.com/Theodor-Lindberg/TeXact
        rev: main
        hooks:
        - id: texact-check
        args: [--no-chktex]

Continuous integration
---------------------

TeXstudio
---------

TeXact can be invoked from TeXstudio and have it's output in the messages log.

In Options->Configure TeXstudio...->Build, add a user command.
Set the name to ``texact:texact`` and let it execute ``texact --no-chktex --html-style ?ame``.
If you have chktex installed, you can remove ``--no-chktex``.
Press OK to save the settings.

TeXact can now be invoked on the current file under Tools->User->texact.
