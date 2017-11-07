from futile.logging import LoggerMixin
from futile import ObjectProxy
from openmtc.model import Collection
from openmtc.mapper.exc import MapperError


class MemberProxy(ObjectProxy):
    def __get__(self, instance, owner=None):
        if instance is None:
            return self._o

        if not instance._synced:
            if not _is_attached(instance) or self.name not in instance._changes:
                instance._mapper._init_resource(instance)
        return self._o.__get__(instance, owner)

    def __set__(self, instance, value):
        if _is_attached(instance):
            instance._changes.add(self._o.name)
        return self._o.__set__(instance, value)


class MapperCollection(Collection):
    def __init__(self, name, type, parent, collection=(), *args, **kw):
        super(MapperCollection, self).__init__(name=name, type=type,
                                               parent=parent,
                                               collection=collection, *args,
                                               **kw)

    def _handle_newitem(self, item):
        if _is_attached(item) or item.path is not None:
            raise NotImplementedError()
        super(MapperCollection, self)._handle_newitem(item)
        self._changes.added.add(item)
        if _is_attached(self.parent):
            self.parent._changes.collection_changes.add(self.name)
            if self.parent.parent is not None:
                self.parent.parent._changes.subresource_changes.add(
                    self.parent.name)


class BasicMapper(LoggerMixin):
    def __init__(self, *args, **kw):
        super(BasicMapper, self).__init__(*args, **kw)
        # self._patch_model()
        self._send_request = lambda x: x

    def create(self, path, instance):
        raise NotImplementedError()

    def update(self, instance, fields):
        raise NotImplementedError()

    def _do_update(self, instance, fields):
        raise NotImplementedError()

    def get(self, path):
        raise NotImplementedError()

    def delete(self, instance):
        raise NotImplementedError()

    def _get_data(self, path):
        raise NotImplementedError()

    def _map(self, path, typename, data):
        raise NotImplementedError()

    def _init_resource(self, res):
        return self._fill_resource(res, self._get_data(res.path)[1])

    def _make_subresource(self, type, path, parent):
        subresource = type(path=path, parent=parent)
        subresource._synced = False
        # return self._attach_instance(subresource)
        return subresource

    def _fill_resource(self, res, data):
        raise NotImplementedError()

    @classmethod
    def _patch_model(cls):
        import openmtc.model as model

        model.Resource._synced = True
        model.Resource._mapper = None

        for t in model.get_types():
            if "_initialized" not in t.__dict__:
                setattr(t, "_initialized", True)
                for a in t.__members__:
                    # TODO: deal with name differences
                    setattr(t, a.name, MemberProxy(a))
                for a in t.collections:
                    if a.type is not Collection:
                        raise NotImplementedError()
                    a.type = MapperCollection
