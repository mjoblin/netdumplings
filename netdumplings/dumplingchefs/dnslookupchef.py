import time

from netdumplings import DumplingChef


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
                "when": 1499040017.811247
            }
        }

    Per poke-interval: ::

        {
            "lookups_seen": {
                "srirachamadness.com": {
                    "count": 28,
                    "latest": 1499040017.811247
                },
                "www.fleegle.com": {
                    "count": 1,
                    "latest": 1499045642.57563
                },
                "floople.com": {
                    "count": 7,
                    "latest": 1499043343.104648
                }
            }
        }
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.lookups_seen = {}

    def packet_handler(self, packet):
        """
        Processes a packet from nd-sniff.  Makes a dumpling summarizing the
        contents of each each valid DNS lookup.

        :param packet: Packet from nd-sniff.
        """
        if not packet.haslayer('DNS'):
            return

        dns_query = packet.getlayer('DNS')
        query = dns_query.fields['qd']
        hostname = query.qname.decode('utf-8')

        if hostname.endswith('.'):
            hostname = hostname[:-1]

        now_millis = time.time()

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
                'when': now_millis
            }
        }

        return payload

    def interval_handler(self, interval=None):
        """
        Makes a dumpling at regular intervals which summarizes all the host
        lookups seen so far along with the count and latest lookup time for
        each host.
        """
        payload = {
            'lookups_seen': self.lookups_seen
        }

        return payload
