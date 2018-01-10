import asyncio
import builtins
import json
import logging
import types

import asynctest
import click.testing
import pytest

from netdumplings.console.snifty import (
    snifty_cli, get_valid_chefs, network_sniffer, dumpling_emitter,
    notify_shifty,
)


class TestSniftyCLI:
    """
    Test the snifty_cli() function.
    """
    def test_default_case(self, mocker):
        # We exit the infinite loop by faking the death of the sniffer process.
        mock_sniffer_process = mocker.Mock()
        mock_sniffer_process.is_alive.side_effect = [True, True, False, False]

        mock_dumpling_emitter_process = mocker.Mock()
        mock_dumpling_emitter_process.is_alive.return_value = True

        mock_queue = mocker.patch('netdumplings.console.snifty.Queue')
        mock_configure_logging = mocker.patch(
            'netdumplings.console.snifty.configure_logging'
        )
        mocker.patch('netdumplings.console.snifty.sleep')
        mock_process = mocker.patch(
            'netdumplings.console.snifty.Process',
            side_effect=[mock_sniffer_process, mock_dumpling_emitter_process],
        )

        runner = click.testing.CliRunner()
        result = runner.invoke(
            snifty_cli,
            [
                '--kitchen-name', 'test_kitchen',
                '--shifty', 'test_shifty:5000',
                '--interface', 'test_interface',
                '--filter', 'test_filter',
                '--chef-module', 'netdumplings.dumplingchefs',
                '--chef', 'ARPChef',
                '--poke-interval', 10,
            ],
        )

        mock_configure_logging.assert_called_once()

        # Check that the sniffer & dumpling emitter processes were created and
        # started.

        assert mock_process.call_count == 2

        mock_process.assert_any_call(
            target=network_sniffer,
            args=(
                'test_kitchen',
                'test_interface',
                ('ARPChef',),
                ('netdumplings.dumplingchefs',),
                {
                    'netdumplings.dumplingchefs': ['ARPChef'],
                },
                'test_filter',
                10.0,
                mock_queue.return_value,
            )
        )

        mock_process.assert_any_call(
            target=dumpling_emitter,
            args=(
                'test_kitchen',
                'test_shifty:5000',
                mock_queue.return_value,
                {
                    'kitchen_name': 'test_kitchen',
                    'interface': 'test_interface',
                    'filter': 'test_filter',
                    'chefs': ['netdumplings.dumplingchefs.ARPChef'],
                    'poke_interval': 10.0,
                },
            ),
        )

        # We exited the infinite loop by faking the end of the sniffer process.
        # This means we should have called terminate() on the emitter process.
        mock_sniffer_process.start.assert_called_once()
        assert mock_sniffer_process.terminate.call_count == 0

        mock_dumpling_emitter_process.start.assert_called_once()
        mock_dumpling_emitter_process.terminate.assert_called_once()

        assert result.exit_code == 0

    def test_no_valid_chefs(self, mocker):
        """
        Test that no valid chefs results in an error log and an exit code of 1.
        """
        mocker.patch(
            'netdumplings.console.snifty.get_valid_chefs',
            return_value={},
        )

        logger = logging.getLogger('netdumplings.console.snifty')
        mock_error = mocker.patch.object(logger, 'error')

        runner = click.testing.CliRunner()
        result = runner.invoke(
            snifty_cli,
            [
                '--kitchen-name', 'test_kitchen',
            ],
        )

        mock_error.assert_called_once_with(
            'test_kitchen: No valid chefs found. Not starting sniffer.'
        )

        assert result.exit_code == 1


class TestSniftyChefList:
    """
    Test the chef_list() function.
    """
    def test_chef_list(self, mocker):
        """
        Test requesting a chef list.
        """
        mock_list_chefs = mocker.patch(
            'netdumplings.console.snifty.list_chefs'
        )

        runner = click.testing.CliRunner()
        result = runner.invoke(
            snifty_cli,
            [
                '--chef-list',
                '--chef-module', 'testchefs.one',
                '--chef-module', 'morechefs',
            ],
        )

        assert result.exit_code == 0
        mock_list_chefs.assert_called_once_with(('testchefs.one', 'morechefs'))


class TestSniftyNetworkSniffer:
    """
    Test the network_sniffer() function.
    """
    def test_network_sniffer(self, mocker):
        """
        Test calling network_sniffer(). We pass in a single valid chef and
        perform the following checks:

         - The kitchen gets instantiated.
         - The chef is instantiated, assigned to the kitchen, and given the
           dumpling queue.
         - The kitchen's run() method is called.
        """
        # network_sniffer() uses the __import__ builtin to import chefs, so we
        # need to patch that.
        builtin_import = builtins.__import__
        chef_class_callable = mocker.Mock()

        def import_side_effect(*args, **kwargs):
            if args[0] == 'chefmodule':
                return types.SimpleNamespace(ChefName=chef_class_callable)

            return builtin_import(*args, **kwargs)

        mocker.patch.object(
            builtins, '__import__', side_effect=import_side_effect
        )

        mock_dumpling_kitchen = mocker.patch('netdumplings.DumplingKitchen')

        kitchen_name = 'test_kitchen'
        interface = 'test_interface'
        chefs = ''
        chef_modules = ''
        valid_chefs = {'chefmodule': ['ChefName']}
        sniffer_filter = 'test_filter'
        chef_poke_interval = 10
        dumpling_queue = mocker.Mock()

        network_sniffer(
            kitchen_name, interface, chefs, chef_modules, valid_chefs,
            sniffer_filter, chef_poke_interval, dumpling_queue,
        )

        # Check that the DumplingKitchen was instantiated and run() was called.
        mock_dumpling_kitchen.assert_called_once_with(
            name=kitchen_name,
            interface=interface,
            sniffer_filter=sniffer_filter,
            chef_poke_interval=chef_poke_interval,
            dumpling_queue=dumpling_queue,
        )

        mock_dumpling_kitchen.return_value.run.assert_called_once()

        chef_class_callable.assert_called_once_with(
            kitchen=mock_dumpling_kitchen.return_value,
        )


class TestSniftyListChefs:
    """
    Test the list_chefs() function.
    """
    def test_list_chefs_default(self):
        """
        Test default import of chefs from netdumplings.dumplingchefs.
        """
        runner = click.testing.CliRunner()
        result = runner.invoke(
            snifty_cli,
            [
                '--chef-list',
            ],
        )

        assert result.exit_code == 0
        assert result.output == (
            '\nnetdumplings.dumplingchefs\n'
            '  ARPChef\n'
            '  DNSLookupChef\n'
            '  PacketCountChef\n\n'
        )

    def test_invalid_module(self, mocker):
        """
        Test attempt to list chefs from one valid and one missing module.
        """
        mocker.patch(
            'netdumplings.DumplingKitchen.get_chefs_in_modules',
            return_value={
                'doesnotexist': {
                    'import_error': 'does not exist',
                    'chef_classes': [],
                },
                'valid': {
                    'import_error': False,
                    'chef_classes': ['ValidOneChef', 'ValidTwoChef'],
                }
            }
        )

        runner = click.testing.CliRunner()
        result = runner.invoke(
            snifty_cli,
            [
                '--chef-list',
                '--chef-module', 'doesnotexist'
            ],
        )

        assert result.exit_code == 0
        assert result.output == (
            '\n'
            'doesnotexist\n'
            '  error importing module: does not exist\n'
            '\n'
            'valid\n'
            '  ValidOneChef\n'
            '  ValidTwoChef\n'
            '\n'
        )


class TestSniftyGetValidChefs:
    """
    Test the get_valid_chefs() function.
    """
    def test_chef_retrieval(self, mocker):
        """
        We fame two chef modules containing three chefs total, but one of them
        has its assignable_to_kitchen set to False. Only the remaining two
        should be imported. We also request a missing chef, and check that a
        warning was logged for that one.
        """
        test_chef_info = {
            'moduleone': {
                'import_error': False,
                'chef_classes': ['ValidOneAChef', 'ValidOneBChef'],
            },
            'moduletwo': {
                'import_error': False,
                'chef_classes': ['ValidTwoAChef'],
            },
        }

        mocker.patch(
            'netdumplings.DumplingKitchen.get_chefs_in_modules',
            return_value=test_chef_info,
        )

        # We retain a reference to the __import__ builtin, then we patch it for
        # testing purposes. If we're not importing a test chef module then the
        # patch will call the builtin __import__ instead.
        builtin_import = builtins.__import__

        def import_side_effect(*args, **kwargs):
            if args[0] in test_chef_info.keys():
                chef_classes = test_chef_info[args[0]]['chef_classes']
                chef_module = types.SimpleNamespace()
                for chef_class in chef_classes:
                    setattr(
                        chef_module,
                        chef_class,
                        types.SimpleNamespace(
                            assignable_to_kitchen=(
                                False if chef_class == 'ValidOneBChef'
                                else True
                            )
                        )
                    )
                return chef_module

            return builtin_import(*args, **kwargs)

        mocker.patch.object(
            builtins, '__import__', side_effect=import_side_effect
        )

        mock_log = mocker.Mock()

        result = get_valid_chefs(
            'test_kitchen',
            chef_modules=test_chef_info.keys(),
            chefs_requested=[
                'ValidOneAChef',
                'ValidOneBChef',
                'ValidTwoAChef',
                'MissingChef'
            ],
            log=mock_log,
        )

        # We should only have gotten two of our requested chefs back (one from
        # each of our test modules). This is because one has its
        # assignable_to_kitchen attribute set to False; and one was missing.
        assert result == {
            'moduleone': ['ValidOneAChef'],
            'moduletwo': ['ValidTwoAChef'],
        }

        mock_log.warning.assert_called_with(
            'test_kitchen: Chef MissingChef not found'
        )


class TestSniftyDumplingEmitter:
    """
    Test the dumpling_emitter() function and the closely-related
    notify_shifty() async function.
    """
    def test_dumpling_emitter(self, mocker):
        """
        Test that the dumpling emitter kicks off an async event loop running
        notify_shifty().
        """
        log = logging.getLogger('netdumplings.snifty')

        mock_queue = mocker.Mock()
        mock_get_event_loop = mocker.patch('asyncio.get_event_loop')

        mock_notify_shifty = mocker.patch(
            'netdumplings.console.snifty.notify_shifty',
            return_value=asynctest.CoroutineMock(),
        )

        dumpling_emitter('test_kitchen', 'test_shifty:5000', mock_queue, {})

        # Check that an event loop was retrieved, and that run_until_complete
        # wa called on it, running notify_shifty.
        mock_get_event_loop.assert_called_once()

        mock_notify_shifty.assert_called_once_with(
            'test_kitchen', 'test_shifty:5000', mock_queue, {}, log
        )

        mock_loop = mock_get_event_loop.return_value
        mock_loop.run_until_complete.assert_called_once_with(
            mock_notify_shifty.return_value
        )

    @pytest.mark.asyncio
    async def test_notify_shfty(
            self, mocker, test_dumpling_dns, test_dumpling_pktcount,
            test_kitchen):
        """
        Test a conventional execution of notify_shifty(). We make sure a
        websocket connection is opened to shifty; and that two dumplings are
        successfully retrieved from the dumpling queue and re-emitted down the
        websocket connection.
        """
        log = logging.getLogger('netdumplings.snifty')

        # Mock the dumpling queue to contain a dumpling then throw a
        # RuntimeError to break out of the infinite loop.
        mock_queue = mocker.Mock()
        mock_queue.get.side_effect = [
            json.dumps(test_dumpling_dns),
            json.dumps(test_dumpling_pktcount),
            RuntimeError,
        ]

        test_kitchen_name = 'test_kitchen'
        test_shifty = 'test_shifty:5000'

        mock_websockets_connect = mocker.patch(
            'websockets.connect',
            new=asynctest.CoroutineMock(),
        )

        mock_websocket = mock_websockets_connect.return_value
        mock_websocket.send = asynctest.CoroutineMock()

        try:
            await notify_shifty(
                kitchen_name=test_kitchen_name,
                shifty=test_shifty,
                dumpling_queue=mock_queue,
                kitchen_info=test_kitchen,
                log=log,
            )
        except RuntimeError:
            pass

        # Check that we connected to shifty.
        mock_websockets_connect.assert_called_with(
            'ws://{}'.format(test_shifty)
        )

        # Check that the kitchen announced itself first, before forwarding
        # a dumpling from the queue to shifty.
        assert mock_queue.get.call_count == 3

        assert mock_websocket.send.call_args_list == [
            ((json.dumps(test_kitchen),),),
            ((json.dumps(test_dumpling_dns),),),
            ((json.dumps(test_dumpling_pktcount),),),
        ]

    @pytest.mark.asyncio
    async def test_websocket_connection_problem(self, mocker, test_kitchen):
        """
        Test that we log an error when there's a probem connection over the
        websocket to shifty.
        """
        log = logging.getLogger('netdumplings.snifty')
        mock_error = mocker.patch.object(log, 'error')

        mock_websockets_connect = mocker.patch(
            'websockets.connect',
            side_effect=OSError,
        )

        mock_websocket = mock_websockets_connect.return_value
        mock_websocket.send = asynctest.CoroutineMock()

        test_kitchen_name = 'test_kitchen'
        test_shifty = 'test_shifty:5000'

        await notify_shifty(
            kitchen_name=test_kitchen_name,
            shifty=test_shifty,
            dumpling_queue=mocker.Mock(),
            kitchen_info=test_kitchen,
            log=log,
        )

        # Check that we logged an error and never attempted to send anything
        # over the websocket.
        assert mock_error.call_count >= 1
        assert mock_websocket.send.call_count == 0

    @pytest.mark.asyncio
    async def test_cancelled_error(self, mocker, test_kitchen):
        """
        Test that an asyncio.CancelledError attempts to close the websocket.
        """
        log = logging.getLogger('netdumplings.snifty')

        mock_queue = mocker.Mock()
        mock_queue.get.side_effect = [
            asyncio.CancelledError,
        ]

        test_kitchen_name = 'test_kitchen'
        test_shifty = 'test_shifty:5000'

        mock_websockets_connect = mocker.patch(
            'websockets.connect',
            new=asynctest.CoroutineMock(),
        )

        mock_websocket = mock_websockets_connect.return_value
        mock_websocket.send = asynctest.CoroutineMock()
        mock_websocket.close = asynctest.CoroutineMock()

        await notify_shifty(
            kitchen_name=test_kitchen_name,
            shifty=test_shifty,
            dumpling_queue=mock_queue,
            kitchen_info=test_kitchen,
            log=log,
        )

        mock_websocket.close.assert_called_once()
