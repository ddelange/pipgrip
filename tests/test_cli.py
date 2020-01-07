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
        "wheel": "/Users/david.de-lange/Library/Caches/pip/wheels/pipgrip/wheel-0.33.6-py2.py3-none-any.whl",
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
        "keras-applications==1.0.4": "./tests/assets/Keras_Applications-1.0.4-py2.py3-none-any.whl",
        "h5py": "./tests/assets/h5py-2.10.0-cp27-cp27m-macosx_10_6_intel.whl",
    }
    return wheelhouse[package]


def mock_get_available_versions(package, *args, **kwargs):
    versions = {
        "setuptools": [u"44.0.0"],
        "pkginfo": [u"0.1", u"0.1.1", u"0.2", u"0.3", u"0.4", u"0.4.1", u"0.5", u"0.6", u"0.7", u"0.8", u"0.9", u"0.9.1", u"1.0", u"1.1", u"1.2", u"1.2.1", u"1.3.0", u"1.3.1", u"1.3.2", u"1.4.0", u"1.4.1", u"1.4.2", u"1.5.0", u"1.5.0.1"],
        "packaging": [u"14.0", u"14.1", u"14.2", u"14.3", u"14.4", u"14.5", u"15.0", u"15.1", u"15.2", u"15.3", u"16.0", u"16.1", u"16.2", u"16.3", u"16.4", u"16.5", u"16.6", u"16.7", u"16.8", u"17.0", u"17.1", u"18.0", u"19.0", u"19.1", u"19.2", u"20.0"],
        "click": [u"0.1", u"0.2", u"0.3", u"0.4", u"0.5", u"0.5.1", u"0.6", u"0.7", u"1.0", u"1.1", u"2.0", u"2.1", u"2.2", u"2.3", u"2.4", u"2.5", u"2.6", u"3.0", u"3.1", u"3.2", u"3.3", u"4.0", u"4.1", u"5.0", u"5.1", u"6.0", u"6.1", u"6.2", u"6.3", u"6.4", u"6.5", u"6.6", u"6.7", u"7.0"],
        "anytree": [u"0.0.1", u"1.0.0", u"1.0.1", u"1.0.2", u"1.0.4", u"2.0.0", u"2.1.0", u"2.1.1", u"2.1.2", u"2.1.3", u"2.1.4", u"2.2.0", u"2.2.1", u"2.2.2", u"2.3.0", u"2.4.0", u"2.4.1", u"2.4.2", u"2.4.3", u"2.5.0", u"2.6.0", u"2.7.0", u"2.7.1", u"2.7.2", u"2.7.3"],
        "six": [u"0.9.0", u"0.9.1", u"0.9.2", u"1.0.0", u"1.1.0", u"1.2.0", u"1.3.0", u"1.4.0", u"1.4.1", u"1.5.0", u"1.5.1", u"1.5.2", u"1.6.0", u"1.6.1", u"1.7.0", u"1.7.1", u"1.7.2", u"1.7.3", u"1.8.0", u"1.9.0", u"1.10.0", u"1.11.0", u"1.12.0", u"1.13.0"],
        "wheel": ["0.1", "0.2", "0.3", "0.4", "0.4.1", "0.4.2", "0.5", "0.6", "0.7", "0.8", "0.9", "0.9.1", "0.9.2", "0.9.3", "0.9.4", "0.9.5", "0.9.6", "0.9.7", "0.10.0", "0.10.1", "0.10.2", "0.10.3", "0.11.0", "0.12.0", "0.13.0", "0.14.0", "0.15.0", "0.16.0", "0.17.0", "0.18.0", "0.19.0", "0.21.0", "0.22.0", "0.23.0", "0.24.0", "0.25.0", "0.26.0", "0.27.0", "0.28.0", "0.29.0", "0.30.0", "0.31.0", "0.31.1", "0.32.0", "0.32.1", "0.32.2", "0.32.3", "0.33.0", "0.33.1", "0.33.4", "0.33.5", "0.33.6"],
        "pyparsing": [u"1.4.6", u"1.4.7", u"1.4.8", u"1.4.11", u"1.5.0", u"1.5.1", u"1.5.2", u"1.5.3", u"1.5.4", u"1.5.5", u"1.5.6", u"1.5.7", u"2.0.0", u"2.0.1", u"2.0.2", u"2.0.3", u"2.0.4", u"2.0.5", u"2.0.6", u"2.0.7", u"2.1.0", u"2.1.1", u"2.1.2", u"2.1.3", u"2.1.4", u"2.1.5", u"2.1.6", u"2.1.7", u"2.1.8", u"2.1.9", u"2.1.10", u"2.2.0", u"2.2.1", u"2.2.2", u"2.3.0", u"2.3.1", u"2.4.0", u"2.4.1.1", u"2.4.2", u"2.4.3", u"2.4.4", u"2.4.5", u"2.4.6"],
        u"requests": [u"2.22.0"],
        "urllib3": [u"0.3", u"1.0", u"1.0.1", u"1.0.2", u"1.1", u"1.2", u"1.2.1", u"1.2.2", u"1.3", u"1.4", u"1.5", u"1.6", u"1.7", u"1.7.1", u"1.8", u"1.8.2", u"1.8.3", u"1.9", u"1.9.1", u"1.10", u"1.10.1", u"1.10.2", u"1.10.3", u"1.10.4", u"1.11", u"1.12", u"1.13", u"1.13.1", u"1.14", u"1.15", u"1.15.1", u"1.16", u"1.17", u"1.18", u"1.18.1", u"1.19", u"1.19.1", u"1.20", u"1.21", u"1.21.1", u"1.22", u"1.23", u"1.24", u"1.24.1", u"1.24.2", u"1.24.3", u"1.25", u"1.25.1", u"1.25.2", u"1.25.3", u"1.25.4", u"1.25.5", u"1.25.6", u"1.25.7"],
        "idna": [u"0.2", u"0.3", u"0.4", u"0.5", u"0.6", u"0.7", u"0.8", u"0.9", u"1.0", u"1.1", u"2.0", u"2.1", u"2.2", u"2.3", u"2.4", u"2.5", u"2.6", u"2.7", u"2.8"],
        "chardet": [u"1.0", u"1.0.1", u"1.1", u"2.1.1", u"2.2.1", u"2.3.0", u"3.0.0", u"3.0.1", u"3.0.2", u"3.0.3", u"3.0.4"],
        "certifi": [u"0.0.1", u"0.0.2", u"0.0.3", u"0.0.4", u"0.0.5", u"0.0.6", u"0.0.7", u"0.0.8", u"1.0.0", u"1.0.1", u"14.5.14", u"2015.4.28", u"2015.9.6", u"2015.9.6.1", u"2015.9.6.2", u"2015.11.20", u"2015.11.20.1", u"2016.2.28", u"2016.8.2", u"2016.8.8", u"2016.8.31", u"2016.9.26", u"2017.1.23", u"2017.4.17", u"2017.7.27", u"2017.7.27.1", u"2017.11.5", u"2018.1.18", u"2018.4.16", u"2018.8.13", u"2018.8.24", u"2018.10.15", u"2018.11.29", u"2019.3.9", u"2019.6.16", u"2019.9.11", u"2019.11.28"],
        u"keras": [u"0.2.0", u"0.3.0", u"0.3.1", u"0.3.2", u"0.3.3", u"1.0.0", u"1.0.1", u"1.0.2", u"1.0.3", u"1.0.4", u"1.0.5", u"1.0.6", u"1.0.7", u"1.0.8", u"1.1.0", u"1.1.1", u"1.1.2", u"1.2.0", u"1.2.1", u"1.2.2", u"2.0.0", u"2.0.1", u"2.0.2", u"2.0.3", u"2.0.4", u"2.0.5", u"2.0.6", u"2.0.7", u"2.0.8", u"2.0.9", u"2.1.0", u"2.1.1", u"2.1.2", u"2.1.3", u"2.1.4", u"2.1.5", u"2.1.6", u"2.2.0", u"2.2.1", u"2.2.2", u"2.2.3", u"2.2.4", u"2.2.5", u"2.3.0", u"2.3.1"],
        "scipy": [u"0.8.0", u"0.9.0", u"0.10.0", u"0.10.1", u"0.11.0", u"0.12.0", u"0.12.1", u"0.13.0", u"0.13.1", u"0.13.2", u"0.13.3", u"0.14.0", u"0.14.1", u"0.15.0", u"0.15.1", u"0.16.0", u"0.16.1", u"0.17.0", u"0.17.1", u"0.18.0", u"0.18.1", u"0.19.0", u"0.19.1", u"1.0.0", u"1.0.1", u"1.1.0", u"1.2.0", u"1.2.1", u"1.2.2"],
        "pyyaml": [u"3.10", u"3.11", u"3.12", u"3.13", u"5.1", u"5.1.1", u"5.1.2", u"5.2", u"5.3"],
        "numpy": [u"1.3.0", u"1.4.1", u"1.5.0", u"1.5.1", u"1.6.0", u"1.6.1", u"1.6.2", u"1.7.0", u"1.7.1", u"1.7.2", u"1.8.0", u"1.8.1", u"1.8.2", u"1.9.0", u"1.9.1", u"1.9.2", u"1.9.3", u"1.10.1", u"1.10.2", u"1.10.4", u"1.11.0", u"1.11.1", u"1.11.2", u"1.11.3", u"1.12.0", u"1.12.1", u"1.13.0", u"1.13.1", u"1.13.3", u"1.14.0", u"1.14.1", u"1.14.2", u"1.14.3", u"1.14.4", u"1.14.5", u"1.14.6", u"1.15.0", u"1.15.1", u"1.15.2", u"1.15.3", u"1.15.4", u"1.16.0", u"1.16.1", u"1.16.2", u"1.16.3", u"1.16.4", u"1.16.5", u"1.16.6"],
        "keras-preprocessing": [u"1.0.0", u"1.0.1", u"1.0.2", u"1.0.3", u"1.0.4", u"1.0.5", u"1.0.6", u"1.0.8", u"1.0.9", u"1.1.0"],
        "keras-applications": [u"1.0.0", u"1.0.1", u"1.0.2", u"1.0.4", u"1.0.5", u"1.0.6", u"1.0.7", u"1.0.8"],
        "h5py": [u"2.2.1", u"2.3.0", u"2.3.1", u"2.4.0", u"2.5.0", u"2.6.0", u"2.7.0", u"2.7.1", u"2.8.0", u"2.9.0", u"2.10.0"],
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
            [
                u"keras==2.2.2 (2.2.2)",
                u"\u251c\u2500\u2500 h5py (2.10.0)",
                u"\u2502   \u251c\u2500\u2500 numpy>=1.9.1 (1.16.6)",
                u"\u2502   \u2514\u2500\u2500 six>=1.9.0 (1.13.0)",
                u"\u251c\u2500\u2500 keras-applications==1.0.4 (1.0.4)",
                u"\u2502   \u251c\u2500\u2500 h5py (2.10.0)",
                u"\u2502   \u2502   \u251c\u2500\u2500 numpy>=1.9.1 (1.16.6)",
                u"\u2502   \u2502   \u2514\u2500\u2500 six>=1.9.0 (1.13.0)",
                u"\u2502   \u251c\u2500\u2500 keras==2.2.2 (2.2.2, cyclic)",
                u"\u2502   \u2514\u2500\u2500 numpy>=1.9.1 (1.16.6)",
                u"\u251c\u2500\u2500 keras-preprocessing==1.0.2 (1.0.2)",
                u"\u2502   \u251c\u2500\u2500 keras==2.2.2 (2.2.2, cyclic)",
                u"\u2502   \u251c\u2500\u2500 numpy>=1.9.1 (1.16.6)",
                u"\u2502   \u251c\u2500\u2500 scipy>=0.14 (1.2.2)",
                u"\u2502   \u2502   \u2514\u2500\u2500 numpy>=1.9.1 (1.16.6)",
                u"\u2502   \u2514\u2500\u2500 six>=1.9.0 (1.13.0)",
                u"\u251c\u2500\u2500 numpy>=1.9.1 (1.16.6)",
                u"\u251c\u2500\u2500 pyyaml (5.3)",
                u"\u251c\u2500\u2500 scipy>=0.14 (1.2.2)",
                u"\u2502   \u2514\u2500\u2500 numpy>=1.9.1 (1.16.6)",
                u"\u2514\u2500\u2500 six>=1.9.0 (1.13.0)",
            ],
        )
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

    assert result.exit_code == 0
    assert result.output.strip() == "\n".join(expected)


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
