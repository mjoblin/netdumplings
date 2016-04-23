#!/usr/bin/env python

import argparse
import sys

from netdumplings import DumplingHub
from netdumplings.exceptions import NetDumplingsError
from netdumplings.shared import (configure_logging, get_config, get_config_file,
                                 get_logging_config_file)


def set_config(field, args, config_file_overrides, config):
    """
    Returns a value to use for a specified config field.  Priority order is:
    commandline args; config file overrides; then default config.

    :param field: Config field name.
    :param args: Parsed command-line arguments.
    :param config_file_overrides: Dict of config file overrides.
    :param config: Dict from default config file.
    :return: The value to use for the given config field.
    """
    arg_val = getattr(args, field)
    if arg_val is not None:
        result = arg_val
    else:
        try:
            result = config_file_overrides['shifty'][field]
        except (KeyError, TypeError):
            result = config['shifty'][field]

    return result


def get_commandline_args():
    """
    Parse commandline arguments.

    :return: address, port, status_freq
    """
    config = get_config()
    default_address = config['shifty']['address']
    default_in_port = config['shifty']['in_port']
    default_out_port = config['shifty']['out_port']
    default_status_freq = config['shifty']['status_freq']
    default_config_file = get_config_file()
    default_log_level = 'INFO'
    default_log_config_file = get_logging_config_file()

    parser = argparse.ArgumentParser(description="""
        Sends dumplings received from all kitchens (usually any running
        instances of nd-snifty) to all dumpling eaters.  All kitchens and
        eaters need to connect to the nd-shifty --in-port or --out-port
        respectively.
    """)

    parser.add_argument(
        "--address", default=None,
        help="address to listen on (default: {0})".format(default_address))
    parser.add_argument(
        "--in-port", default=None, type=int,
        help="port to receive incoming dumplings from (default: {0})".format(
            default_in_port))
    parser.add_argument(
        "--out-port", default=None, type=int,
        help="port to send outgoing dumplings to (default: {0})".format(
            default_out_port))
    parser.add_argument(
        "--status-freq", default=None, type=int,
        help="frequency (secs) to send status dumplings (default: {0})".format(
            default_status_freq))
    parser.add_argument(
        "--config", default=None,
        help="configuration file (default: {0})".format(default_config_file))
    parser.add_argument(
        "--log-level", default=default_log_level,
        help="logging level (default: {0})".format(default_log_level))
    parser.add_argument(
        "--log-config", default=default_log_config_file,
        help="logging config file (default: in netdumplings.data module)")

    args = parser.parse_args()

    # Get config overrides from non-default config file (if specified).
    config_overrides = None
    if args.config:
        try:
            config_overrides = get_config(args.config)
        except NetDumplingsError as e:
            print("error: {0}".format(e))
            sys.exit(0)

    for config_field in ['address', 'in_port', 'out_port', 'status_freq']:
        config['shifty'][config_field] = \
            set_config(config_field, args, config_overrides, config)

    return config, args.log_level, args.log_config


def main():
    """
    This is `nd-shifty`.  `nd-shifty` instantiates the :class:`DumplingHub`
    which sends dumplings from all the kitchens to all the eaters.
    """
    config, log_level, logging_config_file = get_commandline_args()

    configure_logging(
        log_level, logging_config_file, logger_name='netdumplings.shifty')

    config = config['shifty']

    dumpling_hub = DumplingHub(
        address=config['address'], in_port=config['in_port'],
        out_port=config['out_port'], status_freq=config['status_freq'])

    try:
        dumpling_hub.run()
    except NetDumplingsError as e:
        print("shifty error: {0}".format(e))


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
