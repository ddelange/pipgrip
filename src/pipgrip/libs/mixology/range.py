from typing import Any, NoReturn, Optional
from typing import Union as _Union

from pipgrip.libs.mixology.union import Union


class Range(object):
    """
    A range of versions represented by a minimum version,
    a maximum version and whether they are included in the range.

    Both the minimum and maximum versions can be left out
    to represent unbounded ranges.

    A single version is represented by Range(version, version, True, True).
    """

    def __init__(
        self, min=None, max=None, include_min=False, include_max=False, string=None
    ):  # type: (Any, Any, bool, bool, Optional[str]) -> None
        self._min = min
        self._max = max
        self._include_min = include_min
        self._include_max = include_max
        self._hash = None
        self._string = string

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def include_min(self):
        return self._include_min

    @property
    def include_max(self):
        return self._include_max

    @property
    def inverse(self):  # type: () -> _Union[Range, Union]
        if self.is_any():
            return EmptyRange()

        low = Range(max=self.min, include_max=not self.include_min)
        high = Range(min=self.max, include_min=not self.include_max)

        if self.min is None:
            return high

        if self.max is None:
            return low

        return low.union(high)

    def is_empty(self):
        return False

    def is_any(self):
        return self._min is None and self._max is None

    def allows_all(self, other):  # type: (Range) -> bool
        if other.is_empty():
            return True

        if isinstance(other, Union):
            return all([self.allows_all(constraint) for constraint in other.ranges])

        return not other.allows_lower(self) and not other.allows_higher(self)

    def allows_any(self, other):  # type: (Range) -> bool
        if other.is_empty():
            return False

        if isinstance(other, Union):
            return any([self.allows_any(constraint) for constraint in other.ranges])

        return not other.is_strictly_lower(self) and not other.is_strictly_higher(self)

    def intersect(self, other):  # type: (Range) -> Range
        if other.is_empty():
            return other

        if isinstance(other, Union):
            return other.intersect(self)

        if other.is_single_version():
            if self.allows_all(other):
                return other

            return EmptyRange()

        if self.allows_lower(other):
            if self.is_strictly_lower(other):
                return EmptyRange()

            intersect_min = other.min
            intersect_include_min = other.include_min
        else:
            if other.is_strictly_lower(self):
                return EmptyRange()

            intersect_min = self._min
            intersect_include_min = self._include_min

        if self.allows_higher(other):
            intersect_max = other.max
            intersect_include_max = other.include_max
        else:
            intersect_max = self._max
            intersect_include_max = self._include_max

        if intersect_min is None and intersect_max is None:
            return Range()

        # If the range is just a single version.
        if intersect_min == intersect_max:
            # Because we already verified that the lower range isn't strictly
            # lower, there must be some overlap.
            assert intersect_include_min and intersect_include_max

            return Range(intersect_min, intersect_max, True, True)

        # If we got here, there is an actual range.
        return Range(
            intersect_min, intersect_max, intersect_include_min, intersect_include_max
        )

    def union(self, other):  # type: (Range) -> _Union[Range, Union]
        if isinstance(other, Union):
            return other.union(self)

        if not self.is_contiguous_to(other):
            return Union.of(self, other)

        if self.allows_lower(other):
            union_min = self.min
            union_include_min = self.include_min
        else:
            union_min = other.min
            union_include_min = other.include_min

        if self.allows_higher(other):
            union_max = self.max
            union_include_max = self.include_max
        else:
            union_max = other.max
            union_include_max = other.include_max

        return Range(
            union_min,
            union_max,
            include_min=union_include_min,
            include_max=union_include_max,
        )

    def is_contiguous_to(self, other):  # type: (Range) -> bool
        if other.is_empty():
            return False

        return (
            self.allows_any(other)
            or (self.max == other.min and (self.include_max or other.include_min))
            or (self.min == other.max and (self.include_min or other.include_max))
        )

    def difference(self, other):  # type: (_Union[Range, Union]) -> _Union[Range, Union]
        if other.is_empty():
            return self

        if isinstance(other, Union):
            ranges = []
            current = self

            for range in other.ranges:
                # Skip any ranges that are strictly lower than [current].
                if range.is_strictly_lower(current):
                    continue

                # If we reach a range strictly higher than [current], no more ranges
                # will be relevant so we can bail early.
                if range.is_strictly_higher(current):
                    break

                difference = current.difference(range)
                if difference.is_empty():
                    return EmptyRange()
                elif isinstance(difference, Union):
                    # If [range] split [current] in half, we only need to continue
                    # checking future ranges against the latter half.
                    ranges.append(difference.ranges[0])
                    current = difference.ranges[-1]
                else:
                    current = difference

            if not ranges:
                return current

            return Union.of(*(ranges + [current]))

        if not self.allows_any(other):
            return self

        if not self.allows_lower(other):
            before = None
        elif self.min == other.min:
            before = Range(self.min, self.min, True, True)
        else:
            before = Range(self.min, other.min, self.include_min, not other.include_min)

        if not self.allows_higher(other):
            after = None
        elif self.max == other.max:
            after = Range(self.max, self.max, True, True)
        else:
            after = Range(other.max, self.max, not other.include_max, self.include_max)

        if before is None and after is None:
            return EmptyRange()

        if before is None:
            return after

        if after is None:
            return before

        return Union.of(before, after)

    def allows_lower(self, other):  # type: (Range) -> bool
        if self.min is None:
            return other.min is not None

        if other.min is None:
            return False

        if self.min < other.min:
            return True

        if self.min > other.min:
            return False

        return self.include_min and not other.include_min

    def allows_higher(self, other):  # type: (Range) -> bool
        if self.max is None:
            return other.max is not None

        if other.max is None:
            return False

        if self.max < other.max:
            return False

        if self.max > other.max:
            return True

        return self.include_max and not other.include_max

    def is_strictly_lower(self, other):  # type: (Range) -> bool
        if self.max is None or other.min is None:
            return False

        if self.max < other.min:
            return True

        if self.max > other.min:
            return False

        return not self.include_max or not other.include_min

    def is_strictly_higher(self, other):  # type: (Range) -> bool
        return other.is_strictly_lower(self)

    def is_adjacent_to(self, other):  # type: (Range) -> bool
        if self.max != other.min:
            return False

        return (
            self.include_max
            and not other.include_min
            or not self.include_max
            and other.include_min
        )

    def is_single_version(self):  # type: () -> bool
        return (
            self.min is not None
            and self.min == self.max
            and self.include_min
            and self.include_max
        )

    def __eq__(self, other):
        if not isinstance(other, Range):
            return False

        return (
            self._min == other.min
            and self._max == other.max
            and self._include_min == other.include_min
            and self._include_max == other.include_max
        )

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __gt__(self, other):
        return self._cmp(other) > 0

    def __ge__(self, other):
        return self._cmp(other) >= 0

    def _cmp(self, other):  # type: (Range) -> int
        if self.min is None:
            if other.min is None:
                return self._compare_max(other)

            return -1
        elif other.min is None:
            return 1

        if self.min != other.min:
            return -1 if self.min < other.min else 1

        if self.include_min != other.include_min:
            return -1 if self.include_min else 1

        return self._compare_max(other)

    def _compare_max(self, other):  # type: (Range) -> int
        if self.max is None:
            if other.max is None:
                return 0

            return 1
        elif other.max is None:
            return -1

        if self.max != other.max:
            return 1 if self.max < other.max else -1

        if self.include_max != other.include_max:
            return 1 if self.include_max else -1

        return 0

    def __str__(self):
        if self._string is not None:
            return self._string

        text = ""

        if self.min is not None:
            if self.min == self.max and self.include_min and self.include_max:
                return "{}".format(self.min)

            text += ">=" if self.include_min else ">"
            text += self.min.text

        if self.max is not None:
            if self.min is not None:
                text += ","

            text += "{}{}".format("<=" if self.include_max else "<", self.max.text)

        if self.min is None and self.max is None:
            return "*"

        return text

    def __repr__(self):
        return "<Range ({})>".format(str(self))

    def __hash__(self):
        if self._hash is None:
            self._hash = (
                hash(self.min)
                ^ hash(self.max)
                ^ hash(self.include_min)
                ^ hash(self.include_max)
            )

        return self._hash


class EmptyRange(Range):
    @property
    def min(self):  # type: () -> NoReturn
        raise NotImplementedError()

    @property
    def max(self):  # type: () -> NoReturn
        raise NotImplementedError()

    @property
    def include_min(self):  # type: () -> NoReturn
        raise NotImplementedError()

    @property
    def include_max(self):  # type: () -> NoReturn
        raise NotImplementedError()

    def is_empty(self):  # type: () -> bool
        return True

    def is_any(self):  # type: () -> bool
        return False

    def __eq__(self, other):  # type: (Range) -> bool
        return other.is_empty()

    def intersect(self, other):  # type: (Range) -> Range
        return self

    def allows_all(self, other):  # type: (Range) -> bool
        return other.is_empty()

    def allows_any(self, other):  # type: (Range) -> bool
        return other.is_empty()

    def is_single_version(self):  # type: () -> bool
        return False

    @property
    def inverse(self):  # type: () -> _Union[Range, Union]
        return Range()

    def __str__(self):  # type: () -> str
        return "(no versions)"
