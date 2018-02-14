import os
import time
import logging
from typing import Any, DefaultDict, Callable, List, Tuple
from inspect import signature
from functools import wraps
from collections import defaultdict

from slackclient import SlackClient

# TODO: This is a dependency of slackclient needed for exception handling. In
# the future, we might be able to remove this. For now we don't want to declare
# it as an explicit dependency.
from websocket import WebSocketConnectionClosedException

__author__ = 'Reilly Tucker Siemens'
__email__ = 'reilly@tuckersiemens.com'
__version__ = '1.0.0b'

# Type alias for the complex type signature of the handlers defaultdict.
Handlers = DefaultDict[str, List[Tuple[Callable, dict]]]

log = logging.getLogger(__name__)


class LayaboutError(Exception):
    """ Base error for all Layabout exceptions. """


class MissingSlackToken(LayaboutError):
    """ Raised if a Slack API token could not be found. """


class FailedConnection(LayaboutError, ConnectionError):
    """
    Raised if the Slack client could not connect to the Slack API.

    Inherits from both :obj:`LayaboutError` and the built-in
    :obj:`ConnectionError` for convenience in exception handling.
    """


class Layabout:
    """
    An event handler on top of the Slack RTM API.

    Args:
        name: A unique name for this :obj:`Layabout` instance.
        env_var: The environment variable to try to load a Slack API token
            from. Defaults to ``SLACK_API_TOKEN``.

    Attributes:
        name: A unique name for this :obj:`Layabout` instance.
        slack (SlackClient): A :obj:`slackclient.SlackClient` instance.
            Initially :obj:`None`, the attribute is set after calling the
            :obj:`Layabout.connect` or :obj:`Layabout.run`
            methods.

    Example:

        .. code-block:: python

           from layabout import Layabout

           layabout = Layabout('app')


           @layabout.handle('message')
           def echo(slack, event):
               \"\"\" Echo all messages seen by the app. \"\"\"
               channel = event['channel']
               message = event['text']
               subtype = event.get('subtype')

               # Avoid an infinite loop of echoing our own messages.
               if subtype != 'bot_message':
                   slack.rtm_send_message(channel, message)

           layabout.run()
    """
    def __init__(self, name: str, env_var: str = 'SLACK_API_TOKEN') -> None:
        # TODO: Consider keyword only arguments.
        self.name = name
        self._env_var = env_var
        self._token: str = None
        self.slack: SlackClient = None
        self._handlers: Handlers = defaultdict(list)

    def handle(self, type: str, kwargs: dict = None) -> Callable:
        """
        Register an event handler with the :obj:`Layabout` instance.

        Args:
            type: The name of a Slack RTM API event to be handled. As a
                special case, although it is not a proper RTM event, ``*`` may
                be provided to handle all events. For more information about
                available events see the
                `Slack RTM API <https://api.slack.com/rtm>`_.
            kwargs: Optional arbitrary keyword arguments passed to the event
                handler when the event is triggered.

        Returns:
            A decorator that validates and registers a Layabout event handler.

        Raises:
            TypeError: If the decorated :obj:`Callable`'s signature does not
                permit at least 2 parameters.
        """
        def _decorator(fn: Callable):
            # Validate that the wrapped callable is a suitable event handler.
            sig = signature(fn)
            if len(sig.parameters) < 2:
                raise TypeError("Layabout event handlers take at least 2 "
                                "positional arguments, a slack client and an "
                                "event")

            # Register a tuple of the callable and its kwargs, if any.
            self._handlers[type].append((fn, kwargs or {}))

            @wraps(fn)
            def _wrapper(*args: Any, **kwargs: Any) -> Any:
                # We don't actually do anything with the return value, but this
                # might make unit testing easier for users.
                return fn(*args, **kwargs)
            return _wrapper
        return _decorator

    def connect(self, token: str = None) -> bool:
        """
        Attempt to establish or reset a connection to Slack's API.

        Note:
            It isn't normally necessary to use this method as
            :obj:`Layabout.run` will take care of establishing a connection for
            you. This is mostly helpful if you want to take advantage of the
            embedded :obj:`slackclient.SlackClient` on the :obj:`Layabout`
            instance *before* entering into the :obj:`Layabout.run` loop.

        Args:
            token: A Slack API token. If given it will override an existing
                connection (if one exists), otherwise an existing token or
                an environment variable will be used.

        Returns:
            bool: Whether the connection succeeded.

        Raises:
            MissingSlackToken: If no API token is available.
        """
        resetting = False

        # If we were given a token let's prefer the new one and establish or
        # reset the connection.
        if token is not None:
            self._token = token
            resetting = True

        # We don't have an existing token, so let's try to get one from an
        # environment variable or give up.
        if self._token is None:
            try:
                self._token = os.environ[self._env_var]
            except KeyError:
                raise MissingSlackToken('Cannot connect to the Slack API'
                                        ' without a token.')

        # Either we've never connected before or we're purposefully resetting
        # the connection.
        if self.slack is None or resetting:
            # TODO: Maybe set an appropriate user agent string here using
            # self.name.
            self.slack = SlackClient(token=self._token)

        # Use whatever token we've got to attempt to connect (or reconnect).
        return self.slack.rtm_connect()

    def _reconnect(self, retries: int,
                   backoff: Callable[[int], float]) -> bool:
        """
        Attempt to reconnect to the Slack API.

        Args:
            retries (int): The number of retry attempts to make if a connection
                to Slack if not established or is lost.
            backoff (Callable): The strategy used to determine how
                long to wait between retries. Must take as input the number of
                the current retry and output a :obj:`float`.

        Returns:
            bool: Whether the reconnection succeeded.
        """
        # TODO: Should retries start at 0 or 1?
        for retry in range(retries):
            if self.connect():
                return True
            else:
                interval = backoff(retry)
                log.debug("Waiting %.3fs before retrying", interval)
                time.sleep(interval)

        return False

    def run(self, token: str = None, interval: float = 0.5,
            retries: int = 4, backoff: Callable[[int], float] = None,
            until: Callable[[List[dict]], bool] = None) -> None:
        """
        Connect to the Slack API and run the event handler loop.

        Args:
            token: A Slack API token. If absent an attempt will be made to use
                the environment variable supplied at instantiation. Defaults
                to ``None``.
            interval: The number of seconds to wait between fetching events
                from the Slack API.
            retries: The number of retry attempts to make if a connection to
                Slack if not established or is lost.
            backoff: The strategy used to determine how long to wait between
                retries. Must take as input the number of the current retry and
                output a :obj:`float`. If absent an exponential backoff
                strategy will be used.
            until: The condition used to evaluate whether this method
                terminates. Must take as input an :obj:`list` of :obj:`dict`
                representing Slack RTM API events and return a :obj:`bool`. If
                absent this method will run forever.

        Raises:
            FailedConnection: If connecting to the Slack API fails.
        """
        backoff = backoff or _exponential
        until = until or _forever

        # The initial connection may use a given token or attempt to use an
        # environment variable.
        if not self.connect(token=token):
            if not self._reconnect(retries=retries, backoff=backoff):
                raise FailedConnection('Failed to connect to the Slack API')

        # TODO: Should we force callers to handle KeyboardInterrupt on their
        # own, or should we try to handler it for them? 🤔
        while True:
            try:
                # Fetch new RTM events from the API.
                events = self.slack.rtm_read()

            # This is necessary to handle an error caused by a bug in Slack's
            # Python client. For more information see
            # https://github.com/slackhq/python-slackclient/issues/127
            #
            # TODO: The TimeoutError could be more elegantly resolved by making
            # a PR to the websocket-client library and letting them coerce that
            # exception to a WebSocketTimeoutException.
            except (WebSocketConnectionClosedException, TimeoutError):
                log.debug('Lost connection to the Slack API, attempting to '
                          'reconnect')
                # Attempt to re-use our existing SlackClient and token.
                if self._reconnect(retries=retries, backoff=backoff):
                    log.debug('Reconnected to the Slack API')
                    # We continue so we can fetch new events before proceeding.
                    continue

                raise FailedConnection('Failed to reconnect to the Slack API')

            if not until(events):
                # TODO: Is this even a good debugging message?
                log.debug('Terminal condition met')
                break

            # Handle events!
            for event in events:
                type_ = event.get('type')
                # TODO: Should * handlers be run first?
                for handler in self._handlers['*'] + self._handlers[type_]:
                    fn, kwargs = handler
                    fn(self.slack, event, **kwargs)

            # Maybe don't pester the Slack API too much.
            time.sleep(interval)


def _forever(events: List[dict]) -> bool:  # pragma: no cover
    return True


def _exponential(retry: int) -> float:
    return (2 ** retry) / 8
