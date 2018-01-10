import pytest

from netdumplings import DumplingChef, DumplingKitchen


class ChefForTests(DumplingChef):
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
        assert chef.name == 'DumplingChef'
        assert chef.dumplings_sent_count == 0

    def test_subclass_chef_name(self):
        """
        Test the setting of the name for a subclass of DumplingChef. The name
        should match the class name.
        """
        chef = ChefForTests()
        assert chef.name == 'ChefForTests'

    def test_kitchen_registration(self, mock_kitchen):
        """
        Test registering the chef with the given kitchen.
        """
        chef = ChefForTests(kitchen=mock_kitchen)

        mock_kitchen.register_chef.assert_called_once_with(chef)

    def test_default_packet_handler(self, mock_kitchen, mock_packet, mocker):
        """
        Test the default packet handler. It should return a dumpling with a
        string payload matching "<ChefName>: <packet summary string>".
        """
        chef = ChefForTests(kitchen=mock_kitchen)
        mock_logger = mocker.patch.object(chef, '_logger')

        dumpling = chef.packet_handler(mock_packet)
        assert dumpling == 'ChefForTests: packet summary string'
        assert mock_logger.debug.call_count >= 1

    def test_default_interval_handler(self, mock_kitchen, mocker):
        """
        Test the default interval handler. It should return None (no dumpling).
        """
        chef = ChefForTests(kitchen=mock_kitchen)
        mock_logger = mocker.patch.object(chef, '_logger')

        dumpling = chef.interval_handler(interval=5)
        assert dumpling is None
        assert mock_logger.debug.call_count >= 1

    def test_repr(self):
        """
        Test the string representation.
        """
        chef = DumplingChef()
        assert repr(chef) == 'DumplingChef(kitchen=None)'

        kitchen = DumplingKitchen()
        chef = DumplingChef(kitchen=kitchen)

        assert repr(chef) == 'DumplingChef(kitchen={})'.format(repr(kitchen))
