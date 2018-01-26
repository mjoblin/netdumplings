.. _writing eater:

.. automodule:: netdumplings

Writing a dumpling eater
========================

A dumpling eater has a very simple mission: receive dumplings from ``nd-hub``
and do whatever it wants with them. The `netmomo`_ and `packscape`_
Web applications are examples of dumpling eaters.

To create an eater with Python you subclass :class:`DumplingEater` and
implement ``on_dumpling()``. All eaters will receive all dumplings being sent
from ``nd-hub``.

The DumplingEater handlers, like ``on_dumpling()``, are async methods so you
need to define them with the ``async`` keyword.

The following eater prints the payload of every dumpling sent from
``nd-hub``: ::

    import json
    import netdumplings

    class PrinterEater(netdumplings.DumplingEater):
        async def on_connect(self, hub_uri, websocket):
            print(f'Connected to nd-hub at {hub_uri}')
            print('Waiting for dumplings...\n')

        async def on_dumpling(self, dumpling):
            # The given dumpling is a netdumplings.Dumpling instance.
            dumpling_printable = json.dumps(dumpling.payload, indent=4)
            print(f'{dumpling_printable}\n')


    def dumpling_printer():
        eater = PrinterEater()
        eater.run()


    if __name__ == '__main__':
        dumpling_printer()

Writing eaters in languages other than Python
---------------------------------------------

Since dumplings are just JSON data sent over a WebSocket connection to and from
``nd-hub``, you can write your dumpling eaters in any language you like.  If
you do this (or otherwise aren't using the provided :class:`DumplingEater`
class) then there's a few things to remember:

* Your eater needs to announce itself when it connects to ``nd-hub`` by
  passing a simple payload of ``{"eater_name": "your_eater_name"}``.
* Your eater will then receive *every* dumpling coming out of ``nd-hub``.  It
  may want to interrogate the ``metadata`` key of each dumpling to check the
  ``chef_name`` (or any other information it cares about) to decide whether
  it's interested in the dumpling or not. Ignoring unwanted dumplings early
  is a good idea.

Example eaters
--------------

See the dumpling eater scripts that come with netdumplings for more examples:

* `nd-print`_
* `nd-hubdetails`_
* `nd-hubstatus`_

See `netmomo`_ and `packscape`_ for examples of dumpling eaters written in
JavaScript.


.. _netmomo: https://github.com/mjoblin/netmomo
.. _packscape: https://github.com/mjoblin/packscape
.. _nd-print: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/console/print.py
.. _nd-hubdetails: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/console/hubdetails.py
.. _nd-hubstatus: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/console/hubstatus.py

