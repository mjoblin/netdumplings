.. automodule:: netdumplings

What's in the box?
==================

When you :ref:`install NetDumplings <installation>` you get the main
``netdumplings`` Python module as well as some command-line scripts.

There's enough in the installation package to get started without writing any
code, but the real fun comes from writing your own :class:`DumplingChef`
objects, and using the :class:`DumplingEater` class to write your own
dumpling eaters.

The netdumplings Python module
------------------------------

This is a Python module which provides the :class:`DumplingChef` and
:class:`DumplingEater` classes -- as well as additional classes -- as
described in :ref:`the API <api>`.

... and some DumplingChefs
^^^^^^^^^^^^^^^^^^^^^^^^^^

The default NetDumplings install includes some pre-made DumplingChefs:

 * :ref:`api-arpchef`
 * :ref:`api-dnslookupchef`
 * :ref:`api-packetcountchef`

Command-line scripts
--------------------

NetDumplings comes with a handful of command-line scripts.  Two of them
(``nd-snifty`` and ``nd-shifty``) are essential for our tasty dumpling
universe to exist.

To see the command-line arguments supported by any of the NetDumplings
command-line scripts, use the ``--help`` flag: ::

    $ nd-snifty --help

nd-snifty
^^^^^^^^^

A packet sniffer which sends every packet which matches a given filter to
every registered :class:`DumplingChef`.

.. Important::
   `nd_snifty` is a packet sniffer so it needs to be run as root, or the
   equivalent in your particular environment.

nd-shifty
^^^^^^^^^

A dumpling hub which receives dumplings from one or more instances of
`nd-snifty`, and forwards those dumplings to every connected dumpling eater.

nd-info
^^^^^^^

A dumpling eater which displays the complete current status of `nd-shifty`.

nd-status
^^^^^^^^^

A dumpling eater which runs forever, displaying a summary of the current
status of `nd-shifty` at regular intervals.

nd-printer
^^^^^^^^^^

A dumpling eater which prints the payloads of any dumplings received from
`nd-shifty`.

I like pictures!
^^^^^^^^^^^^^^^^

Excellent!  Here's how everything is laid out.  The command-line scripts are in
blue and the Python classes are shown in green.

.. image:: ../_static/in_the_box.svg
   :width: 600
   :align: center
