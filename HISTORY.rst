.. :changelog:

Release History
---------------

0.3.0 (2018-01-27)
++++++++++++++++++

This release introduces breaking changes.

* Renamed CLI tools
    * ``nd-shifty`` is now ``nd-hub``
    * ``nd-snifty`` is now ``nd-sniff``
    * ``nd-printer`` is now ``nd-print``
    * ``nd-info`` is now ``nd-hubdetails``
    * ``nd-status`` is now ``nd-hubstatus``
* Changed behavior of commandline tools (new and changed flags, colorized
  output)
* DumplingChefs now ``return`` dumpling payloads from their packet and interval
  handlers rather than calling ``send_dumpling()``
* The ``--chef-module`` flag to ``nd-sniff`` now supports standalone Python
  files
* The ``DumplingEater.on_dumpling()`` handler is now passed a ``Dumpling``
  instance not a dumpling dict.
* The Dumpling class now has a ``from_json()`` factory method for creating a
  Dumpling instance from a JSON-serialized dumpling
* DumplingKitchens now take care of creating and sending Dumplings created from
  the DumplingChef handler payloads
* Changed default sniffer filter to ``‘tcp or udp or arp’`` to meet the needs
  of the sample chefs
* Changed dumpling ``creation_time`` from float microseconds to float
  milliseconds
* DumplingEater’s ``chefs`` parameter renamed to ``chef_filter``
* Changed SystemStatus dumpling payload:
    * ``”total_dumplings_sent”`` renamed to ``“total_dumplings_out”``
    * added ``”total_dumplings_in”``
    * ``”info_from_shifty”`` (under ``”dumpling_eaters”`` and
      ``”dumpling_kitchens”``) renamed to ``”info_from_hub”``
* Renamed InvalidDumplingError to InvalidDumpling and added
  InvalidDumplingPayload exception
* Removed ``commandline_helper()`` from DumplingEater (no longer useful after
  the migration to ``click``)
* Removed ability to configure kitchens and chefs with an external config file
  (it added unnecessary complexity)
* Simplified logging support
* Allowed for logging config JSON to be overridden with the
  ``NETDUMPLINGS_LOGGING_CONFIG`` environment variable
* Changed logging timestamps to GMT, ``YYYY-MM-DDThh:mm:ss.sss``
* Added a ``__repr__()`` to classes
* Replaced ``argparse`` with ``click`` for commandline argument parsing
* Added developer dependencies: ``flake8`` for linting and ``pytest`` for tests
* Added unit tests
* Added type hints
* Updated documentation

0.2.0 (2017-10-15)
++++++++++++++++++

* snifty now maintains more information on the chefs it's sending packets to
* Added time to ARPChef dumpling payload
* Added time of last lookup to DNSLookupChef
* Changed time format to float milliseconds
* Minor code style and documentation tweaks

0.1.0 (2016-11-05)
++++++++++++++++++

* First actual github release (0.0.1 was really just the first git commit)

0.0.1 (2016-04-22)
++++++++++++++++++

* Initial release
