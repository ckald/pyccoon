import os
import time


class cached_property(object):
    """
    Descriptor (non-data) for building an attribute on-demand on first use.
    """
    def __init__(self, factory):
        """
        <factory> is called such: factory(instance) to build the attribute.
        """
        self._attr_name = factory.__name__
        self._factory = factory

    def __get__(self, instance, owner):
        # Build the attribute.
        attr = self._factory(instance)

        # Cache the value; hide ourselves.
        setattr(instance, self._attr_name, attr)

        return attr


def shift(list, default):
    """
    Shift items off the front of the `list` until it is empty, then return
    `default`.
    """

    try:
        return list.pop(0)
    except IndexError:
        return default


def ensure_directory(directory):
    """ === Ensure directory ===
        Ensure that the destination directory exists."""

    if not os.path.isdir(directory):
        os.makedirs(directory)


def monitor(path, func):
    """Monitor each source file and re-generate documentation on change."""

    # The watchdog modules are imported in `main()` but we need to re-import\
    # here to bring them into the local namespace.
    import watchdog.events
    import watchdog.observers

    class RegenerateHandler(watchdog.events.FileSystemEventHandler):
        """A handler for recompiling files which triggered watchdog events"""
        def on_any_event(self, event):
            """Regenerate documentation for a file which triggered an event"""
            # Re-generate documentation from a source file if it was listed on\
            # the command line. Watchdog monitors whole directories, so other\
            # files may cause notifications as well.
            func()

    # Set up an observer which monitors all directories for files given on\
    # the command line and notifies the handler defined above.
    event_handler = RegenerateHandler()
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, path=path, recursive=True)

    # Run the file change monitoring loop until the user hits Ctrl-C.
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
