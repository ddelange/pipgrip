from enum import Enum


class SetRelation(Enum):
    """
    An enum of possible relationships between two sets.
    """

    SUBSET = "subset"

    DISJOINT = "disjoint"

    OVERLAPPING = "overlapping"
