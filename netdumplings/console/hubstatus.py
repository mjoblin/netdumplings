import datetime

import click
import termcolor

import netdumplings
from netdumplings._shared import HUB_HOST, HUB_OUT_PORT

from ._shared import CLICK_CONTEXT_SETTINGS


PRINT_COLOR = False


async def on_connect(hub_uri, websocket):
    """
    Called when the connection to ``nd-hub`` has been created.

    :param hub_uri: The ``nd-hub`` websocket URI.
    :param websocket: The websocket object used for talking to ``nd-hub``
        (websockets.WebSocketClientProtocol).
    """
    print('nd-hub status from {0}'.format(hub_uri))
    print('Waiting for data... ', end='', flush=True)


async def on_dumpling(dumpling):
    """
    Called when a new dumpling is received from ``nd-hub``. Prints summary
    information about the current state of ``nd-hub``.

    :param dumpling: The received dumpling.
    """
    payload = dumpling.payload

    up_mins, up_secs = divmod(int(payload['server_uptime']), 60)
    up_hrs, up_mins = divmod(up_mins, 60)
    up_str = '{0:02d}:{1:02d}:{2:02d}'.format(up_hrs, up_mins, up_secs)

    up_str = (
        termcolor.colored(up_str, attrs=['bold']) if PRINT_COLOR else up_str
    )

    dumplings_in = (
        termcolor.colored(payload['total_dumplings_in'], attrs=['bold'])
        if PRINT_COLOR else payload['total_dumplings_in']
    )

    dumplings_out = (
        termcolor.colored(payload['total_dumplings_out'], attrs=['bold'])
        if PRINT_COLOR else payload['total_dumplings_out']
    )

    kitchens = (
        termcolor.colored(payload['dumpling_kitchen_count'], attrs=['bold'])
        if PRINT_COLOR else payload['dumpling_kitchen_count']
    )

    eaters = (
        termcolor.colored(payload['dumpling_eater_count'], attrs=['bold'])
        if PRINT_COLOR else payload['dumpling_eater_count']
    )

    status_msg = (
        '\r{now}  uptime: {uptime}  dumplings in: {dumplings_in}  '
        'out: {dumplings_out}  kitchens: {kitchens}  eaters: {eaters} '.format(
            now=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            dumplings_in=dumplings_in,
            dumplings_out=dumplings_out,
            uptime=up_str,
            kitchens=kitchens,
            eaters=eaters,
        )
    )

    print(status_msg, end='', flush=True)


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
    default='statuseater',
    show_default=True,
)
@click.option(
    '--color / --no-color',
    help='Print color output.',
    default=True,
    show_default=True,
)
@click.version_option(version=netdumplings.__version__)
def hubstatus_cli(hub, eater_name, color):
    """
    A dumpling eater.

    Connects to nd-hub (the dumpling hub) and continually prints summary status
    information from any SystemStatusChef dumplings. This is a system
    monitoring dumpling eater which can be used to keep an eye on nd-hub.
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

    eater.run()


if __name__ == '__main__':
    hubstatus_cli()
