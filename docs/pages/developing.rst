Developing
==========

Configure a virtual environment, then:

Clone the source repository: ::

    $ git clone git://github.com/mjoblin/netdumplings.git
    $ cd netdumplings

Install the developer dependencies: ::

    $ pip install .[dev]

Run the linter: ::

    $ flake8

Run the unit tests: ::

    $ pytest

Coverage is generated in ``coverage_html/index.html``.

Build the documentation: ::

    $ cd docs
    $ make html

The documentation will be available at ``_build/html/index.html``.