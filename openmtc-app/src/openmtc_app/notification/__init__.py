from gevent import spawn
from gevent.pywsgi import WSGIServer
from inspect import getargspec
from futile.logging import LoggerMixin
from openmtc_onem2m.exc import OneM2MError
from openmtc_onem2m.model import (
    EventNotificationCriteria,
    NotificationEventTypeE,
    Subscription,
    BatchNotify,
    AggregatedNotification,
)
from openmtc_onem2m.serializer import get_onem2m_decoder
from urlparse import urlparse

from openmtc_onem2m.util import split_onem2m_address

_handler_map = {}


def register_handler(cls, schemes=()):
    _handler_map.update({
        scheme: cls for scheme in map(str.lower, schemes)
    })


def get_handler(scheme, poa, callback_func, ssl_certs=None):
    return _handler_map[scheme](poa, callback_func, ssl_certs)


class NotificationManager(LoggerMixin):
    handlers = []
    endpoints = []
    callbacks = {}

    def __init__(self, poas, ep, onem2m_mapper, ca_certs=None, cert_file=None, key_file=None):
        """
        :param list poas:
        :param str ep:
        :param openmtc_onem2m.mapper.OneM2MMapper onem2m_mapper:
        """
        self.mapper = onem2m_mapper
        self.sp_id, self.cse_id, _ = split_onem2m_address(onem2m_mapper.originator)
        self.ssl_certs = {
            'ca_certs': ca_certs,
            'cert_file': cert_file,
            'key_file': key_file
        }

        for poa in map(urlparse, poas):
            if poa.hostname == 'auto':
                poa = poa._replace(netloc="%s:%s" % (self._get_auto_host(ep), poa.port))

            if not poa.scheme:
                poa = poa._replace(scheme='http')

            try:
                self.handlers.append(get_handler(poa.scheme, poa, self._handle_callback,
                                                 self.ssl_certs))
                self.endpoints.append(poa.geturl())
            except:
                pass

        self.logger.debug('Available POAs: %s' % ', '.join(self.endpoints))

        super(NotificationManager, self).__init__()

    @staticmethod
    def _get_auto_host(ep):
        try:
            import socket
            from urlparse import urlparse
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            netloc = urlparse(ep).netloc.split(':')
            s.connect((netloc[0], int(netloc[1])))
            host = s.getsockname()[0]
            s.close()
        except:
            host = "127.0.0.1"

        return host

    def _normalize_path(self, path):
        path = path[len(self.sp_id):] if path.startswith(self.sp_id) and self.sp_id else path
        path = path[len(self.cse_id) + 1:] if path.startswith(self.cse_id) and self.cse_id else path
        return path

    def _init(self):
        for handler in self.handlers:
            try:
                handler.start()
            except:
                pass

        def nop():
            pass

        self._init = nop

    def register_callback(self, func, sur):
        # Not as beautifull as it should be but it works ......
        self.callbacks[sur] = func if len(getargspec(func)[0]) > 1 \
        else lambda _, **notification: func(notification['not']) if 'not' in notification.keys() \
        else func(notification['rep'])

    def _handle_callback(self, originator, **notification):
        try:
            n = notification["not"][0]
        except KeyError:
            n = notification

        sur = n.pop('sur')
        sur = self._normalize_path(sur)

        try:
            callback = self.callbacks[sur]
        except KeyError:
            if not sur.startswith('/'):
                # TODO(rst): maybe not the best, check alternatives
                # assumes originator is always in the form //SP-ID/CSE-ID
                sur = originator[originator.rfind('/'):] + '/' + sur
                try:
                    callback = self.callbacks[sur]
                except KeyError:
                    return
            else:
                return
        try:
            spawn(callback, originator, **notification)
        except:
            pass

    def get_expiration_time(self):
        return None

    def subscribe(self, path, func, filter_criteria=None, sub_options=None, expiration_time=None,
                  notification_types=(NotificationEventTypeE.updateOfResource,)):
        self._init()

        event_notification_criteria = filter_criteria or EventNotificationCriteria()
        event_notification_criteria.notificationEventType = (
            event_notification_criteria.notificationEventType or list(notification_types))

        subscription = self.mapper.create(path, Subscription(
            notificationURI=[self.mapper.originator],
            expirationTime=expiration_time or self.get_expiration_time(),
            eventNotificationCriteria=event_notification_criteria,
            batchNotify=BatchNotify(**sub_options["batchNotify"] or None)
        ))

        reference = self._normalize_path(subscription.subscriberURI or subscription.path)
        self.register_callback(func, reference)
        return subscription

    def unsubscribe(self, sur):
        self.mapper.delete(sur)
        del self.callbacks[sur]

    def shutdown(self):
        for subscription in self.callbacks.keys():
            try:
                self.unsubscribe(subscription)
            except OneM2MError:
                pass

        for handler in self.handlers:
            try:
                handler.stop()
            except:
                pass


class BaseNotificationHandler(object):
    def __init__(self, poa, callback_func, ssl_certs=None):
        self._endpoint = poa
        self._callback = callback_func
        self._ssl_certs = ssl_certs

    @classmethod
    def _unpack_notification(cls, notification):
        return {
            'sur': notification.subscriptionReference,
            'net': notification.notificationEvent.notificationEventType,
            'rep': notification.notificationEvent.representation,
        }

    def start(self):
        raise NotImplementedError

    def stop(self):
        pass


class MqttNotificationHandler(BaseNotificationHandler):
    _client = None

    def start(self):
        from openmtc_onem2m.client.mqtt import get_client
        from openmtc_onem2m.transport import OneM2MResponse
        from openmtc_onem2m.exc import get_response_status

        def wrapper(request):
            notification = self._unpack_notification(request.content)
            self._callback(request.originator, **notification)
            return OneM2MResponse(status_code=get_response_status(2002), request=request)

        self._client = get_client(self._endpoint.geturl(), handle_request_func=wrapper)

    def stop(self):
        self._client.stop()


register_handler(MqttNotificationHandler, ('mqtt', 'mqtts', 'secure-mqtt'))


class HttpNotificationHandler(BaseNotificationHandler):
    server = None

    def __init__(self, poa, callback_func, ssl_certs=None):
        super(HttpNotificationHandler, self).__init__(poa, callback_func, ssl_certs)

        self.ca_certs = ssl_certs.get('ca_certs')
        self.cert_file = ssl_certs.get('cert_file')
        self.key_file = ssl_certs.get('key_file')

        # TODO(rst): maybe tis needs to be tested when the server is started
        if poa.scheme == 'https' and not (self.ca_certs and self.cert_file and self.key_file):
            raise Exception()

    def start(self):
        from flask import (
            Flask,
            request,
            Response,
        )

        app = Flask(__name__)

        @app.after_request
        def attach_headers(response):
            response.headers['x-m2m-ri'] = request.headers['x-m2m-ri']
            return response

        @app.route('/', methods=['POST'])
        def index():
            assert 'x-m2m-origin' in request.headers, 'No originator set'
            assert 'x-m2m-ri' in request.headers, 'Missing request id'
            assert 'content-type' in request.headers, 'Unspecified content type'

            notification = {}
            notification_type = get_onem2m_decoder(request.content_type).decode(request.data)

            if isinstance(notification_type, AggregatedNotification):
                notification["not"] = []

                for n in notification_type.values["notification"]:
                    notification["not"].append(
                        self._unpack_notification(n)
                    )
            else:
                notification = self._unpack_notification(notification_type)
            self._callback(request.headers['x-m2m-origin'], **notification)

            return Response(
                headers={
                    'x-m2m-rsc': 2000,
                },
            )

        if self._endpoint.scheme == 'https':
            self.server = WSGIServer(
                (
                    self._endpoint.hostname,
                    self._endpoint.port or 6050
                ),
                application=app,
                keyfile=self.key_file, certfile=self.cert_file, ca_certs=self.ca_certs
            )
        else:
            self.server = WSGIServer(
                (
                    self._endpoint.hostname,
                    self._endpoint.port or 6050
                ),
                application=app,
            )
        spawn(self.server.serve_forever)

    def stop(self):
        self.server.stop()


register_handler(HttpNotificationHandler, ('http', 'https'))
