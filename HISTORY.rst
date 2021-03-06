.. :changelog:

Release History
---------------

0.5.1 (2020-07-19)
++++++++++++++++++

* Remove dependency on netifaces
* Improve errors when attempting to sniff on unknown interfaces

0.5.0 (2020-07-19)
++++++++++++++++++

* Updated required Python version from 3.6 to 3.7
* Tweaks to get things mostly working out-of-the-box on Windows
* Tweaks to async handling (this likely requires a full modernization overhaul)
* Have ``DNSLookupChef`` quietly ignore DNS packets without a ``qd`` field
* Have ``nd-sniff`` produce some startup initialization output
* Documentation tweaks
* Updated websockets and scapy to latest versions

0.4.0 (2019-06-09)
++++++++++++++++++

Updates to dependencies

* Changed to websockets v7 to fix security warnings
* Switched to main scapy package now that it supports python 3
* Updated docs to explain that nd-sniff might need to be run as root

0.3.2 (2018-01-27)
++++++++++++++++++

* Reverting README back to rst from markdown (to support pypi)

0.3.1 (2018-01-27)
++++++++++++++++++

* Now requires Python 3.6 or higher
* Updates to get documentation to build on readthedocs

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
