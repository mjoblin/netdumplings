import json
import time

import pytest

from netdumplings import Dumpling, DumplingChef, DumplingDriver
from netdumplings.exceptions import InvalidDumpling, InvalidDumplingPayload


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


@pytest.fixture
def mock_time(mocker):
    return mocker.patch.object(time, 'time', return_value=time.time())


@pytest.fixture(scope='function')
def dumpling_dict():
    return {
        'metadata': {
            'chef': 'PacketCountChef',
            'creation_time': 1515990765.925951,
            'driver': 'interval',
            'kitchen': 'default_kitchen',
        },
        'payload': {
            'packet_counts': {
                'Ethernet': 1426745,
                'IP': 1423352,
                'TCP': 12382,
                'UDP': 1413268,
            },
        },
    }


class TestDumpling:
    """
    Test the Dumpling class.
    """
    def test_init_with_chef_instance(self, mock_chef, mock_kitchen, mock_time):
        """
        Test initialization of a Dumpling.
        """
        dumpling = Dumpling(chef=mock_chef, payload=None)

        assert dumpling.chef is mock_chef
        assert dumpling.chef_name == 'TestChef'
        assert dumpling.kitchen is mock_kitchen
        assert dumpling.driver is DumplingDriver.packet
        assert dumpling.creation_time == mock_time.return_value
        assert dumpling.payload is None

    def test_init_with_chef_string(self, mock_time):
        """
        Test initialization of a Dumpling with a chef string.
        """
        dumpling = Dumpling(chef='test_chef', payload=None)

        assert dumpling.chef == 'test_chef'
        assert dumpling.chef_name == 'test_chef'
        assert dumpling.kitchen is None
        assert dumpling.driver is DumplingDriver.packet
        assert dumpling.creation_time == mock_time.return_value
        assert dumpling.payload is None

    def test_metadata(self, mocker, mock_chef, mock_time):
        """
        Test metadata keys in the to_json() result.
        """
        dumpling = Dumpling(chef=mock_chef, payload=None)
        data = json.loads(dumpling.to_json())
        metadata = data['metadata']

        assert metadata['chef'] == mock_chef.name
        assert metadata['kitchen'] == mock_chef.kitchen.name
        assert metadata['driver'] == 'packet'
        assert metadata['creation_time'] == mock_time.return_value

    def test_to_json_payload_string(self, mock_chef):
        """
        Test string payload in the to_json() result.
        """
        dumpling = Dumpling(chef=mock_chef, payload='test payload')
        data = json.loads(dumpling.to_json())

        assert data['payload'] == 'test payload'

    def test_to_json_payload_list(self, mock_chef):
        """
        Test list payload in the to_json() result.
        """
        test_payload = list(range(10))
        dumpling = Dumpling(chef=mock_chef, payload=test_payload)
        data = json.loads(dumpling.to_json())

        assert data['payload'] == test_payload

    def test_to_json_payload_dict(self, mock_chef):
        """
        Test dict payload in the to_json() result.
        """
        test_payload = {
            'one': 1,
            'two': [1, 2, 3],
            'three': {
                'four': 5,
            }
        }
        dumpling = Dumpling(chef=mock_chef, payload=test_payload)
        data = json.loads(dumpling.to_json())

        assert data['payload'] == test_payload

    def test_unserializable_payload(self, mock_chef):
        """
        Test an unserializable Dumpling payload.
        """
        dumpling = Dumpling(chef=mock_chef, payload=lambda x: x)

        with pytest.raises(InvalidDumplingPayload):
            dumpling.to_json()

    def test_from_json_valid(self, dumpling_dict):
        """
        Test creating a dumpling from valid input JSON.
        """
        dumpling = Dumpling.from_json(json.dumps(dumpling_dict))

        assert dumpling.chef == 'PacketCountChef'
        assert dumpling.creation_time == 1515990765.925951
        assert dumpling.driver is DumplingDriver.interval
        assert dumpling.kitchen == 'default_kitchen'
        assert dumpling.payload == dumpling_dict['payload']

    def test_from_json_invalid(self, dumpling_dict):
        """
        Test creating a dumpling from invalid input JSON. Should raise
        InvalidDumpling.
        """
        dumpling_dict['payload']['invalid'] = self

        with pytest.raises(InvalidDumpling):
            Dumpling.from_json(dumpling_dict)

    def test_repr(self, mock_time, dumpling_dict):
        """
        Test the string representation.
        """
        dumpling = Dumpling(chef='test_chef', payload=None)
        assert repr(dumpling) == (
            "Dumpling(chef='test_chef', "
            'driver=DumplingDriver.packet, '
            'creation_time={}, '
            'payload=None)'.format(mock_time.return_value)
        )

        chef = DumplingChef()
        chef_repr = repr(chef)

        dumpling = Dumpling(
            chef=chef,
            driver=DumplingDriver.interval,
            payload='test_payload'
        )

        assert repr(dumpling) == (
            'Dumpling(chef={}, '
            'driver=DumplingDriver.interval, '
            'creation_time={}, '
            'payload=<str>)'.format(chef_repr, mock_time.return_value)
        )

        dumpling = Dumpling(
            chef=chef,
            driver=DumplingDriver.interval,
            payload=[1, 2, 3]
        )

        assert repr(dumpling) == (
            'Dumpling(chef={}, '
            'driver=DumplingDriver.interval, '
            'creation_time={}, '
            'payload=<list>)'.format(chef_repr, mock_time.return_value)
        )

        dumpling = Dumpling(
            chef=chef,
            driver=DumplingDriver.interval,
            payload={'test': 10}
        )

        assert repr(dumpling) == (
            'Dumpling(chef={}, '
            'driver=DumplingDriver.interval, '
            'creation_time={}, '
            'payload=<dict>)'.format(chef_repr, mock_time.return_value)
        )

        dumpling = Dumpling.from_json(json.dumps(dumpling_dict))

        assert repr(dumpling) == (
            "Dumpling(chef='PacketCountChef', "
            'driver=DumplingDriver.interval, '
            'creation_time=1515990765.925951, '
            'payload=<dict>)'
        )
