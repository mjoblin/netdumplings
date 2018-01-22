.. _api:

API
===

.. automodule:: netdumplings

You subclass the :class:`DumplingChef` class to write dumpling chefs. When
writing dumpling eaters in Python, you can subclass :class:`DumplingEater`.

:class:`Dumpling` objects are passed to the ``on_dumpling()`` handler of
Python DumplingEaters.

DumplingChef
^^^^^^^^^^^^

.. Note::
   Implement your own dumpling chefs by subclassing :class:`DumplingChef`. Your
   dumpling chef implementations are passed to ``nd-sniff`` with the
   ``--chef-module`` flag. See :ref:`Writing a dumpling chef <writing chef>`.

.. autoclass:: DumplingChef
   :members:

DumplingEater
^^^^^^^^^^^^^

.. Note::
   Implement your own dumpling eaters by subclassing :class:`DumplingEater`.
   See :ref:`Writing a dumpling eater <writing eater>`.

.. autoclass:: DumplingEater
   :members:

Dumpling
^^^^^^^^

.. Note::
   :class:`Dumpling` instances are passed into the ``on_dumpling()`` handler of
   your dumpling eaters.

.. autoclass:: Dumpling
   :members:

Exception classes
^^^^^^^^^^^^^^^^^

.. autoexception:: netdumplings.exceptions.NetDumplingsError

.. autoexception:: netdumplings.exceptions.InvalidDumpling

.. autoexception:: netdumplings.exceptions.InvalidDumplingPayload

