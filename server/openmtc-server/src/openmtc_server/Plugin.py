from futile.logging import LoggerMixin
from aplus import Promise
from openmtc.exc import OpenMTCError
from openmtc_server.configuration import Configuration


class BasicPlugin(LoggerMixin):
    started = False
    initialized = False

    def __init__(self, config, *args, **kw):
        super(BasicPlugin, self).__init__(*args, **kw)

        self.config = config or {}

        self.logger.debug("Plugin %s created with config %s" %
                          (type(self).__name__, self.config))

        self.__promise = None

    def initialize(self):
        self.logger.info("Initializing plugin %s", type(self).__name__)
        p = self.__promise = Promise()
        try:
            self._init()
        except BaseException as e:
            self.logger.exception("Failed to initialize plugin")
            self._error(e)

        return p
    init = initialize

    def start(self):
        self.logger.info("Starting plugin %s", type(self).__name__)
        p = self.__promise = Promise()
        try:
            self._start()
        except BaseException as e:
            self.logger.exception("Failed to start plugin")
            self._error(e)

        return p

    def stop(self):
        p = Promise()

        if not self.started:
            p.reject(OpenMTCError("Plugin %s was not started"))
        else:
            self.__promise = p
            try:
                self._stop()
            except BaseException as e:
                self.logger.exception("Failed to stop plugin")
                self._error(e)

        return p

    def _init(self):
        self._initialized()

    def _start(self):
        self._started()

    def _stop(self):
        self._stopped()

    def _ready(self):
        p = self.__promise
        del self.__promise
        p.fulfill(self)

    def _initialized(self):
        self.logger.debug("Plugin %s is initialized", self)
        self.initialized = True
        self._ready()

    def _started(self):
        self.logger.debug("Plugin %s is started", self)
        self.started = True
        self._ready()

    def _stopped(self):
        del self.started
        self._ready()

    def _error(self, e):
        self.__promise.reject(e)
        del self.__promise


class Plugin(BasicPlugin):
    __configuration__ = Configuration

    def __init__(self, api, config, *args, **kw):
        super(Plugin, self).__init__(config=config, *args, **kw)

        self.api = api
        self.events = api.events

    def get_shelve(self, name):
        return self.api.db.get_shelve("%s_%s" % (type(self).__name__, name))
