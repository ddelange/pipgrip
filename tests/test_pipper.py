# BSD 3-Clause License
#
# Copyright (c) 2020 - 2024, ddelange, <ddelange@delange.dev>
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# SPDX-License-Identifier: BSD-3-Clause
import json
import os
import subprocess

import pytest

import pipgrip.pipper
from pipgrip.pipper import _download_wheel, _get_available_versions, _get_package_report


@pytest.mark.parametrize(
    "package, pip_output, expected",
    [
        (
            ".[all]",
            """
            Collecting jupyterlab-black
              Downloading https://files.pythonhosted.org/packages/b3/c9/b3d38a0cc2a5237becb3c2f8843ca5a8e884906e9018029e4c4e5c43f62e/jupyterlab_black-0.2.1.tar.gz
            Building wheels for collected packages: jupyterlab-black
              Running setup.py bdist_wheel for jupyterlab-black: started
              Running setup.py bdist_wheel for jupyterlab-black: finished with status 'done'
              Stored in directory: ~/Library/Caches/pip/wheels/pipgrip
            Successfully built jupyterlab-black
            """,
            "a.whl",
        ),
        (
            "six",
            """
            Collecting six
              Downloading https://files.pythonhosted.org/packages/ee/ff/48bde5c0f013094d729fe4b0316ba2a24774b3ff1c52d924a8a4cb04078a/six-1.15.0-py2.py3-none-any.whl
              Saved ~/Library/Caches/pip/wheels/pipgrip/six-1.15.0-py2.py3-none-any.whl
            Skipping six, due to already being wheel.
            """,
            "six-1.15.0-py2.py3-none-any.whl",
        ),
        (
            "jupyterlab-black",
            """
            Collecting jupyterlab-black
              Downloading https://files.pythonhosted.org/packages/b3/c9/b3d38a0cc2a5237becb3c2f8843ca5a8e884906e9018029e4c4e5c43f62e/jupyterlab_black-0.2.1.tar.gz
            Building wheels for collected packages: jupyterlab-black
              Running setup.py bdist_wheel for jupyterlab-black: started
              Running setup.py bdist_wheel for jupyterlab-black: finished with status 'done'
              Stored in directory: ~/Library/Caches/pip/wheels/pipgrip
            Successfully built jupyterlab-black
            """,
            "jupyterlab_black-0.2.1-py3-none-any.whl",
        ),
        (
            "six",
            """
            Collecting six
              File was already downloaded ~/Library/Caches/pip/wheels/pipgrip/six-1.15.0-py2.py3-none-any.whl
            Skipping six, due to already being wheel.
            """,
            "six-1.15.0-py2.py3-none-any.whl",
        ),
        (
            "six",
            """
            Collecting six
              Using cached six-1.15.0-py2.py3-none-any.whl (10 kB)
              Saved ~/Library/Caches/pip/wheels/pipgrip/six-1.15.0-py2.py3-none-any.whl
            Skipping six, due to already being wheel.
            """,
            "six-1.15.0-py2.py3-none-any.whl",
        ),
        (
            "six",
            """
            Collecting six
              Downloading six-1.15.0-py2.py3-none-any.whl (10 kB)
              Saved ~/Library/Caches/pip/wheels/pipgrip/six-1.15.0-py2.py3-none-any.whl
            Skipping six, due to already being wheel.
            """,
            "six-1.15.0-py2.py3-none-any.whl",
        ),
        (
            "jupyterlab-black",
            """
            Collecting jupyterlab-black
              Downloading jupyterlab_black-0.2.1.tar.gz (3.1 kB)
            Building wheels for collected packages: jupyterlab-black
              Building wheel for jupyterlab-black (setup.py): started
              Building wheel for jupyterlab-black (setup.py): finished with status 'done'
              Created wheel for jupyterlab-black: filename=jupyterlab_black-0.2.1-py3-none-any.whl size=2497 sha256=2d21a5420b39156f7e55da105b8a064889674ae8a1a09f3fd2884c78a994a851
              Stored in directory: ~/Library/Caches/pip/wheels/83/ba/78/469d847858dff4d2e600bff2de9d09bf455bb5be3ffb566af1
            Successfully built jupyterlab-black
            """,
            "jupyterlab_black-0.2.1-py3-none-any.whl",
        ),
        (
            "Keras",
            """
            Collecting Keras
              Using cached https://files.pythonhosted.org/packages/6b/09/756db7ae3dd2ec804963e21db8250ffe347aaba6f6d13d6c0ed833d85109/Keras-2.4.3-py2.py3-none-any.whl
              Saved ~/library/caches/pip/wheels/pipgrip/Keras-2.4.3-py2.py3-none-any.whl
            """,
            "Keras-2.4.3-py2.py3-none-any.whl",
        ),
        (
            "pkginfo>=1.4.2",
            """
            Collecting pkginfo>=1.4.2
              Using cached pkginfo-1.7.0-py2.py3-none-any.whl (25 kB)
            Saved ./Library/Caches/pip/wheels/pipgrip/pkginfo-1.7.0-py2.py3-none-any.whl
            """,
            "pkginfo-1.7.0-py2.py3-none-any.whl",
        ),
    ],
    ids=(
        "pip10 .",
        "pip10 fetched 1",
        "pip10 built 1",
        "pip>10 cached 1",
        "pip>10 cached 2",
        "pip>10 fetched 2",
        "pip>10 built 1",
        "Windows lowercase wheel_dir",
        "cwd_wheel_dir",
    ),
)
def test_download_wheel(package, pip_output, expected, monkeypatch):
    wheel_dir = "~/Library/Caches/pip/wheels/pipgrip"

    def patch_os_walk(*args, **kwargs):
        yield wheel_dir, None, [
            "a.whl",
            "jupyterlab_black-0.2.1-py3-none-any.whl",
            "x.whl",
        ]

    def patch_getmtime(*args, **kwargs):
        return 0

    def patch_pip_output(*args, **kwargs):
        return pip_output

    def patch_getcwd():
        return os.path.expanduser("~")

    monkeypatch.setattr(
        pipgrip.pipper.os,
        "walk",
        patch_os_walk,
    )
    monkeypatch.setattr(
        pipgrip.pipper.os.path,
        "getmtime",
        patch_getmtime,
    )
    monkeypatch.setattr(
        pipgrip.pipper,
        "stream_bash_command",
        patch_pip_output,
    )
    monkeypatch.setattr(
        pipgrip.pipper.os,
        "getcwd",
        patch_getcwd,
    )

    assert _download_wheel(
        package=package,
        index_url="https://pypi.org/simple",
        extra_index_url="https://pypi.org/simple",
        pre=False,
        cache_dir=None,
        no_cache_dir=False,
        wheel_dir=wheel_dir,
    ) == os.path.join(wheel_dir, expected.lstrip(os.path.sep))


@pytest.mark.parametrize(
    "package, pip_output, expected",
    [
        (
            "pip",
            """
            {
              "version": "0",
              "pip_version": "22.2.2",
              "install": [
                {
                  "download_info": {
                    "url": "https://files.pythonhosted.org/packages/50/c2/e06851e8cc28dcad7c155f4753da8833ac06a5c704c109313b8d5a62968a/pip-23.2.1-py3-none-any.whl",
                    "archive_info": {
                      "hash": "sha256=7ccf472345f20d35bdc9d1841ff5f313260c2c33fe417f48c30ac46cccabf5be"
                    }
                  },
                  "is_direct": false,
                  "requested": true,
                  "metadata": {
                    "metadata_version": "2.1",
                    "name": "pip",
                    "version": "23.2.1",
                    "summary": "The PyPA recommended tool for installing Python packages.",
                    "home_page": "https://pip.pypa.io/",
                    "author": "The pip developers",
                    "author_email": "distutils-sig@python.org",
                    "license": "MIT",
                    "classifier": [
                      "Development Status :: 5 - Production/Stable"
                    ],
                    "requires_python": ">=3.7",
                    "project_url": [
                      "Documentation, https://pip.pypa.io",
                      "Source, https://github.com/pypa/pip",
                      "Changelog, https://pip.pypa.io/en/stable/news/"
                    ],
                    "description": "pip - The Python Package Installer"
                  }
                }
              ],
              "environment": {}
            }
            """,
            {
                "version": "0",
                "pip_version": "22.2.2",
                "install": [
                    {
                        "download_info": {
                            "url": "https://files.pythonhosted.org/packages/50/c2/e06851e8cc28dcad7c155f4753da8833ac06a5c704c109313b8d5a62968a/pip-23.2.1-py3-none-any.whl",
                            "archive_info": {
                                "hash": "sha256=7ccf472345f20d35bdc9d1841ff5f313260c2c33fe417f48c30ac46cccabf5be"
                            },
                        },
                        "is_direct": False,
                        "requested": True,
                        "metadata": {
                            "metadata_version": "2.1",
                            "name": "pip",
                            "version": "23.2.1",
                            "summary": "The PyPA recommended tool for installing Python packages.",
                            "home_page": "https://pip.pypa.io/",
                            "author": "The pip developers",
                            "author_email": "distutils-sig@python.org",
                            "license": "MIT",
                            "classifier": [
                                "Development Status :: 5 - Production/Stable"
                            ],
                            "requires_python": ">=3.7",
                            "project_url": [
                                "Documentation, https://pip.pypa.io",
                                "Source, https://github.com/pypa/pip",
                                "Changelog, https://pip.pypa.io/en/stable/news/",
                            ],
                            "description": "pip - The Python Package Installer",
                        },
                    }
                ],
                "environment": {},
            },
        ),
    ],
    ids=("pip",),
)
def test_get_package_report(package, pip_output, expected, monkeypatch):
    def patch_pip_output(*args, **kwargs):
        file_path = args[0][-2]
        with open(file_path, "w") as fp:
            json.dump(json.loads(pip_output), fp)

    def patch_getcwd():
        return os.path.expanduser("~")

    monkeypatch.setattr(
        pipgrip.pipper,
        "stream_bash_command",
        patch_pip_output,
    )

    assert (
        _get_package_report(
            package=package,
            index_url="https://pypi.org/simple",
            extra_index_url="https://pypi.org/simple",
            pre=True,
            cache_dir=None,
            no_cache_dir=False,
        )
        == expected
    )

    assert (
        _get_package_report(
            package=package,
            index_url=None,
            extra_index_url=None,
            pre=False,
            cache_dir=None,
            no_cache_dir=True,
        )
        == expected
    )


@pytest.mark.parametrize(
    "package, pre, pip_output, expected",
    [
        (
            "click",
            True,
            """
            Collecting click==rubbish
              Could not find a version that satisfies the requirement click==rubbish (from versions: 6.6, 6.7.dev0, 6.7, 7.0, 7.1, 7.1.1, 7.1.2)
            No matching distribution found for click==rubbish
            """,
            ["6.6", "6.7.dev0", "6.7", "7.0", "7.1", "7.1.1", "7.1.2"],
        ),
        (
            "click",
            False,
            """
            Collecting click==rubbish
              Could not find a version that satisfies the requirement click==rubbish (from versions: 6.6, 6.7.dev0, 6.7, 7.0, 7.1, 7.1.1, 7.1.2)
            No matching distribution found for click==rubbish
            """,
            ["6.6", "6.7", "7.0", "7.1", "7.1.1", "7.1.2"],
        ),
    ],
    ids=("click pre", "click"),
)
def test_get_available_versions(package, pre, pip_output, expected, monkeypatch):
    def patch_pip_output(*args, **kwargs):
        raise subprocess.CalledProcessError(returncode=1, cmd="", output=pip_output)

    monkeypatch.setattr(
        pipgrip.pipper,
        "stream_bash_command",
        patch_pip_output,
    )

    assert (
        _get_available_versions(
            package=package,
            index_url="https://pypi.org/simple",
            extra_index_url=None,
            pre=pre,
        )
        == expected
    )


def test_stream_bash_command():
    pipgrip.pipper.stream_bash_command("ls", echo=True)
    pipgrip.pipper.stream_bash_command(["ls"])
    with pytest.raises(subprocess.CalledProcessError, match=".nonexist"):
        pipgrip.pipper.stream_bash_command(["cat", ".nonexist"])
