import io
import logging
import os
import tempfile
from collections import OrderedDict
from json import dumps
from subprocess import CalledProcessError

import click
from anytree import Node, RenderTree
from anytree.search import findall_by_attr

from pipgrip.compat import USER_CACHE_DIR
from pipgrip.libs.mixology.failure import SolverFailure
from pipgrip.libs.mixology.package import Package
from pipgrip.libs.mixology.version_solver import VersionSolver
from pipgrip.package_source import PackageSource

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger()
logger.setLevel(logging.ERROR)


def flatten(d):
    out = OrderedDict()
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
        source._versions_for(dep.name, source.convert_dependency(dep).constraint)
    versions = [k for k, v in source._packages[dep.name].items() if v is not None]
    return versions[-1]


def _recurse_dependencies(
    source, decision_packages, dependencies, tree_root, tree_parent
):
    packages = OrderedDict()
    for dep in dependencies:
        name = dep.name
        resolved_version = decision_packages.get(name) or _find_version(source, dep)

        # detect cyclic depenencies
        matches = findall_by_attr(tree_root, name)
        tree_node = Node(
            name,
            version=resolved_version,
            parent=tree_parent,
            # pip_string in metadata might be the wrong one (populated differently beforehand, higher up in the tree)
            # left here in case e.g. versions_available is needed in rendered tree
            metadata=source._packages_metadata[name][str(resolved_version)],
            pip_string=dep.pip_string,
        )
        if matches and matches[0] in tree_node.ancestors:
            logger.warning(
                "Cyclic dependency found: %s depends on %s and vice versa.",
                tree_node.name,
                tree_parent.name,
            )
            setattr(tree_node, "cyclic", True)
            packages[(name, str(resolved_version))] = {}
            continue

        packages[(name, str(resolved_version))] = _recurse_dependencies(
            source,
            decision_packages,
            source._packages[name][resolved_version],
            tree_root,
            tree_node,
        )
    return packages


def build_tree(source, decision_packages):
    tree_root = Node("root")
    exhaustive = _recurse_dependencies(
        source, decision_packages, source._root_dependencies, tree_root, tree_root
    )
    return flatten(exhaustive), tree_root


def render_tree(root_tree, max_depth):
    output = []
    for child in root_tree.children:
        lines = []
        for fill, _, node in RenderTree(child):
            if max_depth and node.depth > max_depth:
                continue
            lines.append(
                u"{}{} ({}{})".format(
                    fill,
                    node.pip_string,
                    node.version,
                    ", cyclic" if hasattr(node, "cyclic") else "",
                )
            )
        output += lines
    return "\n".join(output)


@click.command()
@click.argument("dependencies", nargs=-1)
@click.option(
    "--lock", is_flag=True, help="Write out pins to './pipgrip.lock'.",
)
@click.option(
    "--pipe",
    is_flag=True,
    help="Output space-separated pins instead of newline-separated pins.",
)
@click.option(
    "--json",
    is_flag=True,
    help="Output pins as json dict instead of newline-separated pins.",
)
@click.option(
    "--tree", is_flag=True, help="Output human readable dependency tree (top-down).",
)
@click.option(
    "--reversed-tree",
    is_flag=True,
    help="Output human readable dependency tree (bottom-up).",
)
@click.option(
    "--max-depth",
    type=int,
    default=-1,
    help="Maximum tree rendering depth (defaults to -1).",
)
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
    help="Disable pip cache for the wheels downloaded by pipper. Overrides --cache-dir.",
    # alternatively https://click.palletsprojects.com/en/7.x/options/#boolean-flags
)
@click.option(
    "--index-url",
    envvar="PIP_INDEX_URL",
    default="https://pypi.org/simple",
    help="Base URL of the Python Package Index (default https://pypi.org/simple).",
)
@click.option(
    "--extra_index-url",
    envvar="PIP_EXTRA_INDEX_URL",
    help="Extra URLs of package indexes to use in addition to --index-url.",
)
@click.option(
    "--pre",
    is_flag=True,
    help="Include pre-release and development versions. By default, pip only finds stable versions.",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Control verbosity: -v will print cyclic dependencies (WARNING), -vv will show solving decisions (INFO), -vvv for development (DEBUG).",
)
def main(
    dependencies,
    lock,
    pipe,
    json,
    tree,
    reversed_tree,
    max_depth,
    cache_dir,
    no_cache_dir,
    index_url,
    extra_index_url,
    pre,
    verbose,
):
    if verbose == 1:
        logger.setLevel(logging.WARNING)
    if verbose == 2:
        logger.setLevel(logging.INFO)
    if verbose >= 3:
        logger.setLevel(logging.DEBUG)

    if sum((pipe, json, tree, reversed_tree)) > 1:
        raise click.ClickException("Illegal combination of output formats selected")
    if max_depth == 0 or max_depth < -1:
        raise click.ClickException("Illegal --max_depth selected: {}".format(max_depth))
    if max_depth == -1:
        max_depth = 0
    elif max_depth and not (tree or reversed_tree):
        raise click.ClickException(
            "--max-depth has no effect without --tree or --reversed-tree"
        )

    if reversed_tree:
        tree = True
    if no_cache_dir:
        cache_dir = tempfile.mkdtemp()

    try:
        source = PackageSource(
            cache_dir=cache_dir,
            index_url=index_url,
            extra_index_url=extra_index_url,
            pre=pre,
        )
        for root_dependency in dependencies:
            source.root_dep(root_dependency)

        solver = VersionSolver(source)
        solution = solver.solve()

        decision_packages = OrderedDict()
        for package, version in solution.decisions.items():
            if package == Package.root():
                continue
            decision_packages[package] = version

        logger.debug(decision_packages)

        packages, root_tree = build_tree(source, decision_packages)

        if lock:
            with io.open(
                os.path.join(os.getcwd(), "pipgrip.lock"), mode="w", encoding="utf-8"
            ) as fp:
                # a lockfile containing `.` will break pip install -r
                fp.write(
                    "\n".join(
                        [
                            "==".join(x)
                            for x in packages.items()
                            if not x[0].startswith(".")
                        ]
                    )
                    + "\n"
                )

        if reversed_tree:
            raise NotImplementedError()
            # TODO root_tree = reverse_tree(root_tree)
        if tree:
            output = render_tree(root_tree, max_depth)
        elif pipe:
            output = " ".join(["==".join(x) for x in packages.items()])
        elif json:
            output = dumps(packages)
        else:
            output = "\n".join(["==".join(x) for x in packages.items()])
        click.echo(output)
    except (SolverFailure, click.ClickException, CalledProcessError) as exc:
        raise click.ClickException(str(exc))
    # except Exception as exc:
    #     logger.error(exc, exc_info=exc)
    #     raise click.ClickException(str(exc))
