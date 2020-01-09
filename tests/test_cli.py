import pytest
from click.testing import CliRunner

import pipgrip.pipper
from pipgrip import __version__
from pipgrip.cli import flatten, main
from pipgrip.pipper import _download_wheel

self_wheel = _download_wheel(".", None, None, None, "./tests/assets")


# fmt: off
def mock_download_wheel(package, *args, **kwargs):
    wheelhouse = {
        ".": self_wheel,
        "setuptools>=38.3": "./tests/assets/setuptools-44.0.0-py2.py3-none-any.whl",
        "pkginfo>=1.4.2": "./tests/assets/pkginfo-1.5.0.1-py2.py3-none-any.whl",
        "packaging>=17": "./tests/assets/packaging-20.0-py2.py3-none-any.whl",
        "click": "./tests/assets/Click-7.0-py2.py3-none-any.whl",
        "anytree": "./tests/assets/anytree-2.7.3-py2.py3-none-any.whl",
        "six": "./tests/assets/six-1.13.0-py2.py3-none-any.whl",
        "wheel": "./tests/assets/wheel-0.33.6-py2.py3-none-any.whl",
        "pyparsing>=2.0.2": "./tests/assets/pyparsing-2.4.6-py2.py3-none-any.whl",
        "requests==2.22.0": "./tests/assets/requests-2.22.0-py2.py3-none-any.whl",
        "urllib3<1.25.0|>1.25.0,<1.25.1|>1.25.1,<1.26,>=1.21.1": "./tests/assets/urllib3-1.25-py2.py3-none-any.whl",
        "urllib3==1.25.7": "./tests/assets/urllib3-1.25.7-py2.py3-none-any.whl",
        "idna<2.9,>=2.5": "./tests/assets/idna-2.8-py2.py3-none-any.whl",
        "chardet<3.1.0,>=3.0.2": "./tests/assets/chardet-3.0.4-py2.py3-none-any.whl",
        "certifi>=2017.4.17": "./tests/assets/certifi-2019.11.28-py2.py3-none-any.whl",
        "keras==2.2.2": "./tests/assets/Keras-2.2.2-py2.py3-none-any.whl",
        "six>=1.9.0": "./tests/assets/six-1.13.0-py2.py3-none-any.whl",
        "scipy>=0.14": "./tests/assets/scipy-1.2.2-cp27-cp27m-macosx_10_6_intel.macosx_10_9_intel.macosx_10_9_x86_64.macosx_10_10_intel.macosx_10_10_x86_64.whl",
        "pyyaml": "./tests/assets/PyYAML-5.3-cp27-cp27m-macosx_10_14_x86_64.whl",
        "numpy>=1.9.1": "./tests/assets/numpy-1.16.6-cp27-cp27m-macosx_10_9_x86_64.whl",
        "keras-preprocessing==1.0.2": "./tests/assets/Keras_Preprocessing-1.0.2-py2.py3-none-any.whl",
        "keras-preprocessing": "./tests/assets/Keras_Preprocessing-1.1.0-py2.py3-none-any.whl",
        "keras-applications==1.0.4": "./tests/assets/Keras_Applications-1.0.4-py2.py3-none-any.whl",
        "h5py": "./tests/assets/h5py-2.10.0-cp27-cp27m-macosx_10_6_intel.whl",
    }
    return wheelhouse[package]


def mock_get_available_versions(package, *args, **kwargs):
    versions = {
        "setuptools": ["44.0.0"],
        "pkginfo": ["1.5.0.1"],
        "packaging": ["20.0"],
        "click": ["7.0"],
        "anytree": ["2.7.3"],
        "six": ["1.13.0"],
        "wheel": ["0.33.6"],
        "pyparsing": ["2.4.6"],
        "requests": ["2.22.0"],
        "urllib3": ["1.25.7"],
        "idna": ["2.8"],
        "chardet": ["3.0.4"],
        "certifi": ["2019.11.28"],
        "keras": ["2.2.2", "2.2.3", "2.2.4", "2.2.5", "2.3.0", "2.3.1"],
        "scipy": ["1.2.2"],
        "pyyaml": ["5.3"],
        "numpy": ["1.16.6"],
        "keras-preprocessing": ["1.0.0", "1.0.1", "1.0.2", "1.0.3", "1.0.4", "1.0.5", "1.0.6", "1.0.8", "1.0.9", "1.1.0"],
        "keras-applications": ["1.0.0", "1.0.1", "1.0.2", "1.0.4", "1.0.5", "1.0.6", "1.0.7", "1.0.8"],
        "h5py": ["2.10.0"],
    }
    return versions[package]
# fmt: on


@pytest.mark.parametrize(
    "arguments, expected",
    [
        (
            ["."],
            [
                ".==" + __version__,
                "anytree==2.7.3",
                "six==1.13.0",
                "click==7.0",
                "packaging==20.0",
                "pyparsing==2.4.6",
                "pkginfo==1.5.0.1",
                "setuptools==44.0.0",
                "wheel==0.33.6",
            ],
        ),
        (
            ["--stop-early", "requests==2.22.0"],
            [
                "requests==2.22.0",
                "chardet==3.0.4",
                "idna==2.8",
                "urllib3==1.25.7",
                "certifi==2019.11.28",
            ],
        ),
        (  # cyclic
            ["keras==2.2.2"],
            [
                "keras==2.2.2",
                "h5py==2.10.0",
                "numpy==1.16.6",
                "six==1.13.0",
                "keras-applications==1.0.4",
                "keras-preprocessing==1.0.2",
                "scipy==1.2.2",
                "pyyaml==5.3",
            ],
        ),
        (
            ["--tree", "keras==2.2.2"],
            [  # generated on py2.7 - ipython - %paste a - print a
                u"keras==2.2.2 (2.2.2)",
                u"\u251c\u2500\u2500 h5py (2.10.0)",
                u"\u2502   \u251c\u2500\u2500 numpy>=1.7 (1.16.6)",
                u"\u2502   \u2514\u2500\u2500 six (1.13.0)",
                u"\u251c\u2500\u2500 keras-applications==1.0.4 (1.0.4)",
                u"\u2502   \u251c\u2500\u2500 h5py (2.10.0)",
                u"\u2502   \u2502   \u251c\u2500\u2500 numpy>=1.7 (1.16.6)",
                u"\u2502   \u2502   \u2514\u2500\u2500 six (1.13.0)",
                u"\u2502   \u251c\u2500\u2500 keras>=2.1.6 (2.2.2, cyclic)",
                u"\u2502   \u2514\u2500\u2500 numpy>=1.9.1 (1.16.6)",
                u"\u251c\u2500\u2500 keras-preprocessing==1.0.2 (1.0.2)",
                u"\u2502   \u251c\u2500\u2500 keras>=2.1.6 (2.2.2, cyclic)",
                u"\u2502   \u251c\u2500\u2500 numpy>=1.9.1 (1.16.6)",
                u"\u2502   \u251c\u2500\u2500 scipy>=0.14 (1.2.2)",
                u"\u2502   \u2502   \u2514\u2500\u2500 numpy>=1.8.2 (1.16.6)",
                u"\u2502   \u2514\u2500\u2500 six>=1.9.0 (1.13.0)",
                u"\u251c\u2500\u2500 numpy>=1.9.1 (1.16.6)",
                u"\u251c\u2500\u2500 pyyaml (5.3)",
                u"\u251c\u2500\u2500 scipy>=0.14 (1.2.2)",
                u"\u2502   \u2514\u2500\u2500 numpy>=1.8.2 (1.16.6)",
                u"\u2514\u2500\u2500 six>=1.9.0 (1.13.0)",
            ],
        ),
        (
            ["keras_preprocessing"],
            ["keras-preprocessing==1.1.0", "six==1.13.0", "numpy==1.16.6"],
        ),
        # (  # py3 only, doesnt add aiohttp with --stop-early
        #     ["--stop-early", "keras"],
        #     [
        #         "aiobotocore==0.11.1",
        #         "async-generator==1.10",
        #         "botocore==1.13.14",
        #         "awscli==1.16.278",
        #         "s3transfer==0.2.1",
        #         "wrapt==1.11.2",
        #         "jmespath==0.9.4",
        #         "docutils==0.15.2",
        #         "pyyaml==5.1.2",
        #         "rsa==3.4.2",
        #         "colorama==0.4.1",
        #     ],
        # ),
    ],
    ids=(
        "pipgrip pipgrip",
        "--stop-early requests",
        "--stop-early keras (cyclic)",
        "--tree keras (cyclic)",
        "keras_preprocessing (underscore)",
    ),
)
def test_cli(arguments, expected, monkeypatch):
    def default_environment():
        return {
            "implementation_name": "cpython",
            "implementation_version": "3.7.5",
            "os_name": "posix",
            "platform_machine": "x86_64",
            "platform_release": "5.0.0-1027-azure",
            "platform_system": "Linux",
            "platform_version": "#29~18.04.1-Ubuntu SMP Mon Nov 25 21:18:57 UTC 2019",
            "python_full_version": "3.7.5",
            "platform_python_implementation": "CPython",
            "python_version": "3.7",
            "sys_platform": "linux",
        }

    monkeypatch.setattr(
        pipgrip.pipper, "_download_wheel", mock_download_wheel,
    )
    monkeypatch.setattr(
        pipgrip.pipper, "_get_available_versions", mock_get_available_versions,
    )
    monkeypatch.setattr(
        pipgrip.pipper, "default_environment", default_environment,
    )
    runner = CliRunner()
    result = runner.invoke(main, arguments)

    if result.exit_code:
        raise result.exception
    assert set(result.output.strip().split("\n")) == set(expected)


def test_flatten():
    a = {
        ("aiobotocore", "0.11.1"): {
            ("aiohttp", "3.6.2"): {
                ("async-timeout", "3.0.1"): {},
                ("attrs", "19.3.0"): {},
                ("chardet", "3.0.4"): {},
                ("multidict", "4.7.3"): {},
                ("yarl", "1.4.2"): {("idna", "2.8"): {}, ("multidict", "4.7.3"): {}},
            },
            ("async-generator", "1.10"): {},
            ("awscli", "1.16.278"): {
                ("pyyaml", "5.1.2"): {},
                ("botocore", "1.13.14"): {
                    ("docutils", "0.15.2"): {},
                    ("jmespath", "0.9.4"): {},
                    ("python-dateutil", "2.8.0"): {("six", "1.13.0"): {}},
                    ("urllib3", "1.25.7"): {},
                },
                ("colorama", "0.4.1"): {},
                ("docutils", "0.15.2"): {},
                ("rsa", "3.4.2"): {("pyasn1", "0.4.8"): {}},
                ("s3transfer", "0.2.1"): {
                    ("botocore", "1.13.14"): {
                        ("docutils", "0.15.2"): {},
                        ("jmespath", "0.9.4"): {},
                        ("python-dateutil", "2.8.0"): {("six", "1.13.0"): {}},
                        ("urllib3", "1.25.7"): {},
                    }
                },
            },
            ("botocore", "1.13.14"): {
                ("docutils", "0.15.2"): {},
                ("jmespath", "0.9.4"): {},
                ("python-dateutil", "2.8.0"): {("six", "1.13.0"): {}},
                ("urllib3", "1.25.7"): {},
            },
            ("wrapt", "1.11.2"): {},
        }
    }
    assert flatten(a) == {
        "aiobotocore": "0.11.1",
        "aiohttp": "3.6.2",
        "async-generator": "1.10",
        "async-timeout": "3.0.1",
        "attrs": "19.3.0",
        "awscli": "1.16.278",
        "botocore": "1.13.14",
        "chardet": "3.0.4",
        "colorama": "0.4.1",
        "docutils": "0.15.2",
        "idna": "2.8",
        "jmespath": "0.9.4",
        "multidict": "4.7.3",
        "pyasn1": "0.4.8",
        "python-dateutil": "2.8.0",
        "pyyaml": "5.1.2",
        "rsa": "3.4.2",
        "s3transfer": "0.2.1",
        "six": "1.13.0",
        "urllib3": "1.25.7",
        "wrapt": "1.11.2",
        "yarl": "1.4.2",
    }
