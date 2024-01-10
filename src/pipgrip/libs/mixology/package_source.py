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
from typing import Any, Hashable, List
from typing import Union as _Union

from pipgrip.libs.mixology.constraint import Constraint
from pipgrip.libs.mixology.incompatibility import Incompatibility
from pipgrip.libs.mixology.incompatibility_cause import DependencyCause
from pipgrip.libs.mixology.package import Package
from pipgrip.libs.mixology.range import Range
from pipgrip.libs.mixology.term import Term
from pipgrip.libs.mixology.union import Union


class PackageSource(object):
    """
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

    def __init__(self):  # type: () -> None
        self._root_package = Package.root()

    @property
    def root(self):  # type: () -> Hashable
        return Package.root()

    @property
    def root_version(self):  # type: () -> Any
        raise NotImplementedError()

    def versions_for(
        self, package, constraint=None
    ):  # type: (Hashable, Any) -> List[Hashable]
        """
        Search for the specifications that match the given constraint.
        """
        if package == self._root_package:
            return [self.root_version]

        return self._versions_for(package, constraint)

    def _versions_for(
        self, package, constraint=None
    ):  # type: (Hashable, Any) -> List[Hashable]
        raise NotImplementedError()

    def dependencies_for(self, package, version):  # type: (Hashable, Any) -> List[Any]
        raise NotImplementedError()

    def convert_dependency(
        self, dependency
    ):  # type: (Any) -> _Union[Constraint, Range, Union]
        """
        Converts a user-defined dependency (returned by dependencies_for())
        into a format Mixology understands.
        """
        raise NotImplementedError()

    def incompatibilities_for(
        self, package, version
    ):  # type: (Hashable, Any) -> List[Incompatibility]
        """
        Returns the incompatibilities of a given package and version
        """
        dependencies = self.dependencies_for(package, version)
        package_constraint = Constraint(package, Range(version, version, True, True))

        incompatibilities = []
        for dependency in dependencies:
            constraint = self.convert_dependency(dependency)

            if not isinstance(constraint, Constraint):
                constraint = Constraint(package, constraint)

            incompatibility = Incompatibility(
                [Term(package_constraint, True), Term(constraint, False)],
                cause=DependencyCause(),
            )
            incompatibilities.append(incompatibility)

        return incompatibilities
