class Package(object):
    """
    A project's package.
    """

    def __init__(self, name):  # type: (str) -> None
        self._name = name

    @classmethod
    def root(cls):  # type: () -> Package
        return Package("_root_")

    @property
    def name(self):  # type: () -> str
        return self._name

    def __eq__(self, other):  # type: () -> bool
        return str(other) == self.name

    def __str__(self):  # type: () -> str
        return self._name

    def __repr__(self):  # type: () -> str
        return 'Package("{}")'.format(self.name)

    def __hash__(self):
        return hash(self.name)
