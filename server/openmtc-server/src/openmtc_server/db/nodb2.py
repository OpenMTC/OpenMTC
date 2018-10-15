from openmtc_server.db import DBAdapter, Shelve, DBError
from openmtc_server.db import BasicSession
from copy import copy
from collections import defaultdict, OrderedDict
from openmtc_server.db.exc import DBConflict, DBNotFound
from openmtc_onem2m.model import OneM2MResource


class NoDB2Session(BasicSession):
    def __init__(self, db, std_type, *args, **kw):
        super(NoDB2Session, self).__init__(std_type, *args, **kw)

        self.db = db
        self.std_type = std_type

        if std_type == 'onem2m':
            self.resources = db.onem2m_resources
            self.children = db.onem2m_children
            self.resource_type = OneM2MResource
        else:
            raise DBError('no valid type: %s' % type)

    def store(self, resource):
        path = resource.path

        resource_type = type(resource)

        self.logger.debug("Adding resource to db: %s -> %s (%s)",
                          path, resource, resource_type)

        if path and path in self.resources:
            raise DBConflict(path)

        if resource_type is not self.resource_type:
            parent_path = resource.parent_path
            self.logger.debug("parent path: %s", parent_path)
            try:
                children = self.children[parent_path]
            except KeyError:
                self.logger.debug("No parent found")
            else:
                children[resource_type][resource.path] = resource

        self.children[path] = defaultdict(OrderedDict)
        self.resources[path] = resource
        if self.std_type == 'onem2m':
            self.resources[resource.resourceID] = resource

    def _get(self, path):
        try:
            return self.resources[path]
        except KeyError:
            self.logger.debug("Resource not found")
            raise DBNotFound(path)

    def get(self, path):
        assert path is not None
        self.logger.debug("Getting resource: %s", path)
        resource = self._get(path)
        return copy(resource)

    def get_collection(self, resource_type, parent, filter_criteria=None):
        self.logger.debug("Getting %s children of %s (%s)", resource_type,
                          parent, parent.__model_name__)

        if parent.__model_name__ == "onem2m":
            if resource_type is None:
                resources = []
                for v in self.children[parent.path].values():
                    resources += list(v.values())
            elif isinstance(resource_type, (list, tuple, set)):
                resources = []
                for k, v in self.children[parent.path].items():
                    if k in resource_type:
                        resources + list(v.values())
            else:
                resources = list(self.children[parent.path][resource_type].values())
        else:
            resources = list(self.children[parent.path][resource_type].values())
        self.logger.debug("Found children: %s", resources)
        return resources

    def exists(self, resource_type, fields):
        self.logger.debug("Checking existence of %s with %s", resource_type,
                          fields)
        fields = dict(fields)

        if not fields:
            raise ValueError(fields)

        if len(fields) != 1:
            raise NotImplementedError("exist() only works for path")

        if resource_type is not None:
            if issubclass(resource_type, self.resource_type):
                path = fields.get("path")
                if not path:
                    raise NotImplementedError("exist() only works for path")
                return path in self.resources

        path = fields.get("path")
        if path:
            return path in self.resources

        try:
            return fields["path"] in self.resources
        except KeyError:
            raise NotImplementedError("exist() only works for path")

    def update(self, resource, fields=None):
        old_resource = self._get(resource.path)
        self.logger.debug("Updating resource %s with %s", resource.path, fields)

        if fields is None:
            old_resource.set_values(resource.values)
        else:
            for field in fields:
                setattr(old_resource, field, getattr(resource, field))

    def delete(self, resource):
        self.logger.debug("Deleting: %s", resource)

        del self.resources[resource.path]
        if self.std_type == 'onem2m':
            del self.resources[resource.resourceID]
        del self.children[resource.path]
        try:
            children = self.children[resource.parent_path]
        except KeyError:
            self.logger.debug("No parent found")
        else:
            del children[type(resource)][resource.path]

    def commit(self):
        pass

    def rollback(self):
        pass


class NoDB2Shelve(dict, Shelve):
    def commit(self):
        pass

    def rollback(self):
        pass


class NoDB2(DBAdapter):
    def __init__(self, *args, **kw):
        super(NoDB2, self).__init__(*args, **kw)
        self.onem2m_resources = None
        self.onem2m_children = None
        self.shelves = None
        self.initialized = False

    def initialize(self, force=False):
        if not force and self.is_initialized():
            raise Exception("Already initialized")
        self.onem2m_resources = {}
        self.onem2m_children = {}
        self.shelves = defaultdict(NoDB2Shelve)
        self.initialized = True

    def get_shelve(self, name):
        return self.shelves[name]

    def start_session(self, std_type):
        return NoDB2Session(self, std_type)

    def is_initialized(self):
        return self.initialized
