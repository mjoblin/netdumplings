Configuration
=============

The command-line scripts can be configured via their command-line arguments,
but by default they fall back on the config file found at
``netdumplings/data/config.json`` which looks like this:

.. literalinclude:: ../../netdumplings/data/config.json
   :language: json

This config file sets some defaults for `nd-snifty` and `nd-shifty`, as well
as defining a kitchen called ``packets_per_second``.  This kitchen can be
used by `nd-snifty` like so: ::

   $ nd-snifty --kitchen-name packets_per_second

You can create your own config files and pass them to the command-line scripts
via the ``--config`` flag.  You may want to do this if you're often overriding
the defaults, or have a number of your own kitchen configurations that you want
to pass to `nd-snifty`.

When adding kitchens to your own config file, you only need to specify the
``snifty`` fields that you wish to override.  If you don't specify a field for
your kitchen then it will fall back on the default ``snifty`` value.

Here's what the various configuration fields mean:

shifty
------

* ``address`` : (string) the address to listen on (e.g. ``'localhost'``, ``'0.0.0.0'``, etc.)
* ``in_port`` : (int) port to receive dumplings on.
* ``out_port`` : (int) port to send dumplings out on.
* ``status_freq`` : (int) how often (in seconds) to send SystemStatus dumplings.

snifty
------

The following can be specified at the master ``snifty`` level (affecting all
kitchens) or at the individual kitchen level (under ``kitchens.kitchen_name``):

* ``interface`` : (string) the network interface to sniff on.
* ``filter`` : (string) the PCAP-style packet filter string; ``None`` means no filter.
* ``poke_interval`` : (int) interval frequency (in seconds) to poke chefs.
* ``chefs`` : (list) chefs to send packets to (``True`` sends to all chefs).
* ``chef_modules`` : (list) Python modules where chefs can be found.

