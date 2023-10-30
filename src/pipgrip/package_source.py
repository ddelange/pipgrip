import logging
from typing import Any, Dict, Hashable, List, Optional

from pipgrip.libs.mixology.constraint import Constraint
from pipgrip.libs.mixology.package import Package
from pipgrip.libs.mixology.package_source import PackageSource as BasePackageSource
from pipgrip.libs.mixology.range import Range
from pipgrip.libs.mixology.union import Union
from pipgrip.libs.semver import Version, VersionRange, parse_constraint
from pipgrip.pipper import (
    discover_dependencies_and_versions,
    is_unneeded_dep,
    parse_req,
)

logger = logging.getLogger(__name__)


def is_vcs_version(version):  # type: (str) -> bool
    return Version.parse(version).is_vcs()


def render_pin(package, version):  # type: (str, str) -> str
    if package.startswith("."):
        return package
    sep = " @ " if is_vcs_version(version) else "=="
    return sep.join((package, version))


class Dependency:
    def __init__(self, name, constraint, pip_string):  # type: (str, str) -> None
        self.name = name
        self.constraint = parse_constraint(constraint or "*")
        self.pretty_constraint = constraint
        self.pip_string = pip_string
        self.package = Package(pip_string)

    def __str__(self):  # type: () -> str
        return self.pretty_constraint

    def __repr__(self):  # type: () -> str
        return "Dependency({}, {})".format(self.pip_string, self.pretty_constraint)


class PackageSource(BasePackageSource):
    """Describe requirements, and discover dependencies on demand.

    Provides information about specifications and dependencies to the resolver,
    allowing the VersionResolver class to remain generic while still providing power
    and flexibility.

    This contract contains the methods that users of Mixology must implement
    using knowledge of their own model classes.

    Note that the following concepts needs to be implemented
    in order to make the resolver work as best as possible:


    ## Package

    This user-defined class will be used to represent
    the various packages being resolved.

    __str__() will be called when providing information and feedback,
    in most cases it should return the name of the package.

    It also should implement __eq__ and __hash__.


    ## Version

    This user-defined class will be used to represent a single version.

    Versions of the same package will be compared to each other, however
    they do not need to store their associated package.

    As such they should be comparable. __str__() should also preferably be defined.


    ## Dependency

    This user-defined class represents a requirement of a package to another.

    It is returned by dependencies_for(package, version) and will be passed to
    convert_dependency(dependency) to convert it to a format Mixology understands.

    __eq__() should be defined.

    """

    def __init__(
        self,
        cache_dir,
        no_cache_dir,
        index_url,
        extra_index_url,
        pre,
    ):  # type: () -> None
        self._root_version = Version.parse("0.0.0")
        self._root_dependencies = []
        self._packages = {}
        self._packages_metadata = {}
        self.cache_dir = cache_dir
        self.no_cache_dir = no_cache_dir
        self.index_url = index_url
        self.extra_index_url = extra_index_url
        self.pre = pre

        super(PackageSource, self).__init__()

    @property
    def root_version(self):
        return self._root_version

    def add(
        self, name, extras, version, deps=None
    ):  # type: (str, str, Optional[Dict[str, str]]) -> None
        version = Version.parse(version)
        if name not in self._packages:
            self._packages[name] = {extras: {}}
        if extras not in self._packages[name]:
            self._packages[name][extras] = {}

        if version in self._packages[name][extras]:
            if self._packages[name][extras][version] is not None:
                if deps is not None:
                    raise ValueError("{} ({}) already exists".format(name, version))
                # already discovered, now called with deps is None from discovering a different version
                return

        # not existing and deps undiscovered
        if deps is None:
            self._packages[name][extras][version] = None
            return

        # not existing and deps now discovered
        dependencies = []
        for dep in deps:
            req = parse_req(dep)
            constraint = req.url or ",".join(["".join(tup) for tup in req.specs])
            dependencies.append(Dependency(req.key, constraint, req.__str__()))

        self._packages[name][extras][version] = dependencies

    def discover_and_add(self, package):  # type: (str, str) -> None
        # converting from semver constraint to pkg_resources string
        req = parse_req(package)
        to_create = discover_dependencies_and_versions(
            package=package,
            index_url=self.index_url,
            extra_index_url=self.extra_index_url,
            cache_dir=self.cache_dir,
            no_cache_dir=self.no_cache_dir,
            pre=self.pre,
        )
        for version in to_create["available"]:
            self.add(req.key, req.extras, version)
        self.add(
            req.key,
            req.extras,
            to_create["version"],
            deps=to_create["requires"],
        )

        # currently unused
        if req.key not in self._packages_metadata:
            self._packages_metadata[req.key] = {}
        self._packages_metadata[req.key][to_create["version"]] = {
            "pip_string": req.__str__(),
            "requires": to_create["requires"],
            "available": to_create["available"],
        }

    def root_dep(self, package):  # type: (str, str) -> None
        if is_unneeded_dep(package):
            return
        req = parse_req(package)
        constraint = req.url or ",".join(["".join(tup) for tup in req.specs])
        self._root_dependencies.append(Dependency(req.key, constraint, req.__str__()))

    def _versions_for(
        self, package, constraint=None
    ):  # type: (Hashable, Any) -> List[Hashable]
        """Search for the specifications that match the given constraint.

        Called by BasePackageSource.versions_for

        """
        extras = package.req.extras
        if package not in self._packages or extras not in self._packages[package]:
            # unseen package, safe to take initially parsed req directly
            self.discover_and_add(package.req.__str__())
        if package not in self._packages:
            return []

        versions = []
        for version in self._packages[package][extras].keys():
            if not constraint or constraint.allows_any(
                Range(version, version, True, True)
            ):
                versions.append(version)

        return sorted(versions, reverse=True)

    def dependencies_for(self, package, version):  # type: (Hashable, Any) -> List[Any]
        req = package.req
        if package == self.root:
            return self._root_dependencies

        if (
            req.extras not in self._packages[package]
            or self._packages[package][req.extras][version] is None
        ):
            # populate dependencies for version
            self.discover_and_add(render_pin(req.extras_name, str(version)))
        return self._packages[package][req.extras][version]

    def convert_dependency(self, dependency):  # type: (Dependency) -> Constraint
        """Convert a user-defined dependency into a format Mixology understands."""
        if isinstance(dependency.constraint, VersionRange):
            constraint = Range(
                dependency.constraint.min,
                dependency.constraint.max,
                dependency.constraint.include_min,
                dependency.constraint.include_max,
                dependency.pretty_constraint,
            )
        else:
            # VersionUnion
            ranges = [
                Range(
                    _range.min,
                    _range.max,
                    _range.include_min,
                    _range.include_max,
                    str(_range),
                )
                for _range in dependency.constraint.ranges
            ]
            constraint = Union.of(*ranges)

        return Constraint(dependency.package, constraint)
