#!/usr/bin/env python

import argparse
import asyncio
import json
import logging
import re
import sys
from multiprocessing import Process, Queue
from time import sleep

import websockets

from netdumplings import DumplingKitchen
from netdumplings.exceptions import NetDumplingsError
from netdumplings.shared import (configure_logging, get_config, get_config_file,
                                 get_logging_config_file, ND_CLOSE_MSGS)


def network_sniffer(kitchen_name, interface, chefs, chef_modules,
                    sniffer_filter, chef_poke_interval, dumpling_queue):
    """
    Top-level function for managing the flow of sniffed network packets to
    dumpling chefs (via a kitchen).

    This function is intended to be invoked as a Python process.

    The dumpling chefs found in ``netdumplings.dumplingchefs`` are instantiated
    and passed to the sniffer kitchen so they can register their packet and
    interval handlers.  Use ``chef_modules`` to specify alternative Python
    modules where chefs can be found.

    A dumpling chef will only be instantiated if its ``assignable_to_kitchen``
    class attribute is ``True``.

    All the instantiated dumpling chefs receive every sniffed network packet
    and make their own determination about whether to process the packet and
    if/when they have enough network ingredients to make their dumpling (which
    they will then submit to the dumpling queue).

    :param kitchen_name: Name of the sniffer kitchen.
    :param interface: Network interface to sniff (``all`` sniffs all interfaces).
    :param chefs: List of chefs to send packets to.
    :param chef_modules: List of Python module names in which to find our chefs.
    :param sniffer_filter: PCAP-compliant sniffer filter.
    :param chef_poke_interval: Interval (in secs) to poke chefs.
    :param dumpling_queue: Queue to send fresh dumplings to so they can be
        forwarded on to `nd-shifty` (the dumpling hub).
    """
    log = logging.getLogger('netdumplings.snifty')
    log.info("{0}: Starting network sniffer process".format(kitchen_name))
    log.info("{0}: Interface: {1}".format(kitchen_name, interface))
    log.info("{0}: Requested chefs: {1}".format(kitchen_name,
             "all" if chefs is True else ", ".join(chefs)))
    log.info("{0}: Chef modules: {1}".format(
        kitchen_name, ", ".join(chef_modules)))
    log.info("{0}: Filter: {1}".format(kitchen_name,
             "<all packets>" if not sniffer_filter else sniffer_filter))
    log.info("{0}: Chef poke interval (secs): {1}".format(
        kitchen_name, chef_poke_interval))

    sniffer_kitchen = DumplingKitchen(
        name=kitchen_name, interface=interface, sniffer_filter=sniffer_filter,
        chef_poke_interval=chef_poke_interval)

    chef_info = DumplingKitchen.get_chefs_in_modules(chef_modules)
    chefs_seen = []
    chef_instantiated = False

    # Import and instantiate all the chefs.
    for chef_module in chef_info:
        chef_class_names = chef_info[chef_module]['chef_classes']
        mod = __import__(chef_module, fromlist=chef_class_names)

        for chef_class_name in chef_class_names:
            chefs_seen.append(chef_class_name)
            klass = getattr(mod, chef_class_name)
            if not klass.assignable_to_kitchen:
                log.warning("{0}: Chef {1} is marked as unassignable".format(
                    kitchen_name, chef_class_name))
                continue

            # A 'chefs' value of True means all chefs.
            if chefs is True or chef_class_name in chefs:
                log.info("{0}: Registering {1}.{2} with kitchen".format(
                    kitchen_name, chef_module, chef_class_name))
                klass(kitchen=sniffer_kitchen, dumpling_queue=dumpling_queue)
                chef_instantiated = True

    # Warn about any requested chefs which were not found and instantiated.
    if chefs is not True:
        for chef_not_found in [chef for chef in chefs if chef not in chefs_seen]:
            log.warning("{0}: Chef {1} not found".format(
                kitchen_name, chef_not_found))

    if not chef_instantiated:
        log.error("{0}: No chefs instantiated.  Not starting sniffer.".format(
            kitchen_name))
        return

    sniffer_kitchen.run()


def dumpling_emitter(kitchen_name, shifty, dumpling_queue, kitchen_info):
    """
    Grabs fresh dumplings (made by the dumpling chefs from network packet
    ingredients) from the queue and sends them on to `nd-shifty` (the dumpling
    hub).

    This function is intended to be invoked as a Python process.

    :param kitchen_name: The name of the kitchen.
    :param shifty: The address where shifty is receiving dumplings.
    :param dumpling_queue: Queue to grab fresh dumplings from.
    :param kitchen_info: Dict describing the kitchen.
    """
    async def notify_shifty():
        shifty_uri = 'ws://{0}'.format(shifty)

        log.info(
            "{0}: Connecting to shifty at {1}".format(kitchen_name, shifty_uri))

        try:
            websocket = await websockets.connect(shifty_uri)
        except OSError as e:
            log.error(
                "{0}: There was a problem with the shifty connection. "
                "Is shifty available?".format(kitchen_name))
            log.error("{0}: {1}".format(kitchen_name, e))
            return

        try:
            # Register our kitchen information with shifty.
            await websocket.send(json.dumps(kitchen_info))

            # Send dumplings to shifty when they come in from the chefs.
            while True:
                dumpling = dumpling_queue.get()
                await websocket.send(dumpling)
        except asyncio.CancelledError:
            log.warning(
                "{0}: Connection to shifty cancelled; closing...".format(
                    kitchen_name))
            try:
                await websocket.close(*ND_CLOSE_MSGS['conn_cancelled'])
            except websockets.exceptions.InvalidState:
                pass
        except websockets.exceptions.ConnectionClosed as e:
            log.warning("{0}: Lost connection to shifty: {1}".format(
                kitchen_name, e))
        except OSError as e:
            log.exception(
                "{0}: Error talking to shifty websocket hub: {1}".format(
                    kitchen_name, e))

    log = logging.getLogger('netdumplings.snifty')
    log.info("{0}: Starting dumpling emitter process".format(kitchen_name))
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(notify_shifty())
    except KeyboardInterrupt:
        pass


def list_chefs(chef_modules=None):
    """
    Lists all the chef classes (subclassed from :class:`DumplingChef`) found in
    the given list of ``chef_modules``.

    :param chef_modules: A list of module names to look for chefs in.
    """
    chef_info = DumplingKitchen.get_chefs_in_modules(chef_modules)

    print()
    for chef_module in sorted(chef_info):
        print("{0}".format(chef_module))
        import_error = chef_info[chef_module]['import_error']

        if not import_error:
            for chef_class in chef_info[chef_module]['chef_classes']:
                print("  {0}".format(chef_class))
        else:
            print("  error importing module: {0}".format(import_error))

        print()


def get_override(arg_name, kitchen_config, default):
    """
    Looks to the given ``kitchen_config`` to see if it contains an value for
    the given ``arg_name``.  If not then it returns the given ``default``
    value.

    :param arg_name: The name of the argument to look up in the config.
    :param kitchen_config: The config information for a kitchen.
    :param default: The default value to return if a value is not specified in
        the kitchen_config.
    :return: The value for the argument.
    """
    try:
        result = kitchen_config[arg_name]
    except KeyError:
        result = default

    return result


def set_config(field, args, kitchen_config, config):
    """
    Returns a value to use for a specified config field.  Priority order is:
    commandline args; kitchen config overrides; then default config.

    :param field: Config field name.
    :param args: Parsed command-line arguments.
    :param kitchen_config: Dict of kitchen config overrides.
    :param config: 'snifty' dict from default config file.
    :return: The value to use for the given config field.
    """
    arg_val = getattr(args, field)
    if arg_val is not None:
        if field in ['chefs', 'chef_modules']:
            # Convert comma- or space-separate commandline string of chef or
            # chef module names to Python lists.
            result = re.split("[,\s]+", arg_val)
        else:
            result = arg_val
    else:
        try:
            result = kitchen_config[field]
        except (KeyError, TypeError):
            result = config[field]

    return result


def get_commandline_args():
    """
    Parse commandline arguments.

    :return: kitchen name, config (contains 'shifty' and 'snifty' keys),
        log level, logging config file
    """
    default_kitchen_name = "default_kitchen"

    config = get_config()
    default_interface = config['snifty']['interface']
    default_address = config['shifty']['address']
    default_out_port = config['shifty']['in_port']
    default_shifty = "{0}:{1}".format(default_address, default_out_port)
    default_config_file = get_config_file()
    default_log_level = 'INFO'
    default_log_config_file = get_logging_config_file()
    default_filter = config['snifty']['filter']
    default_chefs = (
        ",".join(config['snifty']['chefs'])
        if config['snifty']['chefs'] is not True else True)
    default_chef_modules = config['snifty']['chef_modules']
    default_poke_interval = config['snifty']['poke_interval']

    parser = argparse.ArgumentParser(description="""
        Sniffs network packets and sends them to chefs for use in the making of
        tasty dumplings.  Dumplings are then sent to nd-shifty for distribution
        to the dumpling eaters.
    """)

    parser.add_argument(
        "--kitchen-name", default=default_kitchen_name,
        help="name of this dumpling kitchen; will also check for kitchen "
             "settings in the config file (default: {0})".format(
                default_kitchen_name))
    parser.add_argument(
        "--shifty", default=None,
        help="address where nd-shifty is receiving dumplings "
             "(default: {0})".format(default_shifty))
    parser.add_argument(
        "--config", default=None,
        help="configuration file (default: {0})".format(default_config_file))
    parser.add_argument(
        "--log-level", default=default_log_level,
        help="logging level (default: {0})".format(default_log_level))
    parser.add_argument(
        "--log-config", default=default_log_config_file,
        help="logging config file (default: in netdumplings.data module)")

    # These arguments may have a kitchen-level override in the config file.
    parser.add_argument(
        "--interface", default=None,
        help="network interface to sniff (default: {0})".format(default_interface))
    parser.add_argument(
        "--filter", default=None,
        help="PCAP-style sniffer packet filter (default: {0})".format(
            default_filter))
    parser.add_argument(
        "--chefs", default=None,
        help="chefs to deliver packets to (all if not specified)")
    parser.add_argument(
        "--chef-modules", default=None,
        help="python modules containing chefs (default: {0})".format(
            ','.join(default_chef_modules)))
    parser.add_argument(
        "--chef-list", action='store_true',
        help="list all available chefs")
    parser.add_argument(
        "--poke-interval", default=None, type=int,
        help="interval (in secs) to poke chefs (default: {0})".format(
            default_poke_interval))

    args = parser.parse_args()

    # Replace config with user-defined config file (if specified).
    if args.config:
        try:
            config = get_config(args.config)
        except NetDumplingsError as e:
            print("error: {0}".format(e))
            sys.exit(0)

    kitchen = args.kitchen_name

    # Look for a configuration for this kitchen in the config file.
    try:
        kitchen_config = config['snifty']['kitchens'][kitchen]
    except (KeyError, TypeError):
        kitchen_config = {}

    # Priority order: commandline, then kitchen config overrides, then defaults.
    # We replace the main snifty config setting with kitchen-specific settings
    # if possible.
    for snifty_field in ['interface', 'filter', 'poke_interval', 'chefs',
                         'chef_modules']:
        config['snifty'][snifty_field] = \
            set_config(snifty_field, args, kitchen_config, config['snifty'])

    # Display the chef list and exit if that's all the user wanted.
    if args.chef_list:
        list_chefs(config['snifty']['chef_modules'])
        sys.exit(1)

    # Handle shifty command-line overrides.
    if args.shifty:
        if ":" in args.shifty:
            (address, port) = args.shifty.split(":")
            config['shifty']['address'] = address
            config['shifty']['in_port'] = port
        else:
            config['shifty']['address'] = args.shifty

    # Remove the kitchens key from the config.  This ensures that the returned
    # config only contains 'shifty' and 'snifty' keys.
    try:
        del config['snifty']['kitchens']
    except KeyError:
        pass

    return kitchen, config, args.log_level, args.log_config


def main():
    """
    `This is nd-snifty`.  `nd-snifty` does a few things:

     * Starts a network-sniffing dumpling-making kitchen process.
     * Starts a dumpling emitter process for sending dumplings (over a
       websocket) from the kitchen to shifty (a websocket hub which ferries
       dumplings between dumpling emitters and dumpling eaters).
     * Creates a queue for the kitchen process to send freshly-made dumplings
       to the emitter process.
    """
    kitchen_name, config, log_level, logging_config_file = get_commandline_args()

    snifty_config = config['snifty']
    shifty_config = config['shifty']

    logger_name = 'netdumplings.snifty'
    configure_logging(log_level, logging_config_file, logger_name)
    log = logging.getLogger(logger_name)

    # A queue for sending dumplings from the sniffer process (dumplings made
    # by the dumplingchef packet handlers) to the dumpling-emitter process.
    q = Queue()

    # Start the sniffer and dumpling-emitter processes.  The sniffer passes
    # each sniffed packet to each of the registered dumpling chefs, and the
    # dumpling chefs populate the queue with new dumplings whenever they're
    # excited to share a tasty new dumpling -- which may or may not be every
    # time they receive a packet to process (it's up to them really).
    sniffer_process = Process(
        target=network_sniffer,
        args=(kitchen_name, snifty_config['interface'], snifty_config['chefs'],
              snifty_config['chef_modules'], snifty_config['filter'],
              snifty_config['poke_interval'], q)
    )

    kitchen_info = {
        'kitchen_name': kitchen_name,
        'interface': snifty_config['interface'],
        'filter': snifty_config['filter'],
        'chefs': snifty_config['chefs'],
        'poke_interval': snifty_config['poke_interval']
    }

    shifty = "{0}:{1}".format(shifty_config['address'], shifty_config['in_port'])

    dumpling_emitter_process = Process(
        target=dumpling_emitter, args=(kitchen_name, shifty, q, kitchen_info))

    sniffer_process.start()
    dumpling_emitter_process.start()

    try:
        while True:
            if sniffer_process.is_alive() and dumpling_emitter_process.is_alive():
                sleep(1)
            else:
                if sniffer_process.is_alive():
                    log.error(
                        "{0}: Dumpling emitter process died; exiting.".format(
                            kitchen_name))
                    sniffer_process.terminate()

                if dumpling_emitter_process.is_alive():
                    log.error(
                        "{0}: Network sniffer process died; exiting.".format(
                            kitchen_name))
                    dumpling_emitter_process.terminate()

                break
    except KeyboardInterrupt:
        log.warning(
            "{0}: Caught keyboard interrupt; exiting.".format(
                kitchen_name))


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
