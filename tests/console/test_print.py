import click.testing

from netdumplings.console.print import print_cli


class TestPrint:
    """
    Test the nd-print commandline tool.
    """
    def test_print(self, mocker):
        """
        Test that the PrinterEater is instantiated as expected.
        """
        mock_eater_instance = mocker.Mock()
        mock_printereater = mocker.patch(
            'netdumplings.console.print.PrinterEater',
            return_value=mock_eater_instance,
        )

        kitchens = ('TestKitchen1', 'TestKitchen2')
        interval_dumplings = False
        packet_dumplings = True
        contents = True
        color = True
        eater_name = 'test_printer'
        hub = 'test_hub'
        chefs = ('TestChef1', 'TestChef2')

        runner = click.testing.CliRunner()
        runner.invoke(
            print_cli,
            [
                '--kitchen', 'TestKitchen1',
                '--kitchen', 'TestKitchen2',
                '--no-interval-dumplings',
                '--packet-dumplings',
                '--contents',
                '--color',
                '--eater-name', 'test_printer',
                '--hub', 'test_hub',
                '--chef', 'TestChef1',
                '--chef', 'TestChef2',
            ],
        )

        mock_printereater.assert_called_once_with(
            kitchens=kitchens,
            interval_dumplings=interval_dumplings,
            packet_dumplings=packet_dumplings,
            contents=contents,
            color=color,
            name=eater_name,
            hub=hub,
            chefs=chefs,
        )

        mock_eater_instance.run.assert_called_once_with()
