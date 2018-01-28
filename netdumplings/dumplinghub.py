import asyncio
import datetime
import json
import logging
import websockets
from websockets.exceptions import ConnectionClosed

from .dumpling import Dumpling, DumplingDriver
from .exceptions import InvalidDumpling, NetDumplingsError

from ._shared import (
    validate_dumpling, HUB_HOST, HUB_IN_PORT, HUB_OUT_PORT, HUB_STATUS_FREQ,
)


class DumplingHub:
    """
    Implements a dumpling hub.

    A dumpling hub is two websocket servers: one receives dumplings from any
    number of running ``nd-sniff`` scripts; and the other sends those dumplings
    to any number of dumpling eaters. The hub also makes its own dumplings
    which describe its own system status which are also sent to all the
    dumpling eaters at regular intervals.

    ``nd-hub`` is a simple wrapper around ``DumplingHub``.

    :param address: Address the hub is running on.
    :param in_port: Port used to receive connections from `nd-sniff`.
    :param out_port: Port used to receive connections from `dumpling eaters`.
    :param status_freq: Frequency (in secs) to send system status dumplings.
    """
    def __init__(
            self,
            address: str = HUB_HOST,
            in_port: int = HUB_IN_PORT,
            out_port: int = HUB_OUT_PORT,
            status_freq: int = HUB_STATUS_FREQ,
    ) -> None:

        self.address = address
        self.in_port = in_port
        self.out_port = out_port
        self.status_freq = status_freq

        # Maintain a dictionary of all connected kitchens and eaters.  The
        # key is the websocket and the value is a dictionary of information
        # on the kitchen/eater.
        self._dumpling_eaters = {}
        self._dumpling_kitchens = {}

        self._start_time = datetime.datetime.now()

        self._system_stats = {
            'dumplings_in': 0,
            'dumplings_out': 0
        }

        self._logger = logging.getLogger(__name__)

    def __repr__(self):
        return (
            '{}('
            'address={}, '
            'in_port={}, '
            'out_port={}, '
            'status_freq={})'.format(
                type(self).__name__,
                repr(self.address),
                repr(self.in_port),
                repr(self.out_port),
                repr(self.status_freq),
            )
        )

    def _get_system_status(self):
        """
        Generates current system status information.

        :return: System status information.
        """
        uptime = (datetime.datetime.now() - self._start_time).total_seconds()

        system_status = {
            'total_dumplings_in': self._system_stats['dumplings_in'],
            'total_dumplings_out': self._system_stats['dumplings_out'],
            'server_uptime': uptime,
            'dumpling_kitchen_count': len(self._dumpling_kitchens),
            'dumpling_eater_count': len(self._dumpling_eaters),
            'dumpling_kitchens':
                [self._dumpling_kitchens[kitchen]['metadata']
                 for kitchen in self._dumpling_kitchens],
            'dumpling_eaters':
                [self._dumpling_eaters[eater]['metadata']
                 for eater in self._dumpling_eaters]
        }

        return system_status

    async def _grab_dumplings(self, websocket, path):
        """
        A coroutine for grabbing dumplings from a single instance of
        ``nd-sniff``. A single instance of this coroutine exists for each
        connected ``nd-sniff`` and is invoked via
        :meth:`websockets.server.serve`.

        :param websocket: A :class:`websockets.server.WebSocketServerProtocol`.
        :param path: Websocket request URI.
        """
        host = websocket.remote_address[0]
        port = websocket.remote_address[1]

        # Retain some information on this dumpling kitchen.
        kitchen_json = await websocket.recv()
        kitchen = {
            'metadata': {
                'info_from_kitchen': json.loads(kitchen_json),
                'info_from_hub': {
                    'host': host,
                    'port': port
                }
            },
            'websocket': websocket
        }

        self._dumpling_kitchens[websocket] = kitchen
        kitchen_name = kitchen['metadata']['info_from_kitchen']['kitchen_name']

        self._logger.info(
            "Received dumpling kitchen connection from {0} at {1}:{2}".format(
                kitchen_name, host, port))

        try:
            while True:
                dumpling_json = await websocket.recv()

                # Validate the dumpling.
                try:
                    dumpling = validate_dumpling(dumpling_json)
                except InvalidDumpling as e:
                    self._logger.error(
                        "Received invalid dumpling: {0}; kitchen: {1}".format(
                            e,
                            json.dumps(
                                kitchen['metadata']['info_from_kitchen']
                            )
                        ))
                    continue

                self._system_stats['dumplings_in'] += 1

                chef = dumpling['metadata']['chef']
                self._logger.debug(
                    "Received {} dumpling from {} at {}:{}; {} bytes".format(
                        chef, kitchen_name, host, port, len(dumpling_json)))

                # Send this dumpling to all the eager dumpling eaters.
                for eater in self._dumpling_eaters:
                    await self._dumpling_eaters[eater]['queue'].put(
                        dumpling_json
                    )
        except ConnectionClosed as e:
            self._logger.info(
                "Dumpling kitchen {0} connection closed: {1}".format(
                    kitchen_name, e))
            del self._dumpling_kitchens[websocket]

    async def _emit_dumplings(self, websocket, path):
        """
        A coroutine for sending all received dumplings to a single connected
        dumpling eater over a websocket connection. A single instance of this
        coroutine exists for each eater and is invoked via
        :meth:`websockets.server.serve`.

        :param websocket: A :class:`websockets.server.WebSocketServerProtocol`.
        :param path: Websocket request URI.
        """
        host = websocket.remote_address[0]
        port = websocket.remote_address[1]

        # Retain some information on this dumpling eater.
        eater_json = await websocket.recv()
        eater = {
            'metadata': {
                'info_from_eater': json.loads(eater_json),
                'info_from_hub': {
                    'host': host,
                    'port': port
                }
            },
            'websocket': websocket,
            'queue': asyncio.Queue()
        }

        self._dumpling_eaters[websocket] = eater
        eater_name = eater['metadata']['info_from_eater']['eater_name']

        self._logger.info(
            "Received dumpling eater connection from {0} at {1}:{2}".format(
                eater_name, host, port))

        # Each dumpling eater has their own queue.  These queues receive all
        # the fresh new dumplings received by each instance of the
        # _grab_dumplings coroutine.
        dumpling_queue = eater['queue']

        try:
            while True:
                dumpling = await dumpling_queue.get()
                dumpling_obj = json.loads(dumpling)
                chef = dumpling_obj['metadata']['chef']

                self._logger.debug(
                    "Sending {0} dumpling to {1} at {2}:{3}; {4} bytes".format(
                        chef, eater_name, host, port, len(dumpling)))

                await websocket.send(dumpling)
                self._system_stats['dumplings_out'] += 1
        except ConnectionClosed as e:
            self._logger.info(
                "Dumpling eater {0} connection closed: {1}".format(
                    eater_name, e))
            del self._dumpling_eaters[websocket]

    async def _announce_system_status(self):
        """
        Sends system status (as a dumpling) to all connected dumpling eaters.

        :param freq_secs: Frequency (in seconds) of status announcements.
        """
        while True:
            # We create our own system status dumplings (rather than going
            # through a chef+kitchen pair).
            status_dumpling = Dumpling(
                chef='SystemStatusChef', driver=DumplingDriver.interval,
                payload=self._get_system_status())

            status_dumpling_json = status_dumpling.to_json()

            for eater in self._dumpling_eaters:
                await self._dumpling_eaters[eater]['queue'].put(
                    status_dumpling_json
                )

            await asyncio.sleep(self.status_freq)

    def run(self):
        """
        Run the dumpling hub.

        Starts two websocket servers: one to receive dumplings from zero or
        more instances of ``nd-sniff``; and another to send those dumplings to
        zero or more dumpling eaters. Also creates its own dumplings at regular
        intervals to send system status information to all connected dumpling
        eaters.
        """
        dumpling_in_server = \
            websockets.serve(self._grab_dumplings, self.address, self.in_port)
        dumpling_out_server = \
            websockets.serve(self._emit_dumplings, self.address, self.out_port)

        loop = asyncio.get_event_loop()

        try:
            srv_in = loop.run_until_complete(dumpling_in_server)
            srv_out = loop.run_until_complete(dumpling_out_server)
        except OSError as e:
            raise NetDumplingsError(
                "Cannot instantiate dumpling hub: {0}".format(e))

        status_task = asyncio.ensure_future(self._announce_system_status())

        self._logger.info("Dumpling hub initiated; waiting for connections")

        in_uri = "ws://{0}:{1}".format(self.address, self.in_port)
        out_uri = "ws://{0}:{1}".format(self.address, self.out_port)
        self._logger.info(
            "Dumplings in: {0}  out: {1}".format(in_uri, out_uri)
        )

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            self._logger.warning(
                "Caught keyboard interrupt; attempting graceful shutdown...")
        finally:
            srv_in.close()
            srv_out.close()
            loop.run_until_complete(srv_in.wait_closed())
            loop.run_until_complete(srv_out.wait_closed())
            if not status_task.cancelled():
                status_task.set_result(None)
            self._logger.info("Dumpling hub signing off.  Thanks!")
