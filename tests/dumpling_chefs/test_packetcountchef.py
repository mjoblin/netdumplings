from scapy.all import IP, TCP, Raw, Ether, ARP

from netdumplings.dumplingchefs import PacketCountChef


class TestPacketCountChef:
    """
    Test the PacketCountChef class.
    """
    def test_init(self):
        """
        Test chef initialization.
        """
        chef = PacketCountChef()

        assert chef.packet_counts == {}
        assert chef.poke_count == 0

    def test_packet_handler(self):
        """
        Test that the packet handler adds layer counts to the packet count
        summaries.
        """
        packets = [
            IP(dst='www.apple.com') / TCP(dport=80) / Raw(b'Some raw bytes'),
            Ether(dst="ff:ff:ff:ff:ff:ff") / ARP(pdst='192.168.1.0/24'),
            IP(dst='www.spinach.net') / TCP(dport=80) / Raw(b'More raw bytes'),
        ]

        chef = PacketCountChef()

        for packet in packets:
            chef.packet_handler(packet)

        assert sorted(chef.packet_counts.keys()) == [
            'ARP', 'Ethernet', 'IP', 'Raw', 'TCP',
        ]

        assert chef.packet_counts['ARP'] == 1
        assert chef.packet_counts['Ethernet'] == 1
        assert chef.packet_counts['IP'] == 2
        assert chef.packet_counts['Raw'] == 2
        assert chef.packet_counts['TCP'] == 2

    def test_interval_handler(self, mocker):
        """
        Test that a call to the interval handler sends an interval dumpling
        which contains the packet count summaries.
        """
        chef = PacketCountChef()
        mock_send_interval_dumpling = mocker.patch.object(
            chef, 'send_interval_dumpling'
        )

        chef.interval_handler()

        mock_send_interval_dumpling.assert_called_once_with({
            'packet_counts': chef.packet_counts,
        })
