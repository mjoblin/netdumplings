import asyncio
import json
import logging
import signal
from typing import Callable, List, Optional
import websockets

from .dumpling import Dumpling
from .exceptions import InvalidDumpling

from ._shared import ND_CLOSE_MSGS, HUB_HOST, HUB_OUT_PORT


class DumplingEater:
    """
    Base helper class for Python-based dumpling eaters.

    Connects to ``nd-hub`` and listens for any dumplings made by the provided
    ``chef_filter`` (or all chefs if ``chef_filter`` is ``None``). Can be
    given ``async`` callables for any of the following events:

    ``on_connect(websocket_uri, websocket_obj)``
        invoked when the connection to ``nd-hub`` is made

    ``on_dumpling(dumpling)``
        invoked whenever a dumpling is emitted from ``nd-hub``

    ``on_connection_lost(e)``
        invoked when the connection to ``nd-hub`` is closed

    **The above callables must be** ``async def`` **methods**.

    :param name: Name of the dumpling eater. Is ideally unique per eater.
    :param hub: Address where ``nd-hub`` is sending dumplings from.
    :param chef_filter: List of chef names whose dumplings this eater wants to
        receive. ``None`` means get all chefs' dumplings.
    :param on_connect: Called when connection to ``nd-hub`` is made. Is passed
        two parameters: the ``nd-hub`` websocket URI (string) and websocket
        object (:class:`websockets.client.WebSocketClientProtocol`).
    :param on_dumpling: Called whenever a dumpling is received. Is passed the
        dumpling as a Python dict.
    :param on_connection_lost: Called when connection to ``nd-hub`` is lost. Is
        passed the associated exception object.
    """
    def __init__(
            self,
            name: str = 'nameless_eater',
            hub: str ='{}:{}'.format(HUB_HOST, HUB_OUT_PORT),
            *,
            chef_filter: Optional[List[str]] = None,
            on_connect: Optional[Callable] = None,
            on_dumpling: Optional[Callable] = None,
            on_connection_lost: Optional[Callable] = None) -> None:

        self.name = name
        self.chef_filter = chef_filter
        self.hub = hub
        self.hub_ws = "ws://{0}".format(hub)

        # Configure handlers. If we're not provided with handlers then we
        # fall back on the default handlers or the handlers provided by a
        # subclass.
        self.on_connect = (
            on_connect if on_connect is not None else self.on_connect
        )
        self.on_dumpling = (
            on_dumpling if on_dumpling is not None else self.on_dumpling
        )
        self.on_connection_lost = (
            on_connection_lost if on_connection_lost is not None
            else self.on_connection_lost
        )

        self._was_connected = False
        self._logger_name = "{}.{}".format(__name__, self.name)
        self.logger = logging.getLogger(self._logger_name)

    def __repr__(self):
        def handler_string(attr):
            # We can't use 'repr(self.handler)' for callables because it causes
            # an infinite loop as the repr of the handler includes the repr of
            # the handler (etc). So we replace handler reprs with
            # '<callable: name>'.
            return (
                '<callable: {}>'.format(attr.__name__) if callable(attr)
                else repr(attr)
            )

        return (
            '{}('
            'name={}, '
            'hub={}, '
            'chef_filter={}, '
            'on_connect={}, '
            'on_dumpling={}, '
            'on_connection_lost={})'.format(
                type(self).__name__,
                repr(self.name),
                repr(self.hub),
                repr(self.chef_filter),
                handler_string(self.on_connect),
                handler_string(self.on_dumpling),
                handler_string(self.on_connection_lost),
            )
        )

    async def _grab_dumplings(self, dumpling_count=None):
        """
        Receives all dumplings from the hub and looks for any dumplings which
        were created by the chef(s) we're interested in. All those dumplings
        are then passed to the on_dumpling handler (after being converted from
        their JSON form back into a Dumpling instance).

        :param dumpling_count: Number of dumplings to eat. ``None`` means eat
            forever.
        """
        dumplings_eaten = 0

        websocket = await websockets.client.connect(self.hub_ws)
        self._was_connected = True

        self.logger.info("{0}: Connected to dumpling hub at {1}".format(
            self.name, self.hub_ws))

        try:
            # Announce ourselves to the dumpling hub.
            await websocket.send(json.dumps({'eater_name': self.name}))

            if self.on_connect:
                await self.on_connect(self.hub_ws, websocket)

            while True:
                # Eat a single dumpling.
                dumpling_json = await websocket.recv()

                # Create a Dumpling from the JSON received over the websocket.
                # Note that invalid dumplings will probably be stripped out by
                # the hub already.
                try:
                    dumpling = Dumpling.from_json(dumpling_json)
                except InvalidDumpling as e:
                    self.logger.error("{0}: Invalid dumpling: {1}".format(
                        self.name, e))
                    continue

                self.logger.debug("{0}: Received dumpling from {1}".format(
                    self.name, dumpling.chef_name))

                # Call the on_dumpling handler if this dumpling is from a
                # chef that we've registered interest in.
                if (self.chef_filter is None or
                        dumpling.chef_name in self.chef_filter):
                    self.logger.debug(
                        "{0}: Calling dumpling handler {1}".format(
                            self.name, self.on_dumpling))

                    dumplings_eaten += 1
                    await self.on_dumpling(dumpling)

                # Stop eating dumplings if we've reached our threshold.
                if dumpling_count is not None and \
                        dumplings_eaten >= dumpling_count:
                    await websocket.close(*ND_CLOSE_MSGS['eater_full'])
                    break
        except asyncio.CancelledError:
            self.logger.warning(
                "{0}: Connection to dumpling hub cancelled; closing...".format(
                    self.name))

            try:
                await websocket.close(*ND_CLOSE_MSGS['conn_cancelled'])
            except websockets.exceptions.InvalidState:
                pass
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.warning(
                "{}: Lost connection to dumpling hub: {}".format(self.name, e)
            )

            if self.on_connection_lost:
                await self.on_connection_lost(e)

    @staticmethod
    def _interrupt_handler():
        """
        Signal handler. Cancels all running async tasks.
        """
        tasks = asyncio.Task.all_tasks()
        for task in tasks:
            task.cancel()

    def run(self, dumpling_count=None):
        """
        Run the dumpling eater.

        This will block until the desired ``dumpling_count`` is met.

        :param dumpling_count: Number of dumplings to eat. ``None`` means eat
            forever.
        """
        self.logger.info("{0}: Running dumpling eater".format(self.name))

        if not callable(self.on_dumpling):
            self.logger.error(
                "{0}: on_dumpling handler is not callable".format(self.name))
            return

        self.logger.debug("{0}: Looking for dumpling hub at {1}".format(
            self.name, self.hub_ws))
        self.logger.debug("{0}: Chefs: {1}".format(
            self.name,
            ", ".join(self.chef_filter) if self.chef_filter else 'all')
        )

        loop = asyncio.get_event_loop()
        dumpling_grabber_task = loop.create_task(
            self._grab_dumplings(dumpling_count)
        )

        for signal_name in ('SIGTERM', 'SIGINT'):
            loop.add_signal_handler(
                getattr(signal, signal_name), DumplingEater._interrupt_handler)

        try:
            loop.run_until_complete(dumpling_grabber_task)
        except KeyboardInterrupt as e:
            self.logger.warning(
                "{0}: Caught keyboard interrupt; attempting graceful "
                "shutdown...".format(self.name))
            tasks = asyncio.Task.all_tasks()
            for task in tasks:
                task.cancel()
            loop.run_forever()
        except OSError as e:
            self.logger.warning(
                "{0}: There was a problem with the dumpling hub connection. "
                "Is nd-hub available?".format(self.name))
            self.logger.warning("{0}: {1}".format(self.name, e))
        finally:
            if self._was_connected:
                self.logger.info(
                    "{0}: Done eating dumplings.".format(self.name))
            loop.close()

    async def on_connect(self, websocket_uri, websocket_obj):
        """
        Default on_connect handler.

        This will be used if an ``on_connect`` handler is not provided during
        instantiation, and if a handler is not provided by a DumplingEater
        subclass.

        Only logs an warning-level log entry.
        """
        self.logger.warning(
            '{}: No on_connect handler specified; ignoring '
            'connection.'.format(self.name)
        )

    async def on_dumpling(self, dumpling):
        """
        Default on_dumpling handler.

        This will be used if an ``on_dumpling`` handler is not provided during
        instantiation, and if a handler is not provided by a DumplingEater
        subclass.

        Only logs an warning-level log entry.
        """
        self.logger.warning(
            '{}: No on_dumpling handler specified; ignoring '
            'dumpling.'.format(self.name)
        )

    async def on_connection_lost(self, e):
        """
        Default on_connection_lost handler.

        This will be used if an ``on_connection_lost`` handler is not provided
        during instantiation, and if a handler is not provided by a
        DumplingEater subclass.

        Only logs an warning-level log entry.
        """
        self.logger.warning(
            '{}: No on_connection_lost handler specified; ignoring '
            'connection loss.'.format(self.name)
        )
