from collections import defaultdict

from netdumplings import DumplingChef


class PacketCountChef(DumplingChef):
    """
    Makes dumplings which describe the total number of packets seen so far per
    network layer.  Sends one dumpling per poke interval.

    Dumpling payload example: ::

        {
            "packet_counts": {
                "DNS": 9678,
                "Ethernet": 2659740,
                "IP": 2367035,
                "IPv6": 292705,
                "NTP": 28,
                "Raw": 2420309,
                "TCP": 535050,
                "UDP": 2124690
            }
        }
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.packet_counts = defaultdict(int)
        self.poke_count = 0

    def packet_handler(self, packet):
        """
        Processes a packet from nd-sniff.  Adds 1 to the layer count for each
        layer found in the packet.  This does not make any dumplings.

        :param packet: Packet from nd-sniff.
        """
        self.packet_counts[packet.name] += 1

        while packet.payload:
            packet = packet.payload
            self.packet_counts[packet.name] += 1

        return None

    def interval_handler(self, interval=None):
        """
        Makes a dumpling at regular intervals which lists all the layers seen
        in all the packets so far, and the count for each layer.
        """
        return {'packet_counts': self.packet_counts}
