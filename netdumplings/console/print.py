import datetime

import click
import termcolor

import netdumplings
from netdumplings import DumplingDriver, DumplingEater
from netdumplings._shared import HUB_HOST, HUB_OUT_PORT

from ._shared import CLICK_CONTEXT_SETTINGS, printable_dumpling


class PrinterEater(DumplingEater):
    """
    A dumpling eater which displays dumpling information to the terminal as it
    arrives from ``nd-hub``.
    """
    def __init__(
            self,
            kitchens=None,
            interval_dumplings=True,
            packet_dumplings=True,
            payload=True,
            color=True,
            **kwargs):

        super().__init__(**kwargs)

        self._kitchens = kitchens
        self._interval_dumplings = interval_dumplings
        self._packet_dumplings = packet_dumplings
        self._payload = payload
        self._color = color

    async def on_connect(self, hub_uri, websocket):
        """
        Called when the connection to ``nd-hub`` has been created.

        :param hub_uri: The ``nd-hub`` websocket URI.
        :param websocket: The websocket object used for talking to nd-hub
            (websockets.WebSocketClientProtocol).
        """
        print('Connected to nd-hub at {0}'.format(hub_uri))
        print('Waiting for dumplings...\n')

    async def on_dumpling(self, dumpling):
        """
        Called when a new dumpling is received from ``nd-hub``. Prints the
        dumpling summary and payload.

        :param dumpling: The received dumpling.
        """
        driver = dumpling.driver

        should_print_dumpling = (
            (driver == DumplingDriver.interval and self._interval_dumplings) or
            (driver == DumplingDriver.packet and self._packet_dumplings)
        ) and (
            self._kitchens is None or dumpling.kitchen in self._kitchens
        )

        if not should_print_dumpling:
            return

        dumpling_creation_time = (
            datetime.datetime.fromtimestamp(dumpling.creation_time).isoformat()
        )

        dumpling_chef = (
            termcolor.colored(dumpling.chef_name, attrs=['bold'])
            if self._color else dumpling.chef_name
        )

        dumpling_kitchen = (
            termcolor.colored(dumpling.kitchen, attrs=['bold'])
            if self._color else dumpling.kitchen
        )

        summary = '{} [{:8s}] {} from {}'.format(
            dumpling_creation_time,
            'packet' if driver == DumplingDriver.packet else 'interval',
            dumpling_chef,
            dumpling_kitchen,
        )

        print(summary)

        if self._payload:
            print('\n{}\n'.format(
                printable_dumpling(dumpling.payload, colorize=self._color)
            ))

    async def on_connection_lost(self, e):
        """
        Called when the ``nd-hub`` connection is lost.

        :param e: The exception thrown during the connection close.
        """
        print('\nLost connection to nd-hub: {}'.format(e))


# -----------------------------------------------------------------------------

@click.command(
    context_settings=CLICK_CONTEXT_SETTINGS,
)
@click.option(
    '--hub', '-h',
    help='Address where nd-hub is sending dumplings from.',
    metavar='HOST:PORT',
    default='{}:{}'.format(HUB_HOST, HUB_OUT_PORT),
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
    help='Dumpling eater name for this tool when connecting to nd-hub.',
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
    '--payload / --no-payload',
    help='Print dumpling payload.',
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
def print_cli(hub, chef, kitchen, eater_name, interval_dumplings,
              packet_dumplings, payload, color):
    """
    A dumpling eater.

    Connects to nd-hub (the dumpling hub) and prints information on all
    received dumplings.
    """
    eater = PrinterEater(
        kitchens=kitchen if kitchen else None,
        interval_dumplings=interval_dumplings,
        packet_dumplings=packet_dumplings,
        payload=payload,
        color=color,
        name=eater_name,
        hub=hub,
        chef_filter=chef if chef else None,
    )

    eater.run()


if __name__ == '__main__':
    print_cli()
