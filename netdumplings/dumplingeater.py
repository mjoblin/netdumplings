import asyncio
import json
import logging
import signal
from typing import Awaitable, Callable, Dict, List, Optional
import websockets

from .exceptions import InvalidDumpling

from ._shared import (
    validate_dumpling, ND_CLOSE_MSGS, DEFAULT_SHIFTY_HOST,
    DEFAULT_SHIFTY_OUT_PORT
)


class DumplingEater:
    """
    Base helper class for Python-based dumpling eaters.

    Connects to `nd-shifty` and listens for any dumplings made by the provided
    list of chefs (or all chefs if ``chefs`` is ``None``).  Can be given
    callables for any of the following events:

    ``on_connect(websocket_uri, websocket_obj)``
        invoked when the connection to `nd-shifty` is made.

    ``on_dumpling(dumpling)``
        invoked whenever a dumpling is emitted from `nd-shifty`.

    ``on_connection_lost(e)``
        invoked when the connection to `nd-shifty` is closed.

    :param name: Name of the dumpling eater. Is ideally unique per eater.
    :param shifty: Address where `nd-shifty` is sending dumplings from.
    :param chefs: List of chef names whose dumplings this eater wants to
        receive. ``None`` means get all chefs' dumplings.
    :param on_connect: Called when connection to shifty is made. Is passed two
        parameters: the shifty websocket URI (string) and websocket
        object (:class:`websockets.client.WebSocketClientProtocol`).
    :param on_dumpling: Called whenever a dumpling is received. Is passed the
        dumpling as a Python dict.
    :param on_connection_lost: Called when connection to `nd-shifty` is lost.
        Is passed the associated exception object.
    """
    def __init__(
            self,
            name: str = 'nameless_eater',
            shifty: str ='{}:{}'.format(
                DEFAULT_SHIFTY_HOST, DEFAULT_SHIFTY_OUT_PORT
            ),
            *,
            chefs: Optional[List[str]] = None,
            on_connect: Optional[
                Callable[
                    [str, websockets.client.WebSocketClientProtocol],
                    Awaitable[None]
                ]
            ] = None,
            on_dumpling: Optional[
                Callable[[Dict], Awaitable[None]]
            ] = None,
            on_connection_lost: Optional[
                Callable[[Exception], Awaitable[None]]
            ] = None,
    ):
        self.name = name
        self.chefs = chefs
        self.shifty = shifty
        self.shifty_uri = "ws://{0}".format(shifty)

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
        return (
            '{}('
            'name={}, '
            'shifty={}, '
            'chefs={}, '
            'on_connect={}, '
            'on_dumpling={}, '
            'on_connection_lost={})'.format(
                type(self).__name__,
                repr(self.name),
                repr(self.shifty),
                repr(self.chefs),
                repr(self.on_connect),
                repr(self.on_dumpling),
                repr(self.on_connection_lost),
            )
        )

    async def _grab_dumplings(self, dumpling_count=None):
        """
        Receives all dumplings from shifty and looks for any dumplings which
        were created by the chef(s) we're interested in.  All those dumplings
        are then passed to the on_dumpling handler.

        :param dumpling_count: Number of dumplings to eat.  None means eat
            forever.
        """
        dumplings_eaten = 0

        websocket = await websockets.client.connect(self.shifty_uri)
        self._was_connected = True

        self.logger.info("{0}: Connected to shifty at {1}".format(
            self.name, self.shifty_uri))

        try:
            # Announce ourselves to shifty.
            await websocket.send(json.dumps({'eater_name': self.name}))

            if self.on_connect:
                await self.on_connect(self.shifty_uri, websocket)

            while True:
                # Eat a single dumpling.
                dumpling_json = await websocket.recv()

                # Validate the dumpling.  Note that invalid dumplings will
                # probably be stripped out by shifty (the DumplingHub).
                try:
                    dumpling = validate_dumpling(dumpling_json)
                except InvalidDumpling as e:
                    self.logger.error("{0}: Invalid dumpling: {1}".format(
                        self.name, e))
                    continue

                dumpling_chef = dumpling['metadata']['chef']

                self.logger.debug("{0}: Received dumpling from {1}".format(
                    self.name, dumpling_chef))

                # Call the on_dumpling handler if this dumpling is from a
                # chef that we've registered interest in.
                if self.chefs is None or dumpling_chef in self.chefs:
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
                "{0}: Connection to shifty cancelled; closing...".format(
                    self.name))

            try:
                await websocket.close(*ND_CLOSE_MSGS['conn_cancelled'])
            except websockets.exceptions.InvalidState:
                pass
        except websockets.exceptions.ConnectionClosed as e:
            self.logger.warning("{0}: Lost connection to shifty: {1}".format(
                self.name, e))

            if self.on_connection_lost:
                await self.on_connection_lost(e)

    @staticmethod
    def _interrupt_handler():
        """
        Signal handler.  Cancels all running async tasks.
        """
        tasks = asyncio.Task.all_tasks()
        for task in tasks:
            task.cancel()

    def run(self, dumpling_count=None):
        """
        Run the dumpling eater.

        :param dumpling_count: Number of dumplings to eat.  ``None`` means eat
            forever.
        """
        self.logger.info("{0}: Running dumpling eater".format(self.name))

        if not callable(self.on_dumpling):
            self.logger.error(
                "{0}: on_dumpling handler is not callable".format(self.name))
            return

        self.logger.debug("{0}: Looking for shifty at {1}".format(
            self.name, self.shifty_uri))
        self.logger.debug("{0}: Chefs: {1}".format(
            self.name, ", ".join(self.chefs) if self.chefs else 'all'))

        loop = asyncio.get_event_loop()
        task = loop.create_task(self._grab_dumplings(dumpling_count))

        for signal_name in ('SIGTERM', 'SIGINT'):
            loop.add_signal_handler(
                getattr(signal, signal_name), DumplingEater._interrupt_handler)

        try:
            loop.run_until_complete(task)
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
                "{0}: There was a problem with the shifty connection. "
                "Is shifty available?".format(self.name))
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
        """
        self.logger.warning(
            '{}: No on_connection_lost handler specified; ignoring '
            'connection loss.'.format(self.name)
        )
