Integration
===========

TeXact can be integrated easily into existing workflows.

Pre-commit hook
---------------

Add the following to your ``.pre-commit-config.yaml`` to run TeXact automatically before commits:

.. code-block:: yaml

    repos:
    - repo: https://github.com/Theodor-Lindberg/texact
        rev: v0.1.0
        hooks:
        - id: texact-check

.. tip::

    Place the configuration file in the repository root, or specify its location as an argument. See :doc:`options`.

Continuous integration
----------------------

If you use pre-commit hooks, the best practice is to run the same configuration in CI.
Create ``.github/workflows/texact.yml``:

.. code-block:: yaml

        name: TeXact

        on:
            push:
                branches: [main]
            pull_request:

        permissions:
            contents: read

        jobs:
            texact:
                runs-on: ubuntu-latest

                steps:
                    - uses: actions/checkout@v7

                    - uses: actions/setup-python@v7
                        with:
                            python-version: "3.13"

                    - name: Install pre-commit
                        run: python -m pip install pre-commit

                    - name: Run TeXact
                        run: pre-commit run texact --all-files


TeXstudio
---------

TeXact can be invoked from TeXstudio and have it's output in the messages log.

In Options->Configure TeXstudio...->Build, add a user command.
Set the name to ``texact:texact`` and let it execute ``texact --no-chktex --html-style ?ame``.
Press OK to save the settings.

TeXact can now be invoked on the current file under Tools->User->texact.
