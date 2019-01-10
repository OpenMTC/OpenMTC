from datetime import datetime

from aplus import (
    Promise,
)
from collections import deque
from futile.caching import LRUCache
import gevent
from gevent import monkey; monkey.patch_all()
from . import OneM2MClient
from openmtc.exc import ConnectionFailed
from ..exc import (
    ERROR_MIN,
    CSEValueError,
    CSEError,
    CSETargetNotReachable)
from ..serializer.util import (
    decode_onem2m_content,
    encode_onem2m_content,
)
from ..transport import (
    OneM2MRequest,
    OneM2MResponse,
    OneM2MErrorResponse,
    OneM2MOperation,
)
from ..model import ResourceTypeE
import paho.mqtt.client as mqtt
from simplejson import (
    JSONDecoder,
    JSONEncoder,
    JSONDecodeError,
)
from socket import error as SocketError
from urllib.parse import urlparse
from openmtc_onem2m.util import split_onem2m_address

#: Dictionary mapping supported schemes to port numbers
portmap = {
    'mqtt':         1883,
    'mqtts':        8883,
    # NB: The correct (i.e. registered with IANA) service-name for SSL/TLS-wrapped MQTT is
    # 'secure-mqtt' in an effort to prevent confusion with MQTT-S/N. But as the entire world seems
    # to insist on using 'mqtts' (including TS 0010, sec. 6.6) ... We are supporting both names here
    # for maximum compliance and robustness.
    'secure-mqtt':  8883,
}

MQTT_QOS_LEVEL = 1
MQTT_RESPONSE_TIMEOUT = 1

_clients = LRUCache(threadsafe=False)


def get_client(m2m_ep, use_xml=False, client_id=None, handle_request_func=None,
               ca_certs=None, cert_file=None, key_file=None, insecure=False):
    """

    :param string m2m_ep:
    :param boolean use_xml:
    :param string client_id:
    :param fun handle_request_func:
    :param string ca_certs:
    :param string cert_file:
    :param string key_file:
    :param string insecure:
    :return OneM2MMQTTClient:
    """
    try:
        return _clients[(m2m_ep.split('#')[0], use_xml)]
    except KeyError:
        client = _clients[(m2m_ep.split('#')[0], use_xml)] = OneM2MMQTTClient(
            m2m_ep, use_xml, client_id, handle_request_func, ca_certs=ca_certs,
            cert_file=cert_file, key_file=key_file, insecure=insecure
        )
        return client


class OneM2MMQTTClient(OneM2MClient):
    """
    This class provides for a transport over the MQTT protocol as described in TS 0010
    """

    __request_fields = frozenset([
        'op',
        'to',
        'fr',
        'rqi',
        'ty',
        'pc',
        'rids',
        'ot',
        'rqet',
        'rset',
        'oet',
        'rt',
        'rp',
        'rcn',
        'ec',
        'da',
        'gid',
        'fc',
        'drt',
        'tids',
        'ltids',
        'tqi',
        'rvi',
        'vsi',
    ])

    __response_fields = frozenset([
        'rsc',
        'rqi',
        'pc',
        'to',
        'fr',
        'ot',
        'rset',
        'ec',
        'cts',
        'cto',
        'rvi',
        'vsi',
    ])

    @staticmethod
    def _mqtt_mask(id):
        return id.lstrip('/').replace('/', ':')

    @staticmethod
    def _build_topic(originator='+', receiver='+', type='req'):
        """
        Helper function to create topic strings

        :param string originator:
        :param string receiver:
        :param string type:
        :return string:
        """
        return '/'.join([
            '/oneM2M',
            type,
            OneM2MMQTTClient._mqtt_mask(originator),
            OneM2MMQTTClient._mqtt_mask(receiver),
        ])

    @staticmethod
    def _get_client_id_from_originator(originator):
        _, cse_id, ae_id = split_onem2m_address(originator)
        if cse_id:
            client_id = cse_id[1:] + ('/' + ae_id if ae_id else '')
        elif ae_id:
            client_id = ae_id
        else:
            # TODO: make this configurable
            client_id = 'ae0'

        return client_id

    def attach_callback(self):
        """
        Wrapper function to attach callback handlers to the MQTT client. Functions attached in this
        manner are expected to have the same name as the handler they seek to implement.
        :return fun:
        """
        def decorator(func):
            def wrapper(_self, *args, **kwargs):
                func(_self, *args, **kwargs)
            setattr(self._client, func.__name__, func)
            return wrapper
        return decorator

    def __init__(self, m2m_ep, _, client_id, handle_request_func=None, subscribe_sys_topics=False,
                 ca_certs=None, cert_file=None, key_file=None, insecure=False):
        """
        :param str m2m_ep:
        :param bool _:
        :param str client_id:
        :param call handle_request_func:
        :param bool subscribe_sys_topics: Whether to subscribe to $SYS topics or not
                    (cf <https://github.com/mqtt/mqtt.github.io/wiki/SYS-Topics>)
        """
        super(OneM2MMQTTClient, self).__init__()
        parsed_url = urlparse(m2m_ep)
        self._default_target_id = parsed_url.fragment

        def _default(x):
            if isinstance(x, datetime):
                try:
                    isoformat = x.isoformat
                except AttributeError:
                    raise TypeError("%s (%s)" % (x, type(x)))

                return isoformat()
            else:
                return x

        self._encode = JSONEncoder(default=_default).encode
        self._decode = JSONDecoder().decode

        self._handle_request_func = handle_request_func

        self._processed_request_ids = deque([], maxlen=200)
        self._request_promises = LRUCache(threadsafe=False, max_items=200)

        if client_id is None:
            import random
            import string
            client_id = ''.join(random.sample(string.letters, 16))
        else:
            client_id = self._get_client_id_from_originator(client_id)

        self._client = mqtt.Client(
            clean_session=False,
            client_id='::'.join([
                'C' if client_id[0].lower() in ['c', 'm'] else 'A',
                self._mqtt_mask(client_id),
            ]),
        )

        self._client_id = client_id

        @self.attach_callback()
        def on_connect(client, userdata, flags_dict, rc):
            """
            :param mqtt.Client client:
            :param All userdata:
            :param dict flags_dict:
            :param integer rc:
            :return void:
            """
            if not rc == mqtt.CONNACK_ACCEPTED:
                raise ConnectionFailed(mqtt.connack_string(rc))

            topics = [
                self._build_topic(originator=client_id, receiver='#', type='resp'),
            ]
            client.message_callback_add(topics[0], self._response_callback)

            if self._handle_request_func is not None:
                topics.append(self._build_topic(receiver=client_id) + '/+')
                client.message_callback_add(topics[1], self._request_callback)

            if subscribe_sys_topics:
                topics.append('$SYS/#')

            self.logger.debug('Subscribing to topic(s) %s ...' % (', '.join(topics), ))
            client.subscribe([
                (str(topic), MQTT_QOS_LEVEL) for topic in topics
            ])

        @self.attach_callback()
        def on_disconnect(client, userdata, rc):
            """
            :param mqtt.Client client:
            :param All userdata:
            :param int rc:
            :return void:
            """
            if not rc == mqtt.MQTT_ERR_SUCCESS:
                self.logger.error(
                    'Involuntary connection loss: %s (code %d). Waiting for reconnect ...'
                    % (mqtt.error_string(rc), rc)
                )

        @self.attach_callback()
        def on_message(client, userdata, message):
            """
            :param mqtt.Client client:
            :param All userdata:
            :param  mqtt.MQTTMessage message:
            :return void:
            """
            self.logger.debug('message received on topic %s' % (message.topic, ))

        @self.attach_callback()
        def on_log(client, userdata, level, buf):
            """
            :param mqtt.Client client:
            :param All userdata:
            :param integer level:
            :param string buf:
            :return void:
            """
            self.logger.debug('pahomqtt-%d: %s' % (level, buf))

        if parsed_url.username:
            self._client.username_pw_set(parsed_url.username, parsed_url.password)

        if parsed_url.scheme != 'mqtt':
            self._client.tls_set(ca_certs=ca_certs, certfile=cert_file, keyfile=key_file)
            self._client.tls_insecure_set(insecure)

        try:
            self._client.connect(
                parsed_url.hostname,
                parsed_url.port or portmap[parsed_url.scheme]
            )
        except SocketError as e:
            raise ConnectionFailed(e.message)

        def loop():
            try:
                while self._client.loop(timeout=0.1) != mqtt.mqtt_cs_disconnecting:
                    gevent.sleep()
            except (SystemExit, KeyboardInterrupt, AttributeError):
                pass

        gevent.spawn(loop)

    def _request_callback(self, client, _, message):
        """
        Catch requests and

        :param mqtt.Client client:
        :param All _:
        :param mqtt.MQTTMessage message:
        :return void:
        """

        def handle_request():
            originator = message.topic.split('/')[3]
            try:
                request = self._decode(message.payload)
            except JSONDecodeError as e:
                self.logger.warn(
                    'Got rubbish request from client %s: %s'
                    % (originator, e.message, )
                )
                return

            try:
                if request['rqi'] in self._processed_request_ids:
                    self.logger.info('Request %s already processed; discarding duplicate.' %
                                     (request['rqi'], ))
                    return
                else:
                    rqi = request['rqi']
            except KeyError:
                self.logger.warn(
                    'Special treatment for special request w/o request id from %s.'
                    % (originator, )
                )
                return

            try:
                request['pc'] = decode_onem2m_content(self._encode(request['pc']),
                                                      'application/json')
                request['ty'] = type(request['pc'])
            except KeyError:
                # No content, eh?
                request['ty'] = None

            self.logger.debug('Decoded JSON request: %s' % (request, ))

            op = list(OneM2MOperation._member_map_.values())[request['op'] - 1]
            to = request['to']
            del request['op'], request['to']

            try:
                response = self._handle_request_func(
                    OneM2MRequest(op, to, **request)
                )
                try:
                    response = response.get()
                except AttributeError:
                    pass
            except OneM2MErrorResponse as response:
                self.logger.debug('OneM2MError: %s' % response)
            except CSEError as e:
                response = OneM2MErrorResponse(status_code=e.response_status_code, rqi=rqi)

            if not response.rqi:
                # This really should not happen. No, really, it shouldn't.
                self.logger.debug(
                    'FIXUP! FIXUP! FIXUP! Adding missing request identifier to response: %s'
                    % (rqi, )
                )
                response.rqi = rqi

            if response.content:
                sp_id, cse_id, _ = split_onem2m_address(response.to)
                response.content = self._decode(
                    encode_onem2m_content(response.content, 'application/json',
                                          path=sp_id + cse_id,
                                          fields=response.fields)[1]
                )

            self._publish_message(
                self._encode({
                    k: getattr(response, k) for k in self.__response_fields
                    if getattr(response, k) is not None
                }),
                self._build_topic(originator, self._client_id, type='resp'),
            )
            self._processed_request_ids.append(rqi)

        gevent.spawn(handle_request)

    def _response_callback(self, client, _, message):
        """

        :param mqtt.Client client:
        :param All _:
        :param mqtt.MQTTMessage message:
        :return:
        """

        def handle_response():
            try:
                response = self._decode(message.payload)
            except JSONDecodeError as e:
                self.logger.error('Discarding response w/ damaged payload: %s', (e.message, ))
                return

            promise_key = (message.topic.split('/')[4], response['rqi'])
            try:
                p = self._request_promises[promise_key]
            except KeyError:
                self.logger.debug(
                    'Response %s could not be mapped to a request. Discarding.'
                    % (response['rqi'], )
                )
                return

            try:
                response['pc'] = decode_onem2m_content(self._encode(response['pc']),
                                                       'application/json')
            except KeyError:
                pass
            except CSEValueError as e:
                self.logger.error(
                    'Content of response %s could not be parsed, throwing on the trash heap: %s'
                    % (response['rqi'], e.message)
                )
                p.reject(e)

            status_code = response['rsc']
            del response['rsc']
            if status_code >= ERROR_MIN:
                p.reject(OneM2MErrorResponse(status_code, **response))
            else:
                p.fulfill(OneM2MResponse(status_code, **response))

        gevent.spawn(handle_response)

    @property
    def handle_request_func(self):
        return self._handle_request_func

    @handle_request_func.setter
    def handle_request_func(self, func):
        if self._handle_request_func is not None:
            raise RuntimeError()

        topic = self._build_topic(receiver=self._client_id) + '/+'
        self._client.message_callback_add(topic, self._request_callback)

        self.logger.debug('Subscribing to topic %s ...' % topic)
        self._client.subscribe((str(topic), MQTT_QOS_LEVEL))
        self._handle_request_func = func

    def _cancel_request(self, promise_key):
        if promise_key in self._request_promises:
            p = self._request_promises[promise_key]
            p.reject(CSETargetNotReachable())

    def _publish_message(self, payload, topic):
        (rc, mid) = self._client.publish(topic, payload, MQTT_QOS_LEVEL)
        if not rc == mqtt.MQTT_ERR_SUCCESS:
            self.logger.info('Code %d while sending message %d: %s' %
                             (rc, mid, mqtt.error_string(rc)))

    def send_onem2m_request(self, request):
        """
        :param openmtc_onem2m.transport.OneM2MRequest request:
        :return Promise:
        """
        p = Promise()

        client_id = self._get_client_id_from_originator(request.originator)

        if request.ty and request.op == OneM2MOperation.create:
            request.ty = ResourceTypeE[request.resource_type.typename].value
        else:
            request.ty = None

        request.op = 1 + list(OneM2MOperation._member_map_.keys()).index(
            OneM2MOperation[request.op].name)
        if request.pc:
            request.pc = self._decode(
                encode_onem2m_content(request.pc, 'application/json', path=request.to)[1]
            )
        if request.fc:
            request.fc = encode_onem2m_content(request.fc, 'application/json', path=request.to)[1]

        if self._default_target_id:
            target_id = self._default_target_id
        else:
            _, cse_id, suffix = split_onem2m_address(request.to)
            if cse_id:
                target_id = cse_id[1:] + ('/' + suffix if request.ae_notifying else '')
            else:
                raise CSETargetNotReachable()

        self.logger.debug('Preparing request for transit: %s' % (request, ))

        promises_key = (OneM2MMQTTClient._mqtt_mask(target_id), request.rqi)

        def cleanup(_):
            self.logger.debug('Clearing request id %s ...' % (promises_key, ))
            del self._request_promises[promises_key]

        p.addCallback(cleanup)
        p.addErrback(cleanup)

        self._request_promises[promises_key] = p
        gevent.spawn_later(MQTT_RESPONSE_TIMEOUT, self._cancel_request, promises_key)

        self._publish_message(
            self._encode({
                str(k): getattr(request, k) for k in self.__request_fields
                if getattr(request, k) is not None
            }),
            self._build_topic(client_id, target_id) + '/json',
        )

        return p

    def stop(self):
        # TODO(rst): cleaning up MQTT clients has to be redesigned
        # two scenarios:
        # 1) receiving request with handle_func -> easy to maintain for stopping
        # 2) send out MQTT request and waiting for a response -> more difficult to handle
        # - need to change the idea of the client_id, maybe two per entity
        # - different clients per broker, maybe per default target_id as well
        if self._client:
            self._client.disconnect()
            # TODO(sho): this is abominable. But for the time being, there seems to be no elegant
            #            solution to this.
            self._client._clean_session = True
            # TS 0010, sec. 6.3 mandates a reconnect in order to leave a clean state with the MQTT
            # broker
            self._client.reconnect()
            self._client.disconnect()
            self._client = None
