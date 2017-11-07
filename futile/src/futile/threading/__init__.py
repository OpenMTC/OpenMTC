import sys

try:
    from threading import current_thread
except ImportError:
    from threading import currentThread as current_thread


if sys.version_info < (2, 7):
    from threading import _Event
    class Event(_Event):
        def wait(self, timeout = None):
            super(_Event, self).wait(timeout = timeout)
            return self.is_set()
else:
    from threading import Event
        
    