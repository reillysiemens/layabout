import os
import time
import random
import logging
from typing import (
    Any,
    Callable,
    DefaultDict,
    Dict,
    List,
    Optional,
    Tuple,
    Union,
)
from inspect import signature, Signature
from functools import singledispatch, wraps
from collections import defaultdict

from slackclient import SlackClient

# TODO: This is a dependency of slackclient needed for exception handling. In
# the future, we might be able to remove this. For now we don't want to declare
# it as an explicit dependency.
from websocket import WebSocketConnectionClosedException

__author__ = 'Reilly Tucker Siemens'
__email__ = 'reilly@tuckersiemens.com'
__version__ = '1.0.0b'

# Private type alias for the complex type of the handlers defaultdict.
_Handlers = DefaultDict[str, List[Tuple[Callable, dict]]]

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


class EnvVar(str):
    """ A newtype for differentiating string tokens from env var names. """


class _SlackClientWrapper:
    def __init__(self, slack: SlackClient, retries: int,
                 backoff: Callable[[int], float]) -> None:
        self.inner = slack
        self.retries = retries
        self.backoff = backoff

        # Slack Connection is Initialization (SCII)
        self.connect_with_retry()

    def connect(self) -> None:
        """ Connect to the Slack API. """
        self.inner.rtm_connect()

    def is_connected(self) -> bool:
        """ Validate whether we're connected to the Slack API. """
        return getattr(self.inner.server.websocket, 'connected', False)

    def connect_with_retry(self) -> None:
        """ Attempt to connect to the Slack API. Retry on failures. """
        if self.is_connected():
            log.debug('Already connected to the Slack API')
            return

        for retry in range(1, self.retries + 1):
            self.connect()
            if self.is_connected():
                log.debug('Connected to the Slack API')
                return
            else:
                interval = self.backoff(retry)
                log.debug("Waiting %.3fs before retrying", interval)
                time.sleep(interval)

        raise FailedConnection('Failed to connect to the Slack API')

    def fetch_events(self) -> List[dict]:
        """ Fetch new RTM events from the API. """
        try:
            return self.inner.rtm_read()

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
            self.connect_with_retry()
            return []


class Layabout:
    """
    An event handler on top of the Slack RTM API.

    Args:
        env_var: The environment variable to try to load a Slack API token
            from.

    Example:

        .. code-block:: python

           from layabout import Layabout

           layabout = Layabout()


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
    def __init__(self) -> None:
        self._env_var = EnvVar('SLACK_API_TOKEN')
        self._slack: Optional[_SlackClientWrapper] = None
        self._handlers: _Handlers = defaultdict(list)

    @staticmethod
    def _format_parameter_error_message(name: str, sig: Signature,
                                        num_params: int) -> str:
        """
        Format an error message for missing positional arguments.

        Args:
            name: The function name.
            sig: The function's signature.
            num_params: The number of function parameters.

        Returns:
            str: A formatted error message.
        """
        if num_params == 0:
            plural = 's'
            missing = 2
            arguments = "'slack' and 'event'"
        else:
            plural = ''
            missing = 1
            arguments = "'event'"

        return (f"{name}{sig} missing {missing} required positional "
                f"argument{plural}: {arguments}")

    def handle(self, type: str, *, kwargs: dict = None) -> Callable:
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
                accept at least 2 parameters.
        """
        def decorator(fn: Callable) -> Callable:
            # Validate that the wrapped callable is a suitable event handler.
            sig = signature(fn)
            num_params = len(sig.parameters)
            if num_params < 2:
                raise TypeError(self._format_parameter_error_message(
                    fn.__name__, sig, num_params))

            # Register a tuple of the callable and its kwargs, if any.
            self._handlers[type].append((fn, kwargs or {}))

            @wraps(fn)
            def wrapper(slack: SlackClient, event: Dict[str, Any],
                        **kwargs: Any) -> Any:
                # We don't actually do anything with the return value, but this
                # might make unit testing easier for users.
                return fn(slack, event, **kwargs)
            return wrapper
        return decorator

    def _ensure_slack(self, connector: Any, retries: int,
                      backoff: Callable[[int], float]) -> None:
        """ Ensure we have a SlackClient. """
        connector = self._env_var if connector is None else connector
        slack = _create_slack(connector)
        self._slack = _SlackClientWrapper(
            slack=slack,
            retries=retries,
            backoff=backoff
        )

    def run(self, *, connector: Union[str, SlackClient, None] = None,
            interval: float = 0.5, retries: int = 16,
            backoff: Callable[[int], float] = None,
            until: Callable[[List[dict]], bool] = None) -> None:
        """
        Connect to the Slack API and run the event handler loop.

        Args:
            connector: A Slack API token or :obj:`SlackClient`. If absent an
                attempt will be made to use the environment variable supplied
                at instantiation.
            interval: The number of seconds to wait between fetching events
                from the Slack API.
            retries: The number of retry attempts to make if a connection to
                Slack if not established or is lost.
            backoff: The strategy used to determine how long to wait between
                retries. Must take as input the number of the current retry and
                output a :obj:`float`. If absent a `truncated exponential
                backoff`_ strategy will be used.
            until: The condition used to evaluate whether this method
                terminates. Must take as input a :obj:`list` of :obj:`dict`
                representing Slack RTM API events and return a :obj:`bool`. If
                absent this method will run forever.

        Raises:
            TypeError: If an unsupported connector is given.
            MissingSlackToken: If no API token is available.
            FailedConnection: If connecting to the Slack API fails.

        .. _truncated exponential backoff:
            https://cloud.google.com/storage/docs/exponential-backoff
        """
        backoff = backoff or _truncated_exponential
        until = until or _forever

        self._ensure_slack(
            connector=connector,
            retries=retries,
            backoff=backoff
        )
        assert self._slack is not None

        while True:
            events = self._slack.fetch_events()

            if not until(events):
                log.debug('Exiting event loop')
                break

            # Handle events!
            for event in events:
                type_ = event.get('type', '')
                for handler in self._handlers[type_] + self._handlers['*']:
                    fn, kwargs = handler
                    fn(self._slack.inner, event, **kwargs)

            # Maybe don't pester the Slack API too much.
            time.sleep(interval)


@singledispatch
def _create_slack(connector: Any):
    """ Default connector. Raises an error with unsupported connectors. """
    raise TypeError(f"Invalid connector: {type(connector)}")


@_create_slack.register(EnvVar)
def _create_slack_with_env_var(env_var: EnvVar) -> SlackClient:
    """ Create a SlackClient with a token from an env var. """
    token = os.getenv(env_var)
    if not token:
        raise MissingSlackToken("Could not acquire token from "
                                f"{env_var}")

    return SlackClient(token=token)


@_create_slack.register(str)
def _create_slack_with_token(token: str) -> SlackClient:
    """ Create a SlackClient with a provided token. """
    if token == '':
        raise MissingSlackToken("The empty string is an invalid Slack API "
                                "token")

    return SlackClient(token=token)


@_create_slack.register(SlackClient)
def _create_slack_with_slack_client(slack: SlackClient) -> SlackClient:
    """ Use an existing SlackClient if we don't already have one. """
    return slack


def _forever(events: List[dict]) -> bool:  # pragma: no cover because duh.
    """ Run Layabout in an infinite loop. """
    return True


def _truncated_exponential(retry: int) -> float:
    """ An exponential backoff strategy for reconnecting to the Slack API. """
    return (min(((2 ** retry) + random.randrange(1000)), 64000) / 1000)
