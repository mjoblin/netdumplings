import datetime
import logging

from netdumplings import Dumpling, DumplingDriver


class DumplingChef:
    """
    Base class for all dumpling chefs.

    **NOTE: DumplingChef objects are instantiated for you by nd-snifty. You
    normally won't need to instantiate DumplingChef objects yourself.  Instead
    you'll normally subclass DumplingChef and let nd-snifty take care of
    instantiating it.**

    When instantiated, a DumplingChef registers its :meth:`packet_handler` and
    :meth:`interval_handler` with the given ``kitchen``.

    A DumplingChef can create many :class:`~Dumpling` objects, where a
    dumpling is a tasty bundle of information which (usually) describes some
    sort of network activity.  A dumpling might say how many network packets
    have been sniffed so far; how many packets of various network layers have
    been sniffed; etc.

    This class implements the following methods which can also be overridden
    by subclasses:

    * :meth:`packet_handler`
    * :meth:`interval_handler`
    * :meth:`send_dumpling`
    """
    # Setting assignable_to_kitchen to False (in a subclass) will ensure the
    # chef cannot be assigned to any kitchens via snifty.
    assignable_to_kitchen = True

    _epoch = datetime.datetime.utcfromtimestamp(0)

    def __init__(self, kitchen=None, dumpling_queue=None, receive_pokes=False):
        """
        :param kitchen: The :class:`DumplingKitchen` which is providing the
            network packet ingredients used to create the dumplings.
        :param dumpling_queue: The :class:`multiprocessing.Queue` to send fresh
            new dumplings to.
        :param receive_pokes: Whether this chef wants to receive time-interval
            pokes to its interval_handler.
        """
        self.kitchen = kitchen
        self.dumpling_queue = dumpling_queue
        self.receive_pokes = receive_pokes

        self.name = type(self).__name__
        self.dumplings_sent_count = 0
        self._logger = logging.getLogger("netdumplings.snifty")

        if self.kitchen:
            interval_handler = \
                self.interval_handler if self.receive_pokes else False

            self.kitchen.register_handler(
                chef_name=self.name,
                packet_handler=self.packet_handler,
                interval_handler=interval_handler
            )

    def packet_handler(self, packet):
        """
        This handler is called automatically by `nd-snifty` whenever a new
        packet has been sniffed.

        This method is expected to be overridden by child classes.

        Base implementation immediately sends a dumpling, the payload of which
        will be a string representation of the packet.

        :param packet: Network packet (from scapy).
        """
        payload = "{0}: {1}".format(type(self).__name__, packet.summary())
        self._logger.debug("{0}: Received packet: {1}",
                           self.name, packet.summary())
        self.send_dumpling(payload, DumplingDriver.packet)

    def interval_handler(self, interval=None):
        """
        This handler is called automatically at regular intervals by
        `nd-snifty`.  Allows for time-based (rather than purely packet-based)
        chefs to keep on cheffing even in the absence of fresh packets.

        This method is expected to be overridden by child classes.

        Base implementation does nothing.

        :param interval: Frequency (in seconds) of the time interval pokes.
        """
        self._logger.debug(
            "{0}: Received interval_handler poke", self.name)
        pass

    def send_dumpling(self, payload, driver):
        """
        Initiates a send of a dumpling to all the dumpling eaters.

        :param payload: The dumpling payload.  Can be anything which is JSON
            serializable.  It's up to the dumpling eaters to make sense of it.
        :param driver: The DumplingDriver; either ``DumplingDriver.packet`` or
            ``DumplingDriver.interval``.
        """
        dumpling = Dumpling(chef=self, driver=driver, payload=payload)
        dumpling_json = dumpling()
        self.dumpling_queue.put(dumpling_json)
        self._logger.debug("{0}: Sent dumpling, {1} bytes".format(
            self.name, len(dumpling_json)))
