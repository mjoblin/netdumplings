import json
import logging.config
import os

from netdumplings.exceptions import NetDumplingsError, InvalidDumplingError


# Tuples of (code, msg) for sending when closing websocket connections.
ND_CLOSE_MSGS = {
    'conn_cancelled': (4101, "connection cancelled"),
    'eater_full': (4102, "dumpling eater is full"),
}


def get_config_file():
    """
    Returns the path to the NetDumplings config file.

    :return: Path to config file.
    """
    return os.path.join(os.path.dirname(__file__), 'data', 'config.json')


def get_config(file=None):
    """
    Returns the NetDumplings configuration data.

    :param file: Path to config; ``None`` falls back on default config.
    :return: A dict of configuration data.
    """
    config_file = get_config_file() if not file else file

    try:
        with open(config_file) as f:
            config = json.load(f)
    except (IOError, json.decoder.JSONDecodeError) as e:
        raise NetDumplingsError("Error loading config from {0}: {1}".format(
            config_file, e))

    return config


def get_logging_config_file():
    """
    Returns the path to the logging config file.

    :return: Path to logging config file.
    """
    return os.path.join(os.path.dirname(__file__), 'data', 'logging.json')


def configure_logging(log_level=None, config_file=None, logger_name=None):
    """
    Configure logging.

    :param log_level: Log level to use.  ``None`` falls back on NetDumplings
        default logging level.
    :param config_file: Path to the logging config file to use.  Defaults to
        file returned by :func:`get_logging_config_file`.
    :param logger_name: Name of the logger to configure.  Defaults to
        ``netdumplings``.
    """
    if config_file is None:
        config_file = get_logging_config_file()

    try:
        with open(config_file) as f:
            logging_config = json.load(f)

        logging.config.dictConfig(logging_config)
    except (IOError, json.decoder.JSONDecodeError) as e:
        print("error loading logging config '{0}': {1}".format(config_file, e))
        logging.basicConfig()

    if log_level:
        log = logging.getLogger(logger_name if logger_name else 'netdumplings')
        try:
            log.setLevel(
                log_level.upper() if isinstance(log_level, str) else log_level)
        except ValueError as e:
            log.warning("logging error: {0}".format(e))


def validate_dumpling(dumpling_json):
    """
    Validates a dumpling received from (or about to be sent to) `nd-shifty`.
    Validation involves ensuring that it's valid JSON and that it includes a
    ``metadata.chef`` key.

    :param dumpling_json: The dumpling JSON.
    :raise: :class:`netdumplings.exceptions.InvalidDumplingError` if the
        dumpling is invalid.
    :return: A dict created from the dumpling JSON.
    """
    try:
        dumpling = json.loads(dumpling_json)
    except json.JSONDecodeError as e:
        raise InvalidDumplingError("Could not interpret dumpling JSON")

    try:
        chef_name = dumpling['metadata']['chef']
    except (KeyError, TypeError) as e:
        raise InvalidDumplingError("Could not determine chef name")

    return dumpling
