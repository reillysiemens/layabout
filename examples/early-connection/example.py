import os
import sys

from layabout import Layabout
from slackclient import SlackClient

app = Layabout()


@app.handle('user_typing')
def someone_is_typing(slack, event):
    print('Someone is typing...')


def channel_to_id(slack, channel):
    """ Surely there's a better way to do this... """
    channels = slack.api_call('channels.list').get('channels') or []
    groups = slack.api_call('groups.list').get('groups') or []

    if not channels and not groups:
        raise RuntimeError("Couldn't get channels and groups.")

    ids = [c['id'] for c in channels + groups if c['name'] == channel]

    if not ids:
        raise ValueError(f"Couldn't find #{channel}")

    return ids[0]


def send_message(slack):
    """ Prompt for and send a message to a channel. """
    channel = input('Which channel would you like to message? ')
    message = input('What should the message be? ')
    channel_id = channel_to_id(slack, channel)

    print(f"Sending message to #{channel} (id: {channel_id})!")
    slack.rtm_send_message(channel_id, message)


def main():
    env_var = 'LAYABOUT_TOKEN'
    token = os.getenv(env_var)

    if not token:
        sys.exit(f"Couldn't load ${env_var}. Try setting it.")

    slack = SlackClient(token=token)

    if not slack.rtm_connect():
        sys.exit("Couldn't connect to the Slack API. Check your token.")

    # Send a message to some channel before running the event loop!
    send_message(slack)

    print('Listening for typing events. Press Ctrl-C to quit.\n')
    # Now run the loop. This will re-use the existing SlackClient connection!
    app.run(connector=slack)


if __name__ == '__main__':
    main()
