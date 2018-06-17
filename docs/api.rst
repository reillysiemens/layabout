.. _api:

API Reference
=============

.. module:: layabout

Layabout
--------

.. autoclass:: layabout.Layabout
   :members:

Connectors
----------

In addition to a :obj:`slackclient.SlackClient` these classes may be
passed as a ``connector`` to :meth:`Layabout.run`.

.. autoclass:: layabout.EnvVar
   :show-inheritance:

.. autoclass:: layabout.Token
   :show-inheritance:


Exceptions
----------

.. autoexception:: layabout.LayaboutError
   :show-inheritance:

.. autoexception:: layabout.MissingSlackToken
   :show-inheritance:

.. autoexception:: layabout.FailedConnection
   :show-inheritance:
