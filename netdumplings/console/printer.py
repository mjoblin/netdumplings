import json

import click

import netdumplings
from netdumplings.console.shared import CLICK_CONTEXT_SETTINGS
from netdumplings.shared import DEFAULT_SHIFTY_HOST, DEFAULT_SHIFTY_OUT_PORT


async def on_connect(shifty_uri, websocket):
    """
    Called when the connection to nd-shifty has been created.

    :param shifty_uri: The nd-shifty websocket URI.
    :param websocket: The websocket object used for talking to nd-shifty
        (websockets.WebSocketClientProtocol).
    :return: None
    """
    print('Connected to nd-shifty at {0}'.format(shifty_uri))
    print('Waiting for dumplings...\n')


async def on_dumpling(dumpling):
    """
    Called when a new dumpling is received from nd-shifty. Prints the dumpling
    contents.

    :param dumpling: The freshly-made new dumpling.
    :return: None
    """
    print('{} {} dumpling:\n'.format(
        dumpling['metadata']['chef'], dumpling['metadata']['driver'])
    )
    print(
        json.dumps(dumpling, sort_keys=True, indent=4, separators=(',', ': '))
    )
    print()


async def on_connection_lost(e):
    """
    Called when the nd-shifty connection is lost.

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
    default='{}:{}'.format(DEFAULT_SHIFTY_HOST, DEFAULT_SHIFTY_OUT_PORT),
    show_default=True,
)
@click.option(
    '--chef', '-c',
    help='Restrict dumplings to those made by this chef.',
    multiple=True,
)
@click.option(
    '--eater-name', '-n',
    help='Dumpling eater name for this tool when connecting to nd-shifty.',
    default='printereater',
    show_default=True,
)
@click.version_option(version=netdumplings.__version__)
def printer(shifty, chef, eater_name):
    """
    A dumpling eater which connects to nd-shifty (the dumpling hub) and prints
    the contents of the dumplings made by the given chefs.
    """
    eater = netdumplings.DumplingEater(
        name=eater_name,
        shifty=shifty,
        chefs=chef if chef else None,
        on_connect=on_connect,
        on_dumpling=on_dumpling,
        on_connection_lost=on_connection_lost,
    )

    eater.run()


if __name__ == '__main__':
    printer()
