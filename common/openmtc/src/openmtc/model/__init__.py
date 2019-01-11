from abc import ABCMeta
from collections import Sequence, OrderedDict, Mapping
from datetime import datetime
from enum import Enum
from iso8601 import parse_date, ParseError
from operator import attrgetter

from futile import basestring, issubclass, NOT_SET
from futile.logging import LoggerMixin
from openmtc.model.exc import ModelError, ModelTypeError


class StrEnum(str, Enum):
    pass


class Collection(Sequence, Mapping):
    def __init__(self, name, type, parent, collection=(), *args, **kw):
        super(Collection, self).__init__(*args, **kw)
        self._map = OrderedDict()
        self.type = type
        self.parent = parent
        self.name = name
        for c in collection:
            self.append(c)

    def __getitem__(self, index):
        if isinstance(index, (int, slice)):
            return list(self._map.values())[index]
        return self._map[index]

    def __contains__(self, v):
        return v in self._map or v in self._map.values()

    def append(self, v):
        if not isinstance(v, self.type):
            raise ModelTypeError(v)

        self._handle_newitem(v)

        assert v.name is not None, "name is None: %s %s" % (v, v.path)
        self._map[v.name] = v

    add = append

    def get(self, k, default=None):
        return self._map.get(k, default)

    def __iter__(self):
        return iter(self._map.values())

    def __len__(self):
        return len(self._map)

    def __delitem__(self, index):
        if isinstance(index, int):
            instance = self[index]
            index = instance.name
        del self._map[index]

    discard = __delitem__

    def _handle_newitem(self, item):
        if item.parent and item.parent is not self.parent:
            # TODO !
            return
            # raise NotImplementedError()
        item.parent = self.parent

    def __str__(self):
        try:
            return "openmtc.Collection(%s, %s)" % (
                self.name, self._map)
        except AttributeError:
            return "openmtc.Collection(%s)" % (self.__len__())


class Member(LoggerMixin):
    def __init__(self, type=str, version="1.0", *args, **kw):
        super(Member, self).__init__(*args, **kw)
        self.type = type
        self.version = version

    def _init(self, name):
        self.name = name

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, self.type):
            value = self.convert(value, instance)
        self.set_value(instance, value)

    def set_value(self, instance, value):
        setattr(instance, "_" + self.name, value)

    def convert(self, value, instance):
        try:
            return self.type(value)
        except (TypeError, ValueError):
            raise ModelTypeError("Illegal value for %s (%s): %r" %
                                 (self.name, self.type, value))

    def __repr__(self):
        return '%s(name="%s", type=%s)' % (type(self).__name__, self.name,
                                           self.type.__name__)


class Attribute(Member):
    RW = "RW"
    RO = "RO"
    WO = "WO"

    def __init__(self, type=str, default=None,
                 accesstype=None, mandatory=None,
                 update_mandatory=None,
                 id_attribute=None, path_attribute=None,
                 id_immutable=None, *args, **kw):
        super(Attribute, self).__init__(type=type, *args, **kw)

        if path_attribute and id_attribute:
            raise ModelError("Attribute can't be id_attribute and "
                             "path_attribute at the same time")

        self.default = default
        self.id_attribute = id_attribute
        self.path_attribute = path_attribute
        self.id_immutable = id_immutable

        if accesstype is None:
            if path_attribute:
                accesstype = self.RO
            elif id_attribute:
                accesstype = self.WO
            else:
                accesstype = self.RW
        self.accesstype = accesstype

        if mandatory is None:
            if accesstype == self.WO:
                mandatory = True
            else:
                mandatory = False
        self.mandatory = mandatory

        if update_mandatory is None:
            if accesstype == self.RW:
                update_mandatory = mandatory
            else:
                update_mandatory = False
        self.update_mandatory = update_mandatory

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        try:
            return getattr(instance, "_" + self.name)
        except AttributeError:
            return self.default


class BytesAttribute(Attribute):
    def __init__(self, default=None, accesstype=None,
                 mandatory=None, *args, **kw):
        super(BytesAttribute, self).__init__(type=bytes,
                                             default=default,
                                             accesstype=accesstype,
                                             mandatory=mandatory, *args,
                                             **kw)

    def convert(self, value, instance):
        if isinstance(value, str):
            return bytes(value, "utf-8")
        return super(BytesAttribute, self).convert(value, instance)


UnicodeAttribute = Attribute


class DatetimeAttribute(Attribute):
    def __init__(self, default=None, accesstype=None,
                 mandatory=False, *args, **kw):
        super(DatetimeAttribute, self).__init__(type=datetime,
                                                default=default,
                                                accesstype=accesstype,
                                                mandatory=mandatory, *args,
                                                **kw)

    def convert(self, value, instance):
        if isinstance(value, str):
            try:
                return parse_date(value)
            except ParseError as e:
                raise ValueError(str(e))
        return super(DatetimeAttribute, self).convert(value, instance)


class ListAttribute(Attribute):
    def __init__(self, content_type=str, type=list,
                 default=NOT_SET, *args, **kw):
        super(ListAttribute, self).__init__(type=type,
                                            default=default, *args, **kw)
        self.content_type = content_type

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        key = "_" + self.name
        try:
            return getattr(instance, key)
        except AttributeError:
            if self.default is NOT_SET:
                subresource = self.type()
            else:
                subresource = self.default
            setattr(instance, key, subresource)
            return subresource

    def _convert_mapping(self, value, instance):
        self.logger.debug("Creating %s from %s", self.content_type, value)
        return self.content_type(**value)

    def convert_content(self, value, instance):
        if isinstance(value, self.content_type):
            return value
        if issubclass(self.content_type, Entity):
            if isinstance(value, Mapping):
                return self._convert_mapping(value, instance)
            raise ValueError("Illegal value for sequence '%s' (%s): %s (%s)" %
                             (self.name, self.content_type, value, type(value)))
        return self.content_type(value)

    def set_value(self, instance, value):
        if value:
            value = self.type([self.convert_content(v, instance)
                               for v in value])
        super(ListAttribute, self).set_value(instance, value)


class StringListAttribute(Attribute):
    def __init__(self, content_type=str, type=list,
                 default=NOT_SET, *args, **kw):
        super(StringListAttribute, self).__init__(type=type, default=default,
                                                  *args, **kw)
        self.content_type = content_type

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        key = "_" + self.name
        try:
            return getattr(instance, key)
        except AttributeError:
            if self.default is NOT_SET:
                subresource = self.type()
            else:
                subresource = self.default
            setattr(instance, key, subresource)
            return subresource

    def convert(self, value, instance):
        if isinstance(value, str):
            return value.strip(' ').split(' ')
        return super(StringListAttribute, self).convert(value, instance)

    def _convert_mapping(self, value, instance):
        self.logger.debug("Creating %s from %s", self.content_type, value)
        return self.content_type(**value)

    def convert_content(self, value, instance):
        if isinstance(value, self.content_type):
            return value
        if issubclass(self.content_type, Entity):
            if isinstance(value, Mapping):
                return self._convert_mapping(value, instance)
            raise ValueError("Illegal value for sequence '%s' (%s): %s (%s)" %
                             (self.name, self.content_type, value, type(value)))
        return self.content_type(value)

    def set_value(self, instance, value):
        if value:
            value = self.type([self.convert_content(v, instance)
                               for v in value])
        super(StringListAttribute, self).set_value(instance, value)


class EntityAttribute(Attribute):
    def __init__(self, type, default=None, accesstype=None, mandatory=None,
                 update_mandatory=None):
        super(EntityAttribute, self).__init__(type=type, default=default,
                                              accesstype=accesstype,
                                              mandatory=mandatory,
                                              update_mandatory=update_mandatory)

    def convert(self, value, instance):
        if isinstance(value, Mapping):
            self.logger.debug("Creating %s from %s", self.type, value)
            return self.type(**value)
        return super(EntityAttribute, self).convert(value, instance)


class CollectionMember(Member):
    def __init__(self, content_type, type=Collection, *args,
                 **kw):  # TODO: kca: use type for content_type
        super(CollectionMember, self).__init__(type=type, *args, **kw)
        self.content_type = content_type

    def convert(self, value, instance):
        try:
            return self.type(collection=value, name=self.name,
                             parent=instance, type=self.content_type)
        except:
            return super(CollectionMember, self).convert(value, instance)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        key = "_" + self.name
        try:
            return getattr(instance, key)
        except AttributeError:
            subresource = self.type(name=self.name, parent=instance,
                                    type=self.content_type)
            setattr(instance, key, subresource)
            return subresource


class SubresourceMember(Member):
    default = None

    def __init__(self, type, virtual=False, default=NOT_SET, *args, **kw):
        if type and not issubclass(type, Resource):
            raise TypeError(type)

        super(SubresourceMember, self).__init__(type=type, *args, **kw)

    def __get__(self, instance, owner=None):
        if instance is None:
            return self

        key = "_" + self.name
        try:
            v = getattr(instance, key)
            if v is not None:
                return v
        except AttributeError:
            pass

        # Here we automatically create missing subresources
        # Might be a stupid idea to do it here
        path = instance.path and instance.path + "/" + self.name or None
        subresource = self.type(
            path=path,
            parent=instance
        )

        # TODO: needs to go into the appropriate resource type(s)
        if hasattr(subresource, "creationTime"):
            creation_time = instance.creationTime
            subresource.creationTime = creation_time
            subresource.lastModifiedTime = creation_time

        setattr(instance, key, subresource)
        return subresource

    @property
    def virtual(self):
        return self.type.virtual


class ResourceType(ABCMeta):
    def __init__(self, *args, **kw):
        super(ResourceType, self).__init__(*args, **kw)

        if ("typename" not in self.__dict__ and
                not self.__name__.endswith("Collection")):
            self.typename = self.__name__[0].lower() + self.__name__[1:]

        self.id_attribute = self.path_attribute = None
        attributes = self.attributes = []
        subresources = self.subresources = []
        collections = self.collections = []

        for name in dir(self):
            if name[0] != "_":
                attr = getattr(self, name)
                if isinstance(attr, Member):
                    if "_" in name:
                        name = name.replace("_", "-")
                        setattr(self, name, attr)
                    attr._init(name)
                    if isinstance(attr, SubresourceMember):
                        subresources.append(attr)
                    elif isinstance(attr, CollectionMember):
                        collections.append(attr)
                    else:
                        attributes.append(attr)

                        if attr.id_attribute and attr.path_attribute:
                            raise ModelTypeError(
                                "Attribute %s of resource %s can only be "
                                "either id_attribute or path_attribute, not "
                                "both." % (name, self.__name__))

                        if attr.id_attribute:
                            if self.id_attribute is not None:
                                raise ModelTypeError(
                                    "Resource %s defines more than one id "
                                    "attribute: %s and %s" %
                                    (self.__name__, self.id_attribute, name))
                            self.id_attribute = attr.name
                            self.id_immutable = attr.id_immutable

                        if attr.path_attribute:
                            if self.path_attribute is not None:
                                raise ModelTypeError(
                                    "Resource %s defines more than one path "
                                    "attribute: %s and %s" %
                                    (self.__name__, self.id_attribute, name))
                            self.path_attribute = attr.name

        self.__members__ = attributes + subresources + collections

    # TODO: caching
    @property
    def attribute_names(self):
        return list(map(attrgetter("name"), self.attributes))

    @property
    def collection_names(self):
        return list(map(attrgetter("name"), self.collections))

    @property
    def subresource_names(self):
        return list(map(attrgetter("name"), self.subresources))

    @property
    def member_names(self):
        return list(map(attrgetter("name"), self.__members__))


class Entity(LoggerMixin, metaclass=ResourceType):
    def __init__(self, *args, **kw):
        self.set_values(kw)

    def set_values(self, values):
        self.logger.debug("Setting values for entity of type %s with %s",
                          type(self), values)
        values = values.copy()

        for member in self.__members__:
            try:
                v = values.pop(member.name)
                if (v is not None and isinstance(member, ListAttribute) and
                        not isinstance(v, (list, tuple, set))):
                    l = [v]
                    v = l
                setattr(self, member.name, v)
            except KeyError:
                try:
                    v = values.pop(member.name + "Reference")
                    # TODO: proper solution?
                    if (v is not None and isinstance(member, ListAttribute) and
                            not isinstance(v, (list, tuple, set))):
                        v = list(v.values())[0]
                    setattr(self, member.name, v)
                except KeyError:
                    pass

        if values:
            self._set_extra_values(values)

    def _set_extra_values(self, values):
        """
        names = type(self).subresource_names
        for k in values.keys():
            if k.strip("Reference") in names:
                values.pop(k)
        print names, values
        from traceback import print_stack
        print_stack()
        """
        if values:
            raise ModelTypeError("%s resource has no attribute %s" %
                                 (self.typename, list(values.keys())[0]))

    @classmethod
    def get_typename(cls):
        return cls.typename

    def get_attribute_values(self, filter=False):
        vals = {}
        for attr in self.attributes:
            a_name = attr.name
            val = getattr(self, a_name)
            if (val is None or val == '' or val == []) and filter:
                continue
            vals[a_name] = val
        return vals
    attribute_values = property(get_attribute_values)

    def get_values_representation(self, fields=None, internal=False):
        vals = {}
        id_attribute = self.id_attribute
        for attr in self.attributes:
            a_name = attr.name
            if (fields is None or a_name == id_attribute or a_name in fields) \
                    and (internal or attr.accesstype is not None):
                val = getattr(self, "_" + a_name, None)
                if val is None:
                    continue
                if isinstance(attr, ListAttribute):
                    # TODO: return simple values. No representation
                    if attr.content_type is AnyURI:  # any uri list
                        vals[a_name] = {"reference": val}
                    elif issubclass(attr.content_type, Entity):  # complex list
                        vals[a_name] = {
                            a_name: [x.get_values_representation() for x in val]
                        }
                    else:  # simple list
                        vals[a_name] = {a_name[:-1]: val}
                elif isinstance(attr, EntityAttribute):
                    vals[a_name] = val.values
                else:
                    try:
                        val = val.isoformat()
                    except AttributeError:
                        pass
                    vals[a_name] = val
        return vals

    def get_values(self, filter=False):
        return self.get_attribute_values(filter)

    @property
    def values(self):
        return self.get_values()

    @property
    def subresource_values(self):
        vals = {}
        for attr in self.subresources:
            vals[attr.name] = getattr(self, attr.name)
        return vals


class ContentResource(Entity):
    virtual = True
    __model_name__ = None
    __model_version__ = None

    def __init__(self, value, *args, **kw):
        kw = {'CONTENT': value}
        super(ContentResource, self).__init__(*args, **kw)

    @property
    def values(self):
        return self.get_values().get('CONTENT')


class Resource(Entity):
    virtual = False
    __model_name__ = None
    __model_version__ = None

    def __init__(self, path=None, parent=None, *args, **kw):
        if path is not None and not isinstance(path, str):
            raise TypeError(path)
        self.__path = path
        self.parent = parent
        super(Resource, self).__init__(*args, **kw)

    def get_path(self):
        return self.__path

    def set_path(self, path):
        self.__path = path
        if self.id_attribute and getattr(self, self.id_attribute) is None:
            setattr(self, self.id_attribute, path.rpartition("/")[-1])
        if self.path_attribute and getattr(self, self.path_attribute) is None:
            setattr(self, self.path_attribute, path)

    path = property(get_path, set_path)

    @property
    def parent_path(self):
        if self.__path is not None:
            return self.__path.rpartition("/")[0]

    # TODO: deprecated
    @property
    def name(self):
        return self.basename

    @property
    def basename(self):
        if self.path is not None:
            return self.path.rpartition("/")[-1]
        if self.id_attribute is not None:
            return getattr(self, self.id_attribute)

    def set_values(self, values):
        values = values.copy()

        keys = [k for k in values.keys() if "_" in k]
        for k in keys:
            values[k.replace("_", "-")] = values.pop(k)

        path = self.path
        if path is not None:
            id_attribute = self.id_attribute
            if (id_attribute is not None and
                    id_attribute not in values):
                values[id_attribute] = path.rpartition("/")[-1]

            path_attribute = self.path_attribute
            if (path_attribute is not None and
                    path_attribute not in values):
                values[path_attribute] = path

        for member in self.__members__:
            try:
                v = values.pop(member.name)
                # FIXME: move into de-serializer and handle dicts
                if (v is not None and isinstance(member, ListAttribute) and
                        not isinstance(v, (list, tuple, set))):
                    v = list(v.values())[0]
                setattr(self, member.name, v)
            except KeyError:
                try:
                    v = values.pop(member.name + "Reference")
                    # TODO: proper solution?
                    if (v is not None and isinstance(member, ListAttribute) and
                            not isinstance(v, (list, tuple, set))):
                        v = list(v.values())[0]
                    setattr(self, member.name, v)
                except KeyError:
                    pass

        if values:
            self._set_extra_values(values)

    def __repr__(self):
        return "%s(path='%s', name='%s')" % (type(self).__name__, self.path,
                                             self.name)

    def __eq__(self, o):
        try:
            return self.path == o.path
        except AttributeError:
            return False

    def __ne__(self, o):
        return not self.__eq__(o)


class FlexibleAttributesMixin(object):
    def __init__(self, path=None, parent=None, *args, **kw):
        self._flex_attrs = set()

        super(FlexibleAttributesMixin, self).__init__(path=path, parent=parent,
                                                      *args, **kw)

    def __setattr__(self, k, v):
        if not k.startswith("_") and not hasattr(self, k) and k != "parent":
            self._flex_attrs.add(k)

        return super(FlexibleAttributesMixin, self).__setattr__(k, v)

    def __delattr__(self, k):
        self._flex_attrs.discard(k)

        return super(FlexibleAttributesMixin, self).__delattr__(k)

    @property
    def flex_values(self):
        return {k: getattr(self, k) for k in self._flex_attrs}

    def get_values(self, filter=False):
        vals = super(FlexibleAttributesMixin, self).get_values(filter)
        vals.update(self.flex_values)
        return vals

    def get_values_representation(self, fields=None, internal=False):
        r = super(FlexibleAttributesMixin, self) \
            .get_values_representation(fields=fields, internal=internal)
        if fields is None:
            r.update(self.flex_values)
        return r

    def _set_extra_values(self, values):
        for k, v in values.items():
            setattr(self, k, v)


class AnyURI(str):
    pass


class AnyURIList(Entity):
    reference = ListAttribute(mandatory=False)
