from distutils.version import LooseVersion

import pip

try:
    from urllib.parse import urlparse
except ImportError:
    # Python 2
    from urlparse import urlparse  # noqa:F401

PIP_VERSION = LooseVersion(pip.__version__).version

if PIP_VERSION < [10]:
    from pip.locations import USER_CACHE_DIR
else:
    from pip._internal.locations import USER_CACHE_DIR  # noqa:F401
