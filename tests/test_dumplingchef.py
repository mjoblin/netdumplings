import json

import pytest

from netdumplings import Dumpling, DumplingChef, DumplingDriver


class TestChef(DumplingChef):
    pass


@pytest.fixture
def mock_kitchen(mocker):
    kitchen = mocker.Mock()
    kitchen.name = 'TestKitchen'
    kitchen.interface = 'en0'
    kitchen.filter = 'tcp'
    kitchen.chef_poke_interval = 5

    return kitchen


@pytest.fixture
def mock_packet(mocker):
    packet = mocker.Mock()
    packet.summary.return_value = 'packet summary string'

    return packet


class TestDumplingChef:
    """
    Test the DumplingChef class.
    """
    def test_init_default(self):
        """
        Test default DumplingChef initialization.
        """
        chef = DumplingChef()

        assert chef.kitchen is None
        assert chef.dumpling_queue is None
        assert chef.receive_pokes is False
        assert chef.name == 'DumplingChef'
        assert chef.dumplings_sent_count == 0

    def test_subclass_chef_name(self):
        """
        Test the setting of the name for a subclass of DumplingChef. The name
        should match the class name.
        """
        chef = TestChef()
        assert chef.name == 'TestChef'

    def test_kitchen_registration_with_pokes(self, mock_kitchen):
        """
        Test registering a chef with a kitchen with interval pokes enabled.
        """
        chef = TestChef(kitchen=mock_kitchen, receive_pokes=True)

        mock_kitchen.register_handler.assert_called_once_with(
            chef_name='TestChef',
            packet_handler=chef.packet_handler,
            interval_handler=chef.interval_handler,
        )

    def test_kitchen_registration_without_pokes(self, mock_kitchen):
        """
        Test registering a chef with a kitchen with interval pokes disabled.
        """
        chef = TestChef(kitchen=mock_kitchen, receive_pokes=False)

        mock_kitchen.register_handler.assert_called_once_with(
            chef_name='TestChef',
            packet_handler=chef.packet_handler,
            interval_handler=False,
        )

    def test_default_packet_handler(self, mocker, mock_kitchen, mock_packet):
        """
        Test the default packet handler. It should send a dumpling with a
        string payload matching "<ChefName>: <packet summary string>".
        """
        chef = TestChef(kitchen=mock_kitchen, receive_pokes=False)
        mocker.patch.object(chef, 'send_packet_dumpling')

        expected_payload = 'TestChef: packet summary string'
        chef.packet_handler(mock_packet)
        chef.send_packet_dumpling.assert_called_with(expected_payload)

    def test_send_interval_dumpling(self, mocker, mock_kitchen):
        """
        Test sending an interval dumpling. It should invoke _send_dumpling
        with the interval dumpling driver.
        """
        chef = TestChef(kitchen=mock_kitchen, receive_pokes=True)
        mocker.patch.object(chef, '_send_dumpling')

        test_payload = {'one': 1, 'two': 2}
        chef.send_interval_dumpling(test_payload)

        chef._send_dumpling.assert_called_with(
            test_payload, driver=DumplingDriver.interval
        )

    def test_send_packet_dumpling(self, mocker, mock_kitchen):
        """
        Test sending an interval dumpling. It should invoke _send_dumpling
        with the packet dumpling driver.
        """
        chef = TestChef(kitchen=mock_kitchen, receive_pokes=True)
        mocker.patch.object(chef, '_send_dumpling')

        test_payload = {'one': 1, 'two': 2}
        chef.send_packet_dumpling(test_payload)

        chef._send_dumpling.assert_called_once_with(
            test_payload, driver=DumplingDriver.packet
        )

    def test_dumpling_send(self, mocker, mock_kitchen):
        """
        Test the _send_dumpling method to ensure that it puts the dumpling
        contents onto the queue.
        """
        test_payload = {
            'one': 1,
            'two': 2,
        }
        test_payload_json = json.dumps(test_payload)

        mock_queue = mocker.Mock()
        chef = TestChef(
            kitchen=mock_kitchen,
            dumpling_queue=mock_queue,
            receive_pokes=True,
        )

        patch_dumpling_callable = mocker.patch.object(Dumpling, '__call__')
        patch_dumpling_callable.return_value = test_payload_json

        # Ensure that _send_dumpling() puts the return value of the
        # dumpling call (which is the same as Dumpling.make()) onto the queue.
        chef._send_dumpling(test_payload, driver=DumplingDriver.packet)
        mock_queue.put.assert_called_once_with(test_payload_json)
