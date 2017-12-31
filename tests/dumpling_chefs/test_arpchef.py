from scapy.all import Ether, ARP, IP, TCP, Raw

from netdumplings.dumplingchefs import ARPChef


class TestARPChef:
    """
    Test the ARPChef class.
    """
    def test_init(self):
        """
        Test chef initialization.
        """
        chef = ARPChef()

        assert chef.ip_mac == {}

    def test_packet_handler_arp_request(self, mocker):
        """
        Test an ARP request packet.
        """
        packet = Ether() / ARP(op='who-has')
        arp = packet[ARP]

        chef = ARPChef()
        mock_send_packet_dumpling = mocker.patch.object(
            chef, 'send_packet_dumpling'
        )

        chef.packet_handler(packet)

        mock_send_packet_dumpling.assert_called_once_with({
            'operation': 'request',
            'src_hw': arp.hwsrc,
            'src_ip': arp.psrc,
            'dst_hw': arp.hwdst,
            'dst_ip': arp.pdst,
            'time': arp.time,
            'notes': None,
        })

        assert chef.ip_mac == {}

    def test_packet_handler_arp_reply_new_device(self, mocker):
        """
        Test an ARP reply packet for a new device.
        """
        packet = Ether() / ARP(op='is-at')
        arp = packet[ARP]

        chef = ARPChef()
        mock_send_packet_dumpling = mocker.patch.object(
            chef, 'send_packet_dumpling'
        )

        assert chef.ip_mac == {}

        chef.packet_handler(packet)

        # We should have added the new device to our ip_mac structure.
        assert len(chef.ip_mac.keys()) == 1
        assert chef.ip_mac[arp.psrc] == arp.hwsrc

        # Check dumpling payload, including 'notes'.
        mock_send_packet_dumpling.assert_called_once_with({
            'operation': 'reply',
            'src_hw': arp.hwsrc,
            'src_ip': arp.psrc,
            'dst_hw': arp.hwdst,
            'dst_ip': arp.pdst,
            'time': arp.time,
            'notes': 'source device is new',
        })

    def test_packet_handler_arp_reply_new_ip(self, mocker):
        """
        Test an ARP reply packet for a new ip address for a known device.
        """
        packet = Ether() / ARP(op='is-at')
        arp = packet[ARP]

        chef = ARPChef()
        mock_send_packet_dumpling = mocker.patch.object(
            chef, 'send_packet_dumpling'
        )

        # Configure the ip_mac struct to think it's already seen the source.
        chef.ip_mac = {
            arp.psrc: 'old_ip',
        }

        chef.packet_handler(packet)

        # We should have updated the ip_mac structure with the new ip address.
        assert chef.ip_mac[arp.psrc] == arp.hwsrc

        # Check dumpling payload, including 'notes'.
        mock_send_packet_dumpling.assert_called_once_with({
            'operation': 'reply',
            'src_hw': arp.hwsrc,
            'src_ip': arp.psrc,
            'dst_hw': arp.hwdst,
            'dst_ip': arp.pdst,
            'time': arp.time,
            'notes': 'source device has new IP address',
        })

    def test_ignore_non_arp_packets(self, mocker):
        """
        Test that non-ARP packets are ignored.
        """
        packet = IP(dst='www.apple.com') / TCP(dport=80) / Raw(b'test')

        chef = ARPChef()
        mock_send_packet_dumpling = mocker.patch.object(
            chef, 'send_packet_dumpling'
        )

        chef.packet_handler(packet)

        assert chef.ip_mac == {}
        assert mock_send_packet_dumpling.call_count == 0
