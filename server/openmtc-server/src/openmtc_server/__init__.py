from futile.logging import LoggerMixin
from abc import ABCMeta, abstractmethod


class Component(LoggerMixin):
    def initialize(self, api):
        pass

    def start(self):
        pass

    def stop(self):
        pass


class Serializer(LoggerMixin):
    __metaclass__ = ABCMeta

    @abstractmethod
    def encode(self, resource):
        raise NotImplementedError()

    @abstractmethod
    def decode(self, input):
        raise NotImplementedError()
