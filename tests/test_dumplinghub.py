import asyncio
import datetime
import json
import numbers

import asynctest
import pytest
from websockets.exceptions import ConnectionClosed

from netdumplings import DumplingDriver, DumplingHub
from netdumplings.exceptions import NetDumplingsError


# -----------------------------------------------------------------------------
# Fixtures for kitchen, eater, and dumpling payloads.

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


# -----------------------------------------------------------------------------

class TestDumplingHub:
    """
    Test the DumplingHub class.
    """
    def test_init_default(self, mocker):
        """
        Test default DumplingHub initialization.
        """
        baked_out_now = datetime.datetime.now()
        mock_datetime = mocker.patch('datetime.datetime')
        mock_datetime.now.return_value = baked_out_now

        hub = DumplingHub()

        assert hub.address == 'localhost'
        assert hub.in_port == 11347
        assert hub.out_port == 11348
        assert hub.status_freq == 5
        assert hub._start_time == baked_out_now

    def test_init_with_overrides(self):
        """
        Test DumplingHub initialization with overrides.
        """
        hub = DumplingHub(
            address='testhost',
            in_port=123,
            out_port=456,
            status_freq=10,
        )

        assert hub.address == 'testhost'
        assert hub.in_port == 123
        assert hub.out_port == 456
        assert hub.status_freq == 10

    def test_repr(self):
        """
        Test the string representation.
        """
        hub = DumplingHub(
            address='test_host',
            in_port=1234,
            out_port=5678,
            status_freq=10
        )

        assert repr(hub) == (
            "DumplingHub("
            "address='test_host', "
            "in_port=1234, "
            "out_port=5678, "
            "status_freq=10)"
        )


# -----------------------------------------------------------------------------

class TestSystemStatus:
    """
    Test functionality related to DumplingHub system status.
    """
    def test_start_status(self):
        """
        Test that the starting status looks good.
        """
        hub = DumplingHub()

        start_status = hub._get_system_status()

        # Make sure we have all the keys we expect, and only those keys.
        assert sorted(start_status.keys()) == [
            'dumpling_eater_count',
            'dumpling_eaters',
            'dumpling_kitchen_count',
            'dumpling_kitchens',
            'server_uptime',
            'total_dumplings_sent',
        ]

        assert start_status['total_dumplings_sent'] == 0
        assert start_status['dumpling_kitchen_count'] == 0
        assert start_status['dumpling_eater_count'] == 0
        assert start_status['dumpling_kitchens'] == []
        assert start_status['dumpling_eaters'] == []
        assert isinstance(
            start_status['server_uptime'], numbers.Number) is True

    @pytest.mark.asyncio
    async def test_announce_system_status(self, mocker):
        """
        Test that the system status announcer is putting SystemStatus dumplings
        onto each of the eaters queues, and sleeping for status_freq seconds.
        """
        test_status_freq = 10
        test_status_dumpling = {'one': 1, 'two': 2}
        test_status_dumpling_json = json.dumps(test_status_dumpling)

        hub = DumplingHub(status_freq=test_status_freq)
        mocker.patch.object(
            hub, '_get_system_status', return_value=test_status_dumpling
        )

        # Configure a couple of fake eaters which only expose queues so we
        # can see whether our fake status dumpling got put to them.
        eater_1_queue = asyncio.Queue()
        eater_2_queue = asyncio.Queue()

        hub._dumpling_eaters = {
            'eater1': {
                'queue': eater_1_queue,
            },
            'eater2': {
                'queue': eater_2_queue,
            },
        }

        mock_dumpling = mocker.patch('netdumplings.dumplinghub.Dumpling')
        mock_dumpling.return_value.make.return_value = (
            test_status_dumpling_json
        )

        # Make asyncio.sleep() throw an Exception to force
        # _announce_system_status() to break out of its infinite loop.
        mock_sleep = mocker.patch.object(
            asyncio, 'sleep', side_effect=Exception
        )

        try:
            await hub._announce_system_status()
        except Exception:
            pass

        # We expect a SystemStatusChef dumpling to have been created and put
        # onto each of the eater's queues (after being serialized to JSON).
        # We also expect the system status announcer to have slept for
        # status_freq seconds.
        mock_dumpling.assert_called_once_with(
            chef='SystemStatusChef',
            driver=DumplingDriver.interval,
            payload=test_status_dumpling,
        )
        mock_sleep.assert_called_once_with(test_status_freq)

        eater1_queue_payload = await eater_1_queue.get()
        eater2_queue_payload = await eater_2_queue.get()

        assert eater1_queue_payload == test_status_dumpling_json
        assert eater2_queue_payload == test_status_dumpling_json


# -----------------------------------------------------------------------------

class TestDumplingGrabber:
    """
    Test the management of a single kitchen's websocket connection.
    """
    @pytest.mark.asyncio
    async def test_dumpling_grabber(
            self, mocker, test_kitchen, test_dumpling_pktcount):
        """
        Test receiving a new valid kitchen connection followed by a dumpling
        from the kitchen.
        """
        # Mock the websocket connection to a single kitchen. The recv() method
        # is called repeatedly: the first time to retrieve kitchen information
        # and subsequent times to retrieve dumplings. We fake the kitchen info
        # and the first dumpling, then we raise a RuntimeError exception to
        # force an exit out of the _grab_dumplings() infinite loop.

        mock_websocket = mocker.Mock()
        mock_websocket.remote_address = ['kitchenhost', 11111]

        mock_websocket.recv = asynctest.CoroutineMock(side_effect=[
            json.dumps(test_kitchen),
            json.dumps(test_dumpling_pktcount),
            RuntimeError,
        ])

        hub = DumplingHub()

        # Set up some mock eaters.
        eater_1 = mocker.Mock()
        eater_2 = mocker.Mock()

        hub._dumpling_eaters = {
            eater_1: {
                'queue': mocker.Mock(),
            },
            eater_2: {
                'queue': mocker.Mock(),
            },
        }

        hub._dumpling_eaters[eater_1]['queue'].put = asynctest.CoroutineMock()
        hub._dumpling_eaters[eater_2]['queue'].put = asynctest.CoroutineMock()

        # We should start with no kitchens.
        assert len(hub._dumpling_kitchens) == 0

        try:
            await hub._grab_dumplings(mock_websocket, path=None)
        except RuntimeError:
            pass

        # Check that the kitchen was added to the kitchen list.
        assert len(hub._dumpling_kitchens) == 1
        assert hub._dumpling_kitchens[mock_websocket] == {
            'metadata': {
                'info_from_kitchen': test_kitchen,
                'info_from_hub': {
                    'host': 'kitchenhost',
                    'port': 11111,
                }
            },
            'websocket': mock_websocket,
        }

        # Check that the dumpling was put onto all of the eater queues.
        hub._dumpling_eaters[eater_1]['queue'].put.assert_called_once_with(
            json.dumps(test_dumpling_pktcount)
        )

        hub._dumpling_eaters[eater_2]['queue'].put.assert_called_once_with(
            json.dumps(test_dumpling_pktcount)
        )

    @pytest.mark.asyncio
    async def test_invalid_dumpling_from_kitchen(
            self, mocker, test_kitchen, test_dumpling_pktcount):
        """
        Test receiving an invalid (non-JSON) dumpling from a kitchen. The hub
        should log an error and move on.
        """
        mock_websocket = mocker.Mock()
        mock_websocket.remote_address = ['kitchenhost', 11111]

        # We send three messages from the kitchen: the initial connection
        # information, followed by a bogus dumpling, followed by a legit
        # dumpling.
        mock_websocket.recv = asynctest.CoroutineMock(side_effect=[
            json.dumps(test_kitchen),
            '{invalid dumpling',
            json.dumps(test_dumpling_pktcount),
            RuntimeError,
        ])

        hub = DumplingHub()

        # Set up a mock eater.
        eater_1 = mocker.Mock()

        hub._dumpling_eaters = {
            eater_1: {
                'queue': mocker.Mock(),
            },
        }

        hub._dumpling_eaters[eater_1]['queue'].put = asynctest.CoroutineMock()

        hub._logger = mocker.Mock()

        try:
            await hub._grab_dumplings(mock_websocket, path=None)
        except RuntimeError:
            pass

        # We should have logged the error.
        hub._logger.error.assert_called_once()

        # Check the eater only had 1 dumpling put on its queue.
        assert hub._dumpling_eaters[eater_1]['queue'].put.call_count == 1

    @pytest.mark.asyncio
    async def test_kitchen_connection_closed(
            self, mocker, test_kitchen, test_dumpling_pktcount):
        """
        Test getting a ConnectionClosed exception from the websocket. The hub
        should remove the kitchen from its kitchen list.
        """
        mock_websocket = mocker.Mock()
        mock_websocket.remote_address = ['kitchenhost', 11111]

        mock_websocket.recv = asynctest.CoroutineMock(side_effect=[
            json.dumps(test_kitchen),
            json.dumps(test_dumpling_pktcount),
            ConnectionClosed(1006, reason='unknown'),
        ])

        hub = DumplingHub()

        # Set up a mock eater.
        eater_1 = mocker.Mock()

        hub._dumpling_eaters = {
            eater_1: {
                'queue': mocker.Mock(),
            },
        }

        hub._dumpling_eaters[eater_1]['queue'].put = asynctest.CoroutineMock()

        # We should start with no kitchens.
        assert len(hub._dumpling_kitchens) == 0

        await hub._grab_dumplings(mock_websocket, path=None)

        # Check that our kitchen list is empty again.
        assert len(hub._dumpling_kitchens) == 0

        # Check that the dumpling was still put onto the eater queue.
        hub._dumpling_eaters[eater_1]['queue'].put.assert_called_once_with(
            json.dumps(test_dumpling_pktcount)
        )


# -----------------------------------------------------------------------------

class TestDumplingEmitter:
    """
    Test the management of a single eater's websocket connection.
    """
    @pytest.mark.asyncio
    async def test_dumpling_emitter(
            self, mocker, test_eater, test_dumpling_pktcount,
            test_dumpling_dns):
        """
        Test receiving a new valid eater connection and sending two dumplings
        from its queue to its websocket.
        """
        mock_websocket = mocker.Mock()
        mock_websocket.remote_address = ['eaterhost', 22222]

        # The hub calls recv() once to retrieve the eater name.
        mock_websocket.recv = asynctest.CoroutineMock(
            return_value=json.dumps(test_eater)
        )

        # Test that two dumplings successfully migrate from the eater's queue
        # to the eater's websocket. After the two dumplings are retrieved from
        # the queue, we throw RuntimeError to break out of the hub's infinite
        # loop.
        mock_websocket.send = asynctest.CoroutineMock()

        mock_queue = mocker.patch('asyncio.Queue')
        mock_queue.return_value.get = asynctest.CoroutineMock(
            side_effect=[
                json.dumps(test_dumpling_pktcount),
                json.dumps(test_dumpling_dns),
                RuntimeError,
            ]
        )

        hub = DumplingHub()

        assert len(hub._dumpling_eaters) == 0
        assert hub._system_stats['dumplings_sent'] == 0

        try:
            await hub._emit_dumplings(mock_websocket, path=None)
        except RuntimeError:
            pass

        # We expect to have one eater registered with the hub, and to have sent
        # two dumplings.
        assert len(hub._dumpling_eaters) == 1
        assert hub._system_stats['dumplings_sent'] == 2

        assert hub._dumpling_eaters[mock_websocket] == {
            'metadata': {
                'info_from_eater': test_eater,
                'info_from_hub': {
                    'host': 'eaterhost',
                    'port': 22222,
                }
            },
            'websocket': mock_websocket,
            'queue': mock_queue.return_value,
        }

        assert mock_websocket.send.call_count == 2

        assert mock_websocket.send.call_args_list == [
            ((json.dumps(test_dumpling_pktcount),),),
            ((json.dumps(test_dumpling_dns),),),
        ]

    @pytest.mark.asyncio
    async def test_eater_connection_closed(
            self, mocker, test_eater, test_dumpling_pktcount):
        """
        Test getting a ConnectionClosed exception from the websocket. The hub
        should remove the eater from its eater list.
        """
        mock_websocket = mocker.Mock()
        mock_websocket.remote_address = ['eaterhost', 22222]

        mock_websocket.recv = asynctest.CoroutineMock(
            return_value=json.dumps(test_eater)
        )

        mock_websocket.send = asynctest.CoroutineMock()

        # Prepare to send one dumpling before faking a ConnectionClosed.
        mock_queue = mocker.patch('asyncio.Queue')
        mock_queue.return_value.get = asynctest.CoroutineMock(
            side_effect=[
                json.dumps(test_dumpling_pktcount),
                ConnectionClosed(1006, reason='unknown'),
            ]
        )

        hub = DumplingHub()

        assert len(hub._dumpling_eaters) == 0
        assert hub._system_stats['dumplings_sent'] == 0

        await hub._emit_dumplings(mock_websocket, path=None)

        # Check that we don't have any eaters in the eater list, but that we
        # still sent a dumpling.
        assert len(hub._dumpling_eaters) == 0
        assert hub._system_stats['dumplings_sent'] == 1

        mock_websocket.send.assert_called_once_with(
            json.dumps(test_dumpling_pktcount)
        )


# -----------------------------------------------------------------------------

class TestRun:
    """
    Test the run() method of the DumplingHub.
    """
    def test_run(self, mocker):
        """
        Test a normal run.
        """
        # Patch websockets.serve, asyncio.get_event_loop(), and
        # asyncio.ensure_future(). We do this to prevent the event loop from
        # actually running while confirming that the websockets and event loop
        # are configured as we expect.

        mock_serve = mocker.patch('websockets.serve')
        mock_get_event_loop = mocker.patch('asyncio.get_event_loop')
        mock_ensure_future = mocker.patch('asyncio.ensure_future')

        hub = DumplingHub()
        mocker.patch.object(hub, '_announce_system_status')
        mocker.patch.object(hub, '_logger')

        hub.run()

        # Check that the two websocket servers are started correctly.
        assert mock_serve.call_count == 2
        assert mock_serve.call_args_list == [
            ((hub._grab_dumplings, hub.address, hub.in_port),),
            ((hub._emit_dumplings, hub.address, hub.out_port),),
        ]

        # Check that the event look was retrieved and that run_forever() was
        # invoked on it.
        mock_get_event_loop.assert_called_once()
        mock_get_event_loop.return_value.run_forever.assert_called_once()

        # Check that _announce_system_status was registered with the loop.
        mock_ensure_future.assert_called_once_with(
            hub._announce_system_status()
        )

    def test_websocket_error(self, mocker):
        """
        Test that the hub raise NetDumplingsError if there's a websocket
        problem (denoted by OSError).
        """
        mocker.patch('websockets.serve')
        mocker.patch('asyncio.ensure_future')

        # Force run_until_complete() to raise OSError. This simulates a
        # websocket problem.
        mock_get_event_loop = mocker.patch('asyncio.get_event_loop')
        mock_get_event_loop.return_value.run_until_complete.side_effect = (
            OSError
        )

        hub = DumplingHub()

        with pytest.raises(NetDumplingsError):
            hub.run()

    def test_keyboard_interrupt(self, mocker):
        """
        Test that the hub logs a warning on KeyboardInterrupt.
        """
        mocker.patch('websockets.serve')
        mocker.patch('asyncio.ensure_future')

        # Force run_forever() to raise KeyboardInterrupt.
        mock_get_event_loop = mocker.patch('asyncio.get_event_loop')
        mock_get_event_loop.return_value.run_forever.side_effect = (
            KeyboardInterrupt
        )

        hub = DumplingHub()

        mocker.patch.object(hub, '_announce_system_status')
        mock_logger = mocker.patch.object(hub, '_logger')

        hub.run()

        mock_logger.warning.assert_called_once()
