import importlib
import inspect
import logging
import multiprocessing
import os
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
    A network packet sniffer kitchen.  Every sniffed packet gets passed to all
    the :class:`DumplingChef` objects via the handler they each register with
    the kitchen via :meth:`register_handler`.

    The ``DumplingKitchen`` will attempt to find available
    :class:`DumplingChef` subclasses and automatically instantiate them so that
    they can register their handlers with the kitchen.

    The ``DumplingKitchen`` runs the sniffer and maintains a separate thread
    for poking the chefs at regular time intervals.
    """
    def __init__(
            self,
            dumpling_queue: multiprocessing.Queue,
            name: str = 'default',
            interface: str = 'all',
            sniffer_filter: str = 'tcp',
            chef_poke_interval: int = 5,
    ) -> None:
        """
        :param dumpling_queue: Queue for sending dumplings to the dumpling hub.
        :param name: Kitchen name.
        :param sniffer_filter: PCAP-compliant sniffer filter (``None`` means
            sniff all packets).
        :param chef_poke_interval: Frequency (in secs) to call all registered
            chef poke handlers.  ``None`` disables poking.
        """
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

    def _send_dumpling(
            self,
            chef: DumplingChef,
            payload: JSONSerializable,
            driver: DumplingDriver,
    ):
        """
        Initiates a send of a dumpling to all the dumpling eaters by putting
        the dumpling on the dumpling queue.

        :param payload: The dumpling payload.  Can be anything which is JSON
            serializable.  It's up to the dumpling eaters to make sense of it.
        :param driver: The DumplingDriver; either ``DumplingDriver.packet`` or
            ``DumplingDriver.interval``.
        """
        dumpling = Dumpling(chef=chef, payload=payload, driver=driver)
        dumpling_json = dumpling.make()
        self.dumpling_queue.put(dumpling_json)
        self._logger.debug("{0}: Put dumpling on queue, {1} bytes".format(
            self.name, len(dumpling_json)
        ))

    def _process_packet(self, packet: scapy.packet.Raw):
        """
        Passes the given network packet to each of the registered
        :class:`DumplingChef` packet handlers. Takes the returned payload and
        sends it to the dumpling hub.

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
                self._send_dumpling(chef, payload, DumplingDriver.packet)

    def _poke_chefs(self, interval: int):
        """
        Call any registered :class:`DumplingChef` interval handlers at regular
        time intervals.  Intended to be run in a separate thread managed by the
        ``DumplingKitchen``.

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
                    self._send_dumpling(chef, payload, DumplingDriver.interval)

            sleep(interval)

    @staticmethod
    def get_chefs_in_modules(chef_modules: Optional[List[str]] = None) -> Dict:
        """
        Finds available :class:`DumplingChef` subclasses.  Looks inside the
        given ``chef_modules`` list of Python module names for classes which
        are subclasses of :class:`DumplingChef`.

        :return: A dict where the keys are the module name, and the values are
            a dict containing keys ``import_error`` (``False`` if no error),
            and ``chef_classes`` (a list of class names subclassed from
            :class:`DumplingChef`).
        """
        # Allow for a chef module to be relative to the current working
        # directory (wherever the script calling this method is being run
        # from). There's potential for this to result in unexpected behaviour
        # as we're effectively modifying the PYTHONPATH.
        sys.path.append(os.getcwd())

        chef_info = {}

        for chef_module in chef_modules:
            chef_info[chef_module] = {
                'import_error': False,
                'chef_classes': []
            }

            # Import the module for subsequent Chef extraction.
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
        Called by each :class:`DumplingChef` to register themselves with the
        kitchen.

        :param chef: The DumplingChef being registered.
        """
        self._chefs.append(chef)

        self._logger.debug("{0}: Received chef registration from {1}".format(
            self.name, chef.name
        ))

    def run(self):
        """
        Starts the kitchen (i.e. the packet sniffer and the chef poking
        thread).  This will loop forever (or until execution stops).
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
