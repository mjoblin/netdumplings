.. automodule:: netdumplings

Installation
============

Python 3.7 or higher is required.

To install netdumplings: ::

   pip install netdumplings

This should be enough for Linux and OS X. On Windows you may also need to `install Npcap`_.

Installing netdumplings gives you the ``netdumplings`` Python module with the
:class:`DumplingChef` and :class:`DumplingEater` classes.

Installation also provides the commandline tools: ``nd-sniff``, ``nd-hub``,
``nd-print``, ``nd-hubdetails``, and ``nd-hubstatus``.

All commandline tools support the ``--help`` flag for usage information.
Following is the help for the two main tools, ``nd-sniff`` and ``nd-hub``.

nd-sniff
--------
::

    Usage: nd-sniff [OPTIONS]

      A dumpling kitchen.

      Sniffs network packets matching the given PCAP-style filter and sends them to chefs for
      processing into dumplings. Dumplings are then sent to nd-hub for distribution to the dumpling
      eaters.

      This tool likely needs to be run as root, or as an Administrator user.

    Options:
      -n, --kitchen-name KITCHEN_NAME
                                      Dumpling kitchen name to assign to the sniffer  [default:
                                      default_kitchen]
      -h, --hub HOST:PORT             Address where nd-hub is receiving dumplings.  [default:
                                      localhost:11347]
      -i, --interface INTERFACE       Network interface to sniff.  [default: all]
      -f, --filter PCAP_FILTER        PCAP-style sniffer packet filter.  [default: tcp or udp or arp]
      -m, --chef-module PYTHON_MODULE
                                      Python module containing chef implementations. Multiple can be
                                      specified.  [default: netdumplings.dumplingchefs]
      -c, --chef CHEF_NAME            Chef (as found in a --chef-module) to deliver packets to.
                                      Multiple can be specified. Default is to send packets to all
                                      chefs.
      -p, --poke-interval SECONDS     Interval (in seconds) to poke chefs instructing them to send
                                      their interval dumplings.  [default: 5.0]
      -l, --chef-list                 List all available chefs (as found in the given --chef-module
                                      Python modules, or the default netdumplings.dumplingchefs
                                      module) and exit.
      --version                       Show the version and exit.
      --help                          Show this message and exit.

nd-hub
------
::

    Usage: nd-hub [OPTIONS]

      The dumpling hub.

      Sends dumplings received from all kitchens (usually any running instances of nd-sniff) to all
      dumpling eaters. All kitchens and eaters need to connect to the nd-hub --in-port or --out-port
      respectively.

    Options:
      -a, --address HOSTNAME     Address where nd-hub will send dumplings from.  [default: localhost]
      -i, --in-port PORT         Port to receive incoming dumplings from.  [default: 11347]
      -o, --out-port PORT        Port to send outgoing dumplings on.  [default: 11348]
      -f, --status-freq SECONDS  Frequency (in seconds) to send status dumplings.  [default: 5]
      --version                  Show the version and exit.
      --help                     Show this message and exit.


.. _install Npcap: https://nmap.org/npcap/#download