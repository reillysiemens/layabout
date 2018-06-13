Why Layabout?
=============

Why Layabout when the Slack `Events API`_ exists and there's already an
officially supported `events library`_?

Simply put, if you don't want to run a web server so Slack can call you when
events happen, then Layabout is for you.

Most `events`_ are supported by the Slack `RTM API`_ as well and Layabout
enables you to start handling events quickly without worrying about setting up
Flask, configuring a reverse proxy, acquiring an SSL certificate, and the
myriad other tasks that come with hosting a web app.

That said, if you can't afford to have a persistent WebSocket connection to the
Slack API, then you probably *do* want to use the official `events library`_.

.. _Events API: https://api.slack.com/events-api
.. _events library: https://github.com/slackapi/python-slack-events-api
.. _events: https://api.slack.com/events
.. _RTM API: https://api.slack.com/rtm
