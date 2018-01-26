.. automodule:: netdumplings

netdumplings
============

A framework for distributed network packet sniffing and processing.

netdumplings requires Python 3.5 or later. The source is on `GitHub`_. It can
be used as the back-end for tools like `netmomo`_ and `packscape`_.

.. toctree::
   :maxdepth: 1

   pages/installation
   pages/overview
   pages/quickstart
   pages/writing_chef
   pages/writing_eater
   pages/api
   pages/developing

Summary
-------

To use netdumplings you:

* Run one or more **packet sniffer kitchens** (using ``nd-sniff``), giving each one:
   * A PCAP-style packet filter
   * Some **dumpling chefs** you've written for packet processing and dumpling
     creation
* Run the **dumpling hub** (called ``nd-hub``) which forwards dumplings from
  the sniffers to the eaters
* Write **dumpling eaters** to display or process the dumpling contents

You can run the sniffer kitchens and dumpling eaters on as many different hosts
as you like; but you only run one instance of the hub. The sniffers, hub, and
eaters all communicate over WebSockets.


.. _GitHub: https://github.com/mjoblin/netdumplings
.. _netmomo: https://github.com/mjoblin/netmomo
.. _packscape: https://github.com/mjoblin/packscape

