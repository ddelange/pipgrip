from pipgrip.libs.mixology.failure import SolverFailure
from pipgrip.libs.mixology.package import Package
from pipgrip.libs.mixology.version_solver import VersionSolver


def check_solver_result(source, result=None, error=None, tries=None):
    solver = VersionSolver(source)

    try:
        solution = solver.solve()
    except SolverFailure as e:
        if error:
            assert str(e) == error

            if tries is not None:
                assert solver.solution.attempted_solutions == tries

            return

        raise

    packages = {
        package: str(version)
        for package, version in solution.decisions.items()
        if package != Package.root()
    }

    assert result == packages

    if tries is not None:
        assert solution.attempted_solutions == tries
