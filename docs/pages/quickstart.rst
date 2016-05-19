.. automodule:: netdumplings

Quickstart
==========

Run the following (after :ref:`installation <installation>`) to see it in action: ::

    # in terminal 1: start the dumpling hub
    $ nd-shifty

    # in terminal 2: start a network sniffer
    $ nd-snifty --kitchen packets_per_second

    # in terminal 3: start a dumpling eater
    $ nd-printer --chef PacketCountChef

For more on how to run everything, see the :ref:`run it section<run-it>`.

The above quickstart doesn't require writing any code, but it also doesn't do
much.  You'll be able to do a lot more when you start writing your own dumpling
chefs and dumpling eaters.

What's going on
---------------

Following is a quick technical overview of NetDumplings.  You can
:ref:`read more details here <more-details>`.

* NetDumplings provides a network sniffing script called **nd-snifty**.
* `nd-snifty` instantiates all your :class:`DumplingChef` sub-classes and invokes a ``packet_handler()`` method on each one whenever a new packet is sniffed.
* Your :class:`DumplingChef` sub-classes receive each sniffed packet, processes them, and call ``self.send_dumpling()`` (whenever they're ready; not necessarily every time they receive a packet) to send a dumpling.  The dumplings they send will be made from the contents of the network packets they've received.
* (Dumplings are just bundles of information stored in a Python dictionary).
* `nd-snifty` manages the forwarding of those dumplings (which are converted to JSON payloads) to **nd-shifty** over a websocket connection.
* `nd-shifty`, which is also a command-line script, then forwards those dumplings to all connected dumpling eaters (also using websockets).
* The dumpling eaters then process (and usually visualize) the dumplings they've received.

Everything is somewhat loosely-coupled so you can configure the pieces in
whatever way you want.  The dumplings are JSON so you can interact with them
in any language.  And websockets are used so that you can plug into the system
from anywhere.

Usually you'll have a single `nd-shifty` (the dumpling hub) running; one or
more `nd-snifty` (network sniffer) scripts running; and one or more
dumpling eaters (the visualizers) running.  The eaters can be Python scripts
written using the :class:`DumplingEater` class, or might instead be running in
a web browser (JavaScript) or elsewhere.

In pictures
-----------

Here's what it looks like with boxes and arrows:

.. image:: ../_static/in_the_box.svg
   :width: 600
   :align: center

