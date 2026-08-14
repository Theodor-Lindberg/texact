.. TeXact documentation master file

TeXact's documentation
==================================

TeXact is a tool for finding miscellaneous mistakes in LaTeX code and article writing.

The repository can be found at `GitHub <https://github.com/Theodor-Lindberg/texact>`_. Please
report any issues or suggestions there. Contributions are also welcome.

Installation
------------

TeXact can be installed using pip, either directly from git or after cloning the repository.

.. admonition:: Install TeXact from git

    .. code-block:: console

        $ pip install "git+ssh://git@github.com/Theodor-Lindberg/texact.git"

.. admonition:: Install TeXact after cloning

    .. code-block:: console

        $ pip install .

If Texact has already been installed, chances are a cached version will be used instead of the latest from Git.
To be sure the latest is installed, to the following:

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

.. toctree::
   :maxdepth: 1
   :caption: Contents:

   options
   rules/index
   integration
   development
   licenses



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. image:: _static/texactlogo.svg
   :scale: 500%
