.. _api:

NetDumplings API
================

`Commonly-used classes`_

 You'll probably find yourself using these classes if you develop with NetDumplings.

 * `DumplingChef`_
 * `DumplingEater`_
 * `DumplingDriver`_
 * `Exception classes`_

`Some dumpling chefs`_

 These also double as some useful chef example code.

 * `ARPChef`_
 * `DNSLookupChef`_
 * `PacketCountChef`_

`Utility functions`_

 Some miscellaneous functions used throughout NetDumplings.

`Command-line scripts`_

 Not really part of the API, but this is the code behind the command-line scripts.

 * `nd-snifty`_
 * `nd-shifty`_
 * `nd-info`_
 * `nd-printer`_
 * `nd-status`_

`Additional classes`_

 You probably won't use these but it's good to know they're there.

 * `Dumpling`_
 * `DumplingHub`_
 * `DumplingKitchen`_


Commonly-used classes
---------------------

These are the classes commonly used when developing with NetDumplings.

The most important two are :class:`~DumplingChef` and :class:`~DumplingEater`,
which are the classes you're likely to use to write your own chefs and eaters.

You'll probably also find yourself using :class:`~DumplingDriver` and
the exception classes.

.. automodule:: netdumplings

DumplingChef
^^^^^^^^^^^^

.. autoclass:: DumplingChef
   :members:

DumplingEater
^^^^^^^^^^^^^

.. autoclass:: DumplingEater
   :members:

DumplingDriver
^^^^^^^^^^^^^^

.. autoclass:: DumplingDriver
   :members:

Exception classes
^^^^^^^^^^^^^^^^^

.. autoexception:: netdumplings.exceptions.NetDumplingsError

.. autoexception:: netdumplings.exceptions.InvalidDumplingError


Some dumpling chefs
-------------------

These are the dumpling chefs that come with NetDumplings.  They do some useful
things, and do double duty as examples for how to write your own chefs.

.. automodule:: netdumplings.dumplingchefs

.. _api-arpchef:

ARPChef
^^^^^^^

.. autoclass:: ARPChef

.. _api-dnslookupchef:

DNSLookupChef
^^^^^^^^^^^^^

.. autoclass:: DNSLookupChef

.. _api-packetcountchef:

PacketCountChef
^^^^^^^^^^^^^^^

.. autoclass:: PacketCountChef


Utility functions
-----------------

These are some shared utility functions, found in ``netdumplings.shared``.

.. automodule:: netdumplings.shared
   :members:


Command-line scripts
--------------------

nd-snifty
^^^^^^^^^

.. automodule:: netdumplings.console.snifty
   :members:
   :exclude-members: dumpling_emitter, get_commandline_args, get_override, list_chefs, network_sniffer, set_config

nd-shifty
^^^^^^^^^

.. automodule:: netdumplings.console.shifty
   :members:
   :exclude-members: get_commandline_args, set_config

Dumpling eaters
^^^^^^^^^^^^^^^

nd-printer
**********

.. automodule:: netdumplings.console.info
   :members:
   :exclude-members: on_connect, on_dumpling, on_connection_lost

nd-info
*******

.. automodule:: netdumplings.console.printer
   :members:
   :exclude-members: on_connect, on_dumpling, on_connection_lost

nd-status
*********

.. automodule:: netdumplings.console.status
   :members:
   :exclude-members: on_connect, on_dumpling, on_connection_lost


Additional classes
------------------

These are the additional classes included in NetDumplings.  You probably don't
want or need to use these but you might want to know they're there.

Dumpling
^^^^^^^^

.. autoclass:: netdumplings.Dumpling
   :members:

DumplingHub
^^^^^^^^^^^

.. autoclass:: netdumplings.DumplingHub
   :members:

DumplingKitchen
^^^^^^^^^^^^^^^

.. autoclass:: netdumplings.DumplingKitchen
   :members:
