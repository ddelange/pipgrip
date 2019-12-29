from typing import Any, Dict, Hashable


class SolverResult:
    def __init__(
        self, decisions, attempted_solutions
    ):  # type: (Dict[Hashable, Any], int) -> None
        self._decisions = decisions
        self._attempted_solutions = attempted_solutions

    @property
    def decisions(self):  # type: () -> Dict[Hashable, Any]
        return self._decisions

    @property
    def attempted_solutions(self):  # type: () -> int
        return self._attempted_solutions
