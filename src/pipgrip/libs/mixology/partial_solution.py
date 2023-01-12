from typing import Any, Dict, Hashable, List

from pipgrip.libs.mixology._compat import OrderedDict
from pipgrip.libs.mixology.assignment import Assignment
from pipgrip.libs.mixology.constraint import Constraint
from pipgrip.libs.mixology.incompatibility import Incompatibility
from pipgrip.libs.mixology.package import Package
from pipgrip.libs.mixology.set_relation import SetRelation
from pipgrip.libs.mixology.term import Term


class PartialSolution:
    """Represent the (partial) solution.

    A list of Assignments that represent the solver's current best guess about
    what's true for the eventual set of package versions that will comprise the
    total solution.

    See https://github.com/dart-lang/mixology/tree/master/doc/solver.md#partial-solution.
    """

    def __init__(self):  # type: () -> None
        # The assignments that have been made so far, in the order they were
        # assigned.
        self._assignments = []  # type: List[Assignment]

        # The decisions made for each package.
        self._decisions = OrderedDict()  # type: Dict[str, Hashable]

        # The intersection of all positive Assignments for each package, minus any
        # negative Assignments that refer to that package.
        #
        # This is derived from self._assignments.
        self._positive = OrderedDict()  # type: Dict[Hashable, Term]

        # The union of all negative Assignments for each package.
        #
        # If a package has any positive Assignments, it doesn't appear in this
        # map.
        #
        # This is derived from self._assignments.
        self._negative = OrderedDict()  # type: Dict[Hashable, Dict[Hashable, Term]]

        # The number of distinct solutions that have been attempted so far.
        self._attempted_solutions = 1

        # Whether the solver is currently backtracking.
        self._backtracking = False

    @property
    def decisions(self):  # type: () -> Dict[Hashable, Any]
        return self._decisions

    @property
    def decision_level(self):  # type: () -> int
        return len(self._decisions)

    @property
    def attempted_solutions(self):  # type: () -> int
        return self._attempted_solutions

    @property
    def unsatisfied(self):  # type: () -> List[Term]
        decision_packages = {key: key for key in self._decisions.keys()}
        unsatisfied = [
            term
            for term in self._positive.values()
            if term.package not in self._decisions
            # if package is in _decisions, but with less extras, this term is also unsatisfied
            # therefore we need to inspect the key in self._decisions
            or not term.package.req.extras.issubset(
                decision_packages[term.package].req.extras
            )
        ]
        return unsatisfied

    def decide(self, package, version):  # type: (Hashable, Any) -> None
        """Add an assignment of package as decision and increment the decision level."""
        # When we make a new decision after backtracking, count an additional
        # attempted solution. If we backtrack multiple times in a row, though, we
        # only want to count one, since we haven't actually started attempting a
        # new solution.
        if self._backtracking:
            self._attempted_solutions += 1

        self._backtracking = False
        if package in self._decisions:
            # package might contain new extras, so need to replace the key
            del self._decisions[package]
        self._decisions[package] = version

        self._assign(
            Assignment.decision(
                package, version, self.decision_level, len(self._assignments)
            )
        )

    def derive(
        self, constraint, is_positive, cause
    ):  # type: (Constraint, bool, Incompatibility) -> None
        """Add an assignment of package as a derivation."""
        self._assign(
            Assignment.derivation(
                constraint,
                is_positive,
                cause,
                self.decision_level,
                len(self._assignments),
            )
        )

    def _assign(self, assignment):  # type: (Assignment) -> None
        """Add an Assignment to _assignments and _positive or _negative."""
        self._assignments.append(assignment)
        self._register(assignment)

    def backtrack(self, decision_level):  # type: (int) -> None
        """Perform backtracking.

        Resets the current decision level to decision_level, and removes all
        assignments made after that level.
        """
        self._backtracking = True

        packages = set()
        while self._assignments[-1].decision_level > decision_level:
            removed = self._assignments.pop(-1)
            packages.add(removed.package)
            if removed.is_decision() and removed.package in self._decisions:
                del self._decisions[removed.package]

        # Re-compute _positive and _negative for the packages that were removed.
        for package in packages:
            if package in self._positive:
                del self._positive[package]

            if package in self._negative:
                del self._negative[package]

        for assignment in self._assignments:
            if assignment.package in packages:
                self._register(assignment)

    def _register(self, assignment):  # type: (Assignment) -> None
        """Register an Assignment in _positive or _negative."""
        package = assignment.package
        old_positive = self._positive.get(package)
        if old_positive is not None:
            self._positive[package] = old_positive.intersect(assignment)
            return

        ref = assignment.package
        negative_by_ref = self._negative.get(package)
        old_negative = None if negative_by_ref is None else negative_by_ref.get(ref)
        if old_negative is None:
            term = assignment
        else:
            term = assignment.intersect(old_negative)

        if term.is_positive():
            if package in self._negative:
                del self._negative[package]

            self._positive[package] = term
        else:
            if package not in self._negative:
                self._negative[package] = {}

            self._negative[package][package] = term

    def satisfier(self, term):  # type: (Term) -> Assignment
        """Return Assignment that satisfies Term.

        Returns the first Assignment in this solution such that the sublist of
        assignments up to and including that entry collectively satisfies term.
        """
        assigned_term = None  # type: Term

        for assignment in self._assignments:
            if assignment.package != term.package:
                continue

            if (
                assignment.package != Package.root()
                and not assignment.package == term.package
            ):
                if not assignment.is_positive():
                    continue

                assert not term.is_positive()

                return assignment

            if assigned_term is None:
                assigned_term = assignment
            else:
                assigned_term = assigned_term.intersect(assignment)
                if assigned_term is None:
                    continue

            # As soon as we have enough assignments to satisfy term, return them.
            if assigned_term.satisfies(term):
                return assignment

        raise RuntimeError("[BUG] {} is not satisfied.".format(term))

    def satisfies(self, term):  # type: (Term) -> bool
        return self.relation(term) == SetRelation.SUBSET

    def relation(self, term):  # type: (Term) -> SetRelation
        positive = self._positive.get(term.package)
        if positive is not None:
            relation = positive.relation(term)
            if (
                relation is SetRelation.DISJOINT
                and not term.package.req.extras.issubset(positive.package.req.extras)
            ):
                # force further inspection when term's extras are not in current solution
                return SetRelation.OVERLAPPING
            return relation

        by_ref = self._negative.get(term.package)
        if by_ref is None:
            return SetRelation.OVERLAPPING

        negative = by_ref[term.package]
        if negative is None:
            return SetRelation.OVERLAPPING

        return negative.relation(term)
