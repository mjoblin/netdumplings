.. automodule:: netdumplings

NetDumplings
============

NetDumplings helps you build your own computer network visualizations.  It lets
you sniff your network for interesting packets and display the results in any
way you please.  What NetDumplings listens for -- and how that information is
displayed -- is up to you.

NetDumplings requires `Python 3.5`_ and relies on the fantastic `scapy3k`_
and `websockets`_ modules.  The source is on `GitHub`_.

What's a dumpling?
------------------

A dumpling is a description of network activity, defined by you and encoded in
JSON.  It can contain anything you want based on one or more network packets
sniffed on your network.  You control the dumpling contents through the
:class:`DumplingChef` objects you write, as well as how those contents are
displayed by the **dumpling eaters** you write.  You can make as many dumplings
as you want; and since dumplings are just JSON data sent to eaters over
websockets, you could even write your eaters in JavaScript and display them in
a web browser.

OK so how do I visualize my network?
------------------------------------

1. Write :class:`DumplingChef` Python objects to interpret your network packets and make dumplings.
#. Write **dumpling eaters** (in any language) to visualize the information in the dumplings you've made.  If you're using Python then you can use the :class:`DumplingEater` helper class.
#. Run `nd-snifty` (a command-line script included with NetDumplings) to sniff your network for the packets your chefs want to see.
#. Run `nd-shifty` (also a command-line script included with NetDumplings) to forward the dumplings from `nd-snifty` to the eaters.

Tell me more!
-------------

.. toctree::
   :maxdepth: 1

   pages/why_netdumplings
   pages/tech_summary

**Running it:**

.. toctree::
   :maxdepth: 1

   pages/installation
   pages/in_the_box
   pages/run_it

**Developer documentation:**

.. toctree::
   :maxdepth: 1

   pages/more_details

.. toctree::
   :maxdepth: 2

   pages/api

.. toctree::
   :maxdepth: 1

   pages/writing_chef
   pages/writing_eater

.. toctree::
   :maxdepth: 1

   pages/config
   pages/resources

.. _Python 3.5: https://www.python.org/downloads/
.. _scapy3k: https://github.com/phaethon/scapy
.. _websockets: https://websockets.readthedocs.org/en/stable/
.. _GitHub: https://github.com/mjoblin/netdumplings

