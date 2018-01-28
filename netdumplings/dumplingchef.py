import logging
from typing import Optional

import scapy.packet

import netdumplings  # noqa
from ._shared import JSONSerializable


class DumplingChef:
    """
    Base class for all dumpling chefs.

    **DumplingChef objects are instantiated for you by nd-sniff. You normally
    won't need to instantiate DumplingChef objects yourself. Instead you'll
    normally subclass DumplingChef in a Python module which you'll pass to
    nd-sniff on the commandline.**

    When instantiated, a DumplingChef registers itself with the given
    ``kitchen`` which will then take care of calling the chef's packet and
    interval handlers as appropriate.

    This class implements the following methods which will usually be
    overridden by subclasses:

    * :meth:`packet_handler`
    * :meth:`interval_handler`

    :param kitchen: The dumpling kitchen which is providing the network packets
        used to create the dumplings.
    """
    # Setting assignable_to_kitchen to False (in a subclass) will ensure the
    # chef cannot be assigned to any kitchens via nd-sniff.
    assignable_to_kitchen = True

    def __init__(
            self,
            kitchen: Optional['netdumplings.DumplingKitchen'] = None,
    ) -> None:
        """
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
        Called automatically by the dumpling kitchen (``nd-sniff``) whenever a
        new packet has been sniffed.

        This method is expected to be overridden by child classes. This base
        implementation returns a payload which is the string representation of
        the packet.

        The return value is turned into a dumpling by the kitchen. If ``None``
        is returned then no dumpling will be created.

        :param packet: Network packet (from scapy).
        :rtype: Anything which is JSON-serializable.
        :return: Dumpling payload.
        """
        payload = "{0}: {1}".format(type(self).__name__, packet.summary())
        self._logger.debug("{0}: Received packet: {1}",
                           self.name, packet.summary())

        return payload

    def interval_handler(
            self, interval: Optional[int] = None) -> JSONSerializable:
        """
        Called automatically at regular intervals by the dumpling kitchen
        (``nd-sniff``).

        Allows for time-based (rather than purely packet-based) chefs to keep
        on cheffing even in the absence of fresh packets.

        This method is expected to be overridden by child classes. This base
        implementation does nothing but log a debug entry.

        The return value is turned into a dumpling by the kitchen. If ``None``
        is returned then no dumpling will be created.

        :param interval: Frequency (in secs) of the time interval pokes.
        :rtype: Anything which is JSON-serializable.
        :return: Dumpling payload.
        """
        self._logger.debug(
            "{0}: Received interval_handler poke", self.name)

        return None
