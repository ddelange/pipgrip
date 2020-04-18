# pipgrip

[![build](https://img.shields.io/github/workflow/status/ddelange/pipgrip/GH/master?logo=github&cacheSeconds=86400)](https://github.com/ddelange/pipgrip/actions?query=branch%3Amaster)
[![codecov](https://img.shields.io/codecov/c/github/ddelange/pipgrip/master?logo=codecov&logoColor=white)](https://codecov.io/gh/ddelange/pipgrip)
[![pypi Version](https://img.shields.io/pypi/v/pipgrip.svg?logo=pypi&logoColor=white)](https://pypi.org/project/pipgrip/)
[![python](https://img.shields.io/pypi/pyversions/pipgrip.svg?logo=python&logoColor=white)](https://pypi.org/project/pipgrip/)
[![downloads](https://pepy.tech/badge/pipgrip)](https://pypistats.org/packages/pipgrip)
[![black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/python/black)

[pipgrip](https://github.com/ddelange/pipgrip) is a lightweight pip dependency resolver with deptree preview functionality based on the [PubGrub algorithm](https://medium.com/@nex3/pubgrub-2fb6470504f), which is also used by [poetry](https://github.com/python-poetry/poetry). For one or more [PEP 508](https://www.python.org/dev/peps/pep-0508/) dependency specifications, pipgrip recursively fetches/builds the Python wheels necessary for version solving, and optionally renders the full resulting dependency tree.

<!--
  give example with multiple packages
  reversed tree
  two times pypi.org in `looking in indexes`?
  multicore pip?
-->

#### pipgrip vs. poetry

[poetry](https://github.com/python-poetry/poetry) offers package management with dependency resolution, essentially replacing pip/setuptools. This means that poetry packages don't contain `setup.py`, and hence are not compatible with `pip install -e`: poetry projects would have to be converted to setuptools-based projects with e.g. [dephell](https://github.com/dephell/dephell). To avoid such hassle, pipgrip only requires the selected package(s) + dependencies to be available to pip in the ususal way.

#### pipgrip vs. pipdeptree

For offline usage, [pipdeptree](https://github.com/naiquevin/pipdeptree) can inspect the current environment and show how the currently installed packages relate to each other. This however requires the packages to be pip-installed, and (despite warnings about e.g. cyclic dependencies) offers no form of dependency resolution since it's only based on the (single) package versions installed in the environment. Such shortcomings are avoided when using pipgrip, since packages don't need to be installed and all versions available to pip are considered.


## Installation

This pure-Python, OS independent package is available on [PyPI](https://pypi.org/project/pipgrip/):

```
pip install pipgrip
```


## Usage

This package can be used to:
- **Render** an exhaustive dependency tree for any given pip-compatible package(s) with `--tree`
- **Alleviate** [Python dependency hell](https://medium.com/knerd/the-nine-circles-of-python-dependency-hell-481d53e3e025) by resolving the latest viable combination of required packages
- **Avoid** bugs by running pipgrip as a stage in CI pipelines
- **Detect** version conflicts for given constraints and give human readable feedback about it
- **Warn** for cyclic dependencies in local projects [and install them anyway]:
  - `pipgrip -v --tree . [--install -e]`
- **Install** complex packages without worries using:
  - `pipgrip --install aiobotocore[awscli]`
  - `pipgrip --lock aiobotocore[awscli] && pip install aiobotocore[awscli] --constraint ./pipgrip.lock`
- **Generate** a lockfile with a complete working set of dependencies for worriless installs:
  - `pipgrip --lock --install --tree -v aiobotocore[awscli]`
  - `pipgrip --lock -tree aiobotocore[awscli] && pip install -U --no-deps -r ./pipgrip.lock`
  <!-- - `pipgrip aiobotocore[awscli] | pip install -U --no-deps -r /dev/stdin` -->
- **Combine** dependency trees of multiple packages into one unified set of pinned packages:
  - `pipgrip --lock --install --tree -v .[boto3] s3transfer==0.2.1`

See also [known caveats](#known-caveats).

```
$ pipgrip --help

Usage: pipgrip [OPTIONS] [DEPENDENCIES]...

  pipgrip is a lightweight pip dependency resolver with deptree preview
  functionality based on the PubGrub algorithm, which is also used by poetry.
  For one or more PEP 508 dependency specifications, pipgrip recursively
  fetches/builds the Python wheels necessary for version solving, and optionally
  renders the full resulting dependency tree.

Options:
  --install                     Install full dependency tree after resolving.
  -e, --editable                Install a project in editable mode.
  -r, --requirements-file FILE  Install from the given requirements file. This
                                option can be used multiple times.
  --lock                        Write out pins to './pipgrip.lock'.
  --pipe                        Output space-separated pins instead of newline-
                                separated pins.
  --json                        Output pins as json dict instead of newline-
                                separated pins.
  --tree                        Output human readable dependency tree (top-down).
  --reversed-tree               Output human readable dependency tree (bottom-up).
  --max-depth INTEGER           Maximum tree rendering depth (defaults to -1).
  --cache-dir DIRECTORY         Use a custom cache dir.
  --no-cache-dir                Disable pip cache for the wheels downloaded by
                                pipper. Overrides --cache-dir.
  --index-url TEXT              Base URL of the Python Package Index (default
                                https://pypi.org/simple).
  --extra-index-url TEXT        Extra URLs of package indexes to use in addition
                                to --index-url.
  --pre                         Include pre-release and development versions. By
                                default, pip only finds stable versions.
  -v, --verbose                 Control verbosity: -v will print cyclic
                                dependencies (WARNING), -vv will show solving
                                decisions (INFO), -vvv for development (DEBUG).
  -h, --help                    Show this message and exit.
```

#### Dependency trees

Exhaustive dependency trees without the need to install any packages (at most build some wheels).
```
$ pipgrip --tree pipgrip

pipgrip (0.2.1)
├── anytree (2.8.0)
│   └── six>=1.9.0 (1.14.0)
├── click (7.1.1)
├── packaging>=17 (20.3)
│   ├── pyparsing>=2.0.2 (2.4.7)
│   └── six (1.14.0)
├── pip>=7.1.0 (20.0.2)
├── pkginfo>=1.4.2 (1.5.0.1)
├── setuptools>=38.3 (46.1.3)
└── wheel (0.34.2)
```

#### Lockfile generation

Using the `--lock` option, resolved (pinned) dependencies are additionally written to `./pipgrip.lock`.
```
$ pipgrip --tree --lock botocore==1.13.48 'boto3>=1.10,<1.10.50'

botocore==1.13.48 (1.13.48)
├── docutils<0.16,>=0.10 (0.15.2)
├── jmespath<1.0.0,>=0.7.1 (0.9.5)
├── python-dateutil<3.0.0,>=2.1 (2.8.1)
│   └── six>=1.5 (1.14.0)
└── urllib3<1.26,>=1.20 (1.25.8)
boto3<1.10.50,>=1.10 (1.10.48)
├── botocore<1.14.0,>=1.13.48 (1.13.48)
│   ├── docutils<0.16,>=0.10 (0.15.2)
│   ├── jmespath<1.0.0,>=0.7.1 (0.9.5)
│   ├── python-dateutil<3.0.0,>=2.1 (2.8.1)
│   │   └── six>=1.5 (1.14.0)
│   └── urllib3<1.26,>=1.20 (1.25.8)
├── jmespath<1.0.0,>=0.7.1 (0.9.5)
└── s3transfer<0.3.0,>=0.2.0 (0.2.1)
    └── botocore<2.0.0,>=1.12.36 (1.13.48)
        ├── docutils<0.16,>=0.10 (0.15.2)
        ├── jmespath<1.0.0,>=0.7.1 (0.9.5)
        ├── python-dateutil<3.0.0,>=2.1 (2.8.1)
        │   └── six>=1.5 (1.14.0)
        └── urllib3<1.26,>=1.20 (1.25.8)

$ cat ./pipgrip.lock

botocore==1.13.48
docutils==0.15.2
jmespath==0.9.5
python-dateutil==2.8.1
six==1.14.0
urllib3==1.25.8
boto3==1.10.48
s3transfer==0.2.1
```
NOTE:
Since the selected botocore version is older than the one required by the recent versions of boto3, all boto3 versions will be checked for compatibility with botocore==1.13.48.

#### Version conflicts

If version conflicts exist for the given (ranges of) package version(s), a verbose explanation is raised.
```
$ pipgrip auto-sklearn~=0.6 dragnet==2.0.4

Error: Because dragnet (2.0.4) depends on scikit-learn (>=0.15.2,<0.21.0)
 and auto-sklearn (0.6.0) depends on scikit-learn (<0.22,>=0.21.0), dragnet (2.0.4) is incompatible with auto-sklearn (0.6.0).
And because no versions of auto-sklearn match >0.6.0,<1.0, dragnet (2.0.4) is incompatible with auto-sklearn (>=0.6.0,<1.0).
So, because root depends on both auto-sklearn (~=0.6) and dragnet (==2.0.4), version solving failed.
```
NOTE:
If older versions of auto-sklearn are allowed, PubGrub will try all acceptable versions of auto-sklearn. In this case, auto-sklearn==0.5.2 requires scikit-learn (<0.20,>=0.19), making it compatible with dragnet==2.0.4.

#### Cyclic dependencies

If cyclic dependencies are found, it is noted in the resulting tree.
```
$ pipgrip --tree -v keras==2.2.2

WARNING: Cyclic dependency found: keras depends on keras-applications and vice versa.
WARNING: Cyclic dependency found: keras depends on keras-preprocessing and vice versa.
keras==2.2.2 (2.2.2)
├── h5py (2.10.0)
│   ├── numpy>=1.7 (1.18.1)
│   └── six (1.14.0)
├── keras-applications==1.0.4 (1.0.4)
│   ├── h5py (2.10.0)
│   │   ├── numpy>=1.7 (1.18.1)
│   │   └── six (1.14.0)
│   ├── keras>=2.1.6 (2.2.2, cyclic)
│   └── numpy>=1.9.1 (1.18.1)
├── keras-preprocessing==1.0.2 (1.0.2)
│   ├── keras>=2.1.6 (2.2.2, cyclic)
│   ├── numpy>=1.9.1 (1.18.1)
│   ├── scipy>=0.14 (1.4.1)
│   │   └── numpy>=1.13.3 (1.18.1)
│   └── six>=1.9.0 (1.14.0)
├── numpy>=1.9.1 (1.18.1)
├── pyyaml (5.3)
├── scipy>=0.14 (1.4.1)
│   └── numpy>=1.13.3 (1.18.1)
└── six>=1.9.0 (1.14.0)
```


## Known caveats

- ``pip install -U `pipgrip --pipe package` `` without `--no-deps` is unsafe while pip doesn't [yet](https://twitter.com/di_codes/status/1193980331004743680) have a built-in dependency resolver, and leaves room for interpretation by pip
- Package names are canonicalised in wheel metadata, resulting in e.g. `path.py -> path-py` and `keras_preprocessing -> keras-preprocessing` in output
- [VCS Support](https://pip.pypa.io/en/stable/reference/pip_install/#vcs-support) isn't implemented yet
- `--reversed-tree` isn't implemented yet
- Since `pip install -r` does not accept `.` as requirement, it is omitted from lockfiles, so `--install` or `--pipe` should be used when installing local projects
- The equivalent of e.g. `pip install ../aiobotocore[boto3]` is not yet implemented. However, e.g. `pipgrip --install .[boto3]` is allowed.


## Development

[![gitmoji](https://img.shields.io/badge/gitmoji-%20%F0%9F%98%9C%20%F0%9F%98%8D-ffdd67)](https://github.com/carloscuesta/gitmoji-cli)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

First, create a virtual environment. Then, get ready to develop:

```
make install
```

This [make-command](Makefile) is equivalent to the following steps:

Install pre-commit and other continous integration dependencies in order to make commits and run tests.

```
pip install -r requirements/ci.txt
pre-commit install
```

With requirements installed, `make lint` and `make test` can now be run. There is also `make clean`, and `make all` which runs all three.

To import the package in the python environment, install the package (`-e` for editable installation, upon import, python will read directly from the repository).

```
pip install -e .
```


## See also

- [PubGrub spec](https://github.com/dart-lang/pub/blob/SDK-2.2.1-dev.3.0/doc/solver.md)
- [pip needs a dependency resolver](https://github.com/pypa/pip/issues/988)
- [pipdeptree](https://github.com/naiquevin/pipdeptree)
- [mixology](https://github.com/sdispater/mixology)
- [poetry-semver](https://github.com/python-poetry/semver)
- [johnnydep](https://github.com/wimglenn/johnnydep)

-----

BSD 3-Clause License

Copyright (c) 2020, ddelange\
All rights reserved.
