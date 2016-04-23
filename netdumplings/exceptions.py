class NetDumplingsError(Exception):
    """
    Base exception for all NetDumplings errors.
    """


class InvalidDumplingError(NetDumplingsError):
    """
    Raised when a Dumpling does not appear to be valid.  This is either because
    the Dumpling is not valid JSON or it doesn't contain a ``metadata.chef``
    key.
    """
