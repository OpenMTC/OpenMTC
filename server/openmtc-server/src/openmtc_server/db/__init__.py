from abc import ABCMeta, abstractmethod
from futile.logging import LoggerMixin
from openmtc_onem2m.model import ContentInstance as Cin
from openmtc_server.db.exc import DBError
from collections import MutableMapping


class DBAdapter(LoggerMixin):
    __metaclass__ = ABCMeta

    def __init__(self, config, *args, **kw):
        super(DBAdapter, self).__init__(*args, **kw)

        self.config = config

    @abstractmethod
    def start_session(self, std_type):
        raise NotImplementedError()

    def start_onem2m_session(self):
        return self.start_session('onem2m')

    @abstractmethod
    def get_shelve(self, name):
        raise NotImplementedError()

    @abstractmethod
    def is_initialized(self):
        raise NotImplementedError()

    @abstractmethod
    def initialize(self, force=False):
        raise NotImplementedError()

    def stop(self):
        pass


class Shelve(LoggerMixin, MutableMapping):
    __metaclass__ = ABCMeta

    @abstractmethod
    def commit(self):
        raise NotImplementedError()

    @abstractmethod
    def rollback(self):
        raise NotImplementedError()


class Session(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def store(self, resource):
        raise NotImplementedError()

    @abstractmethod
    def get(self, resource):
        raise NotImplementedError()

    @abstractmethod
    def get_collection(self, resource_type, parent, filter_criteria=None):
        raise NotImplementedError()

    @abstractmethod
    def get_oldest_content_instance(self, parent):
        raise NotImplementedError()

    @abstractmethod
    def get_latest_content_instance(self, parent):
        raise NotImplementedError()

    @abstractmethod
    def exists(self, resource_type, fields):
        raise NotImplementedError()

    @abstractmethod
    def update(self, resource, fields=None):
        raise NotImplementedError()

    @abstractmethod
    def delete(self, resource):
        raise NotImplementedError()

    @abstractmethod
    def delete_children(self, resource_type, parent):
        raise NotImplementedError()

    @abstractmethod
    def commit(self):
        raise NotImplementedError()

    @abstractmethod
    def rollback(self):
        raise NotImplementedError()


class BasicSession(Session, LoggerMixin):
    __metaclass__ = ABCMeta

    def __init__(self, resource_type, *args, **kw):
        super(BasicSession, self).__init__(*args, **kw)

        if resource_type == 'onem2m':
            self.cinType = Cin
        else:
            raise DBError('no valid type: %s' % type)

    @staticmethod
    def _filter_oldest(collection):
        if not collection:
            raise DBError("ContentInstance collection is empty")
        return collection[0]

    def get_oldest_content_instance(self, parent):
        collection = self._get_content_instances(parent)
        return self._filter_oldest(collection)

    @staticmethod
    def _filter_latest(collection):
        if not collection:
            raise DBError("ContentInstance collection is empty")
        return collection[-1]

    def get_latest_content_instance(self, parent):
        collection = self._get_content_instances(parent)
        return self._filter_latest(collection)

    def delete_children(self, resource_type, parent):
        children = self.get_collection(resource_type, parent)
        map(self.delete, children)

    def _get_content_instances(self, parent):
        return self.get_collection(self.cinType, parent)
