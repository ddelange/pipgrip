# pipgrip

[![Current Release Version](https://img.shields.io/github/release/ddelange/pipgrip.svg&logo=github)](https://github.com/ddelange/pipgrip/releases/latest)
[![pypi Version](https://img.shields.io/pypi/v/pipgrip.svg&logo=pypi&logoColor=white)](https://pypi.org/project/pipgrip/)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)
[![python](https://img.shields.io/static/v1?label=python&message=3.7%2B&color=informational&logo=python&logoColor=white)](https://github.com/ddelange/pipgrip/releases/latest)
<!-- [![codecov](https://codecov.io/gh/ddelange/pipgrip/branch/master/graph/badge.svg?token=<add_token_here>)](https://codecov.io/gh/ddelange/pipgrip) -->
[![Actions Status](https://github.com/ddelange/pipgrip/workflows/GH/badge.svg)](https://github.com/ddelange/pipgrip/actions)  <!-- use badge.svg?branch=develop to deviate from default branch -->

## Installation

This package is available on [PyPI](https://pypi.org/project/pipgrip/):

```sh
pip install pipgrip
```

## Usage


```sh
pipgrip keras==2.2.2  # cyclic dependencies

# TODO pipgrip --tree .
# think about cyclic
# https://github.com/scele/rules_python/pull/1
```

## Development

Create a virtual environment and get ready to develop:

```sh
make install
```

This [make-command](Makefile) is equivalent to the following steps:

Install pre-commit and other continous integration dependencies in order to make commits and run tests.

```sh
pip install -r requirements/ci.txt
pre-commit install
```

With requirements installed, `make lint` and `make test` can now be run. There is also `make clean`, and `make all` which runs all three.

To import the package in the python environment, install the package (`-e` for editable installation, upon import, python will read directly from the repository).

```sh
pip install -e .
```
