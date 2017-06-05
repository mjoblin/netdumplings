import time

from netdumplings import DumplingChef, DumplingDriver


class DNSLookupChef(DumplingChef):
    """
    Makes dumplings which describe DNS activity.  Sends per-packet dumplings
    for individual DNS (Domain Name System) lookups; and poke-interval
    dumplings which describe the hosts lookups seen so far with per-host lookup
    counts and timestamp of last lookup.

    Dumpling payload examples:

    Per DNS lookup: ::

        {
            "lookup": {
                "hostname": "srirachamadness.com",
                "when": 1496620761
            }
        }

    Per poke-interval: ::

        {
            "lookups_seen": {
                "srirachamadness.com": {
                    "count": 28,
                    "latest": 1496620761
                },
                "www.fleegle.com": {
                    "count": 1,
                    "latest": 1496614232
                },
                "floople.com": {
                    "count": 7,
                    "latest": 1497983761
                }
            }
        }
    """
    def __init__(self, kitchen=None, dumpling_queue=None, receive_pokes=True):
        """
        """
        super().__init__(kitchen=kitchen, dumpling_queue=dumpling_queue,
                         receive_pokes=receive_pokes)
        self.lookups_seen = {}

    def packet_handler(self, packet):
        """
        Processes a packet from nd-snifty.  Makes a dumpling summarizing the
        contents of each each valid DNS lookup.

        :param packet: Packet from nd-snifty.
        """
        if not packet.haslayer('DNS'):
            return

        dns_query = packet.getlayer('DNS')
        query = dns_query.fields['qd']
        hostname = query.qname.decode('utf-8')

        if hostname.endswith('.'):
            hostname = hostname[:-1]

        now_millis = int(round(time.time() * 1000))

        try:
            self.lookups_seen[hostname]['count'] += 1
            self.lookups_seen[hostname]['latest'] = now_millis
        except KeyError:
            self.lookups_seen[hostname] = {
                'count': 1,
                'latest': now_millis,
            }

        payload = {
            'lookup': {
                'hostname': hostname,
                'when': int(round(time.time() * 1000))
            }
        }

        self.send_dumpling(payload=payload, driver=DumplingDriver.packet)

    def interval_handler(self, interval=None):
        """
        Makes a dumpling at regular intervals which summarizes all the host
        lookups seen so far along with the count and latest lookup time for
        each host.
        """
        payload = {
            'lookups_seen': self.lookups_seen
        }

        self.send_dumpling(payload=payload, driver=DumplingDriver.interval)

