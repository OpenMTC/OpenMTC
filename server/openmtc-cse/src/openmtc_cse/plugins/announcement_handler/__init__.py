from collections import namedtuple

from openmtc_onem2m.exc import CSEError
from openmtc_onem2m.model import AnnounceableResource, get_onem2m_type, \
    CSEBase, RemoteCSE

from openmtc_onem2m.transport import OneM2MRequest, MetaInformation, \
    OneM2MOperation
from openmtc_server.Plugin import Plugin
from copy import deepcopy
from openmtc_server.util.async_ import async_all
from re import sub
from urllib.parse import urlparse
# url join with coap compatibility
from urllib.parse import urljoin, uses_relative, uses_netloc

uses_relative.append('coap')
uses_netloc.append('coap')

AnncResult = namedtuple('AnncResult', ['cse_uri', 'res_con'])


class AnnouncementHandler(Plugin):
    # method constants
    _CREATE = 'create'
    _UPDATE = 'update'
    _DELETE = 'delete'

    def __init__(self, api, config, *args, **kw):
        super(AnnouncementHandler, self).__init__(api, config, *args, **kw)
        self._announcements = {}
        self._cse_base = urlparse(self.config['global']['cse_base']).path
        # TODO_oneM2M: self._cse_links should be filled with registration plugin, using a static value in the mean time
        # self._cse_links = {}
        self._cse_links = {
            'http://localhost:15000/onem2m': 'http://localhost:15000/onem2m'}

    def _init(self):
        # subscribe for announceable resources
        self.events.resource_created.register_handler(self._update_annc_create,
                                                      AnnounceableResource)
        self.events.resource_updated.register_handler(self._update_annc_update,
                                                      AnnounceableResource)
        self.events.resource_deleted.register_handler(self._delete_annc,
                                                      AnnounceableResource)

        # We keep track of the CSEs that are registered,
        # in case we need to set default announceTo
        self.events.resource_created.register_handler(self._cse_created,
                                                      CSEBase)
        self.events.resource_deleted.register_handler(self._cse_deleted,
                                                      CSEBase)

        self._initialized()

    def _start(self):
        def retrieve_remote_cse_list():
            def get_collection(session):
                p = session.get_collection(None, RemoteCSE,
                                           CSEBase(path="/onem2m"))
                session.commit()
                return p

            return self.api.db.start_session().then(get_collection)

        def get_cse(cse):
            cse_req = OneM2MRequest(OneM2MOperation.retrieve, cse, None,
                                    MetaInformation(None))
            return (self.api.handle_onem2m_request(cse_req)
                    .then(lambda r: r.resource))

        def handle_remote_cse_list(remote_cse_list):
            self.logger.debug("Loaded RemoteCSE list is %s" % remote_cse_list)
            for cse in remote_cse_list:
                self.logger.debug("Adding CSE %s in the list" % cse)
                self._cse_links[cse.path] = cse.link

        return retrieve_remote_cse_list() \
            .then(
            lambda remote_cse_list: async_all(list(map(get_cse, remote_cse_list)))) \
            .then(handle_remote_cse_list) \
            .then(self._started)
        # return self._started()

    def _cse_created(self, cse, req):
        # TODO_oneM2M: Test this with RemoteCSE registration
        self._cse_links[cse.path] = cse.link

    def _cse_deleted(self, resource, req):
        self._cse_links.pop(req.to, None)

    def _update_annc_create(self, resource, onem2m_req):
        self.logger.debug("_update_annc_create: resource.announceTo is %s",
                          resource.announceTo)
        self.logger.debug("_update_annc_create: request is %s", onem2m_req)
        self._announcements[resource.path] = {
            'resource': deepcopy(resource),
            'uris': {}
        }
        try:
            # self._announcements[resource.path]['resource'].announceTo[
            #    'cseList']['reference'] = []
            self._announcements[resource.path]['resource'].announceTo = []
        except KeyError:
            pass
        # except TypeError:
        #    self._announcements[resource.path]['resource'].announceTo = {
        #        'cseList': {
        #            'reference': []
        #        }
        #    }

        if resource.typename == 'AE':
            req_ent = resource.path
        else:
            # req_ent = onem2m_req.requestingEntity
            req_ent = onem2m_req.originator
        self._update_annc(resource, self._CREATE, req_ent)

    def _update_annc_update(self, resource, onem2m_req):
        self.logger.debug("_update_annc_update: %s", resource)
        # if not req_ind.do_announce:
        #    return
        # self._update_annc(resource, self._UPDATE, req_ind.requestingEntity)
        self._update_annc(resource, self._UPDATE, onem2m_req.originator)

    def _update_annc(self, resource, method, req_ent):
        self.logger.debug("_update_annc %s - %s: ", resource,
                          resource.announceTo)

        if resource.announceTo:
            # This action shall apply if the following conditions are met:
            # * A new announceable resource is created in the local CSE and the
            # CREATE request contains an announceTo attribute.
            # * The announceTo attribute of the announceable resource is
            # added/changed.
            self._update_annc_by_app(resource, method, req_ent)
            # else:
            #    # This action shall apply if the following conditions are met:
            #    # * A new announceable resource is created in the local CSE, the
            #    # CREATE request does not contain an announceTo attribute.
            #    # * The announceTo attribute is removed from the resource
            #    # representation by an XXXUpdateRequestIndication (where XXX
            #    # represents the resource that contains the announceTo attribute).
            #    self._update_annc_by_cse(resource, req_ent)

    def _update_annc_by_app(self, resource, method, req_ent):

        # 1) If the announceTo attribute contains the activated element set
        # to FALSE and the original request that triggered this action is
        # not a CREATE, then the local CSE shall reject the original
        # request with STATUS_NOT_FORBIDDEN and then this procedure stops.
        # if method != self._CREATE:
        #    resource.announce_to.set('activated', True)

        # 2) If the announceTo attribute contains the activated element set
        # to FALSE and the original request that trigger this action is a
        # CREATE, then the announceTo attribute value is stored as-is in the
        # resource. No further actions are required.
        # else:
        #   self._update_resource(resource)

        # In oneM2M, if announceTo is present, it has to be handled. (no ignoring)
        # TODO_oneM2M: Deal w/ updates
        force = method == 'update'
        self._handle_announce_to(resource, req_ent) \
            .then(lambda l: self._update_resource(resource, l[0], l[1], force))

    """ TODO_oneM2M: Check if this really is obsolete
    def _update_annc_by_cse(self, resource, req_ent):
        # 1) It checks if the issuer is an application registered to this local
        # CSE, if not the procedure stops here, otherwise the local CSE checks
        # if global element is set to TRUE. (If global is set to FALSE the
        # procedure does not apply).
        def get_app():
            get_app_req_ind = RetrieveRequestIndication(urlparse(req_ent).path)
            return self.api.handle_request_indication(get_app_req_ind) \
                .then(lambda r: r.resource)

        def handle_app(app):
            # Todo: get application if resource is not an application
            # 2) The cseList of announceTo of the application Registration is
            # used (note that the list may be empty, in case the issuer wants
            # to forbid announcing any created resources).

            # 3) If the activate element of the announceTo attribute from the
            # application resource is set to FALSE, then the local CSE adds the
            # announceTo attribute in the announceable resource (that trigger
            # this procedure) and it sets the activate element to FALSE. The
            # action returns.

            # 4) Otherwise (i.e. global set to FALSE or no announceTo is
            # present), the CSE determines based on its policies, if the
            # resource shall be announced:
            #resource.announceTo = {'cseList': {'reference': []}}
            resource.announceTo = []

            # a) If the policies state the resource shall not be announced,
            # this action returns and the original procedure is continued.

            # b) Otherwise, the CSE determines which CSEs shall be in the
            # cseList element of the announceTo attribute. The CSE also set the
            # active element to TRUE.

            # Then, the local CSE shall announce the resource to the CSEs in the
            # cseList element. This procedure is described in step 3, from a to e
            # in clause 10.3.2.8.1, with the exception that the requestingEntity
            # for any initiated request is set to the CSE hosting the announcing
            # resource.
            # 5) The announceTo with the updated cseList is set on the
            # original resource (that trigger this procedure). This may
            # trigger notifications to resources that have subscribed to
            # changes in the original resource or its announceTo attribute.
            pass

        # get_app().then(handle_app)
        #if self.config.get("auto_announce", True):
        #    #resource.announceTo = {
        #    #    'cseList': {'reference': self._cse_links.values()},
        #    #    'activated': True
        #    #}
        #    resource.announceTo = self._cse_links.values()
        #    # TODO: update the resource internally
        #else:
        #    #resource.announceTo = {'cseList': {'reference': []}}
        #    resource.announceTo = []

        self.logger.debug('resource announceTo is %s'%resource.announceTo)
        self._handle_announce_to(resource, req_ent) \
            .then(lambda l: self._update_resource(resource, l[0], l[1], True))
    """

    def _delete_annc(self, resource, onem2m_req):
        # if req_ind.expired:
        #            return self._announcements.pop(req_ind.path, None)

        # req_ent = req_ind.requestingEntity
        originator = onem2m_req.originator
        try:
            resource = deepcopy(self._announcements[onem2m_req.to]['resource'])
        except KeyError:
            return
        # resource.announceTo = {'cseList': {'reference': []}}
        resource.announceTo = []

        self._handle_announce_to(resource, originator) \
            .then(lambda r: self._announcements.pop(onem2m_req.to, None))

    def _handle_announce_to(self, resource, req_ent):
        self.logger.debug("Handle annouceTo called %s" % resource)
        try:
            old_resource = self._announcements[resource.path]['resource']
        except KeyError:
            # todo: handle missing resource
            raise CSEError()
        try:
            # old_cse_list = old_resource.announceTo.get('cseList') \
            #    .get('reference') \
            #    if old_resource.announceTo.get('activated', True) else []
            old_cse_list = old_resource.announceTo
        except AttributeError:
            old_cse_list = []

        # db_cse_list = resource.announceTo.get('cseList', {
        #    "reference": []
        # }).get('reference')
        db_cse_list = resource.announceTo

        annc_model = get_onem2m_type(resource.typename + "Annc")

        resource_id = getattr(resource, resource.id_attribute)
        annc_id = resource_id + 'Annc'

        # a) Check if the CSEs indicated in the cseList element of the
        # announceTo attribute are registered to/from this local CSE. If any of
        # the CSEs in the cseList is not registered then those CSEs are removed
        # from the cseList and no further actions for those CSEs are performed.
        def check_cse_list():
            self.logger.debug("check_cse_list: %s vs %s" % (
            db_cse_list, list(self._cse_links.values())))
            return [x for x in list(self._cse_links.values()) if x in db_cse_list]

        # b) Send createXXXAnnouncementResourceRequestIndication (where XXX is
        # replaced by the type of the resource to be announced) for each CSE in
        # the cseLists element of the announceTo attribute that is NOT yet
        # included in the previous-announceTo. The request includes:
        def send_create_annc_pre(cse_uri):
            try:
                if resource.accessRightID is None:
                    return send_create_annc(cse_uri)
            except AttributeError:
                return send_create_annc(cse_uri)

            return self.api.is_local_path(resource.accessRightID) \
                .then(lambda local_ar: send_create_annc(cse_uri, local_ar))

        def send_create_annc(cse_uri, local_ar=None):
            annc = annc_model()
            # endpoint = self.api.get_endpoint('mid', urlparse(cse_uri).scheme)
            endpoint = self.config.get('endpoint', '')

            # * labels from the original resource;
            annc.labels = resource.labels

            # * accessRightID from the original resource;
            if local_ar:
                annc.accessRightID = urljoin(endpoint, urlparse(
                    resource.accessRightID).path)
            elif local_ar is None:
                annc.accessRightID = local_ar
            else:
                annc.accessRightID = resource.accessRightID

            # * link is set to the URI of the original resource;
            annc.link = urljoin(endpoint, resource.path)
            # annc.link = self._cse_base + resource.path

            # * requestingEntity is set to the application;
            # req_ent from from outer scope

            # * issuer is set to its own CSE ID (the local CSE performing the
            # action);
            # rst: not needed probably

            # * id of the resource shall be set to the id of the original
            # resource postfixed with Annc. I.e. if the original resource has id
            # "myApp", the announced resource shall have the id "myAppAnnc";
            annc.AE_ID = annc_id
            annc.name = annc_id

            # * expirationTime handling is to the discretion of the CSE
            # implementation. It is the responsibility of the local CSE to keep
            # the announced resource in sync with the lifetime of the original
            # resource, as long as the announcement is active. One strategy to
            # minimize signalling would be to request the same expiration from
            # the original resource. If this is accepted by the remote CSE, then
            # no explicit de-announce is needed in case of expiration of the
            # original resource;
            annc.expirationTime = resource.expirationTime

            # * targetID is set as follow.
            # RODO: inline
            def get_target_id():
                cse_path = cse_uri  # + '/cses/' + self.config['global']['cse_id']
                apps_path = self._cse_base  # + '/applications/'
                if resource.typename == 'AE':  # 'application':  # is appAnnc
                    return cse_path  # + '/applications/'
                else:
                    # TODO_oneM2M: Translate to onem2m
                    parent = sub(r'^locationC', 'c', resource.typename) + 's/'
                    if resource.path.find(apps_path) == 0:  # is under appAnnc
                        # todo: lookup appAnnc in self._announcements
                        return cse_path + '/applications/' + \
                               sub(apps_path, '', resource.path).split('/')[0] + \
                               'Annc/' + parent
                    else:  # is other Annc
                        return cse_path + '/' + parent

            target_id = get_target_id()
            # try:
            #    req_ent_mid = urljoin(endpoint, urlparse(req_ent).path)
            # except AttributeError:
            #    self.logger.exception("Could not midify")
            #    req_ent_mid = None
            req_ent_mid = None

            # create_annc_req_ind =\
            #    CreateRequestIndication(target_id, annc,
            #                            requestingEntity=req_ent_mid)
            #
            # return self.api.send_request_indication(create_annc_req_ind)
            cse_req = OneM2MRequest(OneM2MOperation.create, target_id, req_ent_mid,
                                    MetaInformation(None), cn=annc, ty=annc_id)
            self.logger.debug('Sending Announcement %s' % cse_req)
            return self.api.send_onem2m_request(cse_req)

        # c) Ignore all CSEs in the cseList element of the announceTo attribute
        # that were already included in the previous-announceTo.

        # d) Send deleteXXXAnnouncementResourceRequestIndication (where XXX is
        # replaced by the type of resource to be de-announced) for each CSE in
        # the previous-announceTo that is not included in the cseList of the
        # provided announceTo attribute. The request shall include the URI of
        # the announcement resource to be removed. The request includes:
        def send_delete_annc(cse_uri):
            # * requestingEntity is set to the application;
            # req_ent from from outer scope

            # * issuer is set to its own CSE ID (the local CSE performing the
            # action);
            # rst: not needed probably

            # * targetID is set to the resource URI of the previously
            # announced-resource on the remote CSE. The local CSE received and
            # stored the URI of the announced resource after it was created.
            self.logger.debug("announcements %s" % self._announcements)
            annc_path = self._announcements[resource.path]['uris'][cse_uri]
            target_id = urljoin(cse_uri, '/onem2m/' + annc_path)

            cse_req = OneM2MRequest(OneM2MOperation.delete, target_id, None,
                                    MetaInformation(None))
            self.logger.debug('Deleting Announcement %s' % cse_req)
            return self.api.send_onem2m_request(cse_req)
            # delete_annc_req_ind =\
            #    DeleteRequestIndication(target_id, requestingEntity=req_ent)
            #
            # return self.api.send_request_indication(delete_annc_req_ind)

        # e) Waits until all the createXXXAnnouncementResourceResponseConfirm
        # and/or deleteXXXAnnouncementResourceResponseConfirm are received and
        # it acts as follow:
        def send_anncs(cse_list):
            # i) For each unsuccessful
            # createXXXAnnouncementResourceResponseIndication, the remote CSE is
            # removed from the cseList in the announceTo attribute.
            def handle_create_err(res):
                return res.cse_uri

            # ii) For each successful
            # createXXXAnnouncementResourceResponseIndication, the local CSE
            # shall internally store the resourceURI of the created announced
            # resource. This URI is needed for delete the resource later on.
            def handle_create(res):
                # self._announcements[resource.path]['uris'][res.cse_uri] = \
                #    res.res_con.resourceURI
                self._announcements[resource.path]['uris'][
                    res.cse_uri] = annc_id
                return False

            # iii) For each unsuccessful
            # deleteXXXAnnouncementResourceRequestIndication with the statusCode
            # STATUS_NOT_FOUND, the remote CSE is removed from the cseList in
            # the announceTo attribute.
            # For all other statusCode value, no action is performed.
            def handle_delete_err(res):
                try:
                    if res.res_con.statusCode != 'STATUS_NOT_FOUND':
                        return res.cse_uri
                finally:
                    del self._announcements[resource.path]['uris'][res.cse_uri]
                    return False

            # iv) For each successful
            # deleteXXXAnnouncementResourceRequestIndication, the remote CSE is
            # removed from the cseList in the announceTo attribute.
            def handle_delete(res):
                del self._announcements[resource.path]['uris'][res.cse_uri]
                return False

            create_list = [x for x in cse_list if x not in set(old_cse_list)]
            delete_list = [x for x in old_cse_list if x not in set(cse_list)]
            self.logger.debug(
                'create list %s \n delete list %s' % (cse_list, old_cse_list))

            filtered_cses = [x for x in db_cse_list if x not in set(cse_list)]

            # links the send funcs with the handle result funcs
            create_func = lambda s: send_create_annc_pre(s) \
                .then(lambda r: handle_create(AnncResult(s, r)),
                      lambda r: handle_create_err(AnncResult(s, r)))
            delete_func = lambda s: send_delete_annc(s) \
                .then(lambda r: handle_delete(AnncResult(s, r)),
                      lambda r: handle_delete_err(AnncResult(s, r)))

            # filters out all False in the list
            def filter_func(l):
                return [_f for _f in l if _f]

            return async_all([
                (async_all(list(map(create_func, create_list))).then(filter_func)
                 .then(lambda l: l + filtered_cses)),
                async_all(list(map(delete_func, delete_list))).then(filter_func)
            ])

        return send_anncs(check_cse_list())

    def _update_resource(self, resource, remove_list=None, add_list=None,
                         force=False):
        self.logger.debug('Trying to update resource %s' % resource)
        if not add_list:
            add_list = []
        if not remove_list:
            remove_list = []

        old_resource = self._announcements[resource.path]['resource']
        old_resource.announceTo = resource.announceTo

        def update_announce_to():
            # update_req_ind = UpdateRequestIndication(resource.path +
            #                                         '/announceTo', resource,
            #                                         fields=['announceTo'],
            #                                         do_announce=False)

            # self.api.handle_request_indication(update_req_ind)
            # TODO_oneM2M: Update the resource by sending the request
            cse_req = OneM2MRequest(OneM2MOperation.update, resource.path, str(self),
                                    MetaInformation(None), cn=resource,
                                    ty=resource)
            # self.api.handle_onem2m_request(cse_req)

        if len(remove_list) or len(add_list):
            cse_list = resource.announceTo  # .get('cseList').get('reference')
            for s in remove_list:
                cse_list.remove(s)
            cse_list.extend(add_list)
            # if not len(cse_list):
            #    try:
            #        del resource.announceTo['activated']
            #    except KeyError:
            #        pass
            old_resource.announceTo = resource.announceTo
            update_announce_to()

        if force:
            return update_announce_to()

        return self._update_announcements(resource, add_list)

    def _update_announcements(self, resource, add_list):
        old_resource = self._announcements[resource.path]['resource']
        uris = self._announcements[resource.path]['uris']

        attributes_changed = False

        try:
            if resource.expirationTime != old_resource.expirationTime or \
                            resource.labels != old_resource.labels or \
                            resource.accessRightID != old_resource.accessRightID:
                attributes_changed = True
        except AttributeError:
            if resource.expirationTime != old_resource.expirationTime or \
                            resource.labels != old_resource.labels:
                attributes_changed = True

        if attributes_changed:

            annc_model = get_onem2m_type(resource.typename + "Annc")

            def send_update_annc_pre(cse_uri):
                # TODO_oneM2M: Needs updating
                try:
                    if not resource.accessRightID:
                        return send_update_annc(cse_uri)
                except AttributeError:
                    return send_update_annc(cse_uri)

                return self.api.is_local_path(resource.accessRightID) \
                    .then(lambda local_ar: send_update_annc(cse_uri, local_ar))

            def send_update_annc(cse_uri, local_ar=None):
                # TODO_oneM2M: Update to oneM2M
                # endpoint = self.api.get_endpoint('mid',
                #                                 urlparse(cse_uri).scheme)
                endpoint = self.config.get('endpoint', '')

                annc = annc_model()

                # link hast to be set
                annc.link = urljoin(endpoint, resource.path)

                # * labels from the original resource;
                annc.labels = resource.labels

                # * accessRightID from the original resource;
                if local_ar:
                    annc.accessRightID = urljoin(endpoint, urlparse(
                        resource.accessRightID).path)
                elif local_ar is None:
                    annc.accessRightID = local_ar
                else:
                    annc.accessRightID = resource.accessRightID

                # * expirationTime handling is to the discretion of the CSE
                # implementation. It is the responsibility of the local CSE to
                # keep the announced resource in sync with the lifetime of the
                # original resource, as long as the announcement is active. One
                # strategy to minimize signalling would be to request the same
                # expiration from the original resource. If this is accepted by
                # the remote CSE, then no explicit de-announce is needed in case
                # of expiration of the original resource;
                annc.expirationTime = resource.expirationTime

                # TODO(rst): fix this later
                # update_req_ind = UpdateRequestIndication(uris[cse_uri], annc)
                #
                # # todo investigate response for not accepted expirationTime
                # return self.api.send_request_indication(update_req_ind)

            old_resource.labels = resource.labels
            try:
                old_resource.accessRightID = resource.accessRightID
            except AttributeError:
                pass
            old_resource.expirationTime = resource.expirationTime

            cse_list = resource.announceTo  # .get('cseList', {}).get('reference')
            # TODO: conversion to set()  is questionable
            update_list = [x for x in cse_list if x not in set(add_list)]

            return async_all(list(map(send_update_annc_pre, update_list)))

        self.logger.debug('No attributes changed, returning None')
        return None
