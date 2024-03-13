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


def test_no_version_matching_constraint(source):
    source.root_dep("foo", "^1.0")

    source.add("foo", "2.0.0")
    source.add("foo", "2.1.3")

    check_solver_result(
        source,
        error=(
            "Because root depends on foo (^1.0) "
            "which doesn't match any versions, version solving failed."
        ),
    )


def test_prerelease(source):
    source.root_dep("foo", "<5")

    source.add("foo", "5.0rc1")
    source.add("foo", "5.0")

    check_solver_result(
        source,
        error=(
            "Because root depends on foo (<5) "
            "which doesn't match any versions, version solving failed."
        ),
    )


def test_no_version_that_matches_combined_constraints(source):
    source.root_dep("foo", "1.0.0")
    source.root_dep("bar", "1.0.0")

    source.add("foo", "1.0.0", deps={"shared": ">=2.0.0 <3.0.0"})
    source.add("bar", "1.0.0", deps={"shared": ">=2.9.0 <4.0.0"})
    source.add("shared", "2.5.0")
    source.add("shared", "3.5.0")

    error = """\
Because no versions of shared match >=2.9.0,<3.0.0
 and bar (1.0.0) depends on shared (>=2.9.0 <4.0.0), bar (1.0.0) requires shared (>=3.0.0,<4.0.0).
And because foo (1.0.0) depends on shared (>=2.0.0 <3.0.0), bar (1.0.0) is incompatible with foo (1.0.0).
So, because root depends on both foo (1.0.0) and bar (1.0.0), version solving failed."""

    check_solver_result(source, error=error)


def test_disjoint_constraints(source):
    source.root_dep("foo", "1.0.0")
    source.root_dep("bar", "1.0.0")

    source.add("foo", "1.0.0", deps={"shared": "<=2.0.0"})
    source.add("bar", "1.0.0", deps={"shared": ">3.0.0"})
    source.add("shared", "2.0.0")
    source.add("shared", "4.0.0")

    error = """\
Because bar (1.0.0) depends on shared (>3.0.0)
 and foo (1.0.0) depends on shared (<=2.0.0), bar (1.0.0) is incompatible with foo (1.0.0).
So, because root depends on both foo (1.0.0) and bar (1.0.0), version solving failed."""

    check_solver_result(source, error=error)


def test_disjoint_root_constraints(source):
    source.root_dep("foo", "1.0.0")
    source.root_dep("foo", "2.0.0")

    source.add("foo", "1.0.0")
    source.add("foo", "2.0.0")

    error = """\
Because root depends on both foo (1.0.0) and foo (2.0.0), version solving failed."""

    check_solver_result(source, error=error)


def test_no_valid_solution(source):
    source.root_dep("a", "*")
    source.root_dep("b", "*")

    source.add("a", "1.0.0", deps={"b": "1.0.0"})
    source.add("a", "2.0.0", deps={"b": "2.0.0"})

    source.add("b", "1.0.0", deps={"a": "2.0.0"})
    source.add("b", "2.0.0", deps={"a": "1.0.0"})

    error = """\
Because no versions of b match <1.0.0 || >1.0.0,<2.0.0 || >2.0.0
 and b (1.0.0) depends on a (2.0.0), b (<2.0.0 || >2.0.0) requires a (2.0.0).
And because a (2.0.0) depends on b (2.0.0), b is forbidden.
Because b (2.0.0) depends on a (1.0.0) which depends on b (1.0.0), b is forbidden.
Thus, b is forbidden.
So, because root depends on b (*), version solving failed."""

    check_solver_result(source, error=error, tries=2)


def test_vcs_constraints(source):
    source.root_dep("requests", "git+https://github.com/psf/requests")
    source.root_dep("requests", "git+https://github.com/psf/requests.git")

    source.add("requests", "git+https://github.com/psf/requests")
    source.add("requests", "git+https://github.com/psf/requests.git")

    error = """\
Because root depends on both requests (git+https://github.com/psf/requests) and requests (git+https://github.com/psf/requests.git), version solving failed."""

    check_solver_result(source, error=error)
