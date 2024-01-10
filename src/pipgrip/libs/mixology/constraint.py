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
from typing import Hashable
from typing import Union as _Union

from pipgrip.libs.mixology.package import Package
from pipgrip.libs.mixology.range import Range
from pipgrip.libs.mixology.set_relation import SetRelation
from pipgrip.libs.mixology.union import Union


class Constraint(object):
    """
    A term constraint.
    """

    def __init__(
        self, package, constraint
    ):  # type: (Hashable, _Union[Range, Union]) -> None
        self._package = package
        self._constraint = constraint

    @property
    def package(self):  # type: () -> Hashable
        return self._package

    @property
    def constraint(self):  # type: () -> _Union[Range, Union]
        return self._constraint

    @property
    def inverse(self):  # type: () -> Constraint
        new_constraint = self.constraint.inverse

        return self.__class__(self.package, new_constraint)

    def allows_all(self, other):  # type: (Constraint) -> bool
        return self.constraint.allows_all(other.constraint)

    def allows_any(self, other):  # type: (Constraint) -> bool
        return self.constraint.allows_any(other.constraint)

    def difference(self, other):  # type: (Constraint) -> Constraint
        return self.__class__(
            self.package, self.constraint.difference(other.constraint)
        )

    def intersect(self, other):  # type: (Constraint) -> Constraint
        if other.package != self.package:
            raise ValueError("Cannot intersect two constraints for different packages")

        return self.__class__(self.package, self.constraint.intersect(other.constraint))

    def union(self, other):  # type: (Constraint) -> Constraint
        if other.package != self.package:
            raise ValueError(
                "Cannot build an union of two constraints for different packages"
            )

        return self.__class__(self.package, self.constraint.union(other.constraint))

    def is_subset_of(self, other):  # type: (Constraint) -> bool
        return other.allows_all(self)

    def overlaps(self, other):  # type: (Constraint) -> bool
        return other.allows_any(self)

    def is_disjoint_from(self, other):  # type: (Constraint) -> bool
        return not self.overlaps(other)

    def relation(self, other):  # type: (Constraint) -> SetRelation
        if self.is_subset_of(other):
            return SetRelation.SUBSET
        elif self.overlaps(other):
            return SetRelation.OVERLAPPING
        else:
            return SetRelation.DISJOINT

    def is_any(self):  # type: () -> bool
        return self._constraint.is_any()

    def is_empty(self):  # type: () -> bool
        return self._constraint.is_empty()

    def __eq__(self, other):  # type: (Constraint) -> bool
        if not isinstance(other, Constraint):
            return NotImplemented

        return other.package == self.package and other.constraint == self.constraint

    def __hash__(self):
        return hash(self.package) ^ hash(self.constraint)

    def to_string(self, allow_every=False):  # type: (bool) -> str
        if self.package == Package.root():
            return "root"
        elif allow_every and self.is_any():
            return "every version of {}".format(self.package)

        return "{} ({})".format(
            self.package.req.extras_name, "*" if self.is_any() else str(self.constraint)
        )

    def __str__(self):
        return self.to_string()

    def __repr__(self):
        return "<Constraint {}>".format(str(self))
