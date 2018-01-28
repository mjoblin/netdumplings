class NetDumplingsError(Exception):
    """
    Base exception for all netdumplings errors.
    """


class InvalidDumpling(NetDumplingsError):
    """
    A JSON-serialized dumpling does not appear to be valid.
    """


class InvalidDumplingPayload(NetDumplingsError):
    """
    A dumpling payload is invalid (probably because it is not
    JSON-serializable).
    """
