import pip
from pkg_resources import parse_version

try:
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse  # noqa:F401

PIP_VERSION = list(parse_version(pip.__version__)._version.release)
