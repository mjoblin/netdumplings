.. automodule:: netdumplings

Writing a dumpling eater
========================

A dumpling eater has a very simple mission: receive dumplings from
`nd-shifty` and do whatever it wants with them.

Here's an example of a dumpling eater script.  All it does is pretty-print the
payload of every dumpling it receives.  Note that it uses the
:class:`DumplingEater` class to do most of the hard work::

    #!/usr/bin/env python

    import json

    from netdumplings import DumplingEater


    async def on_dumpling(dumpling):
        print(json.dumps(dumpling['payload'], sort_keys=True, indent=4,
                         separators=(',', ': ')))

    def main():
        eater = DumplingEater(name='simple_eater', on_dumpling=on_dumpling)
        eater.run()


    if __name__ == '__main__':
        main()

Check out the :class:`DumplingEater` documentation for more information on
what the class can do.  And take a look at the dumpling eater scripts that come
with NetDumplings for more examples:

* `nd-status`_
* `nd-info`_
* `nd-printer`_

The above dumpling eaters make use of the ``commandline_helper()`` method which
provides your eater with some useful commandline arguments.  Here's an example
using ``commandline_helper()`` to allow for the default ``nd-shifty`` address
and port to be overridden: ::

    #!/usr/bin/env python

    import json

    from netdumplings import DumplingEater


    async def on_dumpling(dumpling):
        print(json.dumps(dumpling['payload'], sort_keys=True, indent=4,
                         separators=(',', ': ')))


    def main():
        name, config, log_level, chefs = DumplingEater.commandline_helper(
            name='simple_eater')

        shifty_uri = "{0}:{1}".format(
            config['shifty']['address'], config['shifty']['out_port'])

        eater = DumplingEater(
            name=name, shifty=shifty_uri, on_dumpling=on_dumpling)

        eater.run()


    if __name__ == '__main__':
        main()


Writing eaters in languages other than Python
---------------------------------------------

Since dumplings are just JSON documents sent over a websocket connection to
`nd-shifty`, you can write your dumpling eaters in any language you like.  If
you do this (or otherwise aren't using the provided :class:`DumplingEater`
class) then there's a few things to remember:

* Your eater needs to announce itself when it connects to `nd-shifty` by passing a simple payload of ``{"eater_name": "your_eater_name"}``.
* Your eater will then receive `every` dumpling coming out of `nd-shifty`.  It may want to interrogate the ``metadata`` key of each dumpling to check the ``chef_name`` (or any other information it cares about) to decide whether it's interested in the dumpling or not.  Ignoring unwanted packets early will help performance and stability.

.. _nd-status: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/console/statuseater.py
.. _nd-info: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/console/infoeater.py
.. _nd-printer: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/console/printereater.py

