from enum import Enum
import json
import time
from typing import Any, Optional, Union

from .dumplingchef import DumplingChef
from .exceptions import InvalidDumpling, InvalidDumplingPayload


class DumplingDriver(Enum):
    """
    The event driving the creation of a :class:`Dumpling`.

    ``DumplingDriver.packet``
        a network packet being received by a :class:`DumplingChef`.

    ``DumplingDriver.interval``
        a regular time interval poke being received by a :class:`DumplingChef`.
    """
    packet = 1
    interval = 2


class Dumpling:
    """
    Represents a single Dumpling.

    Dumplings are usually created automatically by a dumpling kitchen from the
    payload returned by a :class:`~DumplingChef`.

    A Dumpling exposes the following attributes:

    * ``chef`` - the :class:`DumplingChef` which is responsible for the
      dumpling payload
    * ``chef_name`` - the name of the DumplingChef
    * ``kitchen`` - the name of the kitchen which created the Dumpling
    * ``driver`` - the :class:`DumplingDriver` for the dumpling
    * ``creation_time`` - when the dumpling was created (epoch milliseconds)
    * ``payload`` - the dumpling payload

    :param chef: The chef which created the dumpling payload (usually a
        :class:`DumplingChef` instance, but can be a string).
    :param driver: The event type that drove the dumpling to be created.
    :param creation_time: Dumpling creation time (epoch milliseconds). Defaults
        to current time.
    :param payload: The dumpling payload information. Can be anything (usually
        a dict) which is JSON-serializable.
    """
    def __init__(
            self,
            *,
            chef: Union[DumplingChef, str],
            driver: DumplingDriver = DumplingDriver.packet,
            creation_time: Optional[float] = None,
            payload: Any) -> None:

        self.chef = chef

        try:
            self.chef_name = chef.name
            self.kitchen = chef.kitchen
        except AttributeError:
            self.chef_name = chef
            self.kitchen = None

        self.driver = driver
        self.creation_time = (
            time.time() if creation_time is None else creation_time
        )
        self.payload = payload

    def __repr__(self):
        if self.driver == DumplingDriver.packet:
            driver = 'DumplingDriver.packet'
        elif self.driver == DumplingDriver.interval:
            driver = 'DumplingDriver.interval'
        else:
            driver = repr(self.driver)

        payload = (None if self.payload is None
                   else '<{}>'.format(type(self.payload).__name__))

        return (
            '{}('
            'chef={}, '
            'driver={}, '
            'creation_time={}, '
            'payload={})'.format(
                type(self).__name__,
                repr(self.chef),
                driver,
                self.creation_time,
                payload,
            )
        )

    @classmethod
    def from_json(cls, json_dumpling: str):
        """
        A Dumpling factory which creates a Dumpling from a given
        ``json_dumpling`` string. The given ``json_dumpling`` is expected to be
        a dumpling which has already been JSON-serialized (presumably by a
        dumpling kitchen).

        :param json_dumpling: JSON string to create the Dumpling from.
        :return: A :class:`Dumpling` instance.
        :raise: :class:`InvalidDumpling` if ``json_dumpling`` could not be
            successfully converted into a Dumpling.
        """
        try:
            dumpling_dict = json.loads(json_dumpling)
        except (json.decoder.JSONDecodeError, TypeError, ValueError) as e:
            raise InvalidDumpling(
                'Could not interpret dumpling JSON: {}'.format(e)
            )

        metadata = dumpling_dict['metadata']

        try:
            if metadata['driver'] == 'packet':
                driver = DumplingDriver.packet
            elif metadata['driver'] == 'interval':
                driver = DumplingDriver.interval
            else:
                raise InvalidDumpling(
                    "Dumpling driver was not 'packet' or 'interval'"
                )

            dumpling = cls(
                chef=metadata['chef'],
                driver=driver,
                creation_time=metadata['creation_time'],
                payload=dumpling_dict['payload'],
            )

            dumpling.kitchen = metadata['kitchen']
            return dumpling
        except KeyError as e:
            raise InvalidDumpling(
                'Dumpling JSON was missing key: {}'.format(e)
            )

    def to_json(self) -> str:
        """
        Creates a JSON-serialized dumpling string from the Dumpling.

        :return: A JSON string representation of the Dumpling.
        :raise: :class:`InvalidDumplingPayload` if the Dumpling payload cannot
            be JSON-serialized.
        """
        dumpling = {
            'metadata': {
                'chef': self.chef_name,
                'kitchen': self.kitchen.name if self.kitchen else None,
                'creation_time': self.creation_time,
                'driver': self.driver.name,
            },
            'payload': self.payload,
        }

        try:
            dumpling_serialized = json.dumps(dumpling)
        except TypeError as e:
            raise InvalidDumplingPayload(
                'Could not create dumpling: {}'.format(e)
            )

        return dumpling_serialized
