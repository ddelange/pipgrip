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
