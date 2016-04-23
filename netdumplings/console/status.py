#!/usr/bin/env python

import datetime

from netdumplings import DumplingEater


async def on_connect(shifty_uri, websocket):
    """
    Called when the connection to nd-shifty has been created.

    :param shifty_uri: The nd-shifty websocket URI.
    :param websocket: The websocket object used for talking to nd-shifty
        (websockets.WebSocketClientProtocol).
    :return: None
    """
    print("Shifty status from {0}".format(shifty_uri))
    print("Waiting for data... ", end="", flush=True)


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
    up_str = "{0:02d}:{1:02d}:{2:02d}".format(up_hrs, up_mins, up_secs)

    status_msg = "\r{now}  uptime: {uptime}  dumplings: {dumplings:,}  " \
        "kitchens: {kitchens:,}  eaters: {eaters:,} ".format(
            now=datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S'),
            dumplings=payload['total_dumplings_sent'],
            uptime=up_str,
            kitchens=payload['dumpling_kitchen_count'],
            eaters=payload['dumpling_eater_count']
        )

    print(status_msg, end="", flush=True)


async def on_connection_lost(e):
    """
    Called when nd-shifty connection is lost.

    :param e: The exception thrown during the connection close.
    :return: None
    """
    print("\nLost connection to nd-shifty: {}".format(e))


def main():
    """
    This is a dumpling eater which connects to `nd-shifty` (the dumpling hub)
    and outputs some of the information contained in any ``SystemStatusChef``
    dumplings.  This is a system-monitoring dumpling eater which can be used to
    keep an eye on `nd-shifty`.
    """
    description = """
        A dumpling eater which runs forever, displaying the contents of
        nd-shifty status dumplings.
    """

    default_chef = ['SystemStatusChef']

    name, config, log_level, chefs = DumplingEater.commandline_helper(
        name="statusnommer", description=description, chefs=default_chef)

    shifty_uri = "{0}:{1}".format(
        config['shifty']['address'], config['shifty']['out_port'])

    eater = DumplingEater(
        name=name, shifty=shifty_uri, chefs=chefs, on_connect=on_connect,
        on_dumpling=on_dumpling, on_connection_lost=on_connection_lost
    )

    eater.run()


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
