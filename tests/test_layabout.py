import os
from unittest.mock import MagicMock, call

import pytest

from layabout import (
    Layabout,
    MissingSlackToken,
    FailedConnection,
)

# The likelihood of this ever being a valid Slack token is probably slim.
TOKEN = 'xoxb-13376661337-DeAdb33Fd15EA53fACef33D1'


@pytest.fixture
def slack_client():
    def api_call(method):
        return dict(
            channels=[{'id': 'D3ADB33F1', 'name': 'general'}],
            groups=[{'id': '1800IDGAF', 'name': 'super_secret_club'}],
        )

    slack_client = MagicMock(api_call=api_call)
    return slack_client


def test_layabout_can_register_handlers():
    """
    Test that layabout can register Slack API event handlers normally and as a
    decorator, both with and without keyword arguments.
    """
    layabout = Layabout()
    kwargs = dict(spam='🍳')

    def handle_hello1(slack, event):
        pass

    @layabout.handle('hello')
    def handle_hello2(slack, event):
        pass

    def handle_hello3(slack, event, spam):
        pass

    @layabout.handle('hello', kwargs=kwargs)
    def handle_hello4(slack, event, spam):
        pass

    layabout.handle(type='hello')(fn=handle_hello1)
    layabout.handle(type='hello', kwargs=kwargs)(fn=handle_hello3)


def test_layabout_raises_type_error_with_invalid_handlers():
    """
    Test that layabout raises a TypeError if an event handler is supplied that
    doesn't meet the minimum criteria to be called correctly.
    """
    layabout = Layabout()

    def invalid_handler1(slack):
        pass

    with pytest.raises(TypeError) as exc1:
        layabout.handle(type='hello')(fn=invalid_handler1)

    with pytest.raises(TypeError) as exc2:
        @layabout.handle('hello')
        def invalid_handler2(slack):
            pass

    expected = ("Layabout event handlers take at least 2 positional "
                "arguments, a slack client and an event")
    assert str(exc1.value) == expected and str(exc2.value) == expected


def test_layabout_handlers_can_still_be_used_normally():
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


def test_layabout_can_connect_to_slack_with_token(monkeypatch):
    """
    Test that layabout can connect to the Slack API when given a valid Slack
    API token.
    """
    layabout = Layabout()

    rtm_connect = MagicMock(return_value=True)
    slack = MagicMock(rtm_connect=rtm_connect)
    SlackClient = MagicMock(return_value=slack)
    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    layabout.run(token=TOKEN, until=lambda e: False)

    # Verify we instantiated a SlackClient with the given token and used it to
    # connect to the Slack API.
    SlackClient.assert_called_with(token=TOKEN)
    rtm_connect.assert_called_with()


def test_layabout_can_connect_to_slack_with_env_var(monkeypatch):
    """
    Test that layabout can discover and use a Slack API token from an
    environment variable when not given one directly.
    """
    env_var = '_TEST_SLACK_API_TOKEN'
    environ = {env_var: TOKEN}
    layabout = Layabout(env_var=env_var)

    rtm_connect = MagicMock(return_value=True)
    slack = MagicMock(rtm_connect=rtm_connect)
    SlackClient = MagicMock(return_value=slack)
    monkeypatch.setattr(os, 'environ', environ)
    monkeypatch.setattr('layabout.SlackClient', SlackClient)

    # Purposefully don't provide a token so we have to use an env var.
    layabout.run(until=lambda e: False)

    # Verify we instantiated a SlackClient with the given token and used it to
    # connect to the Slack API.
    SlackClient.assert_called_with(token=TOKEN)
    rtm_connect.assert_called_with()


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

    connections = [
        False,  # Fail the initial connection (_connect).
        False,  # Fail the reconnection attempt (_reconnect).
    ]

    rtm_connect = MagicMock(side_effect=connections)
    slack = MagicMock(rtm_connect=rtm_connect)
    SlackClient = MagicMock(return_value=slack)
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

    connections = [
        True,  # Succeed with the first connection (_connect).
        False,  # Fail later during a reconnection (_reconnect).
    ]

    rtm_connect = MagicMock(side_effect=connections)
    rtm_read = MagicMock(side_effect=TimeoutError)
    slack = MagicMock(rtm_connect=rtm_connect, rtm_read=rtm_read)

    SlackClient = MagicMock(return_value=slack)
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

    connections = [
        False,  # Fail the initial connection (_connect).
        False,  # Fail with the first reconnection attempt (_reconnect).
        True,  # Succeed with the second reconnection attempt (_reconnect).
    ]

    rtm_connect = MagicMock(side_effect=connections)
    slack = MagicMock(rtm_connect=rtm_connect)
    SlackClient = MagicMock(return_value=slack)
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

    connections = [
        True,  # Succeed with the first connection (_connect).
        True,  # Succeed later with a reconnection (_reconnect).
    ]
    reads = [
        TimeoutError,  # Raise an exception on the first read.
        [],  # Return empty events on the second read (after reconnection).
    ]

    rtm_connect = MagicMock(side_effect=connections)
    rtm_read = MagicMock(side_effect=reads)
    slack = MagicMock(rtm_connect=rtm_connect, rtm_read=rtm_read)

    SlackClient = MagicMock(return_value=slack)
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
    events = [
        dict(type='hello'),
        dict(type='goodbye'),
    ]
    layabout = Layabout()

    connections = [
        True,  # Succeed with the first connection (_connect).
    ]

    rtm_connect = MagicMock(side_effect=connections)
    rtm_read = MagicMock(return_value=events)
    slack = MagicMock(rtm_connect=rtm_connect, rtm_read=rtm_read)
    run_twice = MagicMock(side_effect=[True, False])

    SlackClient = MagicMock(return_value=slack)
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
