# TeXact

[![PyPI Version](https://img.shields.io/pypi/v/texact)](https://pypi.org/project/texact/)
[![Conda Version](https://img.shields.io/conda/v/conda-forge/texact)](https://anaconda.org/conda-forge/texact)
[![License](https://img.shields.io/github/license/Theodor-Lindberg/texact)](LICENSE.txt)

TeXact is a tool for finding miscellaneous mistakes in LaTeX code
and article writing.
It does not edit your files, so you can run it fearlessly.
It is also not intended to replace existing tools, such as
[ChkTeX](https://www.nongnu.org/chktex/) and
[lacheck](https://linux.die.net/man/1/lacheck), but rather to
complement and incorporate them.

## Documentation

[https://theodor-lindberg.github.io/texact/](https://theodor-lindberg.github.io/texact/)

## Features

* Check consistency between "\ref" and "\label".
* Make sure certain words have correct casing.
* Warn if the abstract begins with "In this work" or similar.
* Avoid certain modal verbs, such as should, would, could, and might.
* Run [ChkTeX](https://www.nongnu.org/chktex/), if installed, with "appropriate"
settings.
* And more...

## Quickstart

Install TeXact using pip

```bash
pip install texact
```

or conda

```bash
conda install conda-forge::texact
```

then run as

```bash
texact path/to/file.tex
```

For more information, run

```bash
texact -h
```
