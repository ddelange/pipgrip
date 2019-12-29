import logging
import os
import tempfile

import click

from pipgrip.compat import USER_CACHE_DIR
from pipgrip.libs.mixology.package import Package
from pipgrip.libs.mixology.version_solver import VersionSolver
from pipgrip.package_source import PackageSource

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


def flatten(d):
    out = {}
    for key0, val0 in d.items():
        out[key0[0]] = key0[1]
        if not val0:
            continue
        for key1, subdict in val0.items():
            out[key1[0]] = key1[1]
            deeper = flatten(subdict).items()
            for key2, val2 in deeper:
                if key2 in out and out[key2] != val2:
                    raise RuntimeError(
                        "{} has not been solved: both {} and {} found... Please report this bug",
                        key2,
                        val0,
                        val2,
                    )
                else:
                    out[key2] = val2
    return out


def _find_version(source, dep):
    if dep.name not in source._packages:
        # bug in mixology? discover versions and dependencies anyway  see --stop-early flag and tests
        source._versions_for(dep.name, source.convert_dependency(dep).constraint)
    versions = [k for k, v in source._packages[dep.name].items() if v is not None]
    return versions[-1]


def _recurse_dependencies(source, decision_packages, dependencies):
    packages = {}
    for dep in dependencies:
        name = dep.name
        resolved_version = decision_packages.get(name) or _find_version(source, dep)
        packages[(name, str(resolved_version))] = _recurse_dependencies(
            source, decision_packages, source._packages[name][resolved_version]
        )
    return packages


def exhaustive_packages(source, decision_packages):
    exhaustive = _recurse_dependencies(
        source, decision_packages, source._root_dependencies
    )
    return flatten(exhaustive)


@click.command()
@click.argument("dependencies", nargs=-1)
@click.option(
    "--cache-dir",
    envvar="PIP_CACHE_DIR",
    type=click.Path(exists=False, dir_okay=True),
    default=os.path.join(USER_CACHE_DIR, "wheels", "pipgrip"),
    help="Use a custom cache dir.",
)
@click.option(
    "--no-cache-dir",
    # envvar='PIP_NO_CACHE_DIR',  #  this would be counter-intuitive https://github.com/pypa/pip/issues/2897#issuecomment-231753826
    is_flag=True,
    help="Disable pip cache for the wheels downloaded by pipper. Overwrites --cache-dir.",
)
@click.option("--index-url", envvar="PIP_INDEX_URL")
@click.option("--extra_index-url", envvar="PIP_EXTRA_INDEX_URL")
@click.option(
    "--stop-early",
    is_flag=True,
    help="Stop top-down recursion when constraints have been solved. Will not result in exhaustive output when dependencies are satisfied and further down the branch no potential clashes exist.",
)
# @click.option(
#     "--tree",
#     is_flag=True,
#     help="Output human readable dependency tree (top-down). Overwrites --stop-early.",
# )
# @click.option(
#     "--reversed-tree",
#     is_flag=True,
#     help="Output human readable dependency tree (bottom-up). Overwrites --tree and --stop-early.",
# )
def main(
    dependencies,
    *,
    cache_dir,
    no_cache_dir,
    index_url,
    extra_index_url,
    tree,
    reversed_tree,
    stop_early
):
    try:
        if no_cache_dir:
            cache_dir = tempfile.TemporaryDirectory().name
        source = PackageSource(
            cache_dir=cache_dir, index_url=index_url, extra_index_url=extra_index_url,
        )

        for root_dependency in dependencies:
            source.root_dep(root_dependency)

        solver = VersionSolver(source)

        solution = solver.solve()

        decision_packages = {}
        for package, version in solution.decisions.items():
            if package == Package.root():
                continue

            decision_packages[package] = version

        logger.info(decision_packages)

        if stop_early:
            packages = {k: str(v) for k, v in decision_packages.items()}
        else:
            packages = exhaustive_packages(source, decision_packages)

        pinned = "\n".join(["==".join(x) for x in packages.items()])
        click.echo(pinned)
        # return pinned
    except Exception as exc:
        logger.exception(exc, exc_info=exc)
        raise click.ClickException(str(exc))
