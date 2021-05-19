import os
import subprocess

import pytest

import pipgrip.pipper
from pipgrip.pipper import _download_wheel, _get_available_versions


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
        "Windows lowercase cache_dir",
        "cwd_cache_dir",
    ),
)
def test_download_wheel(package, pip_output, expected, monkeypatch):
    cache_dir = "~/Library/Caches/pip/wheels/pipgrip"

    def patch_os_walk(*args, **kwargs):
        yield cache_dir, None, [
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

    assert (
        _download_wheel(
            package,
            "https://pypi.org/simple",
            "https://pypi.org/simple",
            False,
            cache_dir,
        )
        == os.path.join(cache_dir, expected.lstrip(os.path.sep))
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
        _get_available_versions(package, "https://pypi.org/simple", None, pre)
        == expected
    )
