from typing import List
from typing import Union as _Union

import pipgrip.libs.mixology.range


class Union(object):
    """
    An union of Ranges.
    """

    def __init__(self, *ranges):
        self._ranges = list(ranges)

    @property
    def ranges(self):
        return self._ranges

    @classmethod
    def of(cls, *ranges):
        flattened = []
        for constraint in ranges:
            if constraint.is_empty():
                continue

            if isinstance(constraint, Union):
                flattened += constraint.ranges
                continue

            flattened.append(constraint)

        if not flattened:
            return pipgrip.libs.mixology.range.EmptyRange()

        if any(constraint.is_any() for constraint in flattened):
            return pipgrip.libs.mixology.range.Range()

        flattened.sort()

        merged = []
        for constraint in flattened:
            # Merge this constraint with the previous one, but only if they touch.
            if not merged or (
                not merged[-1].allows_any(constraint)
                and not merged[-1].is_adjacent_to(constraint)
            ):
                merged.append(constraint)
            else:
                merged[-1] = merged[-1].union(constraint)

        if len(merged) == 1:
            return merged[0]

        return Union(*merged)

    def is_empty(self):
        return False

    def is_any(self):
        return False

    def allows_all(
        self, other
    ):  # type: (_Union[pipgrip.libs.mixology.range.Range, Union]) -> bool
        our_ranges = iter(self._ranges)
        their_ranges = iter(self._ranges_for(other))

        our_current_range = next(our_ranges, None)
        their_current_range = next(their_ranges, None)

        while our_current_range and their_current_range:
            if our_current_range.allows_all(their_current_range):
                their_current_range = next(their_ranges, None)
            else:
                our_current_range = next(our_ranges, None)

        return their_current_range is None

    def allows_any(
        self, other
    ):  # type: (_Union[pipgrip.libs.mixology.range.Range, Union]) -> bool
        our_ranges = iter(self._ranges)
        their_ranges = iter(self._ranges_for(other))

        our_current_range = next(our_ranges, None)
        their_current_range = next(their_ranges, None)

        while our_current_range and their_current_range:
            if our_current_range.allows_any(their_current_range):
                return True

            if their_current_range.allows_higher(our_current_range):
                our_current_range = next(our_ranges, None)
            else:
                their_current_range = next(their_ranges, None)

        return False

    def intersect(
        self, other
    ):  # type: (_Union[pipgrip.libs.mixology.range.Range, Union]) -> _Union[pipgrip.libs.mixology.range.Range, Union]
        our_ranges = iter(self._ranges)
        their_ranges = iter(self._ranges_for(other))
        new_ranges = []

        our_current_range = next(our_ranges, None)
        their_current_range = next(their_ranges, None)

        while our_current_range and their_current_range:
            intersection = our_current_range.intersect(their_current_range)

            if not intersection.is_empty():
                new_ranges.append(intersection)

            if their_current_range.allows_higher(our_current_range):
                our_current_range = next(our_ranges, None)
            else:
                their_current_range = next(their_ranges, None)

        return Union.of(*new_ranges)

    def union(
        self, other
    ):  # type: (_Union[pipgrip.libs.mixology.range.Range, Union]) -> _Union[pipgrip.libs.mixology.range.Range, Union]
        return Union.of(self, other)

    def difference(
        self, other
    ):  # type: (_Union[pipgrip.libs.mixology.range.Range, Union]) -> _Union[pipgrip.libs.mixology.range.Range, Union]
        our_ranges = iter(self._ranges)
        their_ranges = iter(self._ranges_for(other))
        new_ranges = []

        state = {
            "current": next(our_ranges, None),
            "their_range": next(their_ranges, None),
        }

        def their_next_range():
            state["their_range"] = next(their_ranges, None)
            if state["their_range"]:
                return True

            new_ranges.append(state["current"])
            our_current = next(our_ranges, None)
            while our_current:
                new_ranges.append(our_current)
                our_current = next(our_ranges, None)

            return False

        def our_next_range(include_current=True):
            if include_current:
                new_ranges.append(state["current"])

            our_current = next(our_ranges, None)
            if not our_current:
                return False

            state["current"] = our_current

            return True

        while True:
            if state["their_range"] is None:
                break

            if state["their_range"].is_strictly_lower(state["current"]):
                if not their_next_range():
                    break

                continue

            if state["their_range"].is_strictly_higher(state["current"]):
                if not our_next_range():
                    break

                continue

            difference = state["current"].difference(state["their_range"])
            if isinstance(difference, Union):
                assert len(difference.ranges) == 2
                new_ranges.append(difference.ranges[0])
                state["current"] = difference.ranges[-1]

                if not their_next_range():
                    break
            elif difference.is_empty():
                if not our_next_range(False):
                    break
            else:
                state["current"] = difference

                if state["current"].allows_higher(state["their_range"]):
                    if not their_next_range():
                        break
                else:
                    if not our_next_range():
                        break

        if not new_ranges:
            return pipgrip.libs.mixology.range.EmptyRange()

        if len(new_ranges) == 1:
            return new_ranges[0]

        return Union.of(*new_ranges)

    def excludes_single_version(self):  # type: () -> bool
        difference = self.difference(pipgrip.libs.mixology.range.Range())

        return (
            isinstance(difference, pipgrip.libs.mixology.range.Range)
            and difference.is_single_version()
        )

    def _ranges_for(
        self, constraint
    ):  # type: (_Union[Union, pipgrip.libs.mixology.range.Range]) -> List[pipgrip.libs.mixology.range.Range]
        if constraint.is_empty():
            return []

        if isinstance(constraint, Union):
            return constraint.ranges

        return [constraint]

    def __eq__(self, other):
        if not isinstance(other, Union):
            return False

        return self._ranges == other.ranges

    def __str__(self):
        if self.excludes_single_version():
            return "!={}".format(pipgrip.libs.mixology.range.Range().difference(self))

        return " || ".join([str(r) for r in self._ranges])

    def __repr__(self):
        return "<Union {}>".format(str(self))
