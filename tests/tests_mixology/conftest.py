import pytest

from tests.tests_mixology.package_source import PackageSource


@pytest.fixture()
def source():
    return PackageSource()
