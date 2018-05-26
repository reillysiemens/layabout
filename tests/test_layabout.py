import os
from unittest.mock import MagicMock, call
from typing import Iterable

import pytest
from slackclient import SlackClient

from layabout import (
    EnvVar,
    FailedConnection,
    Layabout,
    MissingSlackToken,
    _SlackClientWrapper,
    _truncated_exponential,
)

TOKEN = "This ain't no Slack API token."

# ---- Auxiliary functions ----------------------------------------------------


def mock_slack(connections: Iterable = None,
               reads: Iterable = None) -> MagicMock:
    """
    Mock a :obj:`slackclient.SlackClient`.

    Args:
        connections: Side effects for the ``rtm_connect`` method.
        reads: Side effects for the ``rtm_read`` method.

    Returns:
        tuple: A 2-tuple containing a mock :obj:`slackclient.SlackClient`
            and an associated instance.
    """
    slack = MagicMock(spec=SlackClient)
    slack.server = MagicMock()

    if connections:
        slack.rtm_connect = MagicMock(side_effect=connections)

    if reads:
        slack.rtm_read = MagicMock(side_effect=reads)

    return MagicMock(spec=SlackClient, return_value=slack), slack


def mock_slack_wrapper(connections: Iterable = None):
    slack_wrapper = MagicMock(spec=_SlackClientWrapper)

    if connections:
        slack_wrapper.is_connected = MagicMock(side_effect=connections)

    cls = MagicMock(spec=_SlackClientWrapper, return_value=slack_wrapper)
    return cls, slack_wrapper

# ---- Fixtures ---------------------------------------------------------------


@pytest.fixture(scope='function')
def run_once():
    return MagicMock(side_effect=(True, False))


@pytest.fixture(scope='module')
def events():
    return [dict(type='hello'), dict(type='goodbye')]

# ---- Handler registration tests ---------------------------------------------


def test_layabout_can_register_handler():
    """
    Test that layabout can register Slack API event handlers normally.
    """
    layabout = Layabout()

    def handle_hello(slack, event):
        pass

    layabout.handle(type='hello')(fn=handle_hello)

    assert len(layabout._handlers) == 1


def test_layabout_can_register_handler_via_decorator():
    """
    Test that layabout can register Slack API event handlers via decorator.
    """
    layabout = Layabout()

    @layabout.handle('hello')
    def handle_hello(slack, event):
        pass

    assert len(layabout._handlers) == 1


def test_layabout_can_register_handler_with_kwargs():
    """
    Test that layabout can register Slack API event handlers with keyword
    arguments normally.
    """
    layabout = Layabout()
    kwargs = dict(spam='🍳')

    def handle_hello(slack, event):
        pass

    layabout.handle(type='hello', kwargs=kwargs)(fn=handle_hello)

    assert len(layabout._handlers) == 1


def test_layabout_can_register_handler_with_kwargs_via_decorator():
    """
    Test that layabout can register Slack API event handlers with keyword
    arguments via decorator.
    """
    layabout = Layabout()
    kwargs = dict(spam='🍳')

    @layabout.handle('hello', kwargs=kwargs)
    def handle_hello(slack, event, spam):
        pass

    assert len(layabout._handlers) == 1


def test_layabout_raises_type_error_with_invalid_handler():
    """
    Test that layabout raises a TypeError if an event handler that doesn't meet
    the minimum criteria to be called correctly is registered.
    """
    layabout = Layabout()

    def invalid_handler():
        pass

    with pytest.raises(TypeError) as exc:
        layabout.handle(type='hello')(fn=invalid_handler)

    expected = ("invalid_handler() missing 2 required positional arguments: "
                "'slack' and 'event'")
    assert str(exc.value) == expected


def test_layabout_raises_type_error_with_invalid_decorated_handler():
    """
    Test that layabout raises a TypeError if an event handler that doesn't meet
    the minimum criteria to be called correctly is registered via decorator.
    """
    layabout = Layabout()

    with pytest.raises(TypeError) as exc:
        @layabout.handle('hello')
        def invalid_handler(slack):
            pass

    expected = ("invalid_handler(slack) missing 1 required positional "
                "argument: 'event'")
    assert str(exc.value) == expected


def test_layabout_handlers_can_be_decorated_and_used_normally():
    """
    Test that layabout can decorate event handlers that can still be used as
    though they were undecorated. Most importantly, that they can still return
    and that their docstrings are intact.
    """
    layabout = Layabout()
    cheese_shop = dict(shop='🧀')

    @layabout.handle('hello')
    def handle_hello(slack, event):
        """ This docstring must be preserved. """
        return cheese_shop

    assert handle_hello(None, None) == cheese_shop
    assert handle_hello.__doc__ == ' This docstring must be preserved. '

# ---- Connection tests -------------------------------------------------------


def test_layabout_raises_type_error_with_invalid_connector():
    """
    Test that layabout cannot connect to Slack with a pineapple.
    """
    layabout = Layabout()

    class Pineapple:
        pass

    with pytest.raises(TypeError):
        # Turns out you can't connect to Slack with a Pineapple.
        layabout.run(connector=Pineapple)


def test_layabout_can_connect_to_slack_with_token(monkeypatch):
    """
    Test that layabout can connect to the Slack API when given a valid Slack
    API token.
    """
    layabout = Layabout()
    SlackClient, slack = mock_slack(connections=(True,))
    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.run(connector=TOKEN, until=lambda e: False)

    # Verify we instantiated a SlackClient with the given token.
    SlackClient.assert_called_with(token=TOKEN)


def test_layabout_can_connect_to_slack_with_env_var(monkeypatch):
    """
    Test that layabout can discover and use a Slack API token from an
    environment variable when not given one directly.
    """
    env_var = EnvVar('_TEST_SLACK_API_TOKEN')
    environ = {env_var: TOKEN}
    layabout = Layabout()
    SlackClient, slack = mock_slack(connections=(True,))

    monkeypatch.setattr(os, 'environ', environ)
    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    # Purposefully don't provide a connector so we have to use an env var.
    layabout.run(connector=env_var, until=lambda e: False)

    # Verify we instantiated a SlackClient with the given token and used it to
    # connect to the Slack API.
    SlackClient.assert_called_with(token=TOKEN)


def test_layabout_can_connect_to_slack_with_existing_slack_client(monkeypatch):
    """
    TODO:
        - make this test actually useful
        - reorder conn tests
        - test unconnected slack gets connected
        - connected slack isn't touched
    """
    layabout = Layabout()
    _, slack = mock_slack(connections=(True,))

    layabout.run(connector=slack, until=lambda e: False)


def test_layabout_raises_missing_slack_token_without_token(monkeypatch):
    """
    Test that layabout raises a MissingSlackToken if there is no Slack API
    token for it to use.
    """
    environ = dict()
    layabout = Layabout()

    monkeypatch.setattr(os, 'environ', environ)

    with pytest.raises(MissingSlackToken) as exc:
        # until will exit early here just to be safe.
        layabout.run(until=lambda e: False)

    assert str(exc.value) == 'Could not acquire token from SLACK_API_TOKEN'


def test_layabout_raises_missing_slack_token_with_empty_token():
    """
    Test that layabout raises a MissingSlackToken if given an empty Slack API
    token.
    """
    layabout = Layabout()

    with pytest.raises(MissingSlackToken) as exc:
        # until will exit early here just to be safe.
        layabout.run(connector='', until=lambda e: False)

    assert str(exc.value) == 'The empty string is an invalid Slack API token'


def test_layabout_can_connect_to_slack():
    wrapper = _SlackClientWrapper(
        slack=MagicMock(),
        retries=1,
        backoff=lambda r: 0
    )
    # Retry once after failure.
    wrapper.is_connected = MagicMock(side_effect=(False, True))

    wrapper.connect_with_retry()
    wrapper.inner.rtm_connect.assert_called_with()


def test_layabout_raises_failed_connection_on_failed_connection():
    """
    Test that layabout raises a FailedConnection if the connection to the Slack
    API fails.
    """
    wrapper = _SlackClientWrapper(
        slack=MagicMock(),
        retries=1,
        backoff=lambda r: 0
    )
    # Retry once after failure.
    wrapper.is_connected = MagicMock(side_effect=(False, False))

    with pytest.raises(FailedConnection) as exc:
        wrapper.connect_with_retry()

    assert str(exc.value) == 'Failed to connect to the Slack API'


def test_layabout_can_reuse_an_existing_client_to_reconnect(monkeypatch):
    """
    Test that layabout can reuse an existing SlackClient instance to reconnect
    to the Slack API rather than needlessly instantiating a new one on each
    reconnection attempt.
    """
    layabout = Layabout()
    # Fail initial connection, fail reconnection, succeed at last.
    connections = (False, False, True)
    SlackClient, _ = mock_slack(connections=connections)

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    # Retry connecting twice to verify reconnection logic was evaluated.
    # until will exit early just to be safe.
    layabout.run(
        connector=TOKEN,
        retries=2,
        backoff=lambda r: 0,
        until=lambda e: False
    )

    # Make sure the SlackClient was only instantiated once so we know that we
    # reused the existing instance.
    SlackClient.assert_called_once_with(token=TOKEN)


def test_layabout_can_continue_after_successful_reconnection(monkeypatch):
    """
    Test that layabout can continue to handle events after successfully
    reconnecting to the Slack API.
    """
    layabout = Layabout()
    # Succeed with the first connection and the subsequent reconnection.
    connections = (True, True)
    # Raise an exception on the first read and return empty events next.
    reads = (TimeoutError, [])
    SlackClient, _ = mock_slack(connections=connections, reads=reads)

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.run(
        connector=TOKEN,
        retries=1,
        backoff=lambda r: 0,
        until=lambda e: False
    )


def test_layabout_backoff_backs_off(monkeypatch):
    """ This is _truly_ a useless test. Why have I done this? """
    monkeypatch.setattr('random.randrange', lambda n: 0)
    assert _truncated_exponential(0) == 0.001


def test_layabout_backoff_does_not_exceed_64_seconds():
    """ It doesn't go to 65.0. """
    assert _truncated_exponential(16) == 64.0
    assert _truncated_exponential(17) == 64.0

# ---- Event loop tests -------------------------------------------------------


def test_layabout_can_handle_an_event(events, run_once, monkeypatch):
    """
    Test that layabout can handle an event.
    """
    layabout = Layabout()
    SlackClient, slack = mock_slack(connections=(True,), reads=(events, []))
    handle_hello = MagicMock()

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.handle('hello')(handle_hello)
    layabout.run(
        connector=TOKEN,
        interval=0,
        retries=0,
        backoff=lambda r: 0,
        until=run_once
    )

    handle_hello.assert_called_once_with(slack, events[0])


def test_layabout_can_handle_an_event_with_kwargs(events, run_once,
                                                  monkeypatch):
    """
    Test that layabout can call an event handler that requires kwargs.
    """
    layabout = Layabout()
    SlackClient, slack = mock_slack(connections=(True,), reads=(events, []))
    kwargs = dict(caerbannog='🐰')
    handle_hello = MagicMock()

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.handle('hello', kwargs=kwargs)(handle_hello)
    layabout.run(
        connector=TOKEN,
        interval=0,
        retries=0,
        backoff=lambda r: 0,
        until=run_once
    )

    handle_hello.assert_called_once_with(slack, events[0], **kwargs)


def test_layabout_can_only_handle_events_that_happen(events, run_once,
                                                     monkeypatch):
    """
    Test that layabout only handles events that actually happen.
    """
    layabout = Layabout()
    SlackClient, _ = mock_slack(connections=(True,), reads=(events, []))
    aint_happenin = MagicMock()

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.handle('this will never happen')(aint_happenin)
    layabout.run(
        connector=TOKEN,
        interval=0,
        retries=0,
        backoff=lambda r: 0,
        until=run_once
    )

    aint_happenin.assert_not_called()


def test_layabout_can_handle_one_event_multiple_times(events, run_once,
                                                      monkeypatch):
    """
    Test that layabout calls all handlers for a given event.
    """
    layabout = Layabout()
    SlackClient, slack = mock_slack(connections=(True,), reads=(events, []))
    handle_hello1, handle_hello2 = MagicMock(), MagicMock()

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.handle('hello')(handle_hello1)
    layabout.handle('hello')(handle_hello2)
    layabout.run(
        connector=TOKEN,
        interval=0,
        retries=0,
        backoff=lambda r: 0,
        until=run_once
    )

    handle_hello1.assert_called_once_with(slack, events[0])
    handle_hello2.assert_called_once_with(slack, events[0])


def test_layabout_can_handle_multiple_events(events, run_once, monkeypatch):
    """
    Test that layabout calls all handlers for their respective events.
    """
    layabout = Layabout()
    SlackClient, slack = mock_slack(connections=(True,), reads=(events, []))
    handle_hello, handle_goodbye = MagicMock(), MagicMock()

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.handle('hello')(handle_hello)
    layabout.handle('goodbye')(handle_goodbye)
    layabout.run(
        connector=TOKEN,
        interval=0,
        retries=0,
        backoff=lambda r: 0,
        until=run_once
    )

    handle_hello.assert_called_once_with(slack, events[0])
    handle_goodbye.assert_called_once_with(slack, events[1])


def test_layabout_can_handle_an_event_with_a_splat_handler(events, run_once,
                                                           monkeypatch):
    """
    Test that layabout can handle any event with a splat handler.
    """
    layabout = Layabout()
    events = events[:1]
    SlackClient, slack = mock_slack(connections=(True,), reads=(events, []))
    splat = MagicMock()

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.handle('*')(splat)
    layabout.run(
        connector=TOKEN,
        interval=0,
        retries=0,
        backoff=lambda r: 0,
        until=run_once
    )

    splat.assert_called_once_with(slack, events[0])


def test_layabout_can_handle_all_events_with_a_splat_handler(events, run_once,
                                                             monkeypatch):
    """
    Test that layabout can handle all events with a splat handler.
    """
    layabout = Layabout()
    SlackClient, slack = mock_slack(connections=(True,), reads=(events, []))
    splat = MagicMock()

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.handle('*')(splat)
    layabout.run(
        connector=TOKEN,
        interval=0,
        retries=0,
        backoff=lambda r: 0,
        until=run_once
    )

    splat.assert_has_calls([call(slack, e) for e in events])


def test_layabout_can_handle_events_with_normal_and_splat_handlers(
    events,
    run_once,
    monkeypatch
):
    """
    Test that layabout can handle an event with normal handlers as well as
    a splat handler.
    """
    layabout = Layabout()
    SlackClient, slack = mock_slack(connections=(True,), reads=(events, []))
    handle_hello, splat = MagicMock(), MagicMock()

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.handle('hello')(handle_hello)
    layabout.handle('*')(splat)
    layabout.run(
        connector=TOKEN,
        interval=0,
        retries=0,
        backoff=lambda r: 0,
        until=run_once
    )

    handle_hello.assert_called_once_with(slack, events[0])
    splat.assert_has_calls([call(slack, e) for e in events])
