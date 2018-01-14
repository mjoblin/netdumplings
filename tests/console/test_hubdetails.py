import click.testing

import netdumplings.console.hubdetails as hubdetails


class TestHubDetails:
    """
    Test the nd-hubdetails commandline tool.
    """
    def test_hubdetails(self, mocker):
        """
        Test that the DumplingEater is instantiated as expected.
        """
        mock_details_eater = mocker.Mock()
        mock_dumplingeater = mocker.patch(
            'netdumplings.DumplingEater',
            return_value=mock_details_eater,
        )

        eater_name = 'test_eater'
        hub = 'test_hub'

        runner = click.testing.CliRunner()
        runner.invoke(
            hubdetails.hubdetails_cli,
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
            on_connect=hubdetails.on_connect,
            on_dumpling=hubdetails.on_dumpling,
            on_connection_lost=hubdetails.on_connection_lost,
        )

        assert hubdetails.PRINT_COLOR is False
        mock_details_eater.run.assert_called_once_with(dumpling_count=1)
