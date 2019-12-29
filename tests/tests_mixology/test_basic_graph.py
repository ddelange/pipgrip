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
