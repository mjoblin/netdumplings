import json
import logging
import logging.config
import os
import time
from typing import Dict, List, Union

from .exceptions import InvalidDumpling


# For typing.
JSONSerializable = Union[str, int, List, Dict, None]

# Tuples of (code, msg) for sending when closing websocket connections.
ND_CLOSE_MSGS = {
    'conn_cancelled': (4101, "connection cancelled"),
    'eater_full': (4102, "dumpling eater is full"),
}

LOGGING_CONFIG_FILE = os.path.join(
    os.path.dirname(__file__), 'data', 'logging.json'
)

HUB_HOST = 'localhost'
HUB_IN_PORT = 11347
HUB_OUT_PORT = 11348
HUB_STATUS_FREQ = 5


def configure_logging(log_level=logging.INFO, config_file=LOGGING_CONFIG_FILE):
    """
    Configure logging. Configuration is retrieved from an external
    file (``data/logging.json`` in the netdumplings package), which can be
    overridden with ``config_file`` or with the `NETDUMPLINGS_LOGGING_CONFIG``
    environment variable.

    :param log_level: Log level to use. Defaults to ``'INFO'``.
    :param config_file: Path to the logging config file to use. Defaults to
        ``data/logging.json`` in the netdumplings package.
    """
    # Format timestamps in GMT, YYYY-MM-DDThh:mm:ss.sss
    logging.Formatter.converter = time.gmtime
    logging.Formatter.default_time_format = '%Y-%m-%dT%H:%M:%S'
    logging.Formatter.default_msec_format = '%s.%03d'

    use_basic_config = False

    try:
        config_file = os.environ['NETDUMPLINGS_LOGGING_CONFIG']
    except KeyError:
        pass

    if os.path.exists(config_file):
        try:
            with open(config_file) as logging_config_handler:
                logging_config = json.load(logging_config_handler)

            logging.config.dictConfig(logging_config)
        except (IOError, json.decoder.JSONDecodeError) as e:
            use_basic_config = True
            print(
                'error loading logging config: {}: {}'.format(config_file, e)
            )
    else:
        use_basic_config = True

    if use_basic_config:
        logging.basicConfig(level=log_level)


def validate_dumpling(dumpling_json):
    """
    Validates a dumpling received from (or about to be sent to) the dumpling
    hub. Validation involves ensuring that it's valid JSON and that it includes
    a ``metadata.chef`` key.

    :param dumpling_json: The dumpling JSON.
    :raise: :class:`netdumplings.exceptions.InvalidDumpling` if the
        dumpling is invalid.
    :return: A dict created from the dumpling JSON.
    """
    try:
        dumpling = json.loads(dumpling_json)
    except json.JSONDecodeError as e:
        raise InvalidDumpling("Could not interpret dumpling JSON")

    try:
        dumpling['metadata']['chef']
    except (KeyError, TypeError) as e:
        raise InvalidDumpling("Could not determine chef name")

    return dumpling
