from scapy.all import ARP

from netdumplings import DumplingChef, DumplingDriver


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
            "src_ip": "10.0.1.100"
        }
    """
    request = 1
    reply = 2

    def __init__(self, kitchen=None, dumpling_queue=None, receive_pokes=False):
        super().__init__(kitchen=kitchen, dumpling_queue=dumpling_queue,
                         receive_pokes=receive_pokes)

        self.ip_mac = {}

    def packet_handler(self, packet):
        """
        Processes a packet from nd-snifty.  Makes a dumpling summarizing the
        contents of each each valid ARP packet.

        :param packet: Packet from nd-snifty.
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

        result = {
            'operation': operation,
            'src_hw': arp.hwsrc,
            'src_ip': arp.psrc,
            'dst_hw': arp.hwdst,
            'dst_ip': arp.pdst,
            'notes': None,
        }

        if arp.op == ARPChef.reply:
            if self.ip_mac.get(arp.psrc) is None:
                result['notes'] = "source device is new"
            elif self.ip_mac.get(arp.psrc) and self.ip_mac[arp.psrc] != arp.hwsrc:
                result['notes'] = "source device has new IP address"

            # Remember this IP -> MAC mapping.
            self.ip_mac[arp.psrc] = arp.hwsrc

        self.send_dumpling(payload=result, driver=DumplingDriver.packet)
