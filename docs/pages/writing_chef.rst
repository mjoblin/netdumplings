.. _writing chef:

.. automodule:: netdumplings

Writing a dumpling chef
=======================

The mission of a dumpling chef is to receive network packets from ``nd-sniff``,
process those packets, and ultimately create dumplings.

To create a dumpling chef you subclass :class:`DumplingChef` and implement one
or both of ``packet_handler()`` and ``interval_handler()``. The packet handler
is called every time a packet is sniffed by ``nd-sniff``; and the interval
handler is called at regular intervals regardless of network packet activity.
Whatever the handlers ``return`` is automatically packaged into a dumpling by
``nd-sniff`` and sent to ``nd-hub`` which then sends it on to all the eaters.

Dumpling chefs can be housed in three places:

#. Python modules accessible via ``PYTHONPATH`` (e.g. ``module.with.chefs``)
#. Python modules located under the directory where ``nd-sniff`` is run from
#. Standalone Python files (e.g. ``/path/to/chefs.py``)

You tell ``nd-sniff`` where to find dumpling chefs using the ``--chef-module``
flag. You can specify this flag multiple times.

The following dumpling chef creates a dumpling for every DNS lookup. ::

    import time
    import netdumplings

    class DNSLookupChef(netdumplings.DumplingChef):
        def packet_handler(self, packet):
            # The incoming packet is a scapy packet object.
            # https://scapy.readthedocs.io

            # Ignore packets that we don't care about.
            if not packet.haslayer('DNS'):
                return

            # Determine the name of the host that was looked up.
            dns_query = packet.getlayer('DNS')
            query = dns_query.fields['qd']
            hostname = query.qname.decode('utf-8')

            # Generate a dumpling payload from the DNS lookup.
            dumpling_payload = {
                'lookup': {
                    'hostname': hostname,
                    'when': time.time(),
                }
            }

            # The handler is returning a dict, which will be automatically
            # converted into a dumpling and sent to nd-hub, which will then
            # forward it on to all the eaters.
            return dumpling_payload

If you put the above chef code into a file in your home directory called
``my_chefs.py`` then you can tell ``nd-sniff`` where to find it with: ::

   $ nd-sniff --chef-module ~/my_chefs.py

.. Important::
   The very first thing the above chef does in its ``packet_handler()`` method
   is check the incoming network packet to ensure it's a packet it actually
   cares about (in this case a DNS packet): ::

       if not packet.haslayer('DNS'):
           return

   Every chef gets every packet sniffed by ``nd-sniff``, and chefs aren't in
   control of the sniffer filter being used by ``nd-sniff``, so it's a good
   practice to check the packet right at the start to make sure it's one that
   the chef wants to process.

Packet and interval handlers
----------------------------

You don't have to send a dumpling for every packet your chef receives. For
example you may want your chef to receive and process multiple packets before
deciding it's ready to send a dumpling. You can instead have your chef do
something at regular time intervals by implementing an ``interval_handler()``
method in your dumpling chef.

Dumplings will only be sent as the result of a packet or interval handler being
called if that handler returns something. If a handler doesn't return anything,
or returns ``None``, then no dumpling will be produced. This means your chef
can process every packet with its packet handler, but only send dumplings with
its interval handler.

The packet format
-----------------

The packets passed to your packet handler are `scapy`_ packets.

If you're writing your own dumpling chefs then you're probably going to want
to get good and comfy with what scapy packets look like.  You can do that by
`using scapy to sniff some packets`_ and interrogate the results in an
interactive Python session.  Following is one way to get started with that.
Since we're sniffing packets, you may need to run this as an administrator on
your system. ::

    $ python
    >>> from scapy.all import sniff
    >>> packet = sniff(filter='tcp', count=1)
    >>> packet[0].show()

The ``filter`` argument is the same format that you're passing to ``nd-sniff``
with the ``--filter`` flag. You can read more about the format of the `filter
string here`_.

There's a series of articles called `Building Network Tools with Scapy`_ which
provides a lot of useful information, including part 4: `Looking at Packets`_.

Telling nd-sniff where to find your chefs
-----------------------------------------

By default ``nd-sniff`` will only look for chefs in the
``netdumplings.dumplingchefs`` module that comes with netdumplings.  You can
tell ``nd-sniff`` to find its chefs elsewhere with the ``--chef-module``
flag, which can be given either a Python module name or a path to a Python
file. Also, you can ask ``nd-sniff`` to tell you what chefs it knows about with
the ``--chef-list`` flag.

Chef locations
``````````````

You tell ``nd-sniff`` where to find your chefs with the ``--chef-module`` flag.
You can give this flag either a Python module name or a path to a standalone
Python file. You can specify the flag multiple times. For example, the
following tells ``nd-sniff`` to look for chefs in the ``mychefs`` module and
in a file called ``~/chefs/mychefs.py``: ::

    $ nd-sniff --chef-module mychefs --chef-module ~/chefs/mychefs.py

When specifying a Python module name, the module must be importable. The
easiest way to do this is to put the chefs in a ``.py`` file named the same as
the module name and placed in the same directory as where ``nd-sniff`` is
being run from.

Listing found chefs
```````````````````

You can ask ``nd-sniff`` to list all the chefs it can find in the given chef
modules by specifying the ``--chef-list`` flag: ::

    $ nd-sniff --chef-list \
        --chef-module mychefs \
        --chef-module ~/chefs/mychefs.py \
        --chef-module netdumplings.dumplingchefs

    mychefs
      MyDNSChef

    ~/chefs/mychefs.py
      MyOtherChef
      YetAnotherChef

    netdumplings.dumplingchefs
      ARPChef
      DNSLookupChef
      PacketCountChef

Example chefs
-------------

netumplings comes with some example chefs in the ``netdumplings.dumplingchefs``
module. You can see their source code here:

* `ARPChef`_
* `DNSLookupChef`_
* `PacketCountChef`_


.. _scapy: https://scapy.readthedocs.io
.. _ARPChef: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/dumplingchefs/arpchef.py
.. _DNSLookupChef: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/dumplingchefs/dnslookupchef.py
.. _PacketCountChef: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/dumplingchefs/packetcountchef.py
.. _using scapy to sniff some packets: http://scapy.readthedocs.io/en/latest/usage.html#sniffing
.. _filter string here: http://www.tcpdump.org/manpages/pcap-filter.7.html
.. _Building Network Tools with Scapy: https://thepacketgeek.com/series/building-network-tools-with-scapy/
.. _Looking at Packets: https://thepacketgeek.com/scapy-p-04-looking-at-packets/
