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
from typing import Any, Hashable, Optional

from pipgrip.libs.mixology.constraint import Constraint
from pipgrip.libs.mixology.incompatibility import Incompatibility
from pipgrip.libs.mixology.range import Range
from pipgrip.libs.mixology.term import Term


class Assignment(Term):
    """
    A term in a PartialSolution that tracks some additional metadata.
    """

    def __init__(
        self, constraint, is_positive, decision_level, index, cause=None
    ):  # type: (Constraint, bool, int, int, Optional[Incompatibility]) -> None
        super(Assignment, self).__init__(constraint, is_positive)

        self._decision_level = decision_level
        self._index = index
        self._cause = cause

    @property
    def decision_level(self):  # type: () -> int
        return self._decision_level

    @property
    def index(self):  # type: () -> int
        return self._index

    @property
    def cause(self):  # type: () -> Incompatibility
        return self._cause

    @classmethod
    def decision(
        cls, package, version, decision_level, index
    ):  # type: (Hashable, Any, int, int) -> Assignment
        return cls(
            Constraint(package, Range(version, version, True, True)),
            True,
            decision_level,
            index,
        )

    @classmethod
    def derivation(
        cls, constraint, is_positive, cause, decision_level, index
    ):  # type: (Any, bool, Incompatibility, int, int) -> Assignment
        return cls(constraint, is_positive, decision_level, index, cause)

    def is_decision(self):  # type: () -> bool
        return self._cause is None
