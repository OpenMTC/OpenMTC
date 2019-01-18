from . import controller
import openmtc_onem2m.model as model
from aplus import Promise
from openmtc.util import datetime_now
from openmtc_cse.methoddomain.controller import OneM2MDefaultController
from openmtc_onem2m.exc import (STATUS_INTERNAL_SERVER_ERROR, CSEConflict,
                                CSENotFound, CSENotImplemented)
from openmtc_onem2m.model import (CSEBase, CSETypeIDE)
from openmtc_onem2m.transport import (OneM2MErrorResponse, OneM2MOperation)
from openmtc_server import Component
from openmtc_server.db.exc import DBConflict, DBNotFound
from openmtc_server.exc import ConfigurationError
from openmtc_server.util import log_error


container_virtual_mapping = {
    'la': 'latest',
    'ol': 'oldest'
}


class OneM2MMethodDomain(Component):
    def __init__(self, config, *args, **kw):
        super(OneM2MMethodDomain, self).__init__(*args, **kw)

        self._api = None
        self.events = None
        self.config = config

        self.controller_classes = {
            model.CSEBase: controller.CSEBaseController,
            model.RemoteCSE: controller.RemoteCSEController,
            model.AE: controller.AEController,
            model.Subscription: controller.SubscriptionController,
            model.ContentInstance: controller.ContentInstanceController,
            model.Container: controller.ContainerController,
            model.AccessControlPolicy: controller.AccessControlPolicyController,
            model.SemanticDescriptor: controller.SemanticDescriptorController,
        }

        self._cse_base = None
        self._rel_cse_id = None
        self._abs_cse_id = None

    def initialize(self, api):
        self._api = api
        self.events = self._api.events

        self._api.handle_onem2m_request = self.handle_onem2m_request

    def start(self):
        pass

    def stop(self):
        pass

    def init_cse_base(self):
        # get config values
        onem2m_config = self.config["onem2m"]
        self._cse_base = cse_base_name = onem2m_config.get("cse_base", "onem2m")

        # TODO(rst): check later
        # node_link = 'dummy'

        # cse type
        cse_type = onem2m_config.get("cse_type")
        try:
            cse_type = getattr(CSETypeIDE,
                               str(cse_type).replace("-", "_").upper())
        except (AttributeError, TypeError, ValueError):
            raise ConfigurationError("Invalid value for 'cse_type': %s" %
                                     (cse_type,))
        cse_type = CSETypeIDE(cse_type)

        # cse id
        try:
            self._rel_cse_id = "/" + onem2m_config["cse_id"]
        except KeyError:
            raise ConfigurationError("Missing configuration key: cse_id")

        # sp id
        try:
            self._abs_cse_id = "//" + onem2m_config["sp_id"] + self._rel_cse_id
        except KeyError:
            raise ConfigurationError("Missing configuration key: sp_id")

        # time
        now = datetime_now()

        # resource
        cse_base = CSEBase(
            resourceName=cse_base_name,
            resourceID='cb0',
            parentID=None,
            resourceType=model.ResourceTypeE['CSEBase'],
            creationTime=now,
            lastModifiedTime=now,
            cseType=cse_type,
            CSE_ID=self._rel_cse_id,
            supportedResourceType=[model.ResourceTypeE[x.typename]
                                   for x in self.controller_classes.keys()],
            pointOfAccess=[],
            path=cse_base_name
        )
        db_session = self._api.start_onem2m_session()

        try:
            result = db_session.store(cse_base)
        except Exception as error:
            self.logger.exception("Initialization error")
            db_session.rollback()
            raise error
        else:
            db_session.commit()
            return result

    def handle_onem2m_request(self, onem2m_request):
        self.logger.debug("handling request:\r\n\t%s", onem2m_request)

        db_session = self._api.start_onem2m_session()
        try:
            result = self._handle_onem2m_request(db_session, onem2m_request)
            db_session.commit()
            return result
        except Exception as error:
            if log_error(error):
                self.logger.exception("Error during request: %r", error)
            else:
                self.logger.debug("Error during request: %r", error)
            try:
                status_code = error.response_status_code
            except AttributeError:
                status_code = 500

            p = Promise()
            result = OneM2MErrorResponse(status_code=status_code,
                                         request=onem2m_request)
            db_session.rollback()
            p.reject(result)
            return p

    def _forward(self, onem2m_request, path):
        operation = onem2m_request.op

        # TODO(rst): optimize this (handling of CSE-relative references)
        pre = (self._abs_cse_id if path.startswith('//')
               else self._rel_cse_id) + '/'
        if operation == OneM2MOperation.create:
            if isinstance(onem2m_request.content, model.Subscription):
                cn = onem2m_request.content
                cn.notificationURI = [(pre if not uri.startswith('/') else '') + uri
                                      for uri in cn.notificationURI]
                if cn.subscriberURI and not cn.subscriberURI.startswith('/'):
                    cn.subscriberURI = pre + cn.subscriberURI

        return self._api.send_onem2m_request(onem2m_request)

    def _get_controller_class(self, resource_type):
        try:
            return self.controller_classes[resource_type]
        except KeyError:
            raise CSENotImplemented()

    def _run_controller(self, ctrl, request, resource):
        with Promise() as p:
            try:
                p.fulfill(ctrl(request, resource))
            except Exception as error:
                self.logger.debug("Handling %s: %s", type(error).__name__,
                                  error)
                if isinstance(error, OneM2MErrorResponse):
                    p.reject(error)
                elif isinstance(error, DBConflict):
                    p.reject(CSEConflict())
                elif isinstance(error, DBNotFound):
                    p.reject(CSENotFound())
                else:
                    try:
                        status_code = error.response_status_code
                    except AttributeError:
                        status_code = STATUS_INTERNAL_SERVER_ERROR

                    result = OneM2MErrorResponse(status_code, request=request)
                    p.reject(result)
        return p

    def _normalize_path(self, path):
        if path.startswith(self._rel_cse_id):
            return '/'.join(path.split('/')[2:])
        elif path.startswith(self._abs_cse_id):
            return '/'.join(path.split('/')[4:])
        else:
            return path

    def _check_existence_and_get_resource(self, db_session, path):
        if path.startswith('.'):
            path = self._cse_base + path[1:]

        def get_resource(p):
            try:
                r = db_session.get(p)
            except DBNotFound:
                try:
                    p_segment, ch_segments = p.split('/', 1)
                except ValueError:
                    raise CSENotFound()
                try:
                    p = db_session.get(p_segment)
                    r = db_session.get('/'.join([p.path, ch_segments]))
                except DBNotFound:
                    raise CSENotFound()
            return r

        # virtual resource handling, see TS-0004 6.8
        # oldest, latest -> Container
        # TODO(rst): fanOutPoint -> group
        # TODO(rst): pollingChannelURI -> pollingChannel
        if path.endswith(tuple(container_virtual_mapping.keys())):
            parent_path, virtual = path.rsplit('/', 1)
            parent = get_resource(parent_path)
            if isinstance(parent, model.Container):
                resource = getattr(parent, container_virtual_mapping[virtual])
                if resource is None:
                    raise CSENotFound()
                return resource

        return get_resource(path)

    def _handle_onem2m_request(self, db_session, request):
        self.logger.debug("_handling request:\r\n\t%s", request)

        operation = request.operation

        # strip trailing slashes
        request.to = request.to.rstrip('/')

        # TS-0004 7.3.2.6 -> forwarding
        path = self._normalize_path(request.to)
        if path.startswith('/'):
            return self._forward(request, path)

        def handle_onem2m_request(req):
            return self._handle_onem2m_request(db_session, req)

        def _handle_resource(res):
            if operation in (OneM2MOperation.create, OneM2MOperation.update):
                resource_type = request.resource_type
            else:
                resource_type = type(res)

            ctrl_class = self._get_controller_class(resource_type)
            ctrl = ctrl_class(db_session, resource_type, handle_onem2m_request)
            return self._run_controller(ctrl, request, res)

        # TS-0004 7.3.3.2 -> check existence
        resource = self._check_existence_and_get_resource(db_session, path)
        return _handle_resource(resource)
