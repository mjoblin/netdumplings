import importlib
import importlib.util
import inspect
import logging
import multiprocessing
import os
import os.path
import sys
from threading import Thread
from time import sleep
from typing import Dict, List, Optional

from scapy.all import sniff
import scapy.packet

from .dumpling import Dumpling, DumplingDriver
from .dumplingchef import DumplingChef
from ._shared import JSONSerializable


class DumplingKitchen:
    """
    A network packet sniffer kitchen.

    The sniffer kitchen does the following:

    * Sniffs network packets
    * Allows chefs to be registered with the kitchen
    * Sends all sniffed packets to all registered dumpling chefs' packet
      handlers
    * Optionally pokes the interval handler of all registered dumpling chefs
      at regular time intervals
    * Takes the return values from the packet and interval handlers, converts
      them into dumplings, JSON-serializes the dumplings, and puts them on
      the given dumpling queue

    Once the kitchen has put a dumpling on the dumpling queue, the kitchen's
    involvement in that dumpling's life cycle is complete. It's the
    responsibility of the thing instantiating the kitchen to provide the queue
    and to then pull dumplings off the queue and send them on to the dumpling
    hub.

    Which network packets are sniffed can be controlled with a PCAP-style
    packer filter.

    :param dumpling_queue: Queue for sending dumplings to the dumpling hub.
    :param name: Kitchen name.
    :param interface: Network interface to sniff on.
    :param sniffer_filter: PCAP-compliant sniffer filter (``None`` means sniff
        all packets).
    :param chef_poke_interval: Frequency (in secs) to call all registered chef
        poke handlers. ``None`` disables poking.
    """
    def __init__(
            self,
            dumpling_queue: multiprocessing.Queue,
            name: str = 'default',
            interface: str = 'all',
            sniffer_filter: str = 'tcp',
            chef_poke_interval: int = 5,
    ) -> None:
        self.name = name
        self.interface = interface
        self.filter = sniffer_filter
        self.chef_poke_interval = chef_poke_interval
        self.dumpling_queue = dumpling_queue

        self._chefs = []
        self._logger = logging.getLogger(__name__)

    def __repr__(self):
        return (
            '{}('
            'dumpling_queue={}, '
            'name={}, '
            'interface={}, '
            'sniffer_filter={}, '
            'chef_poke_interval={})'.format(
                type(self).__name__,
                repr(self.dumpling_queue),
                repr(self.name),
                repr(self.interface),
                repr(self.filter),
                repr(self.chef_poke_interval),
            )
        )

    def _put_dumpling_on_queue(
            self,
            chef: DumplingChef,
            payload: JSONSerializable,
            driver: DumplingDriver,
    ):
        """
        Creates a dumpling, JSON-serializes it, and puts it on the dumpling
        queue.

        :param chef: The chef which provided the dumpling payload.
        :param payload: The dumpling payload.
        :param driver: The driver of the dumpling creation.
        """
        dumpling = Dumpling(chef=chef, payload=payload, driver=driver)
        dumpling_json = dumpling.to_json()
        self.dumpling_queue.put(dumpling_json)
        self._logger.debug("{0}: Put dumpling on queue, {1} bytes".format(
            self.name, len(dumpling_json)
        ))

    def _process_packet(self, packet: scapy.packet.Raw):
        """
        Takes a single sniffed packet and:

        * Passes it to each of the registered dumpling chef packet handlers
        * Takes the returned payload from each chef (if any) and initiates the
          process of putting the result on the dumpling queue

        If a packet handler raises an exception then the exception will be
        logged and otherwise ignored.

        :param packet: The network packet to process (from scapy).
        """
        for chef in self._chefs:
            try:
                payload = chef.packet_handler(packet)
            except Exception as e:
                self._logger.exception(
                    "{0}: Error invoking packet handler for chef {1}: "
                    "{2}".format(self.name, chef.name, e)
                )

                continue

            if payload is not None:
                self._put_dumpling_on_queue(
                    chef, payload, DumplingDriver.packet
                )

    def _poke_chefs(self, interval: int):
        """
        Call any registered dumpling chef interval handlers at regular time
        intervals.

        This is intended to be run in a separate thread.

        If an interval handler raises an exception then the exception will be
        logged and otherwise ignored.

        :param interval: Frequency (in secs) of calls to the interval handlers.
        """
        while True:
            self._logger.debug("{0}: Poking chefs".format(self.name))

            for chef in self._chefs:
                try:
                    payload = chef.interval_handler(interval=interval)
                except Exception as e:
                    self._logger.exception(
                        "{0}: Error invoking interval handler for chef {1}: "
                        "{2}".format(self.name, chef.name, e)
                    )

                    continue

                if payload is not None:
                    self._put_dumpling_on_queue(
                        chef, payload, DumplingDriver.interval
                    )

            sleep(interval)

    @staticmethod
    def get_chefs_in_modules(chef_modules: Optional[List[str]] = None) -> Dict:
        """
        Finds available :class:`DumplingChef` subclasses.

        This helper method looks inside the modules provided in
        ``chef_modules`` for classes which are subclasses of
        :class:`DumplingChef`.

        The returned dict contains information on all found chefs. Each key
        is the name of a single module, and the values are dicts which contain
        the follownig keys:

        * ``"chef_classes"`` - a list of DumplingChef class names contained in
          the module
        * ``"import_error"`` - an error string describing a problem encountered
          while finding dumpling chefs in the module (``False`` if no errors)

        :return: Information on chefs found in the give modules.
        """
        # Allow for a chef module to be relative to the current working
        # directory (wherever the script calling this method is being run
        # from). There's potential for this to result in unexpected behaviour
        # as we're effectively modifying the PYTHONPATH.
        sys.path.append(os.getcwd())

        chef_info = {}

        for chef_module in chef_modules:
            is_py_file = True if os.path.isfile(chef_module) else False

            chef_info[chef_module] = {
                'import_error': False,
                'chef_classes': [],
                'is_py_file': is_py_file,
            }

            # Import the module for subsequent Chef extraction.
            if is_py_file:
                try:
                    spec = importlib.util.spec_from_file_location(
                        'chefs', chef_module
                    )
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                except AttributeError:
                    # Non-Python files result in spec not having a loader attr.
                    chef_info[chef_module]['import_error'] = (
                        'does not appear to be an importable Python file'
                    )
                    continue
            else:
                try:
                    module = importlib.import_module(chef_module)
                except ImportError as e:
                    chef_info[chef_module]['import_error'] = str(e)
                    continue

            chef_classes = inspect.getmembers(module, inspect.isclass)

            for chef_class in chef_classes:
                if chef_class[0] == 'DumplingChef':
                    continue

                if issubclass(chef_class[1], DumplingChef):
                    chef_info[chef_module]['chef_classes'].append(
                        chef_class[0]
                    )

        return chef_info

    def register_chef(self, chef: DumplingChef):
        """
        Registers dumpling chef with the kitchen.

        Registered dumpling chefs will have their packet and interval handlers
        invoked by the kitchen as appropriate.

        :param chef: The DumplingChef to register.
        """
        self._chefs.append(chef)

        self._logger.debug("{0}: Received chef registration from {1}".format(
            self.name, chef.name
        ))

    def run(self):
        """
        Starts the kitchen.

        This blocks and will run forever.
        """
        # Start the chef poking thread.
        if self.chef_poke_interval is not None:
            self._logger.info(
                "{0}: Starting interval poker thread".format(self.name))

            interval_poker = Thread(
                target=self._poke_chefs,
                kwargs={'interval': self.chef_poke_interval}
            )

            interval_poker.start()
        else:
            self._logger.info(
                "{0}: Interval poker thread disabled".format(self.name))

        # Start the sniffer.
        self._logger.info("{0}: Starting sniffer thread".format(self.name))

        if self.interface == 'all':
            sniff(filter=self.filter, prn=self._process_packet, store=0)
        else:
            sniff(iface=self.interface, filter=self.filter,
                  prn=self._process_packet, store=0)
