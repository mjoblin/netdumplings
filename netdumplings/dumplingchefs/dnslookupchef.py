from collections import defaultdict

from netdumplings import DumplingChef, DumplingDriver


class DNSLookupChef(DumplingChef):
    """
    Makes dumplings which describe DNS activity.  Sends per-packet dumplings
    for individual DNS (Domain Name System) lookups; and poke-interval
    dumplings which describe the hosts lookups seen so far with per-host lookup
    counts.

    Dumpling payload examples:

    Per DNS lookup: ::

        {
            "lookup": {
                "hostname": "srirachamadness.com"
            }
        }

    Per poke-interval: ::

        {
            "lookups_seen": {
                "srirachamadness.com": 28,
                "www.fleegle.com": 1,
                "floople.com": 7
            }
        }
    """
    def __init__(self, kitchen=None, dumpling_queue=None, receive_pokes=True):
        """
        """
        super().__init__(kitchen=kitchen, dumpling_queue=dumpling_queue,
                         receive_pokes=receive_pokes)
        self.lookups_seen = defaultdict(int)

    def packet_handler(self, packet):
        """
        Processes a packet from nd-snifty.  Makes a dumpling summarizing the
        contents of each each valid DNS lookup.

        :param packet: Packet from nd-snifty.
        """
        if not packet.haslayer("DNS"):
            return

        dns_query = packet.getlayer("DNS")
        query = dns_query.fields['qd']
        hostname = query.qname.decode("utf-8")
        if hostname.endswith("."):
            hostname = hostname[:-1]
        self.lookups_seen[hostname] += 1

        payload = {
            "lookup": {
                "hostname": hostname
            }
        }

        self.send_dumpling(payload=payload, driver=DumplingDriver.packet)

    def interval_handler(self, interval=None):
        """
        Makes a dumpling at regular intervals which summarizes all the host
        lookups seen so far along with the count for each host.
        """
        payload = {
            "lookups_seen": self.lookups_seen
        }

        self.send_dumpling(payload=payload, driver=DumplingDriver.interval)

