import os
from unittest.mock import MagicMock, call
from typing import Iterable

import pytest

from layabout import (
    Layabout,
    MissingSlackToken,
    FailedConnection,
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
    slack = MagicMock()

    if connections:
        slack.rtm_connect = MagicMock(side_effect=connections)

    if reads:
        slack.rtm_read = MagicMock(side_effect=reads)

    return MagicMock(return_value=slack), slack

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

    def invalid_handler(slack):
        pass

    with pytest.raises(TypeError) as exc:
        layabout.handle(type='hello')(fn=invalid_handler)

    expected = ("Layabout event handlers take at least 2 positional "
                "arguments, a slack client and an event")
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

    expected = ("Layabout event handlers take at least 2 positional "
                "arguments, a slack client and an event")
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


def test_layabout_can_connect_to_slack_with_token(monkeypatch):
    """
    Test that layabout can connect to the Slack API when given a valid Slack
    API token.
    """
    layabout = Layabout()
    SlackClient, slack = mock_slack(connections=(True,))

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.run(token=TOKEN, until=lambda e: False)

    # Verify we instantiated a SlackClient with the given token and used it to
    # connect to the Slack API.
    SlackClient.assert_called_with(token=TOKEN)
    slack.rtm_connect.assert_called_with()


def test_layabout_can_connect_to_slack_with_env_var(monkeypatch):
    """
    Test that layabout can discover and use a Slack API token from an
    environment variable when not given one directly.
    """
    env_var = '_TEST_SLACK_API_TOKEN'
    environ = {env_var: TOKEN}
    layabout = Layabout(env_var=env_var)
    SlackClient, slack = mock_slack(connections=(True,))

    monkeypatch.setattr(os, 'environ', environ)
    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    # Purposefully don't provide a token so we have to use an env var.
    layabout.run(until=lambda e: False)

    # Verify we instantiated a SlackClient with the given token and used it to
    # connect to the Slack API.
    SlackClient.assert_called_with(token=TOKEN)
    slack.rtm_connect.assert_called_with()


def test_layabout_raises_failed_connection_without_token(monkeypatch):
    """
    Test that layabout raises a FailedConnection if there is no Slack API token
    for it to use.
    """
    environ = dict()
    layabout = Layabout()

    monkeypatch.setattr(os, 'environ', environ)

    with pytest.raises(MissingSlackToken) as exc:
        # until will exit early here just to be safe.
        layabout.run(until=lambda e: False)

    assert str(exc.value) == 'Cannot connect to the Slack API without a token'


def test_layabout_raises_failed_connection_on_failed_connection(monkeypatch):
    """
    Test that layabout raises a FailedConnection if the connection to the Slack
    API fails.
    """
    layabout = Layabout()
    # Fail the first connection and the subsequent reconnection.
    connections = (False, False)
    SlackClient, _ = mock_slack(connections=connections)

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    # Retry once after failure. until will exit early just to be safe.
    with pytest.raises(FailedConnection) as exc:
        layabout.run(
            token=TOKEN,
            retries=1,
            backoff=lambda r: 0,
            until=lambda e: False
        )

    assert str(exc.value) == 'Failed to connect to the Slack API'


def test_layabout_raises_connection_error_on_failed_reconnection(monkeypatch):
    """
    Test that layabout raises a FailedConnection if attempts to reconnect to
    the Slack API fail.
    """
    layabout = Layabout()
    # Succeed with the first connection and fail the subsequent reconnection.
    connections = (True, False)
    SlackClient, _ = mock_slack(connections=connections, reads=TimeoutError)

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    # Retry once after failure. until will exit early just to be safe. Don't
    # provide a backoff callback so the default behavior will be tested.
    with pytest.raises(FailedConnection) as exc:
        layabout.run(
            token=TOKEN,
            retries=1,
            until=lambda e: False
        )

    assert str(exc.value) == 'Failed to reconnect to the Slack API'


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
        token=TOKEN,
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
        token=TOKEN,
        retries=1,
        backoff=lambda r: 0,
        until=lambda e: False
    )


def test_layabout_can_handle_events(monkeypatch):
    """
    Test that layabout can handle events appropriately given multiple event
    handlers and even * event handlers.
    """
    layabout = Layabout()
    events = [dict(type='hello'), dict(type='goodbye')]
    run_twice = MagicMock(side_effect=(True, False))
    SlackClient, _ = mock_slack(connections=(True,), reads=(events, []))

    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    # Register our handlers to be called with the specified kwargs.
    kwargs = dict(caerbannog='🐰')
    handle_hello = MagicMock()
    handle_goodbye = MagicMock()
    handle_splat = MagicMock()
    layabout.handle(type='hello', kwargs=kwargs)(fn=handle_hello)
    layabout.handle(type='goodbye', kwargs=kwargs)(fn=handle_goodbye)
    layabout.handle(type='*', kwargs=kwargs)(fn=handle_splat)

    layabout.run(
        token=TOKEN,
        interval=0,
        retries=0,
        backoff=lambda r: 0,
        until=run_twice
    )

    # Ensure the hello handler receives only hello events, the goodbye handler
    # receives only goodbye events, and the * handler receives all events.
    call_hello = call(layabout._slack, events[0], **kwargs)
    call_goodbye = call(layabout._slack, events[1], **kwargs)
    all_calls = [call_hello, call_goodbye]
    handle_hello.assert_called_once_with(*call_hello[1], **call_hello[2])
    handle_goodbye.assert_called_once_with(*call_goodbye[1], **call_goodbye[2])
    handle_splat.assert_has_calls(all_calls)
