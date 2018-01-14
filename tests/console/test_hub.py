import click.testing

from netdumplings.console.hub import hub_cli
from netdumplings.exceptions import NetDumplingsError


class TestHub:
    """
    Test the nd-hub commandline tool.
    """
    def test_hub(self, mocker):
        """
        Test that the DumplingHub is instantiated as expected and that run()
        is called.
        """
        mock_hub = mocker.patch('netdumplings.DumplingHub')

        runner = click.testing.CliRunner()
        result = runner.invoke(
            hub_cli,
            [
                '--address', 'testhost',
                '--in-port', 1001,
                '--out-port', 1002,
                '--status-freq', 99,
            ],
        )

        mock_hub.assert_called_once_with(
            address='testhost',
            in_port=1001,
            out_port=1002,
            status_freq=99,
        )

        mock_hub.return_value.run.assert_called_once()
        assert result.exit_code == 0

    def test_hub_with_error(self, mocker):
        """
        Test that a NetDumplingsError in DumplingHub.run() results in the hub
        exiting with status code 1.
        """
        mock_hub = mocker.patch('netdumplings.DumplingHub')
        mock_hub.return_value.run.side_effect = NetDumplingsError

        runner = click.testing.CliRunner()
        result = runner.invoke(hub_cli)

        assert result.exit_code == 1
