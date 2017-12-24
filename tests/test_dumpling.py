import json
import time

import pytest

from netdumplings import Dumpling, DumplingDriver
from netdumplings.exceptions import InvalidDumplingPayload


@pytest.fixture
def mock_kitchen(mocker):
    kitchen = mocker.Mock()
    kitchen.name = 'TestKitchen'
    kitchen.interface = 'en0'
    kitchen.filter = 'tcp'
    kitchen.chef_poke_interval = 5

    return kitchen


@pytest.fixture
def mock_chef(mocker, mock_kitchen):
    chef = mocker.Mock()
    chef.name = 'TestChef'
    chef.kitchen = mock_kitchen

    return chef


class TestDumpling:
    """
    Test the Dumpling class.
    """
    def test_init_default(self):
        """
        Test default Dumpling initialization.
        """
        dumpling = Dumpling()

        assert dumpling.chef is None
        assert dumpling.chef_name is None
        assert dumpling.kitchen is None
        assert dumpling.driver is DumplingDriver.packet
        assert dumpling.payload is None

    def test_init_with_chef_instance(self, mock_chef, mock_kitchen):
        """
        Test initialization of a Dumpling with a DumplingChef instance.
        """
        dumpling = Dumpling(chef=mock_chef)

        assert dumpling.chef is mock_chef
        assert dumpling.chef_name == 'TestChef'
        assert dumpling.kitchen is mock_kitchen
        assert dumpling.driver is DumplingDriver.packet
        assert dumpling.payload is None

    def test_init_with_chef_string(self):
        """
        Test initialization of a Dumpling with a chef string.
        """
        dumpling = Dumpling(chef='test_chef')

        assert dumpling.chef == 'test_chef'
        assert dumpling.chef_name == 'test_chef'
        assert dumpling.kitchen is None
        assert dumpling.driver is DumplingDriver.packet
        assert dumpling.payload is None

    def test_callable(self, mocker, mock_chef):
        """
        Test Dumpling instance is callable and returns the same as make().
        """
        mocker.patch.object(time, 'time')
        time.time.return_value = 'test_timestamp'

        dumpling = Dumpling(chef=mock_chef)
        assert dumpling() == dumpling.make()

    def test_metadata(self, mocker, mock_chef):
        """
        Test metadata keys in the make() result.
        """
        mocker.patch.object(time, 'time')
        time.time.return_value = 'test_timestamp'

        dumpling = Dumpling(chef=mock_chef)
        data = json.loads(dumpling.make())
        metadata = data['metadata']

        assert metadata['chef'] == mock_chef.name
        assert metadata['kitchen'] == mock_chef.kitchen.name
        assert metadata['driver'] == 'packet'
        assert metadata['creation_time'] == 'test_timestamp'

    def test_make_payload_string(self, mock_chef):
        """
        Test string payload in the make() result.
        """
        dumpling = Dumpling(chef=mock_chef, payload='test payload')
        data = json.loads(dumpling.make())

        assert data['payload'] == 'test payload'

    def test_make_payload_list(self, mock_chef):
        """
        Test list payload in the make() result.
        """
        test_payload = list(range(10))
        dumpling = Dumpling(chef=mock_chef, payload=test_payload)
        data = json.loads(dumpling.make())

        assert data['payload'] == test_payload

    def test_make_payload_dict(self, mock_chef):
        """
        Test dict payload in the make() result.
        """
        test_payload = {
            'one': 1,
            'two': [1, 2, 3],
            'three': {
                'four': 5,
            }
        }
        dumpling = Dumpling(chef=mock_chef, payload=test_payload)
        data = json.loads(dumpling.make())

        assert data['payload'] == test_payload

    def test_unserializable_payload(self, mock_chef):
        """
        Test an unserializable Dumpling payload.
        """
        dumpling = Dumpling(chef=mock_chef, payload=lambda x: x)

        with pytest.raises(InvalidDumplingPayload):
            dumpling.make()
