
from openmtc_server.db import DBAdapter, Shelve, DBError
from openmtc_server.db import BasicSession
from copy import copy
from collections import defaultdict, OrderedDict
from openmtc_server.db.exc import DBConflict, DBNotFound
from openmtc_onem2m.model import OneM2MResource, CSEBase, AE, Container, ContentInstance, Subscription, RemoteCSE
from pymongo import MongoClient

res_type = {'2' : AE,
            '3' : Container,
            '4' : ContentInstance,
            '5' : CSEBase,
            '16' : RemoteCSE,
            '23' : Subscription}

class MongoDBSession(BasicSession):


    def __init__(self, db, std_type, *args, **kw):

        self.db = db
        self.std_type = std_type
        self.resources = db['resources']




    def store(self, resource):

        path = resource.path
        resource_type = type(resource)
        document = resource.values
        document ['path'] = path

        self.logger.debug("Adding resource to db: %s -> %s (%s)",
                          path, resource, resource_type)

        self.resources.insert(document)

    def _get(self, path):
        pass


    def get(self, path):

        document = self.resources.find_one({'path': path}, {'_id': False})
        if document is None:
            document = self.resources.find_one({'resourceID':path}, {'_id': False})
            if document is None:
                raise DBNotFound
        res = self.func (document)
        return res

    def func (self, document):
        res_type_value = document['resourceType']

        modelclass = res_type[str(res_type_value)]
        #print modelclass(**document)
        return modelclass(**document)


    def get_collection(self, resource_type, parent, filter_criteria=None):
        self.logger.debug("Getting %s children of %s (%s)", resource_type,
                          parent, parent.__model_name__)
        parentID = parent.resourceID
        find_children = self.resources.find({'parentID':parentID}, {'_id': False})
        children = map (self.func, find_children)
        return children



    def exists(self, resource_type, fields):
        self.logger.debug("Checking existence of %s with %s", resource_type,
                          fields)
        pass

    def update(self, resource, fields=None):

        document = resource.values
        path = resource.path
        #        document ['path'] = path

        #field = document [fields]

        if fields == None or fields == []:
            document = document
        else:
            # change that document
            pass


        modify = self.resources.find_one_and_update({'path': path}, {'$set': document })

        #print doc


        #document[fields] = fields



    def delete(self, resource):
        document = resource.values
        self.resources.remove(document)

    def commit(self):
        pass

    def rollback(self):
        pass


class MongoDBShelve(dict, Shelve):
    def commit(self):
        pass

    def rollback(self):
        pass


class MongoDB(DBAdapter):
    def __init__(self, *args, **kw):
        super(MongoDB, self).__init__(*args, **kw)

        client = MongoClient('localhost', 27017)
        client.drop_database('mongodb')
        self.db = client['mongodb']
        #self.db.drop_collection()

        self.onem2m_resources = None
        self.shelves = None
        self.initialized = False

    def initialize(self, force=False):
        if not force and self.is_initialized():
            raise Exception("Already initialized")
        #self.onem2m_resources = None
        self.shelves = defaultdict(MongoDBShelve)
        self.initialized = True

    def get_shelve(self, name):
        return self.shelves[name]

    def start_session(self, std_type):
        return MongoDBSession(self.db, std_type)

    def is_initialized(self):
        return self.initialized