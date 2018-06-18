from layabout import Layabout

app = Layabout()


@app.handle('*')
def print_all(slack, event):
    """ * is a special event type that allows you to handle all event types """
    print(f"Got event {event}")


# We don't need to pass anything to run. By default the API token will
# be fetched from the LAYABOUT_API_TOKEN environment variable.
if __name__ == "__main__":
    app.run()
