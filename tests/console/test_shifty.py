import click.testing

from netdumplings.console.shifty import shifty
from netdumplings.exceptions import NetDumplingsError


class TestShifty:
    """
    Test the nd-shifty commandline tool.
    """
    def test_shifty(self, mocker):
        """
        Test that the DumplingHub is instantiated as expected and that run()
        is called.
        """
        mock_hub = mocker.patch('netdumplings.DumplingHub')

        runner = click.testing.CliRunner()
        result = runner.invoke(
            shifty,
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

    def test_shifty_with_error(self, mocker):
        """
        Test that a NetDumplingsError in DumplingHub.run() results in shifty
        exiting with status code 1.
        """
        mock_hub = mocker.patch('netdumplings.DumplingHub')
        mock_hub.return_value.run.side_effect = NetDumplingsError

        runner = click.testing.CliRunner()
        result = runner.invoke(shifty)

        assert result.exit_code == 1
