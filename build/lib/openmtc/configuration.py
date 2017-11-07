import logging
from abc import ABCMeta, abstractmethod

from enum import Enum

from futile import NOT_SET, identity
from futile.logging import LoggerMixin
from openmtc.exc import OpenMTCError


class ConfigurationError(OpenMTCError):
    pass


class ConfigurationKeyError(KeyError, ConfigurationError):
    pass


class ConfigurationAttributeError(AttributeError, ConfigurationError):
    pass


class ConfigurationValueError(ValueError, ConfigurationError):
    pass


class ExtraOptionsStrategy(Enum):
    ignore = "ignore"
    warn = "warn"
    prune = "prune"
    fatal = "fatal"


class ConfigurationOption(LoggerMixin):
    __metaclass__ = ABCMeta

    def __init__(self, type, default=NOT_SET, converter=identity,
                 *args, **kw):
        super(ConfigurationOption, self).__init__(*args, **kw)
        self.type = type
        self.default = default
        self.converter = converter

    def convert(self, v):
        if v is None:
            if self.default is not NOT_SET:
                return self.default
            raise ConfigurationValueError("Value must not be None")

        v = self._convert(v)
        return self.converter(v)

    @abstractmethod
    def _convert(self, v):
        return v


class SimpleOption(ConfigurationOption):
    def __init__(self, type=str, default=NOT_SET, converter=identity,
                 *args, **kw):
        super(SimpleOption, self).__init__(type=type, default=default,
                                           converter=converter)

    def _convert(self, v):
        if isinstance(v, self.type):
            return v
        return self.type(v)


class ListOption(SimpleOption):
    def __init__(self, content_type, type=list, default=NOT_SET,
                 converter=identity, *args, **kw):
        super(ListOption, self).__init__(type=type, default=default,
                                         converter=converter)
        self.content_type = content_type

    def _convert(self, v):
        v = super(ListOption, self)._convert(v)
        return map(self._convert_content, v)

    def _convert_content(self, v):
        if not isinstance(v, self.content_type):
            v = self.content_type(v)
        return v


class BooleanOption(ConfigurationOption):
    def __init__(self, default=NOT_SET, converter=identity, *args, **kw):
        super(BooleanOption, self).__init__(type=bool, default=default,
                                            converter=converter)

    def _convert(self, v):
        if isinstance(v, (bool, int)):
            return bool(v)
        if isinstance(v, basestring):
            return v and v.lower() not in ("0", "no", "n", "f", "false")
        raise ConfigurationValueError("Illegal value for boolean: %s" % (v, ))


class EnumOption(SimpleOption):
    def _convert(self, v):
        try:
            return super(EnumOption, self)._convert(v)
        except Exception as exc:
            try:
                return getattr(self.type, v)
            except:
                raise exc


class LowerCaseEnumOption(EnumOption):
    def _convert(self, v):
        try:
            return super(LowerCaseEnumOption, self)._convert(v)
        except Exception as exc:
            try:
                return getattr(self.type, v.lower())
            except:
                raise exc


class Configuration(dict):
    __options__ = {}
    __name__ = "configuration"
    __extra_options_strategy__ = ExtraOptionsStrategy.ignore

    def __init__(self, *args, **kw):
        config = dict(*args, **kw)
        options = self.__options__.copy()

        for k, v in config.copy().items():
            try:
                option = options.pop(k)
            except KeyError:
                strategy = self.__extra_options_strategy__
                if strategy == ExtraOptionsStrategy.fatal:
                    raise ConfigurationError("Unknown configuration key in %s:"
                                             " %s" % (self.__name__, k))
                if strategy == ExtraOptionsStrategy.prune:
                    del config[k]
                elif strategy == ExtraOptionsStrategy.warn:
                    self.logger.warn("Unknown configuration key in %s: %s",
                                     self.__name__, k)
            else:
                config[k] = option.convert(v)

        for k, v in options.items():
            if v.default is NOT_SET:
                raise ConfigurationKeyError("Missing configuration key in"
                                            " %s: %s" %
                                            (self.__name__, k, ))
            config[k] = v.default

        super(Configuration, self).__init__(config)

    def __getitem__(self, k):
        try:
            return dict.__getitem__(self, k)
        except KeyError:
            raise ConfigurationKeyError("Missing configuration key in"
                                        " %s: %s" %
                                        (self.__name__, k, ))

    def __getattr__(self, k, default=NOT_SET):
        try:
            return self[k]
        except ConfigurationKeyError as exc:
            if default is not NOT_SET:
                return default
            raise ConfigurationAttributeError(str(exc))


class LogLevel(Enum):
    trace = logging.DEBUG
    debug = logging.DEBUG
    warning = logging.WARNING
    error = logging.ERROR
    fatal = logging.FATAL
