.. TeXact documentation master file

Welcome to TeXact's documentation!
==================================

TeXact is a tool for finding miscellaneous mistakes in LaTeX code and article writing.
It does not edit your files, so you can run it fearlessly.



A live demo of TeXact can be found in the `Try it here <try-it.html>`_ section.

The repository can be found at `GitHub <https://github.com/Theodor-Lindberg/texact>`_. Reporting any issues or suggestions there is appreciated. Contributions are also welcome!

Installation
------------

The latest released version of TeXact can be installed using pip or conda

.. admonition:: Install TeXact from PyPi

    .. code-block:: console

        $ pip install texact

.. admonition:: Install TeXact from conda-forge

    .. code-block:: console

        $ conda install conda-forge::texact

For the development version, see :doc:`development`.

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
        How to use TeXact in pre-commit, TeXstudio, and more.

    :doc:`options`
        Available options and how to configure TeXact.

Platforms
---------

The plan is to support the major platforms (macOS, Linux, and Windows) and
Python versions that are still receiving active or security support.
For details on Python version support lifecycles, see
`Python End of Life <https://endoflife.date/python>`_.

.. toctree::
    :maxdepth: 1
    :hidden:

    try-it
    options
    rules/index
    integration
    development
    changelog
    licenses

.. image:: _static/texactlogo.svg
   :scale: 500%
