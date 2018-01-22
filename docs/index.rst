.. automodule:: netdumplings

netdumplings
============

A framework for distributed network packet sniffing and processing.

netdumplings requires Python 3.5 or later. The source is on `GitHub`_. It can
be used as the back-end for tools like `netmomo`_ and `packscape`_, which are
implementations of *dumpling eaters*. netdumplings has been tested on OS X
and should work on Linux, and might work on Windows.

Contents
--------

.. toctree::
   :maxdepth: 1

   pages/overview
   pages/quickstart
   pages/writing_chef
   pages/writing_eater
   pages/api
   pages/developing

Summary
-------

To use netdumplings you:

* Run one or more **packet sniffer kitchens** (``nd-sniff``), giving each one:
   * A PCAP-style packet filter
   * Some **dumpling chefs** you've written for packet processing and dumpling
     creation
* Run the **dumpling hub** (``nd-hub``) which forwards dumplings from the
  sniffers to the eaters
* Write and run one or more **dumpling eaters** to display the dumpling
  contents

You can run the sniffer kitchens and dumpling eaters on as many different hosts
as you like (or on the same host if you want to keep things simple). You run
only one instance of the hub. The sniffers, hub, and eaters, all communicate
over WebSockets.

You write the dumpling chefs and dumpling eaters, but netdumplings comes with
some sample chefs and eaters so you can get started quickly.

Installation
------------

To install netdumplings: ::

   $ pip3 install netdumplings

You may want to do that in a virtualenv: ::

   $ python3 -m venv venv-netdumplings
   $ source venv-netdumplings/bin/activate
   $ pip install netdumplings

Installing netdumplings gives you the ``netdumplings`` Python module and the
commandline tools: ``nd-sniff``, ``nd-hub``, ``nd-print``, ``nd-hubdetails``,
and ``nd-hubstatus``. All tools support the ``--help`` flag for usage
information.


.. _GitHub: https://github.com/mjoblin/netdumplings
.. _netmomo: https://github.com/mjoblin/netmomo
.. _packscape: https://github.com/mjoblin/packscape

