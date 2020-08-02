import io
import logging
import os
import re
import subprocess
import sys
from tempfile import NamedTemporaryFile

import pkg_resources
from click import echo as _echo
from packaging.markers import default_environment
from packaging.utils import canonicalize_name
from pkginfo import get_metadata

from pipgrip.compat import PIP_VERSION, urlparse

logger = logging.getLogger(__name__)


def read_requirements(path):
    try:
        with io.open(path, mode="rt", encoding="utf-8") as fp:
            return list(filter(None, (line.split("#")[0].strip() for line in fp)))
    except IndexError:
        raise RuntimeError("{} is broken".format(path))


def parse_req(requirement, extras=None):
    from pipgrip.libs.mixology.package import Package

    if isinstance(requirement, Package) and extras != requirement.req.extras:
        raise RuntimeError(
            "Conflict between package extras and extras kwarg. Please file an issue on GitHub."
        )
    if requirement.startswith("."):
        req = pkg_resources.Requirement.parse(requirement.replace(".", "rubbish", 1))
        if extras is not None:
            req.extras = extras
        req.key = "."
        full_str = req.__str__().replace(req.name, req.key)
        req.name = req.key
    else:
        req = pkg_resources.Requirement.parse(requirement)
        if extras is not None:
            req.extras = extras
        req.key = canonicalize_name(req.key)
        req.name = req.key
        full_str = req.__str__()  # .replace(req.name, req.key)

    def __str__():
        return full_str

    req.__str__ = __str__
    req.extras_name = (
        req.name + "[" + ",".join(req.extras) + "]" if req.extras else req.name
    )
    req.extras = frozenset(req.extras)
    return req


def stream_bash_command(bash_command, echo=False):
    # https://gist.github.com/jaketame/3ed43d1c52e9abccd742b1792c449079
    # https://gist.github.com/bgreenlee/1402841
    logger.debug(bash_command)
    process = subprocess.Popen(
        bash_command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )

    def check_io():
        output = ""
        while True:
            line = process.stdout.readline().decode("utf-8")
            if line:
                output += line
                if echo:
                    _echo(line[:-1])
            else:
                break
        return output

    # keep checking stdout/stderr until the child exits
    out = ""
    while process.poll() is None:
        out += check_io()

    return_code = process.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, bash_command, output=out)

    return out


def _get_install_args(index_url, extra_index_url, pre, cache_dir, editable, user):
    args = [
        sys.executable,
        "-m",
        "pip",
        "install",
        "--cache-dir",
        cache_dir,
    ]
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


def _get_wheel_args(index_url, extra_index_url, pre, cache_dir=None):
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
    if cache_dir is not None:
        args += [
            "--wheel-dir",
            cache_dir,
        ]
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
):
    """Install a list of packages with pip."""
    args = (
        _get_install_args(index_url, extra_index_url, pre, cache_dir, editable, user)
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


def _get_available_versions(package, index_url, extra_index_url, pre):
    logger.debug("Finding possible versions for {}".format(package))
    args = _get_wheel_args(index_url, extra_index_url, pre) + [package + "==rubbish"]

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
            logger.debug(
                str(
                    {
                        package: [
                            v for v in all_versions if not re.findall(r"[a-zA-Z]", v)
                        ]
                    }
                )
            )
            return [v for v in all_versions if not re.findall(r"[a-zA-Z]", v)]
    raise RuntimeError("Failed to get available versions for {}".format(package))


def _download_wheel(package, index_url, extra_index_url, pre, cache_dir):
    """Download/build wheel for package and return its filename."""
    logger.debug("Downloading/building wheel for {}".format(package))
    abs_cache_dir = os.path.abspath(os.path.expanduser(cache_dir))
    args = _get_wheel_args(index_url, extra_index_url, pre, cache_dir) + [package]
    try:
        out = stream_bash_command(args)
    except subprocess.CalledProcessError as err:
        output = getattr(err, "output") or ""
        logger.error(output)
        raise
    out = out.splitlines()[::-1]
    abs_cache_dir_lower = abs_cache_dir.lower()
    cache_dir_lower = cache_dir.lower()
    for i, line in enumerate(out):
        line = line.strip()
        line_lower = line.lower()
        if (
            cache_dir_lower in line_lower
            or abs_cache_dir_lower in line_lower
            or "stored in directory" in line_lower
        ):
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
                        pkg = canonicalize_name(package)
                        for whl in all_wheels:
                            if pkg in canonicalize_name(whl):
                                fname = whl
                                break
                else:
                    fname = fnames[0]
            else:
                # wheel was fetched
                # match on lowercase line for windows compatibility
                fname_len = len(
                    line_lower.split(
                        abs_cache_dir_lower
                        if abs_cache_dir_lower in line_lower
                        else cache_dir_lower,
                        1,
                    )[1].split(".whl", 1)[0]
                    + ".whl"
                )
                fname = line[-fname_len:]

            logger.debug(
                str({package: os.path.join(cache_dir, fname.lstrip(os.path.sep))})
            )
            return os.path.join(cache_dir, fname.lstrip(os.path.sep))
    logger.error(
        "Failed to extract wheel filename from pip stdout: \n{}".format(
            "\n".join(out[::-1])
        )
    )
    raise RuntimeError("Failed to download wheel for {}".format(package))


def _extract_metadata(wheel_fname):
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


def discover_dependencies_and_versions(
    package, index_url, extra_index_url, cache_dir, pre
):
    """Get information for a package.

    Args:
        package (str): pip requirement format spec compliant package
        index_url (str): primary PyPI index url
        extra_index_url (str): secondary PyPI index url
        cache_dir (str): directory for storing wheels
        pre (bool): pip --pre flag

    Returns:
        dict: package information:
            'version': the version resolved by pip
            'available': all available versions resolved by pip
            'requires': all requirements as found in corresponding wheel (dist_requires)

    """
    req = parse_req(package)
    extras_requested = sorted(req.extras)

    wheel_fname = _download_wheel(
        req.__str__(), index_url, extra_index_url, pre, cache_dir
    )
    wheel_metadata = _extract_metadata(wheel_fname)
    wheel_requirements = _get_wheel_requirements(wheel_metadata, extras_requested)
    wheel_version = wheel_metadata["version"]
    available_versions = (
        _get_available_versions(req.extras_name, index_url, extra_index_url, pre)
        if req.key != "."
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
