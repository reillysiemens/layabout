from pprint import pformat
from layabout import Layabout

app = Layabout()


@app.handle('*')
def print_all(slack, event):
    """ * is a special event type that allows you to handle all event types """
    print(f"Got event:\n{pformat(event)}\n")


# We don't need to pass anything to run. By default the API token will
# be fetched from the LAYABOUT_TOKEN environment variable.
if __name__ == "__main__":
    print('Printing all events. Press Ctrl-C to quit.\n')
    app.run()
