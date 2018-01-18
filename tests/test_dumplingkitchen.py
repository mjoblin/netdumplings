import importlib
import json

import pytest

from netdumplings import DumplingKitchen, DumplingChef, DumplingDriver


class TestDumplingKitchen:
    """
    Test the DumplingKitchen class.
    """
    def test_init_default(self, mocker):
        """
        Test default DumplingKitchen initialization.
        """
        mock_queue = mocker.Mock()

        kitchen = DumplingKitchen(dumpling_queue=mock_queue)

        assert kitchen.name == 'default'
        assert kitchen.interface == 'all'
        assert kitchen.filter == 'tcp'
        assert kitchen.chef_poke_interval == 5

        assert len(kitchen._chefs) == 0

    def test_init_with_overrides(self, mocker):
        """
        Test DumplingKitchen initialization with overrides.
        """
        mock_queue = mocker.Mock()

        kitchen = DumplingKitchen(
            dumpling_queue=mock_queue,
            name='test_kitchen',
            interface='en0',
            sniffer_filter='test filter',
            chef_poke_interval=10,
        )

        assert kitchen.dumpling_queue == mock_queue
        assert kitchen.name == 'test_kitchen'
        assert kitchen.interface == 'en0'
        assert kitchen.filter == 'test filter'
        assert kitchen.chef_poke_interval == 10

        assert len(kitchen._chefs) == 0

    def test_chef_registration(self, mocker):
        """
        Test registration of chefs with the kitchen.
        """
        kitchen = DumplingKitchen(dumpling_queue=mocker.Mock())

        assert len(kitchen._chefs) == 0

        test_chef_1 = DumplingChef()
        test_chef_2 = DumplingChef()

        kitchen.register_chef(test_chef_1)
        assert kitchen._chefs == [test_chef_1]

        kitchen.register_chef(test_chef_2)
        assert kitchen._chefs == [test_chef_1, test_chef_2]

    def test_repr(self, mocker):
        """
        Test the string representation.
        """
        kitchen = DumplingKitchen(dumpling_queue=mocker.Mock())
        assert repr(kitchen) == (
            "DumplingKitchen("
            "dumpling_queue={}, "
            "name={}, "
            "interface={}, "
            "sniffer_filter={}, "
            "chef_poke_interval={})".format(
                repr(kitchen.dumpling_queue),
                repr(kitchen.name),
                repr(kitchen.interface),
                repr(kitchen.filter),
                repr(kitchen.chef_poke_interval),
            )
        )


class TestHandlerInvocations:
    """
    Test DumplingKitchen invocations of the packet and interval handlers.
    """
    def test_packet_processing(self, mocker):
        """
        Test invocation of the packet handlers.
        """
        kitchen = DumplingKitchen(dumpling_queue=mocker.Mock())
        mocker.patch.object(kitchen, '_send_dumpling')

        # Set up two valid chefs. One of them returns a dumpling when given a
        # packet, and the other one doesn't.
        mock_chef_with_packet_dumpling = mocker.Mock()
        mock_chef_with_no_packet_dumpling = mocker.Mock()

        mock_chef_with_packet_dumpling.packet_handler.return_value = 'dumpling'
        mock_chef_with_no_packet_dumpling.packet_handler.return_value = None

        kitchen._chefs = [
            mock_chef_with_packet_dumpling,
            mock_chef_with_no_packet_dumpling,
        ]

        packet = 'test_packet'
        kitchen._process_packet(packet)

        # Check that we only sent one packet dumpling.
        kitchen._send_dumpling.assert_called_once_with(
            mock_chef_with_packet_dumpling,
            'dumpling',
            DumplingDriver.packet,
        )

    def test_packet_processing_with_broken_handler(self, mocker):
        """
        Test invocations of the packet handlers where one of them raises an
        exception, which should result in an exception-level log entry being
        created but the processing being otherwise unaffected.
        """
        kitchen = DumplingKitchen(dumpling_queue=mocker.Mock())
        mocker.patch.object(kitchen, '_send_dumpling')
        mocker.patch.object(kitchen, '_logger')

        # Set up two valid chefs. One of them returns a dumpling when given a
        # packet, and the raises an exception.
        mock_chef_with_packet_dumpling = mocker.Mock()
        mock_chef_with_no_packet_dumpling = mocker.Mock()

        mock_chef_with_packet_dumpling.packet_handler.return_value = 'dumpling'
        mock_chef_with_no_packet_dumpling.packet_handler.side_effect = KeyError

        kitchen._chefs = [
            mock_chef_with_packet_dumpling,
            mock_chef_with_no_packet_dumpling,
        ]

        # Add a spy on the logger so we can check it got called.
        mocker.spy(kitchen._logger, 'exception')

        packet = 'test_packet'
        kitchen._process_packet(packet)

        # Check that we only sent one packet dumpling, and that an
        # exception-level log was created.
        kitchen._send_dumpling.assert_called_once_with(
            mock_chef_with_packet_dumpling,
            'dumpling',
            DumplingDriver.packet,
        )
        kitchen._logger.exception.assert_called_once()

    def test_chef_poking(self, mocker):
        """
        Test interval-based chef poking.
        """
        test_interval = 3
        kitchen = DumplingKitchen(
            dumpling_queue=mocker.Mock(),
            chef_poke_interval=test_interval,
        )
        mocker.patch.object(kitchen, '_send_dumpling')

        # _poke_chefs() runs in an infinite loop which we need to break out of.
        # We do that by setting a side effect on the mocked call to sleep()
        # which will raise a RuntimeError. This doesn't interfere with being
        # able to determine the value passed to sleep().
        mock_sleep = mocker.patch(
            'netdumplings.dumplingkitchen.sleep', side_effect=RuntimeError
        )

        # Set up two valid chefs. One of them returns a dumpling when poked and
        # and the other one doesn't.
        mock_chef_with_interval_dumpling = mocker.Mock()
        mock_chef_with_no_interval_dumpling = mocker.Mock()

        dumpling_interval_handler = (
            mock_chef_with_interval_dumpling.interval_handler
        )
        no_dumpling_interval_handler = (
            mock_chef_with_no_interval_dumpling.interval_handler
        )

        dumpling_interval_handler.return_value = 'dumpling'
        no_dumpling_interval_handler.return_value = None

        kitchen._chefs = [
            mock_chef_with_interval_dumpling,
            mock_chef_with_no_interval_dumpling,
        ]

        # Run once through the poker infinite loop.
        with pytest.raises(RuntimeError):
            kitchen._poke_chefs(test_interval)

        # Check that we were asked to sleep by the test interval.
        mock_sleep.assert_called_once_with(test_interval)

        # Check that the two interval handlers were invoked, and that the one
        # that returned a dumpling resulted in that dumpling being sent.
        dumpling_interval_handler.assert_called_once_with(
            interval=test_interval
        )
        no_dumpling_interval_handler.assert_called_once_with(
            interval=test_interval
        )

        kitchen._send_dumpling.assert_called_once_with(
            mock_chef_with_interval_dumpling,
            'dumpling',
            DumplingDriver.interval,
        )

    def test_chef_poking_with_broken_handler(self, mocker):
        """
        Test interval-based chef poking where one of the handlers raises an
        exception, which should result in an exception-level log entry being
        created but the processing being otherwise unaffected.
        """
        test_interval = 3
        kitchen = DumplingKitchen(
            dumpling_queue=mocker.Mock(),
            chef_poke_interval=test_interval,
        )
        mocker.patch.object(kitchen, '_send_dumpling')
        mocker.patch.object(kitchen, '_logger')

        mocker.patch(
            'netdumplings.dumplingkitchen.sleep', side_effect=RuntimeError
        )

        # Set up one valid chefs which returns an interval dumpling, and one
        # chef which raises an exception in its interval handler.
        # and the other one doesn't.
        mock_chef_with_interval_dumpling = mocker.Mock()
        mock_chef_with_interval_error = mocker.Mock()

        dumpling_interval_handler = (
            mock_chef_with_interval_dumpling.interval_handler
        )
        error_interval_handler = (
            mock_chef_with_interval_error.interval_handler
        )

        dumpling_interval_handler.return_value = 'dumpling'
        error_interval_handler.side_effect = KeyError

        kitchen._chefs = [
            mock_chef_with_interval_dumpling,
            mock_chef_with_interval_error,
        ]

        # Run once through the poker infinite loop.
        with pytest.raises(RuntimeError):
            kitchen._poke_chefs(test_interval)

        # Check that the valid dumpling was sent, and that we logged an
        # exception for the other chef.
        kitchen._send_dumpling.assert_called_once_with(
            mock_chef_with_interval_dumpling,
            'dumpling',
            DumplingDriver.interval,
        )
        kitchen._logger.exception.assert_called_once()


class TestDumplingSends:
    """
    Test the sending of dumplings.
    """
    def test_dumpling_send(self, mocker, test_dumpling_dns):
        """
        Test the _send_dumpling method to ensure that it creates a new Dumpling
        and puts the resulting dumpling contents onto the queue.
        """
        test_payload_json = json.dumps(test_dumpling_dns)

        mock_dumpling_class = mocker.patch(
            'netdumplings.dumplingkitchen.Dumpling'
        )

        mock_dumpling_class.return_value.to_json.return_value = (
            test_payload_json
        )

        mock_chef = mocker.Mock()
        mock_queue = mocker.Mock()

        kitchen = DumplingKitchen(dumpling_queue=mock_queue)

        kitchen._send_dumpling(
            chef=mock_chef,
            payload=test_dumpling_dns['payload'],
            driver=DumplingDriver.packet,
        )

        mock_dumpling_class.assert_called_once_with(
            chef=mock_chef,
            payload=test_dumpling_dns['payload'],
            driver=DumplingDriver.packet,
        )

        mock_queue.put.assert_called_once_with(test_payload_json)


class TestChefDiscovery:
    """
    Test DumplingKitchen chef discovery.
    """
    def test_chef_discovery(self, mocker):
        """
        Test discovery of chefs from the two valid test chef modules.
        """
        kitchen = DumplingKitchen(dumpling_queue=mocker.Mock())

        # WARNING: This will actually allow the imports to take place, so we're
        # technically letting this test pollute our namespace.
        spy_importlib = mocker.spy(importlib, 'import_module')

        chef_info = kitchen.get_chefs_in_modules([
            'tests.data.dumplingchefs',
            'tests.data.moredumplingchefs',
        ])

        # Assert that the two chef modules were actually imported.
        assert spy_importlib.call_count == 2

        assert spy_importlib.call_args_list == [
            (('tests.data.dumplingchefs',),),
            (('tests.data.moredumplingchefs',),),
        ]

        # Assert that the return value of get_chefs_in_modules looks correct.
        assert 'tests.data.dumplingchefs' in chef_info
        assert 'tests.data.moredumplingchefs' in chef_info
        assert len(chef_info.keys()) == 2

        chef_module_one = chef_info['tests.data.dumplingchefs']

        assert chef_module_one['import_error'] is False
        assert sorted(chef_module_one['chef_classes']) == sorted([
            'TestChefOne', 'TestChefTwo', 'TestChefThree'
        ])

        chef_module_two = chef_info['tests.data.moredumplingchefs']

        assert chef_module_two['import_error'] is False
        assert 'NotAChef' not in chef_module_two['chef_classes']
        assert sorted(chef_module_two['chef_classes']) == sorted([
            'MoreTestChefOne', 'MoreTestChefTwo'
        ])

    def test_chef_discovery_with_invalid_module(self, mocker):
        """
        Test that attempting to discover chefs from an invalid module
        successfully results in an error for that module, while chefs from a
        valid module are still properly imported.
        """
        kitchen = DumplingKitchen(dumpling_queue=mocker.Mock())

        chef_info = kitchen.get_chefs_in_modules([
            'tests.data.dumplingchefs',
            'tests.data.doesnotexist',
        ])

        # We expect to get two results back, but one of them will be an error.
        assert len(chef_info.keys()) == 2

        valid_module = chef_info['tests.data.dumplingchefs']
        assert valid_module['import_error'] is False

        invalid_module = chef_info['tests.data.doesnotexist']
        assert (
            invalid_module['import_error'] ==
            "No module named 'tests.data.doesnotexist'"
        )
        assert len(invalid_module['chef_classes']) == 0


class TestKitchenRun:
    """
    Test DumplingKitchen run() calls.
    """
    def test_poke_thread_started(self, mocker):
        """
        Test that an attempt is made to start the poke thread when poking is
        enabled.
        """
        kitchen = DumplingKitchen(
            dumpling_queue=mocker.Mock(),
            chef_poke_interval=5,
        )

        mock_thread = mocker.patch('netdumplings.dumplingkitchen.Thread')
        mocker.patch('netdumplings.dumplingkitchen.sniff')

        kitchen.run()
        mock_thread.assert_called_once_with(
            target=kitchen._poke_chefs,
            kwargs={'interval': 5},
        )

    def test_poke_thread_not_started(self, mocker):
        """
        Test that the poke thread is not started when the kitchen is not
        poking.
        """
        kitchen = DumplingKitchen(
            dumpling_queue=mocker.Mock(),
            chef_poke_interval=None,
        )

        mock_thread = mocker.patch('netdumplings.dumplingkitchen.Thread')
        mocker.patch('netdumplings.dumplingkitchen.sniff')

        kitchen.run()
        mock_thread.assert_not_called()

    def test_sniffer_started_with_specified_interface(self, mocker):
        """
        Test that the sniffer was started with the specified interface.
        """
        kitchen = DumplingKitchen(
            dumpling_queue=mocker.Mock(),
            interface='en0',
        )

        mocker.patch('netdumplings.dumplingkitchen.Thread')
        mock_sniffer = mocker.patch('netdumplings.dumplingkitchen.sniff')

        kitchen.run()
        mock_sniffer.assert_called_once_with(
            iface='en0',
            filter='tcp',
            prn=kitchen._process_packet,
            store=0,
        )

    def test_sniffer_started_with_all_interface(self, mocker):
        """
        Test that the sniffer was started with no specified interface when the
        'all' interface is requested. Not passing an interface to the sniffer
        results in all interfaces being sniffed.
        """
        kitchen = DumplingKitchen(
            dumpling_queue=mocker.Mock(),
            interface='all',
        )

        mocker.patch('netdumplings.dumplingkitchen.Thread')
        mock_sniffer = mocker.patch('netdumplings.dumplingkitchen.sniff')

        kitchen.run()
        mock_sniffer.assert_called_once_with(
            filter='tcp',
            prn=kitchen._process_packet,
            store=0,
        )
