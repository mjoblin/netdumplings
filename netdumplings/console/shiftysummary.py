import datetime

import click
import termcolor

import netdumplings
from netdumplings._shared import DEFAULT_SHIFTY_HOST, DEFAULT_SHIFTY_OUT_PORT

from ._shared import CLICK_CONTEXT_SETTINGS


PRINT_COLOR = False


async def on_connect(shifty_uri, websocket):
    """
    Called when the connection to nd-shifty has been created.

    :param shifty_uri: The nd-shifty websocket URI.
    :param websocket: The websocket object used for talking to nd-shifty
        (websockets.WebSocketClientProtocol).
    :return: None
    """
    print('Shifty status from {0}'.format(shifty_uri))
    print('Waiting for data... ', end='', flush=True)


async def on_dumpling(dumpling):
    """
    Called when a new dumpling is received from nd-shifty.  Prints information
    about the current state of nd-shifty.

    :param dumpling: The freshly-made new dumpling.
    :return: None
    """
    payload = dumpling['payload']

    up_mins, up_secs = divmod(int(payload['server_uptime']), 60)
    up_hrs, up_mins = divmod(up_mins, 60)
    up_str = '{0:02d}:{1:02d}:{2:02d}'.format(up_hrs, up_mins, up_secs)

    up_str = (
        termcolor.colored(up_str, attrs=['bold']) if PRINT_COLOR else up_str
    )

    dumplings = (
        termcolor.colored(payload['total_dumplings_sent'], attrs=['bold'])
        if PRINT_COLOR else payload['total_dumplings_sent']
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
        '\r{now}  uptime: {uptime}  dumplings: {dumplings}  '
        'kitchens: {kitchens}  eaters: {eaters} '.format(
            now=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            dumplings=dumplings,
            uptime=up_str,
            kitchens=kitchens,
            eaters=eaters,
        )
    )

    print(status_msg, end='', flush=True)


async def on_connection_lost(e):
    """
    Called when nd-shifty connection is lost.

    :param e: The exception thrown during the connection close.
    :return: None
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
    '--eater-name', '-n',
    help='Dumpling eater name for this tool when connecting to nd-shifty.',
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
def shiftysummary_cli(shifty, eater_name, color):
    """
    A dumpling eater.

    Connects to nd-shifty (the dumpling hub) and prints information from any
    SystemStatusChef dumplings. This is a system-monitoring dumpling eater
    which can be used to keep an eye on nd-shifty.
    """
    global PRINT_COLOR
    PRINT_COLOR = color

    eater = netdumplings.DumplingEater(
        name=eater_name,
        shifty=shifty,
        chefs=['SystemStatusChef'],
        on_connect=on_connect,
        on_dumpling=on_dumpling,
        on_connection_lost=on_connection_lost,
    )

    eater.run()


if __name__ == '__main__':
    shiftysummary_cli()
