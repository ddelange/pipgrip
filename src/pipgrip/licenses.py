from collections import OrderedDict
from zipfile import ZipFile


def extract_licences_from_wheel(wheel_fname):
    """Extract all contents of files containing 'licence' in their filename."""
    zfp = ZipFile(wheel_fname, "r")

    # missing AUTHORS, COPYING and other legal files
    licenses = OrderedDict(
        (name, zfp.read(name))
        for name in zfp.namelist()
        if "license" in name.split("/\\")[-1].lower()
    )

    return licenses


def get_licenses(wheel_fname, wheel_metadata, **kwargs):
    """Extract copyright related info using a wheel as input."""
    # parse all urls mentioned in wheel_metadata
    home_page = wheel_metadata.get("home_page", "")
    project_urls = (
        OrderedDict((("home_page", home_page),)) if home_page else OrderedDict()
    )
    project_urls.update(x.split(", ") for x in wheel_metadata.get("project_urls", []))

    # first attempt at getting licenses based on filename
    # e.g. for pip this is incomplete as the pip wheel doesn't contain vendored licenses
    # https://github.com/pypa/pip/tree/21.0.1/src/pip/_vendor
    # try `pip download pip --no-deps --no-binary :all:` and it will start crashing hard
    # https://github.com/pypa/pip/issues/1884
    # e.g. for matplotlib, wheels do not reproduce matplotlib's LICENSE
    # https://github.com/matplotlib/matplotlib/tree/v3.3.4/LICENSE
    licenses = extract_licences_from_wheel(wheel_fname)

    # potential fallbacks (already incorrect as it's not found in the bdist_wheel used for installation):
    # - use sdist instead (additional downloads):
    #   - scan for sdist on project_urls or [warehouse json api](https://warehouse.readthedocs.io/api-reference/json.html)
    #   - download, unarchive and run scancode-toolkit
    # - existing databases:
    #   - https://libraries.io/pypi (detection method unverified)
    #   - https://clearlydefined.io/?type=pypi (uses scancode-toolkit)
    # - machine readable spdx classifiers [ref](https://softwareengineering.stackexchange.com/a/381907/346730)
    # - other license headers

    wheel_info = OrderedDict(
        (
            ("author", wheel_metadata.get("author", "")),
            ("author_email", wheel_metadata.get("author_email", "")),
            ("project_urls", project_urls),
            ("licenses", licenses),
        )
    )

    return wheel_info
