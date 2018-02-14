Layabout
========

A small event handling library on top of the Slack RTM API.

- Documentation: TODO
- GitHub: https://github.com/reillysiemens/layabout
- PyPi: TODO

What's in the Box?
------------------

- 🎉 The most fun you've had interacting with Slack in a while.
- 🐍 Python 3.6+ support
- 🆓 Free software: ISC License

Features
--------

- Automatically load Slack API tokens from environment variables or provide
  them directly.
- Register multiple event handlers for one event.
- Register a single handler for multiple events by stacking decorators.
- Configurable application shutdown.
- Configurable retry logic in the event of lost connections.
- Lightweight. Depends only on the official Python `slackclient`_ library.

Installation
------------

.. code-block:: bash

   pip install git+https://github.com/reillysiemens/layabout.git@master

Quickstart
----------

Here's a quick example of an echo bot implemented with Layabout:

.. code-block:: python

   from layabout import Layabout

   layabout = Layabout('app')


   @layabout.handle('message')
   def echo(slack, event):
       """ Echo all messages seen by the app. """
       channel = event['channel']
       message = event['text']
       subtype = event.get('subtype')

       # Avoid an infinite loop of echoing our own messages.
       if subtype != 'bot_message':
           slack.rtm_send_message(channel, message)

   layabout.run()

Here's another example that uses Layabout to debug all Slack events seen by a
bot until someone leaves a channel:

.. code-block:: python

   from pprint import pprint
   from layabout import Layabout

   layabout = Layabout('app')


   @layabout.handle('*')
   def debug(slack, event):
       """ Pretty print every event seen by the app. """
       pprint(event)


   def someone_leaves(events):
       """ Return False if a member leaves, otherwise True. """
       return not any(e['type'] == 'member_left_channel' for e in events)

   layabout.run(until=someone_leaves)
   print('Looks like someone left a channel!')

Code of Conduct
---------------

Everyone interacting with the Layabout project's codebase is expected to follow
the `Code of Conduct`_.

.. _slackclient: https://github.com/slackapi/python-slackclient
.. _Code of Conduct: https://github.com/reillysiemens/layabout/blob/master/CODE_OF_CONDUCT.rst
