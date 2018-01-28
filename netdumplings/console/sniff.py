import asyncio
import importlib.util
import json
import logging
import os.path
import sys
import multiprocessing
from time import sleep
from typing import Dict, List, Optional, Union

import click
import websockets

import netdumplings
from netdumplings._shared import (
    configure_logging, ND_CLOSE_MSGS, HUB_HOST, HUB_IN_PORT,
)

from ._shared import CLICK_CONTEXT_SETTINGS


def network_sniffer(
        kitchen_name: str,
        interface: str,
        chefs: Union[List[str], bool],
        chef_modules: List[str],
        valid_chefs: Dict,
        sniffer_filter: str,
        chef_poke_interval: int,
        dumpling_queue: multiprocessing.Queue,
):
    """
    The main network sniffing management function, responsible for:

    * Instantiating a dumpling kitchen (which does the actual sniffing) and
      providing it with a queue to put chef-created dumplings on
    * Instantiating the dumpling chefs and registering them with the kitchen
    * Running the kitchen

    This function is intended to be invoked as a Python process.

    A dumpling chef will only be instantiated if its ``assignable_to_kitchen``
    class attribute is ``True``.

    :param kitchen_name: Name of the sniffer kitchen.
    :param interface: Network interface to sniff (``all`` sniffs all
        interfaces).
    :param chefs: List of chefs to send packets to. Used for display only.
    :param chef_modules: List of Python module names in which to find chefs.
        Used for display only.
    :param valid_chefs: Dict of module+chef combinations we plan on importing.
    :param sniffer_filter: PCAP-compliant sniffer filter.
    :param chef_poke_interval: Interval (in secs) to poke chefs.
    :param dumpling_queue: Queue to pass to the kitchen to put dumplings on.
    """
    log = logging.getLogger('netdumplings.sniff')
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

    sniffer_kitchen = netdumplings.DumplingKitchen(
        dumpling_queue=dumpling_queue,
        name=kitchen_name,
        interface=interface,
        sniffer_filter=sniffer_filter,
        chef_poke_interval=chef_poke_interval,
    )

    # Instantiate all the valid DumplingChef classes and register them with
    # the kitchen.
    for chef_module in valid_chefs:
        chef_class_names = valid_chefs[chef_module]

        if os.path.isfile(chef_module):
            spec = importlib.util.spec_from_file_location('chefs', chef_module)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        else:
            # TODO: Investigate replacing __import__ with
            #   importlib.import_module
            mod = __import__(chef_module, fromlist=chef_class_names)

        for chef_class_name in chef_class_names:
            log.info("{0}: Registering {1}.{2} with kitchen".format(
                kitchen_name, chef_module, chef_class_name))
            klass = getattr(mod, chef_class_name)
            klass(kitchen=sniffer_kitchen)

    sniffer_kitchen.run()


async def send_dumplings_from_queue_to_hub(
        kitchen_name: str,
        hub: str,
        dumpling_queue: multiprocessing.Queue,
        kitchen_info: dict,
        log: logging.Logger,
):
    """
    Grabs dumplings from the dumpling queue and sends them to ``nd-hub``.

    :param kitchen_name: The name of the kitchen.
    :param hub: The address where ``nd-hub`` is receiving dumplings.
    :param dumpling_queue: Queue to grab dumplings from.
    :param kitchen_info: Dict describing the kitchen.
    :param log: Logger.
    """
    hub_ws = 'ws://{0}'.format(hub)

    log.info("{0}: Connecting to the dumpling hub at {1}".format(
        kitchen_name, hub_ws)
    )

    try:
        websocket = await websockets.connect(hub_ws)
    except OSError as e:
        log.error(
            "{0}: There was a problem with the dumpling hub connection. "
            "Is nd-hub available?".format(kitchen_name))
        log.error("{0}: {1}".format(kitchen_name, e))
        return

    try:
        # Register our kitchen information with the dumpling hub.
        await websocket.send(json.dumps(kitchen_info))

        # Send dumplings to the hub when they come in from the chefs.
        while True:
            dumpling = dumpling_queue.get()
            await websocket.send(dumpling)
    except asyncio.CancelledError:
        log.warning(
            "{0}: Connection to dumpling hub cancelled; closing...".format(
                kitchen_name))
        try:
            await websocket.close(*ND_CLOSE_MSGS['conn_cancelled'])
        except websockets.exceptions.InvalidState:
            pass
    except websockets.exceptions.ConnectionClosed as e:
        log.warning("{0}: Lost connection to dumpling hub: {1}".format(
            kitchen_name, e))
    except OSError as e:
        log.exception(
            "{0}: Error talking to dumpling hub: {1}".format(kitchen_name, e)
        )


def dumpling_emitter(
        kitchen_name: str,
        hub: str,
        dumpling_queue: multiprocessing.Queue,
        kitchen_info: Dict,
):
    """
    Starts an async event loop to manage funneling dumplings from the queue to
    the dumpling hub.

    This function is intended to be invoked as a Python process.

    :param kitchen_name: The name of the kitchen that the dumplings will be
        coming from.
    :param hub: The address where ``nd-hub`` is receiving dumplings.
    :param dumpling_queue: Queue to get dumplings from.
    :param kitchen_info: Information on the kitchen.
    """
    log = logging.getLogger('netdumplings.sniff')
    log.info("{0}: Starting dumpling emitter process".format(kitchen_name))
    # TODO: Confirm that this new event loop creation is unnecessary.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(
            send_dumplings_from_queue_to_hub(
                kitchen_name, hub, dumpling_queue, kitchen_info, log
            )
        )
    except KeyboardInterrupt:
        pass


def list_chefs(chef_modules: Optional[List[str]] = None):
    """
    Lists all the chef classes (subclassed from :class:`DumplingChef`) found in
    the given list of ``chef_modules``.

    :param chef_modules: Python module names to look for chefs in.
    """
    chef_info = netdumplings.DumplingKitchen.get_chefs_in_modules(chef_modules)

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


def get_valid_chefs(
        kitchen_name: str,
        chef_modules: List[str],
        chefs_requested: Union[List[str], bool],
        log: logging.Logger,
) -> Dict:
    """
    Retrieves the names of all valid DumplingChef subclasses for later
    instantiation. Valid chefs are all the classes in ``chef_modules`` which
    subclass DumplingChef and are included in our list of ``chefs_requested``.
    They also need to have their ``assignable_to_kitchen`` attribute set to
    True.

    :param kitchen_name: Kitchen name (for logging purposes).
    :param chef_modules: List of modules to look for chefs in.
    :param chefs_requested: List of requested chef names (True means all chefs
        are requested).
    :param log: Logger to log to.
    :return: Dict of valid DumpingChef subclasses. Keys are the Python module
        names and the values are a list of valid chef class names in each
        module.
    """
    valid_chefs = {}
    chef_info = netdumplings.DumplingKitchen.get_chefs_in_modules(chef_modules)
    # TODO: chefs_seen could be a set.
    chefs_seen = []

    # Find all the valid chefs.
    for chef_module in chef_info:
        import_error = chef_info[chef_module]['import_error']
        if import_error:
            log.error('Problem with {}: {}'.format(chef_module, import_error))
            continue

        chef_class_names = chef_info[chef_module]['chef_classes']
        is_py_file = chef_info[chef_module]['is_py_file']

        if is_py_file:
            spec = importlib.util.spec_from_file_location('chefs', chef_module)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
        else:
            # TODO: Investigate replacing __import__ with
            #   importlib.import_module
            mod = __import__(chef_module, fromlist=chef_class_names)

        for chef_class_name in chef_class_names:
            chefs_seen.append(chef_class_name)
            klass = getattr(mod, chef_class_name)
            if not klass.assignable_to_kitchen:
                log.warning("{0}: Chef {1} is marked as unassignable".format(
                    kitchen_name, chef_class_name))
                continue

            # A chefs_requested value of True means all chefs.
            if chefs_requested is True or chef_class_name in chefs_requested:
                try:
                    valid_chefs[chef_module].append(chef_class_name)
                except KeyError:
                    valid_chefs[chef_module] = [chef_class_name]

    # Warn about any requested chefs which were not found.
    if chefs_requested is not True:
        for chef_not_found in [chef for chef in chefs_requested
                               if chef not in chefs_seen]:
            log.warning("{0}: Chef {1} not found".format(
                kitchen_name, chef_not_found))

    return valid_chefs


# -----------------------------------------------------------------------------

@click.command(
    context_settings=CLICK_CONTEXT_SETTINGS,
)
@click.option(
    '--kitchen-name', '-n',
    help='Dumpling kitchen name to assign to the sniffer',
    metavar='KITCHEN_NAME',
    default='default_kitchen',
    show_default=True,
)
@click.option(
    '--hub', '-h',
    help='Address where nd-hub is receiving dumplings.',
    metavar='HOST:PORT',
    default='{}:{}'.format(HUB_HOST, HUB_IN_PORT),
    show_default=True,
)
@click.option(
    '--interface', '-i',
    help='Network interface to sniff.',
    metavar='INTERFACE',
    default='all',
    show_default=True,
)
@click.option(
    '--filter', '-f', 'pkt_filter',
    help='PCAP-style sniffer packet filter.',
    metavar='PCAP_FILTER',
    default='tcp or udp or arp',
    show_default=True,
)
@click.option(
    '--chef-module', '-m',
    help='Python module containing chef implementations. Can be module.name '
         'or /path/to/file.py. Multiple can be specified.',
    metavar='PYTHON_MODULE',
    default=['netdumplings.dumplingchefs'],
    show_default=True,
    multiple=True,
)
@click.option(
    '--chef', '-c',
    help='Chef (as found in a --chef-module) to deliver packets to. Multiple '
         'can be specified. Default is to send packets to all chefs.',
    metavar='CHEF_NAME',
    multiple=True,
)
@click.option(
    '--chef-list', '-l',
    help='List all available chefs (as found in the given --chef-module '
         'Python modules) and exit.',
    is_flag=True,
    default=False,
)
@click.option(
    '--poke-interval', '-p',
    help='Interval (in seconds) to poke chefs instructing them to send their '
         'interval dumplings.',
    metavar='SECONDS',
    type=click.FLOAT,
    default=5.0,
    show_default=True,
)
@click.version_option(version=netdumplings.__version__)
def sniff_cli(kitchen_name, hub, interface, pkt_filter, chef_module, chef,
              chef_list, poke_interval):
    """
    A dumpling sniffer kitchen.

    Sniffs network packets matching the given PCAP-style filter and sends them
    to chefs for processing into dumplings. Dumplings are then sent to nd-hub
    for distribution to the dumpling eaters.
    """
    # NOTE: Since the --chef-module and --chef flags can be specified multiple
    #   times, the associated 'chef_module' and 'chef' parameters are tuples of
    #   zero or more modules/chefs respectively.
    chef = True if len(chef) == 0 else chef

    # Display the chef list and exit if that's all the user wanted.
    if chef_list:
        list_chefs(chef_module)
        sys.exit(0)

    # now do the following:
    #
    # * Create a queue for a network-sniffing kitchen process to put dumplings
    #   onto
    # * Start a kitchen process, which will be putting dumplings onto the queue
    # * Start a dumpling emitter process which takes dumplings from the queue
    #   and sends them to nd-hub over a websocket

    configure_logging()
    logger = logging.getLogger('netdumplings.console.sniff')

    # A queue for passing dumplings from the sniffer kitchen to the
    # dumpling-emitter process.
    dumpling_emitter_queue = multiprocessing.Queue()

    # Determine what chefs we'll be sending packets to.
    valid_chefs = get_valid_chefs(kitchen_name, chef_module, chef, logger)

    if not valid_chefs:
        logger.error('{}: No valid chefs found. Not starting sniffer.'.format(
            kitchen_name
        ))
        sys.exit(1)

    # Generate list of module.class names for all the seemingly-valid chefs
    # we'll be instantiating.  This is for use in the status dumplings.
    valid_chef_list = []
    for chef_module_name in sorted(valid_chefs.keys()):
        for chef_class_name in sorted(valid_chefs[chef_module_name]):
            valid_chef_list.append('{}.{}'.format(
                chef_module_name, chef_class_name)
            )

    # Start the sniffer kitchen and dumpling-emitter processes.
    sniffer_process = multiprocessing.Process(
        target=network_sniffer,
        args=(
            kitchen_name, interface, chef, chef_module, valid_chefs,
            pkt_filter, poke_interval, dumpling_emitter_queue,
        )
    )

    kitchen_info = {
        'kitchen_name': kitchen_name,
        'interface': interface,
        'filter': pkt_filter,
        'chefs': valid_chef_list,
        'poke_interval': poke_interval,
    }

    dumpling_emitter_process = multiprocessing.Process(
        target=dumpling_emitter,
        args=(kitchen_name, hub, dumpling_emitter_queue, kitchen_info),
    )

    sniffer_process.start()
    dumpling_emitter_process.start()

    try:
        while True:
            if (sniffer_process.is_alive() and
                    dumpling_emitter_process.is_alive()):
                sleep(1)
            else:
                if sniffer_process.is_alive():
                    logger.error(
                        "{0}: Dumpling emitter process died; exiting.".format(
                            kitchen_name))
                    sniffer_process.terminate()

                if dumpling_emitter_process.is_alive():
                    logger.error(
                        "{0}: Network sniffer process died; exiting.".format(
                            kitchen_name))
                    dumpling_emitter_process.terminate()

                break
    except KeyboardInterrupt:
        logger.warning(
            "{0}: Caught keyboard interrupt; exiting.".format(
                kitchen_name))


if __name__ == '__main__':
    sniff_cli()
