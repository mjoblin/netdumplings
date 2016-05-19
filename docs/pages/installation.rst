.. _installation:
.. automodule:: netdumplings

Installation
============

NetDumplings requires `Python 3.5`_ or higher.

Using pip
---------

You can install NetDumplings (including all the command-line scripts and the
associated Python modules) with pip: ::

    $ pip install netdumplings

You may want to to that in a `virtual environment`_: ::

    $ virtualenv --python=python3.5 nd-env
    $ source nd-env/bin/activate
    $ pip install netdumplings

Manually from GitHub
--------------------

The full source code is on `GitHub`_ which you can clone into your local
environment: ::

    $ git clone git://github.com/mjoblin/netdumplings.git

You can then install NetDumplings from your local copy: ::

    $ cd netdumplings
    $ python setup.py install


.. _Python 3.5: https://www.python.org/downloads/
.. _virtual environment: http://docs.python-guide.org/en/latest/dev/virtualenvs/
.. _GitHub: https://github.com/mjoblin/netdumplings

