import click

import netdumplings
from netdumplings._shared import HUB_HOST, HUB_OUT_PORT

from ._shared import CLICK_CONTEXT_SETTINGS, printable_dumpling


PRINT_COLOR = False


async def on_connect(hub_uri, websocket):
    """
    Called when the connection to ``nd-hub`` has been created.

    :param hub_uri: The ``nd-hub`` websocket URI.
    :param websocket: The websocket object used for talking to nd-hub
        (websockets.WebSocketClientProtocol).
    """
    print('Connected to nd-hub at {0}'.format(hub_uri))
    print('Waiting for a SystemStatus dumpling...')


async def on_dumpling(dumpling):
    """
    Called when a new dumpling is received from ``nd-hub``. Prints dumpling
    payload.

    :param dumpling: The received dumpling.
    """
    print('\n{}\n'.format(
        printable_dumpling(dumpling.payload, colorize=PRINT_COLOR)
    ))


async def on_connection_lost(e):
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
    '--eater-name', '-n',
    help='Dumpling eater name for this tool when connecting to nd-hub.',
    metavar='EATER_NAME',
    default='detailseater',
    show_default=True,
)
@click.option(
    '--color / --no-color',
    help='Print color output.',
    default=True,
    show_default=True,
)
@click.version_option(version=netdumplings.__version__)
def hubdetails_cli(hub, eater_name, color):
    """
    A dumpling eater.

    Connects to nd-hub (the dumpling hub) and waits for a single SystemStatus
    dumpling which it displays the full contents of and then exits.
    """
    global PRINT_COLOR
    PRINT_COLOR = color

    eater = netdumplings.DumplingEater(
        name=eater_name,
        hub=hub,
        chef_filter=['SystemStatusChef'],
        on_connect=on_connect,
        on_dumpling=on_dumpling,
        on_connection_lost=on_connection_lost,
    )

    eater.run(dumpling_count=1)


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    hubdetails_cli()
