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
from tests.tests_mixology.helpers import check_solver_result


def test_simple_dependencies(source):
    source.root_dep("a", "1.0.0")
    source.root_dep("b", "1.0.0")

    source.add("a", "1.0.0", deps={"aa": "1.0.0", "ab": "1.0.0"})
    source.add("b", "1.0.0", deps={"ba": "1.0.0", "bb": "1.0.0"})
    source.add("aa", "1.0.0")
    source.add("ab", "1.0.0")
    source.add("ba", "1.0.0")
    source.add("bb", "1.0.0")

    check_solver_result(
        source,
        {
            "a": "1.0.0",
            "aa": "1.0.0",
            "ab": "1.0.0",
            "b": "1.0.0",
            "ba": "1.0.0",
            "bb": "1.0.0",
        },
    )


def test_shared_dependencies_with_overlapping_constraints(source):
    source.root_dep("a", "1.0.0")
    source.root_dep("b", "1.0.0")

    source.add("a", "1.0.0", deps={"shared": ">=2.0.0 <4.0.0"})
    source.add("b", "1.0.0", deps={"shared": ">=3.0.0 <5.0.0"})
    source.add("shared", "2.0.0")
    source.add("shared", "3.0.0")
    source.add("shared", "3.6.9")
    source.add("shared", "4.0.0")
    source.add("shared", "5.0.0")

    check_solver_result(source, {"a": "1.0.0", "b": "1.0.0", "shared": "3.6.9"})


def test_shared_dependency_where_dependent_version_affects_other_dependencies(source):
    source.root_dep("foo", "<=1.0.2")
    source.root_dep("bar", "1.0.0")

    source.add("foo", "1.0.0")
    source.add("foo", "1.0.1", deps={"bang": "1.0.0"})
    source.add("foo", "1.0.2", deps={"whoop": "1.0.0"})
    source.add("foo", "1.0.3", deps={"zoop": "1.0.0"})
    source.add("bar", "1.0.0", deps={"foo": "<=1.0.1"})
    source.add("bang", "1.0.0")
    source.add("whoop", "1.0.0")
    source.add("zoop", "1.0.0")

    check_solver_result(source, {"foo": "1.0.1", "bar": "1.0.0", "bang": "1.0.0"})


def test_circular_dependency(source):
    source.root_dep("foo", "1.0.0")

    source.add("foo", "1.0.0", deps={"bar": "1.0.0"})
    source.add("bar", "1.0.0", deps={"foo": "1.0.0"})

    check_solver_result(source, {"foo": "1.0.0", "bar": "1.0.0"})
