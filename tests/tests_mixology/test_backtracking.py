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


def test_circular_dependency_on_older_version(source):
    source.root_dep("a", ">=1.0.0")

    source.add("a", "1.0.0")
    source.add("a", "2.0.0", deps={"b": "1.0.0"})
    source.add("b", "1.0.0", deps={"a": "1.0.0"})

    check_solver_result(source, {"a": "1.0.0"}, tries=2)


def test_diamond_dependency_graph(source):
    source.root_dep("a", "*")
    source.root_dep("b", "*")

    source.add("a", "2.0.0", deps={"c": "^1.0.0"})
    source.add("a", "1.0.0")

    source.add("b", "2.0.0", deps={"c": "^3.0.0"})
    source.add("b", "1.0.0", deps={"c": "^2.0.0"})

    source.add("c", "3.0.0")
    source.add("c", "2.0.0")
    source.add("c", "1.0.0")

    check_solver_result(source, {"a": "1.0.0", "b": "2.0.0", "c": "3.0.0"})


def test_backjumps_after_partial_satisfier(source):
    # c 2.0.0 is incompatible with y 2.0.0 because it requires x 1.0.0, but that
    # requirement only exists because of both a and b. The solver should be able
    # to deduce c 2.0.0's incompatibility and select c 1.0.0 instead.
    source.root_dep("c", "*")
    source.root_dep("y", "^2.0.0")

    source.add("a", "1.0.0", deps={"x": ">=1.0.0"})
    source.add("b", "1.0.0", deps={"x": "<2.0.0"})

    source.add("c", "1.0.0")
    source.add("c", "2.0.0", deps={"a": "*", "b": "*"})

    source.add("x", "0.0.0")
    source.add("x", "1.0.0", deps={"y": "1.0.0"})
    source.add("x", "2.0.0")

    source.add("y", "1.0.0")
    source.add("y", "2.0.0")

    check_solver_result(source, {"c": "1.0.0", "y": "2.0.0"}, tries=2)


def test_rolls_back_leaf_versions_first(source):
    # The latest versions of a and b disagree on c. An older version of either
    # will resolve the problem. This test validates that b, which is farther
    # in the dependency graph from myapp is downgraded first.
    source.root_dep("a", "*")

    source.add("a", "1.0.0", deps={"b": "*"})
    source.add("a", "2.0.0", deps={"b": "*", "c": "2.0.0"})
    source.add("b", "1.0.0")
    source.add("b", "2.0.0", deps={"c": "1.0.0"})
    source.add("c", "1.0.0")
    source.add("c", "2.0.0")

    check_solver_result(source, {"a": "2.0.0", "b": "1.0.0", "c": "2.0.0"})


def test_simple_transitive(source):
    # Only one version of baz, so foo and bar will have to downgrade
    # until they reach it
    source.root_dep("foo", "*")

    source.add("foo", "1.0.0", deps={"bar": "1.0.0"})
    source.add("foo", "2.0.0", deps={"bar": "2.0.0"})
    source.add("foo", "3.0.0", deps={"bar": "3.0.0"})

    source.add("bar", "1.0.0", deps={"baz": "*"})
    source.add("bar", "2.0.0", deps={"baz": "2.0.0"})
    source.add("bar", "3.0.0", deps={"baz": "3.0.0"})

    source.add("baz", "1.0.0")

    check_solver_result(
        source, {"foo": "1.0.0", "bar": "1.0.0", "baz": "1.0.0"}, tries=3
    )


def test_backjump_to_nearer_unsatisfied_package(source):
    # This ensures it doesn't exhaustively search all versions of b when it's
    # a-2.0.0 whose dependency on c-2.0.0-nonexistent led to the problem. We
    # make sure b has more versions than a so that the solver tries a first
    # since it sorts sibling dependencies by number of versions.
    source.root_dep("a", "*")
    source.root_dep("b", "*")

    source.add("a", "1.0.0", deps={"c": "1.0.0"})
    source.add("a", "2.0.0", deps={"c": "2.0.0-nonexistent"})
    source.add("b", "1.0.0")
    source.add("b", "2.0.0")
    source.add("b", "3.0.0")
    source.add("c", "1.0.0")

    check_solver_result(source, {"a": "1.0.0", "b": "3.0.0", "c": "1.0.0"}, tries=2)


def test_traverse_into_package_with_fewer_versions_first(source):
    # Dependencies are ordered so that packages with fewer versions are tried
    # first. Here, there are two valid solutions (either a or b must be
    # downgraded once). The chosen one depends on which dep is traversed first.
    # Since b has fewer versions, it will be traversed first, which means a will
    # come later. Since later selections are revised first, a gets downgraded.
    source.root_dep("a", "*")
    source.root_dep("b", "*")

    source.add("a", "1.0.0", deps={"c": "*"})
    source.add("a", "2.0.0", deps={"c": "*"})
    source.add("a", "3.0.0", deps={"c": "*"})
    source.add("a", "4.0.0", deps={"c": "*"})
    source.add("a", "5.0.0", deps={"c": "1.0.0"})
    source.add("b", "1.0.0", deps={"c": "*"})
    source.add("b", "2.0.0", deps={"c": "*"})
    source.add("b", "3.0.0", deps={"c": "*"})
    source.add("b", "4.0.0", deps={"c": "2.0.0"})
    source.add("c", "1.0.0")
    source.add("c", "2.0.0")

    check_solver_result(source, {"a": "4.0.0", "b": "4.0.0", "c": "2.0.0"})


def test_backjump_past_failed_package_on_disjoint_constraint(source):
    source.root_dep("a", "*")
    source.root_dep("foo", ">2.0.0")

    source.add("a", "1.0.0", deps={"foo": "*"})  # ok
    source.add(
        "a", "2.0.0", deps={"foo": "<1.0.0"}
    )  # disjoint with myapp's constraint on foo

    source.add("foo", "2.0.0")
    source.add("foo", "2.0.1")
    source.add("foo", "2.0.2")
    source.add("foo", "2.0.3")
    source.add("foo", "2.0.4")

    check_solver_result(source, {"a": "1.0.0", "foo": "2.0.4"})
