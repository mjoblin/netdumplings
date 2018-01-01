import pytest


@pytest.fixture(scope='module')
def test_kitchen():
    return {
        'kitchen_name': 'test_kitchen',
        'interface': 'test_interface',
        'filter': 'test_filter',
        'chefs': ['PacketCountChef'],
        'poke_interval': 5,
    }


@pytest.fixture(scope='module')
def test_eater():
    return {
        'eater_name': 'test_eater',
    }


@pytest.fixture(scope='module')
def test_dumpling_pktcount():
    return {
        "metadata": {
            "chef": "PacketCountChef",
            "creation_time": 1111196224.996893,
            "driver": "interval",
            "kitchen": "test_kitchen",
        },
        "payload": {
            "packet_counts": {
                "ARP": 4,
                "Ethernet": 4045,
                "IP": 4041,
                "Padding": 1,
                "Raw": 4040,
                "TCP": 3,
                "UDP": 4038,
            },
        },
    }


@pytest.fixture(scope='module')
def test_dumpling_dns():
    return {
        "metadata": {
            "chef": "DNSLookupChef",
            "creation_time": 1111149803.69614,
            "driver": "packet",
            "kitchen": "default_kitchen"
        },
        "payload": {
            "lookup": {
                "hostname": "foo.com",
                "when": 1111149803.696125
            }
        }
    }
