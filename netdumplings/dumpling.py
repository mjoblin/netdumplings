from enum import Enum
import json
import time
from typing import Any, Union

from .dumplingchef import DumplingChef
from .exceptions import InvalidDumplingPayload


class DumplingDriver(Enum):
    """
    When a new :class:`Dumpling` is created it wants to be told why it's being
    created.  Its creation will be the result of one of two things:

    ``DumplingDriver.packet``
        a network packet being received by a :class:`DumplingChef`.

    ``DumplingDriver.interval``
        a regular time-based poke being received by a :class:`DumplingChef`.
    """
    packet = 1
    interval = 2


class Dumpling:
    """
    Represents a single Dumpling.  Dumplings are created indirectly by a
    :class:`~DumplingChef`.  A Dumpling might be created as the result of
    a :class:`~DumplingChef` receiving a packet, or receiving a poke (which
    happens at regular intervals), from a :class:`~DumplingKitchen`.

    **NOTE: You will normally not instantiate Dumpling objects yourself.
    They will normally be created for you when you call the DumplingChef send()
    method (into which you'll pass a Python dict which will become the payload
    of the dumpling).**

    A single ``Dumpling`` is a callable.  When invoked in this way it returns
    the result of :meth:`make`: ::

        dumpling = Dumpling(
            chef=chef, driver=DumplingDriver.packet, payload=payload)

        print(dumpling())

    A complete JSON-serialized dumpling, as sent to the dumpling eaters, looks
    as follows: ::

        {
            'metadata': {
                'chef': <string: name of the dumpling chef>,
                'kitchen': <string: name of the kitchen which provided the
                            ingredients (packets) to create the dumpling>,
                'creation_time': <float: time the dumpling was created>,
                'count': <int: the number of dumplings made by this chef>
            },
            'payload': <mixed: the meat/veg of the dumpling>
        }
    """
    def __init__(
            self,
            *,
            chef: Union[DumplingChef, str],
            driver: DumplingDriver = DumplingDriver.packet,
            payload: Any,
    ):
        """
        :param chef: The :class:`DumplingChef` who created the dumpling, or
            a string representing the dumpling chef name.  A string can be
            used when a real :class:`DumplingChef` isn't making the dumpling.
        :param driver: The :class:`DumplingDriver` event that drove the
            dumpling to be created; should be ``DumplingDriver.packet`` or
            ``DumplingDriver.interval``.
        :param payload: The payload information.  Can be anything (usually a
            dict) which is JSON-serializable.  It's up to the dumpling eaters
            to make sense of it.
        """
        self.chef = chef

        try:
            self.chef_name = chef.name
            self.kitchen = chef.kitchen
        except AttributeError:
            self.chef_name = chef
            self.kitchen = None

        self.driver = driver
        self.payload = payload

    def __call__(self):
        """
        Makes ``Dumpling`` callable.  When called in this way, ``Dumpling``
        will return the result of :meth:`make`.

        :return: Result of :meth:`make`.
        """
        return self.make()

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
            'payload={})'.format(
                type(self).__name__,
                repr(self.chef),
                driver,
                payload,
            )
        )

    def make(self) -> str:
        """
        Makes a complete JSON-serialized dumpling string from the Dumpling.

        The created dumpling string will include the ``metadata`` and
        ``payload`` components of the dumpling.

        This method will normally not be called directly except in cases where
        the dumpling is being built manually rather than via a
        :class:`DumplingKitchen`.

        :return: A JSON string representation of the dumpling.
        :raises: :class:`InvalidDumplingPayload` if the Dumpling ``payload``
            cannot be JSON-serialized.
        """
        dumpling = {
            'metadata': {
                'chef': self.chef_name,
                'kitchen': self.kitchen.name if self.kitchen else None,
                'creation_time': time.time(),
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
