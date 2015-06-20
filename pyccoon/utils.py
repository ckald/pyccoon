import os
import time
from collections import namedtuple


class SourceFile(namedtuple('SourceFile', 'destination source process prefix')):
    def __new__(cls, destination, source, process=True, prefix=None):
        return super(SourceFile, cls).__new__(cls,
                                              source=source,
                                              destination=destination,
                                              process=process,
                                              prefix=prefix)


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


def shift(array, default):
    """
    Shift items off the front of the `array` until it is empty, then return
    `default`.
    """

    try:
        return array.pop(0)
    except IndexError:
        return default


def ensure_directory(directory):
    """ ### Ensure directory
        Ensure that the destination directory exists."""

    if not os.path.isdir(directory):
        os.makedirs(directory)


def monitor(path, file_modified, file_changed):
    """Monitor each source file and re-generate documentation on change."""

    # The watchdog modules are imported in `main()` but we need to re-import
    # here to bring them into the local namespace.
    import watchdog.events
    import watchdog.observers

    path = os.path.normpath(path)

    class RegenerateHandler(watchdog.events.FileSystemEventHandler):
        """A handler for recompiling files which triggered watchdog events"""

        def dispatch(self, event):

            # Skip files and directories starting with
            if any([f.startswith('.')
                    for f in os.path.relpath(event.src_path, path).split(os.sep)]):
                return

            task = None
            if event.event_type == "modified":
                if not event.is_directory:
                    task = file_modified
                else:
                    return
            else:
                task = file_changed

            if task:
                print("\n")
                print("{} \"{}\" was {}, generating documentation...".format(
                    "Directory" if event.is_directory else "File",
                    event.src_path,
                    event.event_type
                ))
                task()

    # Set up an observer which monitors all directories for files given on
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
