import importlib

import pytest

from netdumplings import DumplingKitchen


class TestDumplingKitchen:
    def test_init_default(self):
        """
        Test default DumplingKitchen initialization.
        """
        kitchen = DumplingKitchen()

        assert kitchen.name == 'default'
        assert kitchen.interface == 'all'
        assert kitchen.filter == 'tcp'
        assert kitchen.chef_poke_interval == 5

        assert len(kitchen._packet_handlers) == 0
        assert len(kitchen._interval_handlers) == 0

    def test_init_with_overrides(self):
        """
        Test DumplingKitchen initialization with overrides.
        """
        kitchen = DumplingKitchen(
            name='test_kitchen',
            interface='en0',
            sniffer_filter='test filter',
            chef_poke_interval=10,
        )

        assert kitchen.name == 'test_kitchen'
        assert kitchen.interface == 'en0'
        assert kitchen.filter == 'test filter'
        assert kitchen.chef_poke_interval == 10

        assert len(kitchen._packet_handlers) == 0
        assert len(kitchen._interval_handlers) == 0

    def test_handler_registration(self):
        """
        Test registration of packet and interval handlers.
        """
        kitchen = DumplingKitchen()

        assert len(kitchen._packet_handlers) == 0
        assert len(kitchen._interval_handlers) == 0

        # For these tests we don't care that we're not registering callables.

        kitchen.register_handler(
            chef_name='TestChefOne',
            packet_handler='TestPacketHandlerOne',
        )

        assert kitchen._packet_handlers == ['TestPacketHandlerOne']
        assert len(kitchen._interval_handlers) == 0

        kitchen.register_handler(
            chef_name='TestChefTwo',
            packet_handler='TestPacketHandlerTwo',
            interval_handler='TestIntervalHandlerOne',
        )

        assert kitchen._packet_handlers == [
            'TestPacketHandlerOne', 'TestPacketHandlerTwo'
        ]
        assert kitchen._interval_handlers == ['TestIntervalHandlerOne']


class TestHandlerInvocations:
    """
    Test invocations of the packet and interval handlers.
    """
    def test_packet_handling(self, mocker):
        """
        Test invocations of the packet handlers.
        """
        kitchen = DumplingKitchen()

        # Set up two valid mock packet handlers (pretending to be chef packet
        # handlers).
        mock_handler_1 = mocker.Mock()
        mock_handler_2 = mocker.Mock()
        kitchen._packet_handlers = [mock_handler_1, mock_handler_2]

        packet = 'test_packet'

        kitchen._process_packet(packet)

        # Now check that that the two mock packet handlers got called as
        # expected.
        mock_handler_1.assert_called_once_with(packet)
        mock_handler_2.assert_called_once_with(packet)

    def test_packet_handling_with_broken_handler(self, mocker):
        """
        Test invocations of the packet handlers where one of them raises an
        exception, which should result in an exception-level log entry being
        created but the processing being otherwise unaffected.
        """
        kitchen = DumplingKitchen()

        # Set up a valid packet handler, and a paxket handler which raises an
        # exception. The exception should only result in a log entry being
        # made.
        mock_handler_1 = mocker.Mock()
        mock_handler_2 = mocker.Mock(side_effect=KeyError)
        kitchen._packet_handlers = [mock_handler_1, mock_handler_2]

        # Add a spy on the logger so we can check it got called.
        mocker.spy(kitchen._logger, 'exception')

        packet = 'test_packet'

        kitchen._process_packet(packet)

        # Check that the two handlers got called, and that an exception-level
        # log was created.
        mock_handler_1.assert_called_once_with(packet)
        mock_handler_2.assert_called_once_with(packet)
        kitchen._logger.exception.assert_called_once()

    def test_chef_poking(self, mocker):
        """
        Test interval-based chef poking.
        """
        test_interval = 3
        kitchen = DumplingKitchen(chef_poke_interval=test_interval)

        # _poke_chefs() runs in an infinite loop which we need to break out of.
        # We do that by setting a side effect on the mocked call to sleep()
        # which will raise an Exception. This doesn't interfere with being able
        # to determine the value passed to sleep().
        mock_sleep = mocker.patch(
            'netdumplings.dumplingkitchen.sleep', side_effect=Exception
        )

        # Set up two valid mock interval handlers (pretending to be chef
        # interval handlers).
        mock_handler_1 = mocker.Mock()
        mock_handler_2 = mocker.Mock()
        kitchen._interval_handlers = [mock_handler_1, mock_handler_2]

        # Run the function under test. We've configured it to throw an
        # exception the first time it attempts to sleep.
        with pytest.raises(Exception):
            kitchen._poke_chefs(test_interval)

        # Now check that that the two mock interval handlers got called as
        # expected, and that the mock sleep also got called as expected.
        mock_sleep.assert_called_once_with(test_interval)

        mock_handler_1.assert_called_once_with(interval=test_interval)
        mock_handler_2.assert_called_once_with(interval=test_interval)

    def test_chef_poking_with_broken_handler(self, mocker):
        """
        Test interval-based chef poking where one of the handlers raises an
        exception, which should result in an exception-level log entry being
        created but the processing being otherwise unaffected.
        """
        test_interval = 3
        kitchen = DumplingKitchen(chef_poke_interval=test_interval)
        mocker.patch(
            'netdumplings.dumplingkitchen.sleep', side_effect=Exception
        )

        # Set up a valid interval handler, and an interval handler which raises
        # an exception. The exception should only result in a log entry being
        # made.
        mock_handler_1 = mocker.Mock()
        mock_handler_2 = mocker.Mock(side_effect=KeyError)
        kitchen._interval_handlers = [mock_handler_1, mock_handler_2]

        # Add a spy on the logger so we can check it got called.
        mocker.spy(kitchen._logger, 'exception')

        with pytest.raises(Exception):
            kitchen._poke_chefs(test_interval)

        # Check that the two handlers got called, and that an exception-level
        # log was created.
        mock_handler_1.assert_called_once_with(interval=test_interval)
        mock_handler_2.assert_called_once_with(interval=test_interval)
        kitchen._logger.exception.assert_called_once()


class TestChefDiscovery:
    def test_chef_discovery(self, mocker):
        """
        Test discovery of chefs from the two valid test chef modules.
        """
        kitchen = DumplingKitchen()

        # This will actually allow the imports to take place, so we're
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

    def test_chef_discovery_with_invalid_nodule(self):
        """
        Test that attempting to discover chefs from an invalid module
        successfully results in an error for that module, while chefs from a
        valid module are still properly imported.
        """
        kitchen = DumplingKitchen()

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
    def test_poke_thread_started(self, mocker):
        """
        Test that an attempt is made to start the poke thread when poking is
        enabled.
        """
        kitchen = DumplingKitchen(chef_poke_interval=5)

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
        kitchen = DumplingKitchen(chef_poke_interval=None)

        mock_thread = mocker.patch('netdumplings.dumplingkitchen.Thread')
        mocker.patch('netdumplings.dumplingkitchen.sniff')

        kitchen.run()
        mock_thread.assert_not_called()

    def test_sniffer_started_with_specified_interface(self, mocker):
        """
        Test that the sniffer was started with the specified interface.
        """
        kitchen = DumplingKitchen(interface='en0')

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
        kitchen = DumplingKitchen(interface='all')

        mocker.patch('netdumplings.dumplingkitchen.Thread')
        mock_sniffer = mocker.patch('netdumplings.dumplingkitchen.sniff')

        kitchen.run()
        mock_sniffer.assert_called_once_with(
            filter='tcp',
            prn=kitchen._process_packet,
            store=0,
        )
