class NetDumplingsError(Exception):
    """
    Base exception for all NetDumplings errors.
    """


class InvalidDumpling(NetDumplingsError):
    """
    A Dumpling does not appear to be valid.  This is either because the
    Dumpling is not valid JSON or it doesn't contain a ``metadata.chef`` key.
    """


class InvalidDumplingPayload(NetDumplingsError):
    """
    A Dumpling payload is invalid (probably because it is not
    JSON-serializable).
    """
