from datetime import timedelta
from openmtc.configuration import (Configuration, BooleanOption, ListOption,
                                   LowerCaseEnumOption, LogLevel, SimpleOption)


def timedelta_in_seconds(sec):
    return timedelta(seconds=sec)


class GlobalConfiguration(Configuration):
    __name__ = "global configuration"
    __options__ = {"disable_forwarding": BooleanOption(default=False),
                   "default_lifetime": SimpleOption(type=int,
                                                    default=timedelta_in_seconds(60 * 60),
                                                    converter=timedelta_in_seconds),
                   "max_lifetime": SimpleOption(type=int,
                                                default=timedelta_in_seconds(60 * 60 * 24),
                                                converter=timedelta_in_seconds),
                   "min_lifetime": SimpleOption(type=int,
                                                default=timedelta_in_seconds(5),
                                                converter=timedelta_in_seconds),
                   "additional_host_names": ListOption(str),
                   "require_auth": BooleanOption(default=False),
                   "default_content_type": SimpleOption()}


class LoggingConfiguration(Configuration):
    __name__ = "logging configuration"
    __options__ = {"level": LowerCaseEnumOption(default=LogLevel.error),
                   "file": SimpleOption(default=None)}


class MainConfiguration(Configuration):
    __name__ = "main configuration"
    __options__ = {"global": SimpleOption(GlobalConfiguration),
                   "logging": SimpleOption(LoggingConfiguration)}
