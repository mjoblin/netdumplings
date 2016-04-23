.. automodule:: netdumplings

Why NetDumplings?
=================

Networks are f-r-e-a-k-i-n-g cool and network protocols and packets are super
interesting.  There's bazillions of packets barreling down your cables and
flying through the wifi in your living room but they're mostly invisible.

Wouldn't it be cool to find interesting, creative, and possibly even useful
ways to display what's happening in all those packets?  That's what
NetDumplings is all about.

NetDumplings provides some Python classes and command-line scripts which you
can build on to do things like:

* Print information about your network packets to a terminal.
* Instruct your Raspberry Pi to spin that `smooooth` disco ball based on your network packets.
* Use a graphics library to build dynamic 3D environments based on your network packets.
* Use an audio library to do some sweet algorithmic music composition based on your network packets.
* Whatever else you want to do based on your network packets.

OK you'll have a little work to do to get most of those up and running, but
that's the fun part.  Hopefully NetDumplings can help you get started.

Here's an example of a dumpling eater running inside a web browser, displaying
dumplings from a :class:`~dumplingchefs.PacketCountChef` (`see source`_) and a
:class:`~dumplingchefs.DNSLookupChef` (`more source`_), as well as some
SystemStatus dumplings made by `nd-shifty`:

.. image:: ../_static/webnom.gif
   :width: 700
   :align: center

You can `see the source code`_ for this web-based dumpling eater, and you can
get it running on your system by following the instructions in :doc:`run_it`

.. _see source: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/dumplingchefs/packetcountchef.py
.. _more source: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/dumplingchefs/dnslookupchef.py
.. _see the source code: https://github.com/mjoblin/netdumplings/blob/master/netdumplings/webnom/
