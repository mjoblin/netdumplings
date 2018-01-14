import logging
from typing import Optional

import scapy.packet

import netdumplings
from ._shared import JSONSerializable


class DumplingChef:
    """
    Base class for all dumpling chefs.

    **NOTE: DumplingChef objects are instantiated for you by nd-snifty. You
    normally won't need to instantiate DumplingChef objects yourself.  Instead
    you'll normally subclass DumplingChef and let nd-snifty take care of
    instantiating it.**

    When instantiated, a DumplingChef registers itself with the given
    ``kitchen`` which will take care of calling the chef's packet and interval
    handlers.

    A DumplingChef can create many :class:`~Dumpling` objects, where a
    dumpling is a tasty bundle of information which (usually) describes some
    sort of network activity.  A dumpling might say how many network packets
    have been sniffed so far; how many packets of various network layers have
    been sniffed; etc.

    This class implements the following methods which will usually be
    overridden by subclasses:

    * :meth:`packet_handler`
    * :meth:`interval_handler`
    """
    # Setting assignable_to_kitchen to False (in a subclass) will ensure the
    # chef cannot be assigned to any kitchens via snifty.
    assignable_to_kitchen = True

    def __init__(
            self,
            kitchen: Optional['netdumplings.DumplingKitchen'] = None,
    ):
        """
        :param kitchen: The :class:`DumplingKitchen` which is providing the
            network packet ingredients used to create the dumplings.
        """
        self.kitchen = kitchen
        self.name = type(self).__name__
        self.dumplings_sent_count = 0
        self._logger = logging.getLogger(__name__)

        if self.kitchen:
            self.kitchen.register_chef(self)

    def __repr__(self):
        return '{}(kitchen={})'.format(type(self).__name__, repr(self.kitchen))

    def packet_handler(self, packet: scapy.packet.Raw) -> JSONSerializable:
        """
        Called automatically by `nd-snifty` whenever a new packet has been
        sniffed.

        This method is expected to be overridden by child classes. This base
        implementation returns a payload which is the string representation of
        the packet.

        :param packet: Network packet (from scapy).
        :return: Dumpling payload.
        """
        payload = "{0}: {1}".format(type(self).__name__, packet.summary())
        self._logger.debug("{0}: Received packet: {1}",
                           self.name, packet.summary())

        return payload

    def interval_handler(
            self, interval: Optional[int] = None) -> JSONSerializable:
        """
        Called automatically at regular intervals by `nd-snifty`.  Allows for
        time-based (rather than purely packet-based) chefs to keep on cheffing
        even in the absence of fresh packets.

        This method is expected to be overridden by child classes. This base
        implementation does nothing.

        :param interval: Frequency (in seconds) of the time interval pokes.
        """
        self._logger.debug(
            "{0}: Received interval_handler poke", self.name)

        return None
