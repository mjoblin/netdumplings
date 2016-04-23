.. _more-details:

.. automodule:: netdumplings

More details
============

.. contents::
   :depth: 1
   :local:

The big picture
---------------

NetDumplings is a small collection of command-line scripts and Python classes
allowing you to:

1. Watch for specific packets on your network.
#. Process those packets in any way you please using the :class:`~DumplingChef` class, which uses the contents of your network packets to make dumplings.
#. Send those dumplings off to your own dumping eaters to display the contents however you like.

How about an example?
---------------------

Sure!  You could configure NetDumplings to listen for all ``port 53`` (DNS)
packets on your network.  Those packets would then be passed to your
:class:`~DumplingChef` which looks at each packet to see if it's able to
extract the name of the remote host being looked up.  Every time it found a
remote host lookup the chef could then create a new dumpling (containing just
the host name being looked up) which gets shipped off to your dumpling eater.
The eater could then (if it's a command-line script) print the host name to the
terminal; or if it's an eater running a web browser it could display the host
name in the browser window.

What are the various pieces?
----------------------------

There's four main parts to NetDumplings:

1. `nd-snifty` (the packet sniffer).  This comes with NetDumplings.
2. The :class:`~DumplingChef` class (which makes the delicious dumplings).  You'll be writing these.
3. `nd-shifty` (the dumpling hub; a connection between `nd-snifty` and the dumpling eaters).  This comes with NetDumplings.
4. The dumpling eaters (with their convenience :class:`~DumplingEater` class).  You'll be writing these.

Parts 1 & 2: nd-snifty and the dumpling chefs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Everything starts with `nd-snifty` which sniffs network packets and passes them
off to the :class:`~DumplingChef` objects for processing.  The
:class:`~DumplingChef` objects treat the network packets as ingredients which
they can use to make their tasty dumplings.  When a dumpling is ready it gets
sent to `nd-shifty` (the dumpling hub).

`nd-snifty` uses the `scapy3k`_ packet sniffer, so it supports the same
sniffing `filter syntax`_ you may already be familiar with.

Parts 3 & 4: nd-shifty and the dumpling eaters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

`nd-shifty` is responsible for receiving freshly-made dumplings and shipping
them off to all the eager dumpling eaters.

When a dumpling eater receives a new dumpling from `nd-shifty` it then
decides what it wants to to with it.  It might print the contents of the
dumpling to the console; or it might paint lips on it and call it Desmond.

.. Caution::
   Their names are similar but `nd-snifty` and `nd-shifty` are two very
   different command-line scripts.  One sniffs and the other shifts.

The dumplings
^^^^^^^^^^^^^

A dumpling is really just JSON data which is passed from `nd-snifty` to the
eaters via websocket connections to `nd-shifty`.  A dumpling's contents is
entirely up to you, but it will usually be created using the information
contained in one or more network packets.

Where you come in
^^^^^^^^^^^^^^^^^

You can write your own :class:`~DumplingChef` objects to create dumplings, and
you can also write your own dumpling eater scripts using the
:class:`~DumplingEater` class.  And since dumplings are just JSON data sent to
eaters over websockets you could even write your eaters in JavaScript and
display network activity in a Web browser.

Cool story bro, can I see a picture?
------------------------------------

Yes you can!  Here you go:

.. image:: ../_static/layout_simple.svg
   :width: 450
   :align: center

*Everything in orange is something you're likely to be creating yourself
(although you can also make your own sniffers and dumpling hubs if you like).*

`nd-shifty` takes care of sniffing the network -- in this case using the
``port 53`` filter (port 53 is used by DNS requests).  Every packet matching
that filter is passed to the :class:`~DumplingChef`.  The :class:`~DumplingChef`
then decides whether or not to make a dumpling (it might make one for every
packet it receives; or it might decide to accumulate a few packets before
making its dumpling).  When it's finished making a dumpling it then sends it
out and moves on to waiting for more packets.

`nd-shifty` receives the new dumpling (over a websocket connection to
`nd-snifty`).  It then immediately sends that dumpling out to the dumpling
eater (over another websocket connection).

The dumpling eater then receives the dumpling and does whatever it wants with
it.  Maybe it will display its contents somehow, perhaps printing it to the
console, or if it's a Web-based eater it may render the contents in a browser.

What does a dumpling look like?
-------------------------------

Dumplings are just JSON documents.  The :class:`~DumplingChef` defines the
``payload`` section (which can be anything that can be serialized into JSON --
usually a Python dict) and `nd-snifty` will automatically generate the
``metadata`` section.

Here's an example: ::

    {
        "metadata": {
            "chef": "chef name",
            "kitchen": "kitchen name",
            "creation_time": 1459632453037.908,
            "driver": "packet"
        },
        "payload": {
            "lookup": {
                "hostname": "srirachamadness.com"
            }
        }
    }

*Remember that the payload section is determined entirely by your DumplingChef.
It usually contains information gleaned from the received network packets but
doesn't have to!*

Some quick notes about ...
--------------------------

... nd-snifty
^^^^^^^^^^^^^

`nd-snifty` is a command-line script.  You tell it what network packets to
listen for via the ``--filter`` argument.  You can also tell it what
:class:`~DumplingChef` instances it should talk to via ``--chefs`` (it will
default to all of them).

The filter you pass to `nd-snifty` should adhere to this `filter syntax`_
(there's some examples listed at the end of that page).

.... dumpling chefs
^^^^^^^^^^^^^^^^^^^

`nd-snifty` will send *every* packet which matches its sniffer filter to every
:class:`~DumpingChef` instance it's talking to.  It's up to each
:class:`~DumplingChef` to decide whether it cares about the packet or not.
The packets themselves are the exact same packet objects that the
`scapy sniff function`_ creates.

... nd-shifty
^^^^^^^^^^^^^

`nd-shifty` is also a command-line script.  It receives dumplings from one of
more instances of `nd-snifty` and forwards them to any connected dumpling
eaters.

An additional feature of `nd-shifty` is that it makes and sends its own
status dumplings thanks to its own chef called ``SystemStatusChef``.  These
dumplings are not created by a :class:`~DumplingChef` instance.  They're
created by `nd-shifty` itself for the purpose of announcing its current status
to any interested eaters.

... dumpling eaters
^^^^^^^^^^^^^^^^^^^

When a dumpling eater is written using the :class:`~DumplingEater` class,
it can optionally specify which :class:`~DumplingChef` dumplings it wants to
receive.  If it doesn't specify then it will receive every dumpling from every
:class:`~DumplingChef`.

Can I have multiple Chefs and Eaters?
-------------------------------------

Absolutely!  You can have as many :class:`~DumplingChef` instances and
dumpling eaters as you want, and you can also have as many running instances
of `nd-snifty` and `nd-shifty` as you want (although usually a single
`nd-shifty` will be enough).

Here's a more complex example:

.. image:: ../_static/layout_more_complex.svg
   :width: 600
   :align: center

The above example shows two running `nd-snifty` instances, where
**packet count kitchen** is listening for ``tcp or udp`` packets and
**dns kitchen** is listening for ``port 53`` packets.  **packet count kitchen**
is sending packets to two registered chefs (PacketCountChef and ICMPCountChef);
and **dns kitchen** is sending packets to a single chef (DNSLookupChef).

All the dumplings created by all the chefs are sent to a single `nd-shifty`
instance, which forwards every dumpling to every dumpling eater.

.. Important::
   It's assumed that the dumpling eaters know how to interpret the dumpling
   payloads made by any of the chefs whose dumplings they want to act on.

An alternative approach
^^^^^^^^^^^^^^^^^^^^^^^

An alternative approach to the above example would be have a single `nd-snifty`
running and listening for just ``tcp or udp``, in which case the DNSLookupChef
could also be attached to that instance of `nd-snifty` and it would just ignore
any packets that weren't destined for port 53 (by interrogating each incoming
packet for its port number).

How you configure your `nd-snifty` instances, chefs, and eaters, is entirely
up to you.  You could even have different `nd-snifty` instances listening on
different network interfaces, and potentially running on entirely separate
computers. You can also have eaters running anywhere you like and be written in
whatever combination of languages you like; so long as they know how to talk to
`nd-shifty` over a websocket.

.. _scapy3k: https://github.com/phaethon/scapy
.. _filter syntax: http://www.tcpdump.org/manpages/pcap-filter.7.html
.. _scapy sniff function: http://phaethon.github.io/scapy/api/usage.html?highlight=prn#sniffing

