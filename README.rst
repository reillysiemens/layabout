Layabout
========

.. image:: https://img.shields.io/travis/reillysiemens/layabout/master.svg?style=flat-square&label=build
    :target: https://travis-ci.org/reillysiemens/layabout
    :alt: Unix build status on Travis CI

.. image:: https://img.shields.io/coveralls/reillysiemens/layabout/master.svg?style=flat-square&label=coverage
    :target: https://coveralls.io/github/reillysiemens/layabout?branch=master
    :alt: Code coverage on Coveralls

.. image:: https://img.shields.io/badge/license-ISC-blue.svg?style=flat-square
    :target: https://github.com/reillysiemens/layabout/blob/master/LICENSE
    :alt: ISC Licensed

.. image:: https://img.shields.io/readthedocs/layabout/latest.svg?style=flat-square
    :target: http://layabout.readthedocs.io/en/latest/
    :alt: Docs on Read the Docs

.. image:: https://img.shields.io/pypi/pyversions/layabout.svg?style=flat-square&label=python
    :target: https://pypi.org/project/layabout
    :alt: Python Version

.. image:: https://img.shields.io/pypi/v/layabout.svg?style=flat-square
    :target: https://pypi.org/project/layabout
    :alt: Layabout on PyPI

⚠️ Layabout is `deprecated`_. There will be no further support. ⚠️
==================================================================

**Layabout** is a small event handling library on top of the Slack RTM API.

.. code-block:: python

   from pprint import pprint
   from layabout import Layabout

   app = Layabout()


   @app.handle('*')
   def debug(slack, event):
       """ Pretty print every event seen by the app. """
       pprint(event)


   @app.handle('message')
   def echo(slack, event):
       """ Echo all messages seen by the app except our own. """
       if event.get('subtype') != 'bot_message':
           slack.rtm_send_message(event['channel'], event['text'])


   def someone_leaves(events):
       """ Return False if a member leaves, otherwise True. """
       return not any(e.get('type') == 'member_left_channel'
                      for e in events)


   if __name__ == '__main__':
       # Automatically load app token from $LAYABOUT_TOKEN and run!
       app.run(until=someone_leaves)
       print("Looks like someone left a channel!")

Installation
------------

To install **Layabout** use `pip`_ and `PyPI`_:

.. code-block:: bash

   pip install layabout

What's It Good For?
-------------------

You can think of **Layabout** as a micro framework for building Slack bots.
Since it wraps Slack's RTM API it does best with tasks like interacting with
users, responding to channel messages, and monitoring events. If you want more
ideas on what you can do with it check out the `examples`_.

Features
--------

Not sold yet? Here's a list of features to sweeten the deal.

- Automatically load Slack API tokens from environment variables, provide
  them directly, or even bring your own SlackClient.
- Register multiple event handlers for one event.
- Register a single handler for multiple events by stacking decorators.
- Configurable application shutdown.
- Configurable retry logic in the event of lost connections.
- Lightweight. Depends only on the official Python `slackclient`_ library.

Code of Conduct
---------------

Everyone interacting with the Layabout project's codebase is expected to follow
the `Code of Conduct`_.

.. _deprecated: https://layabout.readthedocs.io/en/latest/deprecation.html
.. _pip: https://pypi.org/project/pip/
.. _PyPI: https://pypi.org/
.. _examples: https://github.com/reillysiemens/layabout/tree/master/examples
.. _slackclient: https://github.com/slackapi/python-slackclient
.. _Code of Conduct: https://github.com/reillysiemens/layabout/blob/master/CODE_OF_CONDUCT.rst
