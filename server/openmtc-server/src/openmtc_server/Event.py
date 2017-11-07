from abc import abstractmethod, ABCMeta

from futile import issubclass as safe_issubclass
from futile.logging import LoggerMixin
from openmtc.model import Resource


class Event(LoggerMixin):
    __metaclass__ = ABCMeta

    @abstractmethod
    def fire(self, *event_data):
        raise NotImplementedError()

    @abstractmethod
    def register_handler(self, handler, *args, **kw):
        raise NotImplementedError()


class EventSpec(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def matches(self, item):
        raise NotImplementedError()


class BasicEvent(Event):
    def __init__(self):
        super(BasicEvent, self).__init__()

        self._handlers = []

    def _add_handler_data(self, data):
        handler = data
        if handler in self._handlers:
            self.logger.warn("Handler %s is already registered", handler)
        else:
            self._handlers.append(handler)

    def register_handler(self, handler, **kw):
        self._add_handler_data(handler)

    def _execute_handler(self, handler, *event_data):
        self.logger.debug("Running handler %s with %s", handler, event_data)
        try:
            handler(*event_data)
        except Exception:
            self.logger.exception("Error in event handler")
        self.logger.debug("handler %s finished", handler)

    def _fired(self, *event_data):
        for handler in self._handlers:
            self._execute_handler(handler, *event_data)

    def fire(self, *event_data):
        self.logger.debug("Fired: %s with %s", self, event_data)
        self._fired(*event_data)


class ResourceTreeEvent(BasicEvent):
    def _add_handler_data(self, data):
        resource_type = data[0]
        handler = data[1]

        # TODO: kca: error messages
        if resource_type is not None and not safe_issubclass(resource_type,
                                                             Resource):
            raise TypeError(resource_type)

        if not callable(handler):
            raise TypeError(handler)

        if data in self._handlers:
            self.logger.warn("Handler %s is already registered for type %s",
                             handler, resource_type or "<all>")
        else:
            self._handlers.append(data)

    def register_handler(self, handler, resource_type=None, **kw):
        self._add_handler_data((resource_type, handler))

    def _execute_handler(self, data, *event_data):
        handler = data[1]
        self.logger.debug("Running handler %s with %s", handler, event_data)
        handler(*event_data)
        self.logger.debug("handler finished")

    def _fired(self, resource_type, *event_data):
        for data in self._handlers:
            handled_type = data[0]
            if handled_type is None or issubclass(resource_type, handled_type):
                self._execute_handler(data, *event_data)
            else:
                pass
