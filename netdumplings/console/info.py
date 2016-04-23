#!/usr/bin/env python

import json

from netdumplings import DumplingEater


async def on_connect(shifty_uri, websocket):
    """
    Called when the connection to nd-shifty has been created.

    :param shifty_uri: The nd-shifty websocket URI.
    :param websocket: The websocket object used for talking to nd-shifty
        (websockets.WebSocketClientProtocol).
    :return: None
    """
    print("Connected to nd-shifty at {0}".format(shifty_uri))
    print("Waiting for dumpling from SystemStatusChef...")


async def on_dumpling(dumpling):
    """
    Called when a new dumpling is received from nd-shifty.  Prints dumpling
    payload.

    :param dumpling: The freshly-made new dumpling.
    :return: None
    """
    print("{0} dumpling:\n".format(dumpling['metadata']['chef']))
    print(json.dumps(dumpling['payload'], sort_keys=True, indent=4,
                     separators=(',', ': ')))
    print()

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
    and waits for a single ``SystemStatus`` dumpling which it displays and then
    exits.
    """
    description = """
        A dumpling eater which eats a single SystemStatus dumpling from
        nd-shifty and displays its contents.
    """

    default_chefs = ['SystemStatusChef']

    name, config, log_level, chefs = DumplingEater.commandline_helper(
        name="infonommer", description=description, chefs=default_chefs)

    shifty_uri = "{0}:{1}".format(
        config['shifty']['address'], config['shifty']['out_port'])

    eater = DumplingEater(
        name=name, shifty=shifty_uri, chefs=chefs, on_connect=on_connect,
        on_dumpling=on_dumpling, on_connection_lost=on_connection_lost
    )

    eater.run(dumpling_count=1)


# -----------------------------------------------------------------------------

if __name__ == '__main__':
    main()
