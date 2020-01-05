import io
import logging
import os
import tempfile
from collections import OrderedDict
from json import dumps

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
        # bug in mixology? discover versions and dependencies anyway  see --stop-early flag and tests
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
            metadata=source._packages_metadata[name][str(resolved_version)],
        )
        if matches:
            if matches[0] in tree_node.ancestors:
                logger.warning(
                    "Cyclic dependency found: %s depends on %s and vice versa.",
                    tree_node.name,
                    tree_parent.name,
                )
                tree_node.parent = None
                tree_node = Node(
                    name,
                    version=resolved_version,
                    parent=tree_parent,
                    metadata=source._packages_metadata[name][str(resolved_version)],
                    cyclic=True,
                )
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


def exhaustive_packages(source, decision_packages):
    tree_root = Node("root")
    exhaustive = _recurse_dependencies(
        source, decision_packages, source._root_dependencies, tree_root, tree_root
    )
    return flatten(exhaustive), tree_root


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
    "--tree",
    is_flag=True,
    help="Output human readable dependency tree (top-down). Overrides --stop-early.",
)
@click.option(
    "--reversed-tree",
    is_flag=True,
    help="Output human readable dependency tree (bottom-up). Overrides --stop-early.",
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
)
@click.option("--index-url", envvar="PIP_INDEX_URL")
@click.option("--extra_index-url", envvar="PIP_EXTRA_INDEX_URL")
@click.option(
    "--stop-early",
    is_flag=True,
    help="Stop top-down recursion when constraints have been solved. Will not result in exhaustive output when dependencies are satisfied and further down the branch no potential clashes exist.",
)
@click.option(
    "--debug", is_flag=True, help="Set logging level to DEBUG.",
)
def main(
    dependencies,
    *,
    lock,
    pipe,
    json,
    tree,
    reversed_tree,
    cache_dir,
    no_cache_dir,
    index_url,
    extra_index_url,
    stop_early,
    debug,
):
    try:
        if debug:
            logger.setLevel(logging.DEBUG)

        if sum((pipe, json, tree, reversed_tree)) > 1:
            raise ValueError("Illegal combination of output formats selected")

        if reversed_tree:
            tree = True
        if tree:
            stop_early = False
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

        logger.debug(decision_packages)

        if stop_early:
            packages = {k: str(v) for k, v in decision_packages.items()}
        else:
            packages, root_tree = exhaustive_packages(source, decision_packages)

        if lock:
            with io.open(
                os.path.join(os.getcwd(), "pipgrip.lock"), mode="w", encoding="utf-8"
            ) as fp:
                fp.write("\n".join(["==".join(x) for x in packages.items()]) + "\n")

        if reversed_tree:
            raise NotImplementedError()
            # TODO tree = reverse_tree(root_tree)
        if tree:
            output = ""
            for child in root_tree.children:
                lines = []
                for pre, _, node in RenderTree(child):
                    lines.append(
                        "{}{} ({}{})".format(
                            pre,
                            node.metadata["pip_string"],
                            node.version,
                            ", cyclic" if hasattr(node, "cyclic") else "",
                        )
                    )
                output += "\n".join(lines)
        elif pipe:
            output = " ".join(["==".join(x) for x in packages.items()])
        elif json:
            output = dumps(packages)
        else:
            output = "\n".join(["==".join(x) for x in packages.items()])
        click.echo(output)
    except SolverFailure as exc:
        raise click.ClickException(str(exc))
    except Exception as exc:
        logger.exception(exc, exc_info=exc)
        raise click.ClickException(str(exc))
