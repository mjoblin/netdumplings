import click.testing

import netdumplings.console.hubstatus as hubstatus


class TestHubStatus:
    """
    Test the nd-hubstatus commandline tool.
    """
    def test_hubstatus(self, mocker):
        """
        Test that the DumplingEater is instantiated as expected.
        """
        mock_status_eater = mocker.Mock()
        mock_dumplingeater = mocker.patch(
            'netdumplings.DumplingEater',
            return_value=mock_status_eater,
        )

        eater_name = 'test_eater'
        hub = 'test_hub'

        runner = click.testing.CliRunner()
        runner.invoke(
            hubstatus.hubstatus_cli,
            [
                '--eater-name', eater_name,
                '--hub', hub,
                '--no-color',
            ],
        )

        mock_dumplingeater.assert_called_once_with(
            name=eater_name,
            hub=hub,
            chef_filter=['SystemStatusChef'],
            on_connect=hubstatus.on_connect,
            on_dumpling=hubstatus.on_dumpling,
            on_connection_lost=hubstatus.on_connection_lost,
        )

        assert hubstatus.PRINT_COLOR is False
        mock_status_eater.run.assert_called_once_with()
