import sys

import click

import netdumplings
from netdumplings.exceptions import NetDumplingsError
from netdumplings._shared import (
    configure_logging, DEFAULT_SHIFTY_HOST, DEFAULT_SHIFTY_IN_PORT,
    DEFAULT_SHIFTY_OUT_PORT, SHIFTY_STATUS_FREQ,
)

from ._shared import CLICK_CONTEXT_SETTINGS


@click.command(
    context_settings=CLICK_CONTEXT_SETTINGS,
)
@click.option(
    '--address', '-a',
    help='Address where nd-shifty will send dumplings from.',
    metavar='HOSTNAME',
    default=DEFAULT_SHIFTY_HOST,
    show_default=True,
)
@click.option(
    '--in-port', '-i',
    help='Port to receive incoming dumplings from.',
    metavar='PORT',
    type=click.INT,
    default=DEFAULT_SHIFTY_IN_PORT,
    show_default=True,
)
@click.option(
    '--out-port', '-o',
    help='Port to send outgoing dumplings on.',
    metavar='PORT',
    type=click.INT,
    default=DEFAULT_SHIFTY_OUT_PORT,
    show_default=True,
)
@click.option(
    '--status-freq', '-f',
    help='Frequency (in seconds) to send status dumplings.',
    metavar='SECONDS',
    type=click.INT,
    default=SHIFTY_STATUS_FREQ,
    show_default=True,
)
@click.version_option(version=netdumplings.__version__)
def shifty_cli(address, in_port, out_port, status_freq):
    """
    The dumpling hub.

    Sends dumplings received from all kitchens (usually any running instances
    of nd-snifty) to all dumpling eaters. All kitchens and eaters need to
    connect to the nd-shifty --in-port or --out-port respectively.
    """
    configure_logging()

    dumpling_hub = netdumplings.DumplingHub(
        address=address,
        in_port=in_port,
        out_port=out_port,
        status_freq=status_freq,
    )

    try:
        dumpling_hub.run()
    except NetDumplingsError as e:
        print('shifty error: {0}'.format(e))
        sys.exit(1)


if __name__ == '__main__':
    shifty_cli()
