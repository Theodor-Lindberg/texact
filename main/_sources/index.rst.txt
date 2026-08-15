.. TeXact documentation master file

Welcome to TeXact's documentation!
==================================

TeXact is a tool for finding miscellaneous mistakes in LaTeX code and article writing.
A live demo of TeXact can be found in the `Try it here <try-it.html>`_ section.

The repository can be found at `GitHub <https://github.com/Theodor-Lindberg/texact>`_. Reporting any issues or suggestions there is appreciated. Contributions are also welcome.

Installation
------------

The latest released version of TeXact can be installed using pip or conda

.. admonition:: Install TeXact from PyPi

    .. code-block:: console

        $ pip install texact

.. admonition:: Install TeXact from conda-forge

    .. code-block:: console

        $ conda install conda-forge::texact

The latest development version can be installed using pip,
either directly from Git or after cloning the repository.

.. admonition:: Install TeXact from Git

    .. code-block:: console

        $ pip install "git+ssh://git@github.com/Theodor-Lindberg/texact.git"

.. admonition:: Install TeXact after cloning the repository

    .. code-block:: console

        $ pip install .

If TeXact has already been installed via pip Git, chances are a cached version will be used instead of the latest.
To be sure the latest is installed, do the following:

.. admonition:: Install TeXact from git, avoiding caches

    .. code-block:: console

         $ pip install --force-reinstall --no-cache-dir "git+ssh://git@github.com/Theodor-Lindberg/texact.git"



Usage
-----

After installing, run TeXact from the command line:

.. code-block:: console

   $ texact path/to/file.tex

For more information, run

.. code-block:: console

   $ texact -h

.. seealso::

    :doc:`integration`
        Information on how to use TeXact in pre-commit, TeXstudio, and more.

.. seealso::

    :doc:`options`
        Information on the available options and how to configure TeXact.

Platforms
---------

The plan is to support the major platforms (macOS, Linux, and Windows) and
Python versions that are still receiving active or security support.
For details on Python version support lifecycles, see
`Python End of Life <https://endoflife.date/python>`_.

.. toctree::
    :maxdepth: 1

    try-it
    options
    rules/index
    integration
    development
    changelog
    licenses

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. image:: _static/texactlogo.svg
   :scale: 500%
