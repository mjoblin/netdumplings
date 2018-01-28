from scapy.all import ARP

from netdumplings import DumplingChef


class ARPChef(DumplingChef):
    """
    Makes dumplings which describe ARP (Address Resolution Protocol) activity.

    Dumpling payload example: ::

        {
            "dst_hw": "11:22:33:44:55:66",
            "dst_ip": "10.0.1.99",
            "notes": "source device is new",
            "operation": "reply",
            "src_hw": "aa:bb:cc:dd:ee:ff",
            "src_ip": "10.0.1.100",
            "time": 1499041214.205803
        }
    """
    request = 1
    reply = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ip_mac = {}

    def packet_handler(self, packet):
        """
        Processes a packet from nd-sniff.  Makes a dumpling summarizing the
        contents of each each valid ARP packet.

        :param packet: Packet from nd-sniff.
        """
        if not packet.haslayer("ARP"):
            return

        arp = packet[ARP]

        if arp.op == ARPChef.request:
            operation = 'request'
        elif arp.op == ARPChef.reply:
            operation = 'reply'
        else:
            operation = arp.op

        payload = {
            'operation': operation,
            'src_hw': arp.hwsrc,
            'src_ip': arp.psrc,
            'dst_hw': arp.hwdst,
            'dst_ip': arp.pdst,
            'time': arp.time,
            'notes': None,
        }

        if arp.op == ARPChef.reply:
            if self.ip_mac.get(arp.psrc) is None:
                payload['notes'] = 'source device is new'
            elif (self.ip_mac.get(arp.psrc) and
                  self.ip_mac[arp.psrc] != arp.hwsrc):
                payload['notes'] = 'source device has new IP address'

            # Remember this IP -> MAC mapping.
            self.ip_mac[arp.psrc] = arp.hwsrc

        return payload
