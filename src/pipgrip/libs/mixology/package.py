import pkg_resources

from pipgrip.pipper import parse_req


class Package(object):
    """Represent a project's package."""

    def __init__(self, pip_string):  # type: (str) -> None
        req = parse_req(pip_string)
        self._name = req.key
        self._req = req

    @classmethod
    def root(cls):  # type: () -> Package
        return Package("_root_")

    @property
    def name(self):  # type: () -> str
        return self._name

    @property
    def req(self):  # type: () -> pkg_resources.Requirement
        return self._req

    def __eq__(self, other):  # type: () -> bool
        return str(other) == str(self)

    def __ne__(self, other):  # type: () -> bool
        return not self.__eq__(other)

    def __str__(self):  # type: () -> str
        return self.name

    def __repr__(self):  # type: () -> str
        return 'Package("{}")'.format(self.req.extras_name)

    def __hash__(self):
        return hash(str(self))
