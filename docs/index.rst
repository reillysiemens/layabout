.. layabout documentation master file

Layabout
========

Release v\ |release|. (:ref:`Changelog <changelog>`)

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
    :target: http://python-slackclient.readthedocs.io/en/latest/?badge=latest
    :alt: Docs on Read the Docs

.. image:: https://img.shields.io/pypi/pyversions/layabout.svg?style=flat-square&label=python
    :target: https://pypi.python.org/pypi/layabout
    :alt: Python Version

.. image:: https://img.shields.io/pypi/v/layabout.svg?style=flat-square
    :target: https://pypi.org/project/layabout
    :alt: Layabout on PyPI

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
       # Automatically load app token from $SLACK_API_TOKEN and run!
       app.run(until=someone_leaves)
       print("Looks like someone left a channel!")

Installation
------------

To install **Layabout** use `pip`_ and `PyPI`_:

.. code-block:: bash

   pip install layabout

Features
--------

Not sold yet? Here's a list of features to sweeten the deal.

- Automatically load Slack API tokens from environment variables, provide
  them directly, or even bring your own :obj:`SlackClient`.
- Register multiple event handlers for one event.
- Register a single handler for multiple events by stacking decorators.
- Configurable application shutdown.
- Configurable retry logic in the event of lost connections.
- Lightweight. Depends only on the official Python `slackclient`_ library.

API Reference
-------------

.. toctree::
   :maxdepth: 2

   api

Project Info
------------

.. toctree::
   :maxdepth: 1

   why
   changelog
   license
   authors
   contributing
   code_of_conduct

.. note::

   Layabout **only** supports Python 3.6+ and will never be backported to
   Python 2. If you haven't moved over to Python 3 yet please consider the
   `many reasons to do so <http://www.asmeurer.com/python3-presentation/slides.html>`_.

.. _pip: https://pypi.org/project/pip/
.. _PyPI: https://pypi.org/
.. _slackclient: https://pypi.org/project/slackclient/
