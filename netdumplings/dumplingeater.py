import argparse
import asyncio
import json
import logging
import re
import signal
import sys
import websockets

from netdumplings.exceptions import InvalidDumplingError, NetDumplingsError
from netdumplings.shared import (configure_logging, get_config, get_config_file,
                                 get_logging_config_file, validate_dumpling,
                                 ND_CLOSE_MSGS)


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
    """
    def __init__(self, name=None, shifty=None, *, chefs=None, on_connect=None,
                 on_dumpling=None, on_connection_lost=None):
        """
        :param name: Name of the dumpling eater.  Is ideally unique per eater.
        :param shifty: Address where `nd-shifty` is sending dumplings from.
        :param chefs: List of chef names whose dumplings this eater wants to
            receive.  ``None`` means get all chefs' dumplings.
        :param on_connect: Called when connection to shifty is made.  Is passed
            two paramers: the shifty websocket URI (string) and websocket
            object (:class:`websockets.client.WebSocketClientProtocol`).
        :param on_dumpling: Called whenever a dumpling is received.  Is passed
            the dumpling as a Python dict.
        :param on_connection_lost: Called when connection to `nd-shifty` is
            lost.  Is passed the associated exception object.
        """
        self.name = name
        self._was_connected = False
        self._logger_name = "netdumplings.eater.{0}".format(self.name)

        # We're forgiving of not being given a shifty address.  The
        # commandline_helper assists with shifty address generation but it's
        # nice to use the default from the config if the helper isn't used.
        config = get_config()
        if shifty:
            self.shifty = shifty if ":" in shifty else \
                "{0}:{1}".format(shifty, config['shifty']['out_port'])
        else:
            self.shifty = "{0}:{1}".format(config['shifty']['address'],
                                           config['shifty']['out_port'])

        self.chefs = chefs
        self.on_connect = on_connect
        self.on_dumpling = on_dumpling
        self.on_connection_lost = on_connection_lost
        self.shifty_uri = "ws://{0}".format(self.shifty)
        self.logger = logging.getLogger(self._logger_name)

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
                except InvalidDumplingError as e:
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

    @staticmethod
    def commandline_helper(name="dumpling_eater", description=None, chefs=None):
        """
        Helper function for generating and processing eater commandline args.

        :param name: The name of the dumpling eater. Default: "dumpling_eater".
        :param description: Description of the dumpling eater.
        :param chefs: List of chefs whose dumplings we want to eat.
        :return: tuple: ``eater_name`` (string), ``shifty`` (string; address of
            shifty), ``log_level`` (``None`` or Python logging level string),
            ``chefs`` (``None`` or list of strings).
        """
        config = get_config()
        default_config_file = get_config_file()
        default_address = config['shifty']['address']
        default_out_port = config['shifty']['out_port']
        default_shifty = "{0}:{1}".format(default_address, default_out_port)

        default_name = name
        try:
            default_chefs = ",".join(chefs)
        except TypeError:
            default_chefs = chefs
        default_log_level = 'INFO'
        default_log_config_file = get_logging_config_file()

        parser = argparse.ArgumentParser(description=description)

        parser.add_argument(
            "--name", default=default_name,
            help="name of this dumpling eater (default: {0})".format(
                default_name))
        parser.add_argument(
            "--shifty", default=None,
            help="address where nd-shifty is sending dumplings from "
                 "(default: {0})".format(default_shifty))
        parser.add_argument(
            "--chefs", default=default_chefs,
            help="chefs whose dumplings we want to eat (default: {0})".format(
                default_chefs if default_chefs else "all"))
        parser.add_argument(
            "--config", default=None,
            help="configuration file (default: {0})".format(
                default_config_file))
        parser.add_argument(
            "--log-level", default=None,
            help="logging level (default: {0})".format(default_log_level))
        parser.add_argument(
            "--log-config", default=default_log_config_file,
            help="logging config file (default: in netdumplings.data module)")

        args = parser.parse_args()

        # Handle shifty overrides.  Priority order is: command-line args,
        # then any potential config override file, then the default config.
        if args.shifty:
            if ":" in args.shifty:
                (address, port) = args.shifty.split(":")
                config['shifty']['address'] = address
                config['shifty']['out_port'] = port
            else:
                config['shifty']['address'] = args.shifty
        elif args.config:
            try:
                config_overrides = get_config(args.config)
            except NetDumplingsError as e:
                # Printing and exiting from a class is a bit dodgy, but this is
                # a command-line script helper class, so yeah.
                print("error: {0}".format(e))
                sys.exit(0)

            for shifty_setting in ['address', 'out_port']:
                try:
                    config['shifty'][shifty_setting] = \
                        config_overrides['shifty'][shifty_setting]
                except (KeyError, TypeError):
                    # This setting may not be overridden so we quietly ignore.
                    pass

        configure_logging(args.log_level, args.log_config, 'netdumplings.eater')

        return (args.name, config,
                None if not args.log_level else args.log_level.upper(),
                None if not args.chefs else re.split("[,\s]+", args.chefs))

    def run(self, dumpling_count=None):
        """
        Run the dumpling eater.

        :param dumpling_count: Number of dumplings to eat.  ``None`` means eat
            forever.
        """
        self.logger.info("{0}: Running dumpling eater".format(self.name))

        # Check that we have a valid callable on_dumpling handler.
        if not hasattr(self.on_dumpling, '__call__'):
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
