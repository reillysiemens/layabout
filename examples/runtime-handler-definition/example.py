import sys

from pprint import pformat

from layabout import Layabout, MissingToken

app = Layabout()


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


def main():
    channel_name = input('Which channel would you like to debug? ')
    print(f"Debugging events in #{channel_name}. Press Ctrl-C to quit.")

    @app.handle('*')
    def debug(slack, event):
        """ Close over ``channel_name`` and debug only those events. """
        debug_channel = channel_to_id(slack, channel_name)
        if event.get('channel') == debug_channel:
            print(f"Got event in #{channel_name}:\n{pformat(event)}\n")
    try:
      app.run()
    except MissingToken:
      sys.exit('Unable to find Slack API token.\n'
               'Learn more about available token types here:\n'
               'https://api.slack.com/docs/token-types.')


if __name__ == '__main__':
    main()
