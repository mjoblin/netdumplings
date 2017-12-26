import netdumplings
from netdumplings._version import __version__


class TestPackage:
    """
    Test the netdumplings package.
    """
    def test_version(self):
        """
        Test that the __version__ attribute is found on the package and that
        it matches the version in netdumplings/_version.py.
        """
        assert netdumplings.__version__ == __version__
