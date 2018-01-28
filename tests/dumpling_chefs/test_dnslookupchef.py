from scapy.all import UDP, DNS, DNSQR, IP, TCP, Raw

from netdumplings.dumplingchefs import DNSLookupChef


class TestDNSLookupChef:
    """
    Test the DNSLookupChef class.
    """
    def test_init(self):
        """
        Test chef initialization.
        """
        chef = DNSLookupChef()

        assert chef.lookups_seen == {}

    def test_packet_handler(self, mocker):
        """
        Test the packet handler for a single DNS lookup. The lookup should be
        added to the list of lookups, and a packet dumpling representing the
        lookup should be returned.
        """
        test_lookup_host = 'www.apple.com'
        packet = UDP() / DNS(rd=1, qd=DNSQR(qname=test_lookup_host))

        mock_time = mocker.patch('time.time', return_value=1234567890)

        chef = DNSLookupChef()
        dumpling = chef.packet_handler(packet)

        # Check that the hostname is added to our list of lookups.
        assert len(chef.lookups_seen) == 1
        assert chef.lookups_seen[test_lookup_host] == {
            'count': 1,
            'latest': mock_time.return_value,
        }

        # Check that the packet dumpling for this lookup was sent out, with the
        # correct payload.
        assert dumpling == {
            'lookup': {
                'hostname': test_lookup_host,
                'when': mock_time.return_value,
            }
        }

    def test_ignore_non_dns_packets(self, mocker):
        """
        Test that non-DNS packets are ignored.
        """
        packet = IP(dst='www.apple.com') / TCP(dport=80) / Raw(b'test')
        mock_getlayer = packet.getlayer = mocker.Mock()

        chef = DNSLookupChef()
        dumpling = chef.packet_handler(packet)

        assert mock_getlayer.call_count == 0
        assert dumpling is None

    def test_stripping_trailing_period(self, mocker):
        """
        Test that we strip the trailing period off of any host lookups.
        """
        test_host_with_period = 'www.apple.com.'
        test_host_without_period = 'www.apple.com'
        packet = UDP() / DNS(rd=1, qd=DNSQR(qname=test_host_with_period))

        mock_time = mocker.patch('time.time', return_value=1234567890)

        chef = DNSLookupChef()
        dumpling = chef.packet_handler(packet)

        # Check that the hostname is added to our list of lookups.
        assert len(chef.lookups_seen) == 1
        assert chef.lookups_seen[test_host_without_period] == {
            'count': 1,
            'latest': mock_time.return_value,
        }

        # Check that the packet dumpling for this lookup was sent out, with the
        # correct payload.
        assert dumpling == {
            'lookup': {
                'hostname': test_host_without_period,
                'when': mock_time.return_value,
            }
        }

    def test_interval_handler(self):
        """
        Test that a call to the interval handler returns an interval dumpling
        which contains the lookups seen.
        """
        chef = DNSLookupChef()
        dumpling = chef.interval_handler()

        assert dumpling == {
            'lookups_seen': chef.lookups_seen,
        }
