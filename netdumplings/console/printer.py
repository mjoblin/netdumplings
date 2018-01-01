import datetime

import click
import termcolor

import netdumplings
from netdumplings.console.shared import CLICK_CONTEXT_SETTINGS
from netdumplings.shared import DEFAULT_SHIFTY_HOST, DEFAULT_SHIFTY_OUT_PORT

from netdumplings.console.shared import printable_dumpling


class PrinterEater(netdumplings.DumplingEater):
    """
    A dumpling eater which displays dumpling information to the terminal as it
    arrives from nd-shifty.
    """
    def __init__(
            self,
            kitchens=None,
            interval_dumplings=True,
            packet_dumplings=True,
            contents=True,
            color=True,
            **kwargs
    ):
        super().__init__(**kwargs)

        self._kitchens = kitchens
        self._interval_dumplings = interval_dumplings
        self._packet_dumplings = packet_dumplings
        self._contents = contents
        self._color = color

    async def on_connect(self, shifty_uri, websocket):
        """
        Called when the connection to nd-shifty has been created.

        :param shifty_uri: The nd-shifty websocket URI.
        :param websocket: The websocket object used for talking to nd-shifty
            (websockets.WebSocketClientProtocol).
        """
        print('Connected to nd-shifty at {0}'.format(shifty_uri))
        print('Waiting for dumplings...\n')

    async def on_dumpling(self, dumpling):
        """
        Called when a new dumpling is received from nd-shifty. Prints the
        dumpling summary and contents.

        :param dumpling: The freshly-made new dumpling.
        """
        kitchen = dumpling['metadata']['kitchen']
        dumpling_driver = dumpling['metadata']['driver']

        should_print_dumpling = (
            (dumpling_driver == 'interval' and self._interval_dumplings) or
            (dumpling_driver == 'packet' and self._packet_dumplings)
        ) and (
            self._kitchens is None or kitchen in self._kitchens
        )

        if not should_print_dumpling:
            return

        dumpling_creation_time = (
            datetime.datetime.fromtimestamp(
                int(dumpling['metadata']['creation_time'])
            ).isoformat()
        )

        dumpling_chef = (
            termcolor.colored(dumpling['metadata']['chef'], attrs=['bold'])
            if self._color else dumpling['metadata']['chef']
        )

        dumpling_kitchen = (
            termcolor.colored(dumpling['metadata']['kitchen'], attrs=['bold'])
            if self._color else dumpling['metadata']['kitchen']
        )

        summary = '{} [{:8s}] {} from {}'.format(
            dumpling_creation_time,
            dumpling_driver,
            dumpling_chef,
            dumpling_kitchen,
        )

        print(summary)

        if self._contents:
            print('\n{}\n'.format(printable_dumpling(dumpling)))

    async def on_connection_lost(self, e):
        """
        Called when the nd-shifty connection is lost.

        :param e: The exception thrown during the connection close.
        """
        print('\nLost connection to nd-shifty: {}'.format(e))


# -----------------------------------------------------------------------------

@click.command(
    context_settings=CLICK_CONTEXT_SETTINGS,
)
@click.option(
    '--shifty', '-h',
    help='Address where nd-shifty is sending dumplings from.',
    metavar='HOST:PORT',
    default='{}:{}'.format(DEFAULT_SHIFTY_HOST, DEFAULT_SHIFTY_OUT_PORT),
    show_default=True,
)
@click.option(
    '--chef', '-c',
    help='Restrict dumplings to those made by this chef. Multiple can be '
         'specified. Displays all chefs by default.',
    metavar='CHEF_NAME',
    multiple=True,
)
@click.option(
    '--kitchen', '-k',
    help='Restrict dumplings to those emitted by this kitchen. Multiple can '
         'be specified. Displays all kitchens by default.',
    metavar='KITCHEN_NAME',
    multiple=True,
)
@click.option(
    '--eater-name', '-n',
    help='Dumpling eater name for this tool when connecting to nd-shifty.',
    default='printereater',
    metavar='EATER_NAME',
    show_default=True,
)
@click.option(
    '--interval-dumplings / --no-interval-dumplings',
    help='Print interval dumplings.',
    default=True,
    show_default=True,
)
@click.option(
    '--packet-dumplings / --no-packet-dumplings',
    help='Print packet dumplings.',
    default=True,
    show_default=True,
)
@click.option(
    '--contents / --no-contents',
    help='Print dumpling contents.',
    default=True,
    show_default=True,
)
@click.option(
    '--color / --no-color',
    help='Print color output.',
    default=True,
    show_default=True,
)
@click.version_option(version=netdumplings.__version__)
def printer(shifty, chef, kitchen, eater_name, interval_dumplings,
            packet_dumplings, contents, color):
    """
    A dumpling eater.

    Connects to nd-shifty (the dumpling hub) and prints the contents of the
    dumplings made by the given chefs.
    """
    eater = PrinterEater(
        kitchens=kitchen if kitchen else None,
        interval_dumplings=interval_dumplings,
        packet_dumplings=packet_dumplings,
        contents=contents,
        color=color,
        name=eater_name,
        shifty=shifty,
        chefs=chef if chef else None,
    )

    eater.run()


if __name__ == '__main__':
    printer()
