.. _api:

API
===

.. automodule:: netdumplings

There are three main classes in the netdumplings API:

* You subclass :class:`DumplingChef` to write dumpling chefs.
* You subclass :class:`DumplingEater` to write dumpling eaters.
* :class:`Dumpling` instances are passed to the ``on_dumpling()`` handler of
  Python dumpling eaters.

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
   Dumpling instances are created automatically by dumpling kitchens, from the
   payload returned by a :class:`DumplingChef`.

   Dumpling instances are passed to the ``on_dumpling()`` handler of your
   dumpling eaters.

.. autoclass:: Dumpling
   :members:

DumplingDriver
^^^^^^^^^^^^^^

.. autoclass:: DumplingDriver
   :members:

Exception classes
^^^^^^^^^^^^^^^^^

.. autoexception:: NetDumplingsError

.. autoexception:: InvalidDumpling

.. autoexception:: InvalidDumplingPayload

