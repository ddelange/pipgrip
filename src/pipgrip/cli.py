import io
import logging
import os
import shutil
import tempfile
from collections import OrderedDict
from functools import partial
from json import dumps
from subprocess import CalledProcessError

import click
from anytree import AsciiStyle, ContStyle, Node, RenderTree
from anytree.exporter import DictExporter
from anytree.search import findall_by_attr
from packaging.markers import default_environment

from pipgrip.compat import PIP_VERSION, USER_CACHE_DIR
from pipgrip.libs.mixology.failure import SolverFailure
from pipgrip.libs.mixology.package import Package
from pipgrip.libs.mixology.version_solver import VersionSolver
from pipgrip.package_source import PackageSource
from pipgrip.pipper import install_packages, read_requirements

logging.basicConfig(format="%(levelname)s: %(message)s")
logger = logging.getLogger()


class DepTreeDictExporter(DictExporter):
    """Export nested tree in full detail, children renamed to dependencies."""

    def __init__(
        self, dictcls=OrderedDict, attriter=None, childiter=list, maxlevel=None
    ):
        DictExporter.__init__(
            self,
            dictcls=dictcls,
            attriter=attriter,
            childiter=childiter,
            maxlevel=maxlevel,
        )

    @classmethod
    def customsort(cls, tup):
        order = ["name", "extras_name", "version", "pip_string"]
        k, v = tup
        if k in order:
            return order.index(k)
        return tup

    def export(self, node):
        """Export tree starting at `node`."""
        attriter = self.attriter or partial(sorted, key=self.customsort)
        return self.__export(node, self.dictcls, attriter, self.childiter)

    def __export(self, node, dictcls, attriter, childiter, level=1):
        attr_values = attriter(self._iter_attr_values(node))
        data = dictcls(attr_values)
        maxlevel = self.maxlevel
        if maxlevel is None or level < maxlevel:
            children = [
                self.__export(child, dictcls, attriter, childiter, level=level + 1)
                for child in childiter(node.children)
            ]
            if children:
                data["dependencies"] = children
        return data


def flatten(tree_dict):
    """Flatten tree_dict to a shallow OrderedDict with all unique exact pins."""
    out = OrderedDict()
    for key0, val0 in tree_dict.items():
        out[key0[0]] = key0[1]
        if not val0:
            continue
        for key1, subdict in val0.items():
            out[key1[0]] = key1[1]
            deeper = flatten(subdict).items()
            for key2, val2 in deeper:
                if key2 in out and out[key2] != val2:
                    raise RuntimeError(
                        "{} has not been solved: both {} and {} found... Please file an issue on GitHub.",
                        key2,
                        val0,
                        val2,
                    )
                else:
                    out[key2] = val2
    return out


def _find_version(source, dep, extras):
    if dep.package not in source._packages:
        source._versions_for(dep.package, source.convert_dependency(dep).constraint)
    versions = [
        k for k, v in source._packages[dep.package][extras].items() if v is not None
    ]
    return versions[-1]


def _recurse_dependencies(
    source, decision_packages, dependencies, tree_root, tree_parent
):
    packages = OrderedDict()
    for dep in dependencies:
        name = dep.name
        extras = dep.package.req.extras
        resolved_version = decision_packages.get(dep.package) or _find_version(
            source, dep, extras
        )

        tree_node = Node(
            name,
            version=str(resolved_version),
            parent=tree_parent,
            # pip_string in metadata might be the wrong one (populated differently beforehand, higher up in the tree)
            # left here in case e.g. versions_available is needed in rendered tree
            # metadata=source._packages_metadata[name][str(resolved_version)],
            pip_string=dep.pip_string,
            extras_name=dep.package.req.extras_name,
        )

        # detect cyclic depenencies
        matches = findall_by_attr(tree_root, name)
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
            source.dependencies_for(dep.package, resolved_version),
            tree_root,
            tree_node,
        )
    return packages


def build_tree(source, decision_packages):
    tree_root = Node("__root__")
    exhaustive_tree_dict = _recurse_dependencies(
        source, decision_packages, source._root_dependencies, tree_root, tree_root
    )
    exhaustive_tree_dict_flat = flatten(exhaustive_tree_dict)
    return tree_root, exhaustive_tree_dict, exhaustive_tree_dict_flat


def render_tree(tree_root, max_depth, tree_ascii=False):
    style = AsciiStyle() if tree_ascii else ContStyle()
    output = []
    for child in tree_root.children:
        lines = []
        for fill, _, node in RenderTree(child, style=style):
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


def render_json_tree(tree_root, max_depth, exact):
    json_tree = OrderedDict()
    for child in tree_root.children:
        if max_depth and child.depth > max_depth:
            continue
        key = (
            "{}=={}".format(child.extras_name, child.version)
            if exact
            else child.pip_string
        )
        json_tree[key] = render_json_tree(child, max_depth, exact)
    return json_tree


def render_json_tree_full(tree_root, max_depth, sort):
    maxlevel = max_depth + 1 if max_depth else None
    exporter = DepTreeDictExporter(maxlevel=maxlevel, attriter=sorted if sort else None)
    tree_dict_full = exporter.export(tree_root)["dependencies"]
    return tree_dict_full


def render_lock(packages, include_dot=True, sort=False):
    fn = sorted if sort else list
    return fn(
        "==".join(x) if not x[0].startswith(".") else x[0]
        for x in packages.items()
        if include_dot or not x[0].startswith(".")
    )


@click.command(
    context_settings={"help_option_names": ["-h", "--help"], "max_content_width": 84},
    help="pipgrip is a lightweight pip dependency resolver with deptree preview functionality based on the PubGrub algorithm, which is also used by poetry. For one or more PEP 508 dependency specifications, pipgrip recursively fetches/builds the Python wheels necessary for version solving, and optionally renders the full resulting dependency tree.",
)
@click.argument("dependencies", nargs=-1)
@click.option(
    "--install", is_flag=True, help="Install full dependency tree after resolving.",
)
@click.option(
    "-e", "--editable", is_flag=True, help="Install a project in editable mode.",
)
@click.option(
    "--user",
    is_flag=True,
    help=r"Install to the Python user install directory for your platform -- typically ~/.local/, or %APPDATA%\Python on Windows.",
)
@click.option(
    "-r",
    "--requirements-file",
    multiple=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True),
    help="Install from the given requirements file. This option can be used multiple times.",
)
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
    help="Output pins as JSON dict instead of newline-separated pins. Combine with --tree for a detailed nested JSON dependency tree.",
)
@click.option(
    "--sort",
    is_flag=True,
    help="Sort pins alphabetically before writing out. Can be used bare, or in combination with --lock, --pipe, --json, --tree-json, or --tree-json-exact.",
)
@click.option(
    "--tree",
    is_flag=True,
    help="Output human readable dependency tree (top-down). Combine with --json for a detailed nested JSON dependency tree. Use --tree-json instead for a simplified JSON dependency tree (requirement strings as keys, dependencies as values), or --json-tree-exact for exact pins as keys.",
)
@click.option(
    "--tree-ascii",
    is_flag=True,
    help="Output human readable dependency tree with ASCII tree markers.",
)
@click.option(
    "--tree-json",
    is_flag=True,
    hidden=True,
    help="Output nested JSON dependency tree (top-down).",
)
@click.option(
    "--tree-json-exact",
    is_flag=True,
    hidden=True,
    help="Output nested JSON tree with exact pins.",
)
@click.option(
    "--reversed-tree",
    is_flag=True,
    help="Output human readable dependency tree (bottom-up).",
)
@click.option(
    "--max-depth",
    type=click.INT,
    default=-1,
    help="Maximum (JSON) tree rendering depth (default -1).",
)
@click.option(
    "--cache-dir",
    envvar="PIP_CACHE_DIR",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True),
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
    "--extra-index-url",
    envvar="PIP_EXTRA_INDEX_URL",
    help="Extra URLs of package indexes to use in addition to --index-url.",
)
@click.option(
    "--pre",
    is_flag=True,
    help="Include pre-release and development versions. By default, pip implicitly excludes pre-releases (unless specified otherwise by PEP 440).",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Control verbosity: -v will print cyclic dependencies (WARNING), -vv will show solving decisions (INFO), -vvv for development (DEBUG).",
)
def main(
    dependencies,
    requirements_file,
    install,
    editable,
    user,
    lock,
    pipe,
    json,
    sort,
    tree,
    tree_ascii,
    tree_json,
    tree_json_exact,
    reversed_tree,
    max_depth,
    cache_dir,
    no_cache_dir,
    index_url,
    extra_index_url,
    pre,
    verbose,
):
    if verbose == 0:
        logger.setLevel(logging.ERROR)
    if verbose == 1:
        logger.setLevel(logging.WARNING)
    if verbose == 2:
        logger.setLevel(logging.INFO)
    if verbose >= 3:
        logger.setLevel(logging.DEBUG)
        logger.debug("Environment: {}".format(default_environment()))
        logger.debug("Pip version: {}".format(PIP_VERSION))

    if (
        sum(
            (
                pipe,
                (json or tree),
                tree_ascii,
                tree_json,
                tree_json_exact,
                reversed_tree,
            )
        )
        > 1
    ):
        raise click.ClickException("Illegal combination of output formats selected")

    if tree_ascii or reversed_tree:
        tree = True
    elif tree_json_exact:
        tree_json = True

    if max_depth == 0 or max_depth < -1:
        raise click.ClickException("Illegal --max_depth selected: {}".format(max_depth))
    if max_depth == -1:
        max_depth = 0
    elif max_depth and not (tree or tree_json or reversed_tree):
        raise click.ClickException(
            "--max-depth has no effect without --tree, --tree-json, --tree-json-exact, or --reversed-tree"
        )

    if requirements_file:
        if dependencies:
            raise click.ClickException(
                "-r can not be used in conjunction with directly passed requirements"
            )
        dependencies = []
        for path in requirements_file:
            dependencies += read_requirements(path)

    if editable:
        if not install:
            raise click.ClickException("--editable has no effect without --install")
        if not sorted(dependencies)[0].startswith("."):
            raise click.ClickException(
                "--editable does not accept input '{}'".format(" ".join(dependencies))
            )
    if user:
        if not install:
            raise click.ClickException("--user has no effect without --install")

    for dep in dependencies:
        if os.sep in dep:
            raise click.ClickException(
                "'{}' looks like a path, and is not supported yet by pipgrip".format(
                    dep
                )
            )

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

        tree_root, packages_tree_dict, packages_flat = build_tree(
            source, decision_packages
        )

        if lock:
            with io.open(
                os.path.join(os.getcwd(), "pipgrip.lock"), mode="w", encoding="utf-8"
            ) as fp:
                # a lockfile containing `.` will break pip install -r
                fp.write(
                    "\n".join(render_lock(packages_flat, include_dot=False, sort=sort))
                    + "\n"
                )

        if reversed_tree:
            raise NotImplementedError()
            # TODO tree_root = reverse_tree(tree_root)
        if tree:
            if json:
                output = dumps(render_json_tree_full(tree_root, max_depth, sort))
            else:
                output = render_tree(tree_root, max_depth, tree_ascii)
        elif tree_json:
            output = dumps(
                render_json_tree(tree_root, max_depth, tree_json_exact), sort_keys=sort
            )
        elif pipe:
            output = " ".join(render_lock(packages_flat, include_dot=True, sort=sort))
        elif json:
            output = dumps(packages_flat, sort_keys=sort)
        else:
            output = "\n".join(render_lock(packages_flat, include_dot=True, sort=sort))
        click.echo(output)

        if install:
            install_packages(
                # sort to ensure . is added right after --editable
                packages=sorted(dependencies),
                constraints=render_lock(packages_flat, include_dot=False, sort=True),
                index_url=index_url,
                extra_index_url=extra_index_url,
                pre=pre,
                cache_dir=cache_dir,
                editable=editable,
                user=user,
            )
    except (SolverFailure, click.ClickException, CalledProcessError) as exc:
        raise click.ClickException(str(exc))
    finally:
        if no_cache_dir:
            shutil.rmtree(cache_dir)
