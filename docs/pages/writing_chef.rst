.. automodule:: netdumplings

Writing a dumpling chef
=======================

The mission of a dumpling chef is to receive network packets from `nd-snifty`
and process them to create dumplings.  To write your own dumpling chef you need
to:

1. Create your chef by subclassing :class:`DumplingChef`.
#. Tell `nd-snifty` where to find your chef so it can feed your chef the sniffed packets.

A dumpling chef will implement one or both of the ``packet_handler()`` and
``interval_handler()`` methods.  ``packet_handler()`` is invoked every time
a packet is sniffed by `nd-snifty`; and ``interval_handler()`` is invoked
at regular intervals regardless of network packet activity.

Subclassing :class:`DumplingChef`
---------------------------------

Here's an example chef which processes DNS packets, sending a dumpling for
every DNS-related packet it receives: ::

    from netdumplings import DumplingChef, DumplingDriver


    class MyDNSChef(DumplingChef):
        def packet_handler(self, packet):
            # Our packet will always be a scapy packet.

            # We ignore the packet if it's not related to DNS.
            if not packet.haslayer("DNS"):
                return

            # Extract the host name that's being looked up.
            dns_query = packet.getlayer("DNS")
            query = dns_query.fields["qd"]
            hostname = query.qname.decode("utf-8")

            # Strip the trailing period.
            if hostname.endswith("."):
                hostname = hostname[:-1]

            # Make our dumpling payload.  This is just a Python dict
            # which contains the name of the host being looked up.
            # It's up to the eaters to understand this payload.
            payload = {"hostname": hostname}

            # Send the dumpling to all the eaters.  send_dumpling
            # takes care of converting the payload to JSON.
            self.send_dumpling(
                payload=payload, driver=DumplingDriver.packet)

In the simplest case all you need to do is define a ``packet_handler()`` method
which receives a network packet as an argument and calls
``self.send_dumpling()`` when it's done processing the packet.

.. Important::
   The very first thing the above chef does in its ``packet_handler()`` method
   is check the incoming network packet to ensure it's a tasty packet it
   actually cares about (in this case a DNS packet): ::

       if not packet.haslayer("DNS"):
           return

   Every chef gets every packet sniffed by `nd-snifty`, and chefs aren't in
   control of the sniffer filter being used by `nd-snifty`, so checking the
   packet right at the start is a best practice to avoid problems resulting
   from unexpected packets, and to improve performance.

You don't have to send a dumpling for every packet your chef receives (for
example you may want your chef to receive and process multiple packets before
deciding it's ready to send a dumpling).  You can also have your chef do
something at regular time intervals by implementing an ``interval_handler()``
method in your dumpling chef.

Note that when your chef calls ``self.send_dumpling()`` it's required to pass
either ``driver=DumplingDriver.packet`` or ``driver=DumplingDriver.interval``.
This is so the dumpling eaters know what motivated the dumpling's creation.
When ``packet_handler()`` calls ``self.send_dumpling()`` it will normally
specify ``DumplingDriver.packet`` whereas ``interval_handler()`` will specify
``DumplingDriver.interval``.

See the chefs distributed with NetDumplings for more examples:

* `ARPChef`_
* `DNSLookupChef`_
* `PacketCountChef`_

Telling nd-snifty about your chef
---------------------------------

By default `nd-snifty` will only look for chefs in the
``netdumplings.dumplingchefs`` module that comes with NetDumplings.  You can
tell `nd-snifty` to find its chefs elsewhere with the ``--chef-modules``
flag; and you can ask `nd-snifty` to tell you what chefs it knows about with
the ``--chef-list`` flag: ::

    $ nd-snifty --chef-list

    netdumplings.dumplingchefs
      ARPChef
      DNSLookupChef
      PacketCountChef

Here's how you can tell `nd-snifty` where to find your chefs: ::

    $ nd-snifty --chef-modules mychefs

For this to work you need to ensure that ``mychefs`` is a module visible to
Python.  A simple way to achieve this is to have a ``mychefs.py`` file in the
same directory you're running `nd-snifty` from.

You can test whether `nd-snifty` is able to find your chefs or not, alongside
the default NetDumplings chefs, like so: ::

    $ nd-snifty --chef-list \
        --chef-modules mychefs,netdumplings.dumplingchefs

    mychefs
      MyDNSChef

    netdumplings.dumplingchefs
      ARPChef
      DNSLookupChef
      PacketCountChef

Doing it for realzies
---------------------

The following commands should get you started writing your own dumpling chefs.
If you installed NetDumplings in a virtual environment then be sure to have
that environment activated in all the terminals you use for this.

First open a terminal and create your chef module: ::

    $ vi mychefs.py
        [paste all of the above MyDNSChef example and save the file]
    $ nd-snifty --chef-list --chef-modules mychefs

If you see your new chef listed then congratulations!  You've just created your
own chef.

Next, in a different terminal start `nd-shifty`: ::

    $ nd-shifty

Now go back to the terminal you made your chef module in, and kick your new chef
into action using `nd-snifty`: ::

    $ nd-snifty --filter "tcp or udp" --chef-modules mychefs \
        --chefs MyDNSChef

.. Important::
   `nd_snifty` is a packet sniffer so it needs to be run as root,
   or the equivalent in your particular environment.

A good way to see the results is to use `nd-printer` in another terminal to
eat (and display) your dumplings: ::

    $ nd-printer --chefs MyDNSChef

Remember that this example chef is sniffing for DNS traffic so you may need
to hop into a browser and navigate to a website for some DNS traffic to be
created -- otherwise `nd-printer` won't receive any dumplings to print.

Getting comfy with scapy packets
--------------------------------

If you're writing your own dumpling chefs then you're probably going to want
to get good and comfy with scapy packets.  You can do that by
`using scapy to sniff some packets`_ and interrogate the results in an
interactive Python session.  Following is one way to get started with that.
Remember to have your virtal environment activated (if you're using one); and
since we're sniffing packets, you'll need to run this as an administrator on
your system. ::

    $ python
    >>> from scapy.all import sniff
    >>> packet = sniff(filter="tcp", count=1)
    >>> packet[0].show()

The ``filter`` argument is the same format that you're passing to `nd-snifty`
with the ``--filter`` flag.  You can read more about the format of the `filter
string here`_.

There's a series of articles called `Building Network Tools with Scapy`_ which
provides a lot of useful information, including part 4: `Looking at Packets`_.

Scapy is superior legit.

.. _ARPChef: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/dumplingchefs/arpchef.py
.. _DNSLookupChef: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/dumplingchefs/dnslookupchef.py
.. _PacketCountChef: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/dumplingchefs/packetcountchef.py
.. _using scapy to sniff some packets: http://www.secdev.org/projects/scapy/doc/usage.html#sniffing
.. _filter string here: http://www.tcpdump.org/manpages/pcap-filter.7.html
.. _Building Network Tools with Scapy: https://thepacketgeek.com/series/building-network-tools-with-scapy/
.. _Looking at Packets: https://thepacketgeek.com/scapy-p-04-looking-at-packets/
