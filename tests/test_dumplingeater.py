import asyncio
import json
import signal

import asynctest
import pytest
import websockets.exceptions

from netdumplings import DumplingEater
from netdumplings._shared import HUB_HOST, HUB_OUT_PORT


# -----------------------------------------------------------------------------

@pytest.fixture(scope='function')
def mock_websocket(mocker):
    """
    A mocked eater websocket connection.
    """
    mock_connect = mocker.patch(
        'websockets.client.connect',
        new=asynctest.CoroutineMock(),
    )

    mock_ws = mock_connect.return_value
    mock_ws.send = asynctest.CoroutineMock()
    mock_ws.recv = asynctest.CoroutineMock()
    mock_ws.close = asynctest.CoroutineMock()

    return mock_ws


@pytest.fixture(scope='function')
def eater_with_mocked_handlers():
    """
    An eater with mocked handlers for on_connect, on_dumpling, and
    on_connection_lost.
    """
    eater = DumplingEater(
        on_connect=asynctest.CoroutineMock(),
        on_dumpling=asynctest.CoroutineMock(),
        on_connection_lost=asynctest.CoroutineMock(),
    )

    return eater


# -----------------------------------------------------------------------------

class TestDumplingEater:
    """
    Test the DumplingEater class.
    """
    def test_init_default(self):
        """
        Test default DumplingEater initialization.
        """
        eater = DumplingEater()

        assert eater.name == 'nameless_eater'
        assert eater.chef_filter is None
        assert eater.hub_ws == 'ws://{}:{}'.format(HUB_HOST, HUB_OUT_PORT)

    def test_init_overrides(self):
        """
        Test DumplingEater initialization with overrides.
        """
        test_eater_name = 'test_eater'
        test_hub = 'there:1234'
        test_chefs = ['ChefOne', 'ChefTwo', 'ChefThree']

        async def test_handler():
            pass

        eater = DumplingEater(
            name=test_eater_name,
            hub=test_hub,
            chef_filter=test_chefs,
            on_connect=test_handler,
            on_dumpling=test_handler,
            on_connection_lost=test_handler
        )

        assert eater.name == test_eater_name
        assert eater.chef_filter == test_chefs
        assert eater.hub_ws == 'ws://{}'.format(test_hub)
        assert eater.on_connect == test_handler
        assert eater.on_dumpling == test_handler
        assert eater.on_connection_lost == test_handler

    def test_interrupt_handler(self, mocker):
        """
        Test that the interrupt handler attempts to cancel all async tasks.
        """
        mock_asyncio_task = mocker.patch('asyncio.Task')

        # Configure three mock async tasks. We check that cancel() gets called
        # on each of them.
        mock_all_tasks = [
            mocker.Mock(),
            mocker.Mock(),
            mocker.Mock(),
        ]

        mock_asyncio_task.all_tasks.return_value = mock_all_tasks

        eater = DumplingEater()
        eater._interrupt_handler()

        for mock_task in mock_all_tasks:
            mock_task.cancel.assert_called_once()

    def test_repr(self):
        """
        Test the string representation.
        """
        def handler():
            pass

        eater = DumplingEater(
            name='test_eater',
            hub='test_hub',
            chef_filter=['ChefOne', 'ChefTwo'],
            on_connect=handler,
            on_dumpling=handler,
            on_connection_lost=handler,
        )
        assert repr(eater) == (
            "DumplingEater("
            "name='test_eater', "
            "hub='test_hub', "
            "chef_filter=['ChefOne', 'ChefTwo'], "
            "on_connect={}, "
            "on_dumpling={}, "
            "on_connection_lost={})".format(
                '<callable: {}>'.format(handler.__name__),
                '<callable: {}>'.format(handler.__name__),
                '<callable: {}>'.format(handler.__name__),
            )
        )


# -----------------------------------------------------------------------------

class TestDumplingEaterDefaultHandlers:
    """
    Test the default handlers. They should just log warnings.
    """
    @pytest.mark.asyncio
    async def test_default_on_connect(self, mocker):
        eater = DumplingEater(name='test_eater')
        mock_logger = mocker.patch.object(eater, 'logger')

        await eater.on_connect(None, None)

        mock_logger.warning.assert_called_once_with(
            'test_eater: No on_connect handler specified; ignoring connection.'
        )

    @pytest.mark.asyncio
    async def test_default_on_dumpling(self, mocker):
        eater = DumplingEater(name='test_eater')
        mock_logger = mocker.patch.object(eater, 'logger')

        await eater.on_dumpling(None)

        mock_logger.warning.assert_called_once_with(
            'test_eater: No on_dumpling handler specified; ignoring dumpling.'
        )

    @pytest.mark.asyncio
    async def test_default_on_connection_lost(self, mocker):
        eater = DumplingEater(name='test_eater')
        mock_logger = mocker.patch.object(eater, 'logger')

        await eater.on_connection_lost(None)

        mock_logger.warning.assert_called_once_with(
            'test_eater: No on_connection_lost handler specified; ignoring '
            'connection loss.'
        )


# -----------------------------------------------------------------------------

class TestDumplingEaterGrabDumplings:
    """
    Test the _grab_dumplings() method.
    """
    @pytest.mark.asyncio
    async def test_grab_dumplings(self, mocker, test_dumpling_dns):
        """
        Test asking for a single dumpling.
        """
        mock_connect = mocker.patch(
            'websockets.client.connect',
            new=asynctest.CoroutineMock(),
        )

        mock_websocket = mock_connect.return_value
        mock_websocket.send = asynctest.CoroutineMock()
        mock_websocket.recv = asynctest.CoroutineMock()
        mock_websocket.close = asynctest.CoroutineMock()

        # Configure recv() to receive a dumpling and then fake a websocket
        # connection close.
        mock_websocket.recv.side_effect = [
            json.dumps(test_dumpling_dns),
            websockets.exceptions.ConnectionClosed(1006, reason='unknown'),
        ]

        eater = DumplingEater(
            name='test_eater',
            hub='testhub:5000',
            on_connect=asynctest.CoroutineMock(),
            on_dumpling=asynctest.CoroutineMock(),
            on_connection_lost=asynctest.CoroutineMock(),
        )

        await eater._grab_dumplings(dumpling_count=1)

        # Check that the eater connected to the expected hub and announced
        # itself.
        mock_connect.assert_called_with('ws://testhub:5000')
        mock_connect.return_value.send.assert_called_once_with(json.dumps({
            'eater_name': 'test_eater',
        }))

        # Check the on_connect and on_dumpling handlers were called; and that
        # on_connection_lost was not.
        eater.on_connect.assert_called_once()
        eater.on_dumpling.assert_called_once_with(test_dumpling_dns)
        assert eater.on_connection_lost.call_count == 0

        # Check that the eater closed the websocket (it was only eating a
        # single dumpling).
        mock_websocket.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlimited_dumplings(
            self, mock_websocket, test_dumpling_dns, test_dumpling_pktcount,
            eater_with_mocked_handlers):
        """
        Test asking for a unlimited dumplings.
        """
        # Configure recv() to receive 3 dumplings then we use RuntimeError to
        # break out of the infinite loop.
        mock_websocket.recv.side_effect = [
            json.dumps(test_dumpling_dns),
            json.dumps(test_dumpling_pktcount),
            json.dumps(test_dumpling_dns),
            RuntimeError,
        ]

        try:
            # Request no dumpling limit.
            await eater_with_mocked_handlers._grab_dumplings()
        except RuntimeError:
            pass

        # Check the on_connect and on_dumpling handlers were called.
        eater_with_mocked_handlers.on_connect.assert_called_once()

        assert eater_with_mocked_handlers.on_dumpling.call_args_list == [
            ((test_dumpling_dns,),),
            ((test_dumpling_pktcount,),),
            ((test_dumpling_dns,),),
        ]

    @pytest.mark.asyncio
    async def test_invalid_dumpling(
            self, mocker, mock_websocket, test_dumpling_dns,
            test_dumpling_pktcount, eater_with_mocked_handlers):
        """
        Test receiving three dumplings, the second of which is invalid. The
        on_dumpling handler should only be called twice.
        """
        mock_websocket.recv.side_effect = [
            json.dumps(test_dumpling_dns),
            '{invalid',
            json.dumps(test_dumpling_pktcount),
            RuntimeError,
        ]

        mock_logger = mocker.patch.object(eater_with_mocked_handlers, 'logger')

        try:
            await eater_with_mocked_handlers._grab_dumplings()
        except RuntimeError:
            pass

        assert eater_with_mocked_handlers.on_dumpling.call_count == 2
        assert mock_logger.error.call_count >= 1

    @pytest.mark.asyncio
    async def test_chef_filter(
            self, mock_websocket, test_dumpling_dns, test_dumpling_pktcount):
        """
        Test restricting the eater to receive dumplings from only one chef.
        We also limit the desired dumpling count to 2 to ensure that also works
        with a chef filter.
        """
        mock_websocket.recv.side_effect = [
            json.dumps(test_dumpling_pktcount),
            json.dumps(test_dumpling_pktcount),
            json.dumps(test_dumpling_dns),
            json.dumps(test_dumpling_pktcount),
            json.dumps(test_dumpling_dns),
            json.dumps(test_dumpling_pktcount),
            json.dumps(test_dumpling_dns),
        ]

        eater = DumplingEater(
            chef_filter=['DNSLookupChef'],
            on_connect=asynctest.CoroutineMock(),
            on_dumpling=asynctest.CoroutineMock(),
            on_connection_lost=asynctest.CoroutineMock(),
        )

        await eater._grab_dumplings(dumpling_count=2)

        # The on_dumpling handler should only be called twice -- with two of
        # the DNSLookupChef dumplings and none of the PacketCountChef
        # dumplings.
        assert eater.on_dumpling.call_count == 2

        assert eater.on_dumpling.call_args_list == [
            ((test_dumpling_dns,),),
            ((test_dumpling_dns,),),
        ]

    @pytest.mark.asyncio
    async def test_cancelled_error(
            self, mocker, mock_websocket, test_dumpling_dns,
            eater_with_mocked_handlers):
        """
        Test the infinite eater loop being interrupted by an
        asyncio.CancelledError. This should close the websocket and log a
        warning. The on_connection_lost handler shold not be called.
        """
        mock_websocket.recv.side_effect = [
            json.dumps(test_dumpling_dns),
            asyncio.CancelledError,
        ]

        mock_logger = mocker.patch.object(eater_with_mocked_handlers, 'logger')

        await eater_with_mocked_handlers._grab_dumplings(dumpling_count=None)

        mock_websocket.close.assert_called_once_with(
            4101, 'connection cancelled'
        )

        assert eater_with_mocked_handlers.on_connection_lost.call_count == 0
        assert mock_logger.warning.call_count >= 1

    @pytest.mark.asyncio
    async def test_connection_closed(
            self, mocker, mock_websocket, test_dumpling_dns,
            eater_with_mocked_handlers):
        """
        Test the infinite eater loop being interrupted by
        websockets.exceptions.ConnectionClosed. This should invoke the
        on_connection_lost handler, and log a warning. An attempt to close
        the websocket should not be made.
        """
        mock_websocket.recv.side_effect = [
            json.dumps(test_dumpling_dns),
            websockets.exceptions.ConnectionClosed(1006, 'unknown'),
        ]

        mock_logger = mocker.patch.object(eater_with_mocked_handlers, 'logger')

        await eater_with_mocked_handlers._grab_dumplings(dumpling_count=None)

        eater_with_mocked_handlers.on_connection_lost.assert_called_once()
        assert mock_logger.warning.call_count >= 1
        assert mock_websocket.close.call_count == 0

    def additional(self):
        # TODO: Pass in chef name when instantiating DumplingEater
        # TODO: Invalid dumpling
        pass


# -----------------------------------------------------------------------------

class TestDumplingEaterRun:
    """
    Test the run() method.
    """
    def test_run(self, mocker):
        """
        Test a conventional problem-less run.
        """
        mock_get_event_loop = mocker.patch('asyncio.get_event_loop')
        mock_loop = mock_get_event_loop.return_value

        mock_task = asynctest.CoroutineMock()
        mock_loop.create_task.return_value = mock_task

        mock_interrupt_handler = mocker.Mock()
        DumplingEater._interrupt_handler = mock_interrupt_handler

        eater = DumplingEater()

        mock_grab_dumplings = mocker.patch.object(
            eater,
            '_grab_dumplings',
            new=asynctest.CoroutineMock(),
        )

        # Run the eater. It will fall out of its infinite loop right away due
        # to the _grab_dumplings() mock.
        eater.run()

        mock_grab_dumplings.assert_called_once_with(None)

        # Check that run_until_complete() is called on the async loop,
        # and that the loop is closed when the dumpling grabber is done.
        mock_loop.run_until_complete.assert_called_once_with(mock_task)
        assert mock_loop.close.call_count == 1

        # Check that _interrupt_handler() was assigned to SIGTERM and SIGINT.
        assert mock_loop.add_signal_handler.call_args_list == [
            ((signal.SIGTERM, mock_interrupt_handler),),
            ((signal.SIGINT, mock_interrupt_handler),),
        ]

    def test_on_dumpling_not_callable(self, mocker):
        """
        Test invoking run() when the eater's on_dumpling is not callable.
        """
        mock_get_event_loop = mocker.patch('asyncio.get_event_loop')

        eater = DumplingEater(on_dumpling='string')
        mock_logger = mocker.patch.object(eater, 'logger')

        eater.run()

        mock_logger.error.assert_called_once()

        # We should never have attempted to get the event loop.
        assert mock_get_event_loop.call_count == 0

    def test_keyboard_interrupt(self, mocker):
        """
        Test a KeybordInterrupt exception. This should result in logging some
        warning, all async tasks being canceled, and the async loop being
        closed.
        """
        mock_get_event_loop = mocker.patch('asyncio.get_event_loop')
        mock_loop = mock_get_event_loop.return_value
        mock_loop.run_until_complete.side_effect = KeyboardInterrupt

        mock_asyncio_task = mocker.patch('asyncio.Task')

        # Configure three mock async tasks. We check that cancel() gets called
        # on each of them.
        mock_all_tasks = [
            mocker.Mock(),
            mocker.Mock(),
            mocker.Mock(),
        ]

        mock_asyncio_task.all_tasks.return_value = mock_all_tasks

        eater = DumplingEater()

        mocker.patch.object(
            eater,
            '_grab_dumplings',
            new=asynctest.CoroutineMock(),
        )

        mock_logger = mocker.patch.object(eater, 'logger')

        eater.run()

        # Make sure we logged some warnings.
        assert mock_logger.warning.call_count >= 1

        # Make sure we canceled all async tasks.
        for mock_task in mock_all_tasks:
            mock_task.cancel.assert_called_once()

        # Make sure we still closed the loop.
        assert mock_loop.close.call_count == 1

    def test_oserror(self, mocker):
        """
        Test an OSError exception. This should result in logging some warnings
        and the async loop being closed.
        """
        mock_get_event_loop = mocker.patch('asyncio.get_event_loop')
        mock_loop = mock_get_event_loop.return_value
        mock_loop.run_until_complete.side_effect = OSError

        eater = DumplingEater()

        mocker.patch.object(
            eater,
            '_grab_dumplings',
            new=asynctest.CoroutineMock(),
        )

        mock_logger = mocker.patch.object(eater, 'logger')

        eater.run()

        # Make sure we logged some warnings.
        assert mock_logger.warning.call_count >= 1

        # Make sure we still closed the loop.
        assert mock_loop.close.call_count == 1
