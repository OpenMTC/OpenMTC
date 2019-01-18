import logging
import re
import time
from abc import abstractmethod
from base64 import (
    b64decode,
    b64encode,
)
from datetime import datetime
from json import (
    dumps as json_dumps,
    loads as json_loads,
)

from gevent import (
    spawn,
    sleep,
)
from iso8601 import parse_date

from futile.logging import LoggerMixin
from openmtc.util import (
    UTC,
    datetime_now,
    datetime_the_future,
)
from openmtc_app.flask_runner import FlaskRunner
from openmtc_app.notification import NotificationManager
from openmtc_onem2m.exc import (
    CSENotFound,
    CSENotImplemented,
    STATUS_CONFLICT,
)
from openmtc_onem2m.mapper import OneM2MMapper
from openmtc_onem2m.model import (
    AE,
    Container,
    ContentInstance,
    EncodingTypeE,
    NotificationEventTypeE,
    EventNotificationCriteria,
    CSETypeIDE,
    RemoteCSE,
    FilterCriteria
)
from openmtc_onem2m.serializer import get_onem2m_decoder
from openmtc_onem2m.transport import OneM2MErrorResponse

logging.getLogger("iso8601").setLevel(logging.ERROR)

# fix missing SSLv3
try:
    from gevent.ssl import PROTOCOL_SSLv3
except ImportError:
    import gevent.ssl

    gevent.ssl.PROTOCOL_SSLv3 = gevent.ssl.PROTOCOL_TLSv1


class XAE(LoggerMixin):
    """ Generic OpenMTC application class.
    Implements functionality common to all typical OpenMTC applications.
    """

    # TODO(rst): add more features
    # support several AEs using the same App-ID and appName

    name = None
    containers = ()
    labels = ()
    # default_access_right = True
    default_lifetime = 3600
    max_nr_of_instances = 3
    resume_registration = remove_registration = True
    notification_handlers = {}
    mapper = None
    notification_manager = None
    __app = None

    def __init__(self, name=None, cse_base=None, expiration_time=None, announce_to=None, poas=None,
                 originator_pre=None, ca_certs=None, cert_file=None, key_file=None):
        super(XAE, self).__init__()

        self.__subscriptions = []

        self.name = name or type(self).__name__
        self.cse_base = cse_base or "onem2m"

        ae_id = "C" + self.name
        self.originator = (originator_pre + '/' + ae_id) if originator_pre else ae_id

        self.ca_certs = ca_certs
        self.cert_file = cert_file
        self.key_file = key_file

        if expiration_time is not None:
            if isinstance(expiration_time, str):
                expiration_time = parse_date(expiration_time)
            elif isinstance(expiration_time, (int, float)):
                expiration_time = datetime.fromtimestamp(expiration_time, UTC)

            if not isinstance(expiration_time, datetime):
                raise ValueError(expiration_time)

            self.default_lifetime = (expiration_time - datetime_now()).total_seconds()

        self.announceTo = announce_to

        self.__resumed_registration = False
        self.__known_containers = set()
        self.__shutdown = False

        self.allow_duplicate = None
        self.runner = None
        self.poas = poas or []

        self.fmt_json_regex = re.compile(r'^application/(?:[^+]+\+)?json$', re.IGNORECASE)
        self.fmt_xml_regex = re.compile(r'^application/(?:[^+]+\+)?xml$', re.IGNORECASE)

    def get_expiration_time(self):
        if self.default_lifetime is None:
            return None
        return datetime_the_future(self.default_lifetime)

    @property
    def application(self):
        return self.__app

    def run(self, runner, cse, allow_duplicate=True):
        self.mapper = OneM2MMapper(cse, originator=self.originator, ca_certs=self.ca_certs,
                                   cert_file=self.cert_file, key_file=self.key_file)
        self.notification_manager = NotificationManager(self.poas, cse, self.mapper,
                                                        ca_certs=self.ca_certs,
                                                        cert_file=self.cert_file,
                                                        key_file=self.key_file)

        self.allow_duplicate = allow_duplicate
        self.runner = runner
        self.register()

    def shutdown(self):
        """ Graceful shutdown.
        Deletes all Applications and Subscriptions.
        """
        try:
            self._on_shutdown()
        except:
            self.logger.exception("Error in shutdown handler")

        self.logger.debug("shutdown handler is finished")

        self.__shutdown = True

        self.notification_manager.shutdown()

        self._remove_apps()

    def _remove_apps(self):
        if self.remove_registration:
            try:
                if self.__app:
                    self.mapper.delete(self.__app)
            except:
                pass
            self.logger.debug("app deleted")

    @staticmethod
    def run_forever(period=1000, func=None, *args, **kw):
        """ executes a given function repetitively at a given interval
        :param period: (optional) frequency of repeated execution (in Hz)
        :param func: (optional) function to be executed
        """

        if func is None:
            def func(*_):
                pass

        def run_periodically():
            while True:
                func(*args, **kw)
                sleep(period)

        return spawn(run_periodically)

    def periodic_discover(self, path, fc, interval, cb, err_cb=None, auto_cra=True):
        """ starts periodic discovery at a given frequency
        :param path: start directory inside cse for discovery
        :param fc: filter criteria (what to discover)
        :param interval: frequency of repeated discovery (in Hz)
        :param cb: callback function to return the result of the discovery to
        :param err_cb: (optional) callback function for errors to return the error of the discovery to
        :param auto_cra: if created after parameter will be adjusted automatically
        """
        if not isinstance(fc, dict):
            fc = {}

        def run_discovery(o):
            while True:
                try:
                    cb(self.discover(path, o))
                except OneM2MErrorResponse as error_response:
                    if err_cb:
                        return err_cb(error_response)
                else:
                    if auto_cra:
                        o['createdAfter'] = datetime_now()

                sleep(interval)

        return spawn(run_discovery, fc)

    def register(self):
        """ Registers the Application with the CSE. """
        self.logger.info("Registering application as %s." % (self.name,))
        try:
            poa = self.notification_manager.endpoints
        except AttributeError:
            poa = []
        app = AE(resourceName=self.name, labels=list(self.labels),
                 pointOfAccess=poa)
        app.announceTo = self.announceTo
        app.requestReachability = bool(poa)

        try:
            registration = self.create_application(app)
        except OneM2MErrorResponse as error_response:
            if error_response.response_status_code is STATUS_CONFLICT:
                registration = self._handle_registration_conflict(app)
                if not registration:
                    raise
            else:
                self.logger.error('Error at start up')
                self.logger.error(error_response.response_status_code)
                raise SystemExit
        self.__app = registration

        assert registration.path

        try:
            self._on_register()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.logger.exception("Error on initialization")
            raise

    def _handle_registration_conflict(self, app):
        if not self.resume_registration:
            return None
        # TODO(rst): update app here for expiration_time and poas

        app = self.get_application(app)

        self.__start_refresher(app)

        self.__resumed_registration = True

        return app

    def emit(self, event, message=None):
        """ Websocket emit. """
        if not isinstance(self.runner, FlaskRunner):
            raise RuntimeError('Runner is not supporting emit!')
        self.runner.emit(event, message)

    def _on_register(self):
        pass

    def _on_shutdown(self):
        pass

    def get_application(self, application, path=None):
        """ Retrieves an Application resource.
        :param application: old app instance or appId
        :param path: (optional) path in the resource tree
        """
        if path is None:
            # FIXME(rst): use app path and not cse base path
            path = self.cse_base

        if not isinstance(application, AE):
            application = AE(resourceName=application)

        name = application.resourceName

        path = "%s/%s" % (path, name) if path else name
        app = self.mapper.get(path)

        self.logger.debug("retrieved app: %s" % app)

        return app

    def create_application(self, application, path=None):
        """ Creates an Application resource.

        :param application: Application instance or resourceName as str
        :param path: (optional) path in the resource tree
        """
        # TODO(rst): set app_id via config
        # TODO(rst): set requestReachability based on used runner
        if path is None:
            path = self.cse_base

        def restore_app(app):
            self.logger.warn("Restoring app: %s", app.path)
            app.expirationTime = None
            self.create_application(app, path=path)

        if not isinstance(application, AE):
            application = AE(resourceName=application, App_ID='dummy', requestReachability=False)
        else:
            if not application.App_ID:
                application.App_ID = 'dummy'
            if not application.requestReachability:
                application.requestReachability = False

        application.expirationTime = application.expirationTime or self.get_expiration_time()
        app = self.mapper.create(path, application)
        self.logger.debug("Created application at %s", app.path)
        app = self.get_application(application, path)
        assert app.path
        self.__start_refresher(app, restore=restore_app)
        self.logger.info("Registration successful: %s." % (app.path,))

        # TODO(rst): handle when ACP is reimplemented
        # if accessRight:
        #     if not isinstance(accessRight, AccessRight):
        #         accessRight = AccessRight(
        #             id="ar",
        #             selfPermissions={"permission": [{
        #                 "id": "perm",
        #                 "permissionFlags": {
        #                     "flag": ["READ", "WRITE", "CREATE", "DELETE"]
        #                 },
        #                 "permissionHolders": {
        #                     "all": "all"
        #                 }
        #             }]},
        #             permissions={"permission": [{
        #                 "id": "perm",
        #                 "permissionFlags": {
        #                     "flag": ["READ", "WRITE", "CREATE", "DELETE"]
        #                 },
        #                 "permissionHolders": {
        #                     "all": "all"
        #                 }
        #             }]}
        #         )
        #     accessRight = self.create_accessRight(app, accessRight)
        #
        #     app.accessRightID = accessRight.path
        #
        #     self.mapper.update(app, ("accessRightID",))

        return app

    # TODO(rst): use FilterCriteria from model and convert
    def discover(self, path=None, filter_criteria=None, unstructured=True):
        """ Discovers Container resources.

        :param path: (optional) the target path to start the discovery
        :param filter_criteria: (optional) FilterCriteria for the for the discovery
        :param unstructured: (optional) set discovery_result_type
        """
        if path is None:
            path = self.cse_base

        # TODO(rst): use filter_criteria from model
        if not filter_criteria:
            filter_criteria = {}

        filter_criteria['filterUsage'] = 1

        discovery = self.mapper.get(path, FilterCriteria(**filter_criteria),
                                    drt=1 if unstructured else 2)

        return discovery.CONTENT

    def create_container(self, target, container, labels=None, max_nr_of_instances=None):
        """ Creates a Container resource.

        :param target: the target resource/path parenting the Container
        :param container: the Container resource or a valid container ID
        :param labels: (optional) the container's labels
        :param max_nr_of_instances: (optional) the container's maximum number
                                    of instances (0=unlimited)
        """

        def restore_container(c):
            self.logger.warn("Restoring container: %s", c.path)
            c.expirationTime = None
            self.__known_containers.remove(c.path)
            self.create_container(target, c, labels=labels)

        if target is None:
            target = self.__app

        if not isinstance(container, Container):
            container = Container(resourceName=container)

        # if we got max instances..set them
        if max_nr_of_instances:
            container.maxNrOfInstances = max_nr_of_instances
        # if we did not set max instances yet, set them
        else:
            container.maxNrOfInstances = self.max_nr_of_instances

        if container.expirationTime is None:
            container.expirationTime = self.get_expiration_time()

        if labels:
            container.labels = labels

        path = getattr(target, "path", target)

        try:
            container = self.mapper.create(path, container)
        except OneM2MErrorResponse as error_response:
            if error_response.response_status_code is STATUS_CONFLICT:
                c_path = path + '/' + container.resourceName
                container.path = c_path
                if (self.__resumed_registration and
                        c_path not in self.__known_containers):
                    container = self.mapper.update(container)
                else:
                    raise error_response
            else:
                raise error_response

        self.__known_containers.add(container.path)
        self.__start_refresher(container, restore=restore_container)
        self.logger.info("Container created: %s." % (container.path,))
        return container

    # TODO(rst): handle when ACP is reimplemented
    # def create_access_right(self, application, accessRight):
    #     """ Creates an AccessRight resource.
    #
    #     :param application: the Application which will contain the AR
    #     :param accessRight: the AccessRight instance
    #     """
    #     self.logger.debug("Creating accessRight for %s", application)
    #
    #     if application is None:
    #         application = self.__app
    #         assert application.path
    #
    #     path = getattr(application, "path", application)
    #
    #     if not path.endswith("/accessRights"):
    #         path += "/accessRights"
    #
    #     accessRight = self.mapper.create(path, accessRight)
    #     accessRight = self.mapper.get(accessRight.path)
    #     self.__start_refresher(accessRight, extra_fields=["selfPermissions"])
    #     self.logger.info("accessRight created: %s." % (accessRight.path,))
    #     return accessRight
    #
    # create_accessRight = create_access_right

    def get_resource(self, path, app_local=False):
        if app_local:
            path = self.__app.path + '/' + path

        if not path:
            return None

        try:
            return self.mapper.get(path)
        except OneM2MErrorResponse:
            return None

    def push_content(self, container, content, fmt=None, text=None):
        """ Creates a ContentInstance resource in the given container,
        wrapping the content.
        Defaults to serialising the content as JSON and base64 encodes it.
        NOTE: Will attempt to create the container, if not found.

        :param container: Container object or container path string
        :param content: the content data
        :param fmt:
        :param text:
        """
        path = getattr(container, "path", container)

        if isinstance(content, str):
            fmt = 'text/plain' if fmt is None else fmt
            text = True if text is None else text
        elif isinstance(content, (dict, list)):
            fmt = 'application/json' if fmt is None else fmt
            text = False if text is None else text
        else:
            raise CSENotImplemented("Only dict, list and str are supported!")

        if re.search(self.fmt_json_regex, fmt):
            if text:
                # TODO(rst): check if it should be with masked quotation marks
                con = json_dumps(content)
                cnf = fmt + ':' + str(EncodingTypeE.plain.value)
                # raise CSENotImplemented("Only json as b64 is supported!")
            else:
                con = b64encode(json_dumps(content).encode('utf-8'))
                cnf = fmt + ':' + str(EncodingTypeE.base64String.value)
        elif fmt == 'text/plain':
            if text:
                con = content
                cnf = fmt + ':' + str(EncodingTypeE.plain.value)
            else:
                con = b64encode(content.encode('utf-8'))
                cnf = fmt + ':' + str(EncodingTypeE.base64String.value)
        else:
            # TODO(rst): add handling of other formats or raise not implemented
            raise CSENotImplemented("Only json and text are supported!")

        return self.mapper.create(path, ContentInstance(
            content=con,
            contentInfo=cnf,
        ))

    @staticmethod
    def _get_content_from_cin(cin):
        if isinstance(cin, ContentInstance):
            # TODO(rst): handle contentInfo and decode
            # resource.contentInfo -> application/json:1
            # media, encodingType = split(':')
            # encodingType = 1 -> base64.decodeString(resource.content)
            # encodingType = 2 -> not supported
            media_type, encoding_type = cin.contentInfo.split(':')
            content = cin.content
            try:
                if int(encoding_type) == EncodingTypeE.base64String:
                    content = b64decode(content).decode('utf-8')

                if media_type == 'application/json':
                    content = json_loads(content)
            except ValueError:
                pass

            return content

        return cin

    def get_content(self, container):
        """ Retrieve the latest ContentInstance of a Container.

        :param container: Container object or container path string
        """
        return self._get_content_from_cin(
            self.mapper.get(
                getattr(container, 'path', container) + '/la'
            )
        )

    def _get_notification_data(self, data, content_type):
        try:
            return get_onem2m_decoder(content_type).\
                decode(data).\
                notificationEvent.\
                representation
            # serializer = get_onem2m_decoder(content_type)
            # notification = serializer.decode(data)
            # resource = notification.notificationEvent.representation
            # return resource
        except (KeyError, TypeError, ValueError, IndexError):
            self.logger.error("Failed to get notification data from %s" % data)
            return None

    def _remove_route(self, route):
        self.logger.debug("removing route: %s", route)
        self.runner.flask_app.url_map._rules = [x for x in self.runner.flask_app.url_map._rules
                                                if x.rule != route]

    def _add_subscription(self, path, _, handler, delete_handler, filter_criteria=None,
                          sub_options=None, expiration_time=None):
        params = {
            'filter_criteria': filter_criteria,
            'expiration_time': expiration_time,
            'sub_options': sub_options,
        }
        return self.add_subscription_handler(path, handler, delete_handler, **params)

    def add_subscription(self, path, handler, delete_handler=None):
        """ Creates a subscription resource at path.
        And registers handler to receive notification data.

        :param path: path to subscribe to
        :param handler: notification handler
        :param delete_handler: reference to delete handling function
        """
        return self._add_subscription(path, None, handler, delete_handler)

    def add_subscription_handler(self, path, handler, delete_handler=None,
                                 types=(NotificationEventTypeE.updateOfResource, ),
                                 filter_criteria=None, sub_options=None, expiration_time=None):
        """

        :param path:
        :param handler:
        :param delete_handler:
        :param types:
        :param filter_criteria:
        :param sub_options:
        :param expiration_time:
        :return:
        """
        def subscribe():
            return self.notification_manager.subscribe(
                path,
                handler,
                delete_handler,
                notification_types=types,
                filter_criteria=filter_criteria,
                sub_options=sub_options,
                expiration_time=expiration_time
            )

        subscription = subscribe()

        def restore_subscription():
            # called to recreate the subscription
            # for some reason subscription is not assigned here,
            # so we make it a parameter
            self.logger.warn("Restoring subscription: %s", subscription.name)
            self.notification_manager.unsubscribe(subscription.path)
            subscribe()

        # refresh expirationTime regularly
        # TODO(sho): This should rather be handled through the notification manager itself
        self.__start_refresher(subscription, restore=restore_subscription)
        return subscription.path

    def add_container_subscription(self, container, handler, delete_handler=None,
                                   filter_criteria=None, sub_options=None):
        """ Creates a Subscription to the ContentInstances of the given
        Container.

        :param container: Container object or container path string
        :param handler: reference of the notification handling function
        :param delete_handler: reference to delete handling function
        :param filter_criteria: (optional) FilterCriteria for the subscription
        :param sub_options: (optional) SubscriptionOptions for the subscription
        """

        path = getattr(container, "path", container)

        # check if target is container
        if not isinstance(self.mapper.get(path), Container):
            raise RuntimeError('Target is not a container.')

        # event notification criteria
        filter_criteria = filter_criteria or EventNotificationCriteria()
        filter_criteria.notificationEventType = list([
            NotificationEventTypeE.createOfDirectChildResource,
            NotificationEventTypeE.updateOfResource,
        ])

        def content_handler(cin):
            handler(path, self._get_content_from_cin(cin))

        return self._add_subscription(
            path,
            None,
            content_handler,
            delete_handler,
            filter_criteria,
            sub_options,
        )

    def __start_refresher(self, instance, extra_fields=(), restore=None):
        """ Starts a threading.Timer chain,
        to repeatedly update a resource instance's expirationTime.
        NOTE: instance.expirationTime should already be set and the instance
        created.

        :param instance: resource instance
        :param extra_fields: additional fields, needed in the update request
        :param restore: function that will restore the instance, if it has
                        expired accidentally. Has to restart the refresher.
        """
        if not instance.expirationTime:
            return
        interval = time.mktime(instance.expirationTime.timetuple()) - (time.time() + time.timezone)
        if interval > 120:
            interval -= 60
        else:
            interval = max(1, interval * 0.75)

        self.logger.debug("Will update expiration time of %s in %s seconds", instance, interval)
        self.runner.set_timer(interval, self.__update_exp_time, instance=instance,
                              extra_fields=extra_fields, restore=restore)

    def start_refresher(self, instance, extra_fields=(), restore=None):
        self.__start_refresher(instance, extra_fields=extra_fields, restore=restore)

    def __update_exp_time(self, instance=None, the_future=None, extra_fields=(),
                          interval=None, offset=None, restore=None):
        """ Updates a resource instance's expirationTime to the_future
        or a default value sometime in the future.

        :note: If instance is not provided or None or False, self.__app is
               updated.
        :note: Starts a new Timer.
        :param instance: resource instance to update
        :param the_future: new expirationTime value
        :param extra_fields: additional fields, needed in the update request
        :param interval: update interval
        :param offset: expirationTime offset (should be >0)
        :param restore: function that will restore the instance, if it has
                        expired accidentally. Has to restart the refresher.
        :raise CSENotFound: If the instance could not be found and no restore
                            was provided.
        """
        self.logger.debug("updating ExpirationTime of %s", instance)
        if self.__shutdown:
            # not sure this ever happens.
            return

        interval = interval or 60 * 10  # TODO make configurable
        offset = offset or 60 * 10  # 10min default
        if not the_future:
            the_future = datetime.utcfromtimestamp(time.time() + interval + offset)
        fields = ["expirationTime"]
        fields.extend(extra_fields)
        if not instance:
            # does this happen if the instance was deleted?
            instance = self.__app
        instance.expirationTime = the_future
        try:
            self.mapper.update(instance, fields)
        except CSENotFound as e:
            self.logger.warn("ExpirationTime update of %s failed: %s", instance, e)
            # subscription disappeared?
            # missed the expirationTime?
            # mb sync issue?; mb congestion?
            if restore:
                restore(instance)
                return
            else:
                raise
        # NOTE: expirationTime might have been changed by CSE at this point.
        # update could/should return the updated instance in this case, but
        # doesnt. => additional GET to confirm expirationTime ?

        self.logger.debug("Will update expiration time in %s seconds", interval)
        self.runner.set_timer(
            interval,
            self.__update_exp_time,
            instance=instance,
            extra_fields=extra_fields,
            restore=restore,
        )


class ResourceManagementXAE(XAE):

    def __init__(self, interval=10, *args, **kw):
        super(ResourceManagementXAE, self).__init__(*args, **kw)
        self.interval = interval
        self._device_labels = ["openmtc:device"]
        self._sensor_labels = ["openmtc:sensor_data"]
        self._actuator_labels = ["openmtc:actuator_data"]

        # init variables
        self._known_remote_cses = {}
        self._discovered_devices = {}
        self._discovered_sensors = {}
        self._discovered_actuators = {}

    def _discover_openmtc_ipe_entities(self):
        # connected to backend or gateway?
        cse_base = self.get_resource(self.cse_base)
        self._cse_id = cse_base.CSE_ID
        self.logger.debug("CSE_BASE: %s", cse_base)

        if cse_base.cseType in (CSETypeIDE.MN_CSE, CSETypeIDE.AEN_CSE):
            self.logger.info("CSE_BASE identified as gateway")
            # discover gateway
            self._discover_resources(cse_base.CSE_ID + '/' + self.cse_base)
        else:
            self.logger.info("CSE_BASE identified as backend")
            # discover backend
            self._discover_resources(cse_base.CSE_ID + '/' + self.cse_base)
            # discover remote gateways
            self._get_remote_cses(cse_base)

    # get remote CSEs
    def _get_remote_cses(self, cse_base):

        def get_cse_base():
            handle_cse_base(self.get_resource(self.cse_base))

        def handle_cse_base(cb):
            for resource in cb.childResource:
                if (isinstance(resource, RemoteCSE) and
                        resource.path not in self._known_remote_cses):
                    remote_cse = self.get_resource(resource.id)
                    self._known_remote_cses[resource.path] = remote_cse
                    remote_cse_base = (remote_cse.CSE_ID + '/' +
                                       remote_cse.CSEBase)
                    self._discover_resources(remote_cse_base, resource.path)

        handle_cse_base(cse_base)
        self.run_forever(self.interval, get_cse_base)

    # discover resources
    def _discover_resources(self, cse_base, remote_cse_id=None):

        def err_cb(error_response):
            try:
                del self._known_remote_cses[remote_cse_id]
            except KeyError:
                pass
            else:
                self._discovered_devices = {k: v for k, v in self._discovered_devices.items()
                                            if not k.startswith(cse_base)}
                self._discovered_sensors = {k: v for k, v in self._discovered_sensors.items()
                                            if not k.startswith(cse_base)}
        # discover devices
        self.periodic_discover(cse_base, {'labels': self._device_labels}, self.interval,
                               self._discover_devices, err_cb, auto_cra=False)
        sleep(0.3)
        self.periodic_discover(cse_base, {'labels': self._sensor_labels}, self.interval,
                               self._discover_sensors, err_cb, auto_cra=False)
        self.periodic_discover(cse_base, {'labels': self._actuator_labels}, self.interval,
                               self._discover_actuators, err_cb, auto_cra=False)

    def _discover_devices(self, discovery):
        for device_path in set(discovery) - set(self._discovered_devices):
            self._discovered_devices[device_path] = self.get_resource(device_path)
        self.logger.debug("Discovered devices: %s", self._discovered_devices)

    def _discover_sensors(self, discovery):
        for sensor_path in set(discovery) - set(self._discovered_sensors):
            try:
                dev_path = [x for x in self._discovered_devices.keys()
                            if sensor_path.startswith(x)][0]
            except IndexError:
                continue
            sensor = self.get_resource(sensor_path)
            if sensor:
                sensor_info = self._discovered_sensors[sensor_path] = {
                    'ID': sensor_path,
                    'dev_name': dev_path.split('/')[-1],
                    'cse_id': sensor_path.split('/')[1],
                    'dev_labels': self._discovered_devices[dev_path].labels,
                    'sensor_labels': sensor.labels,
                    'type': 'sensor',
                    'n': None,
                    'u': None,
                    'blacklisted': False
                }
                if self._sensor_filter(sensor_info):
                    self._handle_new_sensor(sensor_path)
                else:
                    self._discovered_sensors[sensor_path]['blacklisted'] = True

    def _handle_new_sensor(self, sensor_path):
        latest = self.get_resource(sensor_path + '/la')
        if latest:
            spawn(self._handle_sensor_data, sensor_path, self._get_content_from_cin(latest))

        self.logger.debug("Subscription added for %s", sensor_path)
        sub_ref = self.add_container_subscription(sensor_path, self._handle_sensor_data,
                                                  self._handle_delete)
        self._discovered_sensors[sensor_path]['sub_ref'] = sub_ref

    def _handle_delete(self, sub_ref):
        if sub_ref[0] != '/':
            sub_ref = self._cse_id + '/' + sub_ref
        self._discovered_sensors = {k: v for k, v in self._discovered_sensors.items()
                                    if v['sub_ref'] != sub_ref}
        self._discovered_devices = {k: v for k, v in list(self._discovered_devices.items())
                                    if any([x for x in list(self._discovered_sensors.keys())
                                            if x.startswith(k)])
                                    or not sub_ref.startswith(k)}

    def _handle_sensor_data(self, container, data):
        self.logger.debug("Got Sensor \"%s\" data: %s", container, data)
        try:
            sensor_info = self._discovered_sensors[container]
            sensor_data = data[0]
        except (IndexError, KeyError):
            return
        if not sensor_info['n']:
            try:
                sensor_info['n'] = sensor_data['n']
                sensor_info['u'] = sensor_data['u']
            except KeyError:
                return

        self._sensor_data_cb(sensor_info, sensor_data)

    def _discover_actuators(self, discovery):
        for actuator_path in set(discovery) - set(self._discovered_actuators):
            try:
                dev_path = [x for x in self._discovered_devices.keys()
                            if actuator_path.startswith(x)][0]
            except IndexError:
                continue
            actuator = self.get_resource(actuator_path)
            if actuator:
                actuator_info = self._discovered_actuators[actuator_path] = {
                    'ID': actuator_path,
                    'dev_name': dev_path.split('/')[-1],
                    'cse_id': actuator_path.split('/')[1],
                    'dev_labels': self._discovered_devices[dev_path].labels,
                    'actuator_labels': actuator.labels,
                    'type': 'actuator'
                }
                self._new_actuator(actuator_info)

    @abstractmethod
    def _sensor_data_cb(self, sensor_info, sensor_data):
        pass

    @abstractmethod
    def _sensor_filter(self, sensor_info):
        pass

    def _new_actuator(self, actuator_info):
        pass
