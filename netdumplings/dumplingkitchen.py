import importlib
import inspect
import logging
import os
import sys
from threading import Thread
from time import sleep

from scapy.all import sniff

from netdumplings import DumplingChef


class DumplingKitchen:
    """
    A network packet sniffer kitchen.  Every sniffed packet gets passed to all
    the :class:`DumplingChef` objects via the handler they each register with
    the kitchen via :meth:`register_handler`.

    The ``DumplingKitchen`` will attempt to find available :class:`DumplingChef`
    subclasses and automatically instantiate them so that they can register
    their handlers with the kitchen.

    The ``DumplingKitchen`` runs the sniffer and maintains a separate thread
    for poking the chefs at regular time intervals.
    """
    def __init__(self, name='default', interface='all', sniffer_filter='tcp',
                 chef_poke_interval=5):
        """
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

        self._packet_handlers = []
        self._interval_handlers = []
        self._logger = logging.getLogger("netdumplings.snifty")

    def _process_packet(self, packet):
        """
        Passes the given network packet to each of the :class:`DumplingChef`
        packet handlers.

        If a packet handler raises an exception then the exception will be
        logged and otherwise ignored.

        :param packet: The network packet to process (from scapy).
        """
        for handler in self._packet_handlers:
            try:
                handler(packet)
            except Exception as e:
                self._logger.exception(
                    "{0}: Error invoking packet handler {1}: {2}".format(
                        self.name, handler, e))

    def _poke_chefs(self, interval):
        """
        Poke any :class:`DumplingChef` objects (who have registered an interval
        handler) at regular time intervals.  Intended to be run in a separate
        thread managed by the ``DumplingKitchen``.

        If an interval handler raises an exception then the exception will be
        logged and otherwise ignored.

        :param interval: Frequency (in secs) of calls to the interval handlers.
        """
        while True:
            self._logger.debug("{0}: Poking chefs".format(self.name))

            for handler in self._interval_handlers:
                try:
                    handler(interval=interval)
                except Exception as e:
                    self._logger.exception(
                        "{0}: Error invoking interval handler {1}: {2}".format(
                            self.name, handler, e))
            sleep(interval)

    @staticmethod
    def get_chefs_in_modules(chef_modules=None):
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
        # directory (wherever the script calling this method is being run from).
        # There's potential for this to result in unexpected behaviour as
        # we're effectively modifying the PYTHONPATH.
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
                    chef_info[chef_module]['chef_classes'].append(chef_class[0])

        return chef_info

    def register_handler(
            self, chef_name=None, packet_handler=None, interval_handler=None):
        """
        Called by each :class:`DumplingChef` to register their packet and/or
        interval handlers with the sniffer kitchen.

        :param chef_name: Name of the chef registering their handler(s).
        :param packet_handler: A callable which will be passed each packet as
            they come in via the sniffer.
        :param interval_handler: A callable which will be invoked every time
            the interval number of seconds has passed.
        """
        self._packet_handlers.append(packet_handler)

        if interval_handler:
            self._interval_handlers.append(interval_handler)

        self._logger.debug(
            "{0}: Received chef handler registration from {1}".format(
                self.name, chef_name))

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

