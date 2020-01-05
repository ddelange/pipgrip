import pytest
from click.testing import CliRunner

from pipgrip.cli import flatten, main


@pytest.mark.parametrize(
    "arguments, expected",
    [
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
        (
            ["--stop-early", "aiobotocore[awscli]==0.11.1"],
            [
                "aiobotocore==0.11.1",
                "async-generator==1.10",
                "botocore==1.13.14",
                "awscli==1.16.278",
                "s3transfer==0.2.1",
                "wrapt==1.11.2",
                "jmespath==0.9.4",
                "docutils==0.15.2",
                "pyyaml==5.1.2",
                "rsa==3.4.2",
                "colorama==0.4.1",
            ],
        ),
    ],
    ids=("--stop-early requests", "--stop-early aiobotocore",),
)
def test_cli(arguments, expected):
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
