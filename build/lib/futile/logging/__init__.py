"""
Created on 15.07.2011

@author: kca
"""
import logging
import logging.handlers
from futile.basictypes import ClassType, basestring
from futile.threading import current_thread
from logging import Filter
from futile.collections import get_iterable

# statics
_handlers = []
_formatter = logging.Formatter('%(asctime)s %(levelname)s - %(name)s: %(message)s')
_level = logging.NOTSET

# log level constants for convenience
from logging import CRITICAL, FATAL, ERROR, WARNING, INFO, DEBUG, NOTSET

CRITICAL = CRITICAL
FATAL = FATAL
ERROR = ERROR
WARNING = WARNING
INFO = INFO
DEBUG = DEBUG
NOTSET = NOTSET


def get_default_level():
    return _level


def set_default_level(l):
    global _level
    _level = l
    logging.basicConfig(level=l)


#     try:
#         from colorlog import ColoredFormatter
#         formatter = ColoredFormatter(
#                 "%(blue)s%(asctime)s %(log_color)s%(levelname) - 8s%(reset)s%(name)s: %(message)s",
#                 datefmt=None,
#                 reset=True,
#                 log_colors={
#                         'DEBUG':    'cyan',
#                         'INFO':     'green',
#                         'WARNING':  'yellow',
#                         'ERROR':    'red',
#                         'CRITICAL': 'red',
#                 }
#         )
#         import logging
#         hand = logging.StreamHandler()
#         hand.setFormatter(formatter)
#         futile.logging.add_handler( hand)
#     except ImportError:
#         pass
def get_default_formatter():
    return _formatter


def set_default_formatter(frmt):
    global _formatter
    if frmt and isinstance(frmt, logging.Formatter):
        _formatter = frmt
    else:
        raise TypeError("Not a logging Formatter: %s" % (frmt, ))


def add_handler(h):
    if not isinstance(h, logging.Handler):
        raise TypeError(h)

    _handlers.append(h)


def add_log_file(path, level=None, formatter=None):
    """ Adds a log file to all future loggers.
        Files will be rotated depending on max_bytes and backups parameters.

        @param path: path to logfile
        @param level: minimum log level
        @param formatter: a logging.Formatter for this log file
    """
    handler = logging.handlers.WatchedFileHandler(path)
    handler.setFormatter(formatter or _formatter)
    # TODO(rst): probably try/except is necessary
    handler.setLevel(level or _level)
    add_handler(handler)


def get_logger(logger_name=None, level=None):
    level = level if level is not None else _level
    # logging.basicConfig(level=level)
    if logger_name:
        if not isinstance(logger_name, basestring):
            if not isinstance(logger_name, (type, ClassType)):
                l_class = logger_name.__class__
            else:
                l_class = logger_name
            logger_name = l_class.__module__ + "." + l_class.__name__
    else:
        logger_name = __name__

    try:
        logger = logging.getLogger(logger_name)
    except Exception as e:
        print ("Failed to get logger '%s': %s" % (logger_name, e))
        raise

    try:
        logger.setLevel(level)  # raises TypeError: not a valid string or int
    except TypeError:
        logger.setLevel(NOTSET)  # TODO(rst): set another level if wrong level?
    for h in _handlers:
        logger.addHandler(h)
    return logger


class LoggerMixin(object):

    log_file = None
    log_level = None

    def __init__(self):
        self.__logger = None

    @classmethod
    def _get_logger(cls, logger_name=None):
        logger = get_logger(logger_name, cls.log_level)
        if cls.log_file:
            formatter = get_default_formatter()
            handler = logging.handlers.WatchedFileHandler(cls.log_file)
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    def get_logger(self):
        try:
            if self.__logger is not None:
                return self.__logger
        except AttributeError:
            pass
        self.__logger = l = self.get_class_logger()
        return l

    def set_logger(self, logger):
        self.__logger = logger
    logger = property(get_logger, set_logger)

    @classmethod
    def get_class_logger(cls):
        try:
            return cls.__dict__["__logger__"]
        except KeyError:
            l = cls.__logger__ = cls._get_logger(cls.__name__)
            return l

    def __getstate__(self):
        l = getattr(self, "_LoggerMixin__logger", None)
        self.__logger = None
        try:
            sgs = super(LoggerMixin, self).__getstate__
        except AttributeError:
            state = self.__dict__.copy()
        else:
            state = sgs()
        self.__logger = l
        return state


class ThreadFilter(Filter):
    def __init__(self, thread=None, name=''):
        Filter.__init__(self, name=name)
        self.thread = thread or current_thread()

    def filter(self, record):
        return current_thread() == self.thread


class ErrorLogger(LoggerMixin):
    def __init__(self, name="operation", logger=None,
                 level=get_default_level(), *args, **kw):
        super(ErrorLogger, self).__init__(*args, **kw)
        if logger is not None:
            self.logger = logger
        self.name = name
        self.log_level = level
        assert level is not None

    def __enter__(self):
        self.logger.debug("Entering %s", self.name)
        return self

    def __exit__(self, type, value, traceback):
        if type is not None:
            self.logger.exception("Error in %s", self.name)
        else:
            self.logger.log(self.log_level, "%s finished", self.name)


def log_errors(f):
    def _f(*args, **kw):
        with ErrorLogger(f.__name__):
            result = f(*args, **kw)
        get_logger(f).debug("%s returning: %s", f.__name__, result)
        return result
    _f.__name__ = f.__name__
    return _f


def sanitize_dict(d, keys=("password",), replacement="*", inplace=False):
    keys = get_iterable(keys)
    if not inplace:
        d = dict(d)

    if replacement is None:
        for k in keys:
            d.pop(k, None)
    else:
        for k in keys:
            v = d[k]
            if isinstance(v, basestring):
                d[k] = replacement * len(v)
            else:
                d[k] = replacement
    return d
