import io
import json
import logging
import os
import re
import shutil
import subprocess
import sys
from tempfile import NamedTemporaryFile, mkdtemp

import pkg_resources
from click import echo as _echo
from packaging.markers import default_environment
from packaging.utils import canonicalize_name

from pipgrip.compat import PIP_VERSION, urlparse

logger = logging.getLogger(__name__)


def read_requirements(path):
    re_comments = re.compile(r"(?:^|\s+)#")
    try:
        with io.open(path, mode="rt", encoding="utf-8") as fp:
            return list(
                filter(None, (re_comments.split(line, 1)[0].strip() for line in fp))
            )
    except IndexError:
        raise RuntimeError("{} is broken".format(path))


_parse_req_cache = {}


def parse_req(requirement, extras=None):
    extras = extras or set()
    cache_key = (requirement, frozenset(extras))
    if cache_key in _parse_req_cache:
        return _parse_req_cache[cache_key]
    if requirement == "_root_" or requirement == "." or requirement.startswith(".["):
        req = pkg_resources.Requirement.parse(
            requirement.replace(".", "rubbish", 1)
            if requirement.startswith(".[")
            else "rubbish"
        )
        if extras:
            req.extras = extras
        req.key = "." if requirement.startswith(".[") else requirement
        full_str = req.__str__().replace(req.name, req.key)
        req.name = req.key
    else:
        req = pkg_resources.Requirement.parse(requirement)
        if extras:
            req.extras = extras
        req.key = canonicalize_name(req.key)
        req.name = req.key
        full_str = req.__str__()  # .replace(req.name, req.key)

    def __str__():
        return full_str

    req.__str__ = __str__
    req.extras_name = (
        req.name + "[" + ",".join(sorted(req.extras)) + "]" if req.extras else req.name
    )
    req.extras = frozenset(req.extras)
    _parse_req_cache[cache_key] = req
    return req


def stream_bash_command(args, echo=False):
    """Mimic subprocess.run, while processing the command output in real time."""
    # https://gist.github.com/ddelange/6517e3267fb74eeee804e3b1490b1c1d
    out = []
    env = os.environ.copy()
    # Enable Python's UTF-8 mode.
    env["PYTHONUTF8"] = "1"
    process = subprocess.Popen(  # can use with-statement as of py 3.2
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )
    for line in process.stdout:
        decoded_line = line.decode("utf-8", errors="replace")
        out.append(decoded_line)
        if echo:
            _echo(decoded_line.rstrip())
    process.stdout.close()
    out = "".join(out)
    retcode = process.wait()
    if retcode:
        raise subprocess.CalledProcessError(retcode, args, output=out)
    return out


def _get_install_args(
    index_url, extra_index_url, pre, cache_dir, no_cache_dir, editable, user
):
    args = [
        sys.executable,
        "-m",
        "pip",
        "install",
    ]
    if cache_dir is not None:
        args += [
            "--cache-dir",
            cache_dir,
        ]
    if no_cache_dir:
        args += ["--no-cache-dir"]
    if index_url is not None:
        args += [
            "--index-url",
            index_url,
            "--trusted-host",
            urlparse(index_url).hostname,
        ]
    if extra_index_url is not None:
        args += [
            "--extra-index-url",
            extra_index_url,
            "--trusted-host",
            urlparse(extra_index_url).hostname,
        ]
    if PIP_VERSION >= [10]:
        args.append("--progress-bar=off")
    if pre:
        args += ["--pre"]
    if editable:
        args += ["--editable"]
    if user:
        args += ["--user"]
    return args


def _get_wheel_args(
    index_url, extra_index_url, pre, cache_dir=None, no_cache_dir=False, wheel_dir=None
):
    args = [
        sys.executable,
        "-m",
        "pip",
        "wheel",
        "--no-deps",
        "--disable-pip-version-check",
    ]
    if pre:
        args += ["--pre"]
    if wheel_dir is not None:
        args += [
            "--wheel-dir",
            wheel_dir,
        ]
    if cache_dir is not None:
        args += [
            "--cache-dir",
            cache_dir,
        ]
    if no_cache_dir:
        args += ["--no-cache-dir"]
    if index_url is not None:
        args += [
            "--index-url",
            index_url,
            "--trusted-host",
            urlparse(index_url).hostname,
        ]
    if extra_index_url is not None:
        args += [
            "--extra-index-url",
            extra_index_url,
            "--trusted-host",
            urlparse(extra_index_url).hostname,
        ]
    if PIP_VERSION >= [10]:
        args.append("--progress-bar=off")
    return args


def install_packages(
    packages,
    index_url,
    extra_index_url,
    pre,
    cache_dir,
    editable,
    user,
    constraints=None,
    no_cache_dir=False,
):
    """Install a list of packages with pip."""
    args = (
        _get_install_args(
            index_url=index_url,
            extra_index_url=extra_index_url,
            pre=pre,
            cache_dir=cache_dir,
            no_cache_dir=no_cache_dir,
            editable=editable,
            user=user,
        )
        + packages
    )

    constraints_file = None
    if constraints is not None:
        logger.debug(constraints)
        with NamedTemporaryFile(delete=False, mode="w+") as fp:
            constraints_file = fp.name
            fp.write("\n".join(constraints) + "\n")
        args += ["--constraint", constraints_file]

    try:
        return stream_bash_command(args, echo=True)
    except subprocess.CalledProcessError as err:
        output = getattr(err, "output") or ""
        logger.error(output)
        raise
    finally:
        if constraints_file is not None:
            os.remove(constraints_file)


_available_versions_cache = {}


def _get_available_versions(package, index_url, extra_index_url, pre):
    cache_key = (package, pre)
    if cache_key in _available_versions_cache:
        return _available_versions_cache[cache_key]

    logger.debug("Finding possible versions for {}".format(package))
    args = _get_wheel_args(
        index_url=index_url, extra_index_url=extra_index_url, pre=pre
    ) + [package + "==42.42.post424242"]

    if [20, 3] <= PIP_VERSION < [21, 1]:
        # https://github.com/ddelange/pipgrip/issues/42
        args += ["--use-deprecated", "legacy-resolver"]

    try:
        out = stream_bash_command(args)
    except subprocess.CalledProcessError as err:
        # expected. we forced this by using a non-existing version number.
        out = getattr(err, "output") or ""
    else:
        logger.warning(out)
        raise RuntimeError("Unexpected success:" + " ".join(args))
    out = out.splitlines()
    for line in out[::-1]:
        if "Could not find a version that satisfies the requirement" in line:
            all_versions = line.split("from versions: ", 1)[1].rstrip(")").split(", ")
            if pre:
                return all_versions
            # filter out pre-releases
            available_versions = [
                v for v in all_versions if not re.findall(r"[a-zA-Z]", v)
            ]
            _available_versions_cache[cache_key] = available_versions
            return available_versions
    raise RuntimeError("Failed to get available versions for {}".format(package))


def _get_package_report(
    package,
    index_url,
    extra_index_url,
    pre,
    cache_dir,
    no_cache_dir,
):
    """Get metadata (install report) using pip's --dry-run --report functionality."""
    logger.debug(
        "Getting report for {} (with fallback cache_dir {})".format(package, cache_dir)
    )
    args = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "-qq",
        "--no-deps",
        "--ignore-installed",
        "--disable-pip-version-check",
        "--dry-run",
    ]
    if pre:
        args += ["--pre"]
    if cache_dir is not None:
        args += [
            "--cache-dir",
            cache_dir,
        ]
    if no_cache_dir:
        args += ["--no-cache-dir"]
    if index_url is not None:
        args += [
            "--index-url",
            index_url,
            "--trusted-host",
            urlparse(index_url).hostname,
        ]
    if extra_index_url is not None:
        args += [
            "--extra-index-url",
            extra_index_url,
            "--trusted-host",
            urlparse(extra_index_url).hostname,
        ]
    args += ["--report", "-", package]
    try:
        out = stream_bash_command(args)
    except subprocess.CalledProcessError as err:
        output = getattr(err, "output") or ""
        logger.error(
            "Getting report for {} failed with output:\n{}".format(
                package, output.strip()
            )
        )
        raise RuntimeError("Failed to get report for {}".format(package))
    report = json.loads(out)
    return report


def _download_wheel(
    package,
    index_url,
    extra_index_url,
    pre,
    cache_dir,
    no_cache_dir,
    wheel_dir,
):
    """Download/build wheel for package and return its filename."""
    logger.debug(
        "Downloading/building wheel for {} into wheel_dir {}".format(package, wheel_dir)
    )
    abs_wheel_dir = os.path.abspath(os.path.expanduser(wheel_dir))
    cwd_wheel_dir = abs_wheel_dir.replace(os.getcwd(), ".", 1)
    args = _get_wheel_args(
        index_url=index_url,
        extra_index_url=extra_index_url,
        pre=pre,
        cache_dir=cache_dir,
        no_cache_dir=no_cache_dir,
        wheel_dir=wheel_dir,
    ) + [package]
    try:
        out = stream_bash_command(args)
    except subprocess.CalledProcessError as err:
        output = getattr(err, "output") or ""
        logger.error(
            "Downloading/building wheel for {} failed with output:\n{}".format(
                package, output.strip()
            )
        )
        raise RuntimeError("Failed to download/build wheel for {}".format(package))
    out = out.splitlines()[::-1]
    abs_wheel_dir_lower = abs_wheel_dir.lower()
    cwd_wheel_dir_lower = cwd_wheel_dir.lower()
    wheel_dir_lower = wheel_dir.lower()
    for i, line in enumerate(out):
        line = line.strip()
        line_lower = line.lower()
        if not (
            wheel_dir_lower in line_lower
            or abs_wheel_dir_lower in line_lower
            or cwd_wheel_dir_lower in line_lower
            or "stored in directory" in line_lower
        ):
            continue

        if "stored in directory" in line_lower:
            # wheel was built
            fnames = [
                part.replace("filename=", "")
                for part in out[i + 1].split()
                if part.startswith("filename=")
            ]
            if not fnames:
                # older pip might not state filename, only directory
                whldir = line.replace("Stored in directory:", "").strip()
                dirpath, _, filenames = next(os.walk(whldir))
                all_wheels = sorted(
                    (f for f in filenames if f.endswith(".whl")),
                    key=lambda x: os.path.getmtime(os.path.join(dirpath, x)),
                    reverse=True,
                )
                if package.startswith("."):
                    fname = all_wheels[0]
                else:
                    fname = None
                    pkg = parse_req(package).key
                    for whl in all_wheels:
                        if pkg in canonicalize_name(whl):
                            fname = whl
                            break
                    if not fname:
                        logger.error(
                            "Failed to extract wheel filename from pip stdout: \n{}".format(
                                "\n".join(out[::-1])
                            )
                        )
                        raise RuntimeError(
                            "Failed to find wheel for {} in {}. Wheels found: {}".format(
                                package, whldir, all_wheels
                            )
                        )
            else:
                fname = fnames[0]
        else:
            # wheel was fetched
            # match on lowercase line for windows compatibility
            fname_len = len(
                line_lower.split(
                    abs_wheel_dir_lower
                    if abs_wheel_dir_lower in line_lower
                    else cwd_wheel_dir_lower
                    if cwd_wheel_dir_lower in line_lower
                    else wheel_dir_lower,
                    1,
                )[1].split(".whl", 1)[0]
                + ".whl"
            )
            fname = line[-fname_len:]

        logger.debug(str({package: os.path.join(wheel_dir, fname.lstrip(os.path.sep))}))
        return os.path.join(wheel_dir, fname.lstrip(os.path.sep))
    logger.error(
        "Failed to extract wheel filename from pip stdout: \n{}".format(
            "\n".join(out[::-1])
        )
    )
    raise RuntimeError("Failed to download/build wheel for {}".format(package))


def _extract_metadata(wheel_fname):
    from pkginfo import get_metadata  # not required on python 3.7+

    wheel_fname = os.path.abspath(wheel_fname)
    logger.debug("Searching metadata in %s", wheel_fname)
    if not os.path.exists(wheel_fname):
        raise RuntimeError("File not found: {}".format(wheel_fname))
    info = get_metadata(wheel_fname)
    if info is None:
        raise RuntimeError("Failed to extract metadata: {}".format(wheel_fname))
    data = vars(info)
    data.pop("filename", None)
    return data


def _get_wheel_requirements(metadata, extras_requested):
    """Extract the immediate dependencies from wheel metadata."""
    all_requires = metadata.get("requires_dist", [])
    if not all_requires:
        return []
    result = []
    env_data = default_environment()
    for req_str in all_requires:
        req = parse_req(req_str)
        req_short, _sep, _marker = str(req).partition(";")
        if req.marker is None:
            # unconditional dependency
            result.append(req_short)
            continue
        # conditional dependency - must be evaluated in environment context
        for extra in [None] + extras_requested:
            if req.marker.evaluate(dict(env_data, extra=extra)):
                logger.debug("included conditional dep %s", req_str)
                result.append(req_short)
                break
        else:
            logger.debug("dropped conditional dep %s", req_str)
    result = sorted(set(result))  # this makes the dep tree deterministic/repeatable
    return result


def is_unneeded_dep(package):
    """Evaluate a single package in the context of the current environment."""
    return not _get_wheel_requirements({"requires_dist": [package]}, [])


def discover_dependencies_and_versions(
    package,
    index_url,
    extra_index_url,
    cache_dir,
    pre,
    no_cache_dir=False,  # added as last arg with default to avoid a breaking change
):
    """Get information for a package.

    Args:
        package (str): pip requirement format spec compliant package
        index_url (str): primary PyPI index url
        extra_index_url (str): secondary PyPI index url
        cache_dir (str): directory for storing wheels
        pre (bool): pip --pre flag
        no_cache_dir (bool): pip --no-cache-dir flag

    Returns:
        dict: package information:
            'version': the version resolved by pip
            'available': all available versions resolved by pip
            'requires': all requirements as found in corresponding wheel (dist_requires)

    """
    req = parse_req(package)

    extras_requested = sorted(req.extras)

    logger.info("discovering %s", req)
    if PIP_VERSION >= [22, 2]:
        report = _get_package_report(
            package=req.__str__(),
            index_url=index_url,
            extra_index_url=extra_index_url,
            pre=pre,
            cache_dir=cache_dir,
            no_cache_dir=no_cache_dir,
        )
        wheel_metadata = report["install"][0]["metadata"]
    else:  # old python (<=3.6) fallback
        wheel_dir = mkdtemp()
        try:
            wheel_fname = _download_wheel(
                package=req.__str__(),
                index_url=index_url,
                extra_index_url=extra_index_url,
                pre=pre,
                cache_dir=cache_dir,
                no_cache_dir=no_cache_dir,
                wheel_dir=wheel_dir,
            )
            wheel_metadata = _extract_metadata(wheel_fname)
        finally:
            shutil.rmtree(wheel_dir)
    wheel_requirements = _get_wheel_requirements(wheel_metadata, extras_requested)
    wheel_version = req.url or wheel_metadata["version"]
    available_versions = (
        _get_available_versions(req.name, index_url, extra_index_url, pre)
        if req.key != "." and req.url is None
        else [wheel_version]
    )
    if wheel_version not in available_versions:
        available_versions.append(wheel_version)

    return {
        "name": wheel_metadata["name"],
        "version": wheel_version,
        "available": available_versions,
        "requires": wheel_requirements,
    }
