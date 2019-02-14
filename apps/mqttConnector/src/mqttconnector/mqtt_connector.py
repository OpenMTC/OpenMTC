import re
from base64 import b64decode as base64decode
from itertools import groupby
from json import loads as json_decode
from os import path as ospath

from paho.mqtt import client as mqtt

from openmtc_app.onem2m import XAE


class mqttConnector(XAE):
    interval = 10
    _location_containers = {}
    _device_containers = {}
    _sensor_containers = {}
    client = mqtt.Client()

    def __init__(self,
                 broker_ep,
                 topic_pre,
                 broker_user,
                 broker_user_pw,
                 topic_index_location=1,
                 topic_index_device=-1,
                 fiware_service=None,
                 mqtts_enabled=False,
                 mqtts_ca_certs=None,
                 mqtts_certfile=None,
                 mqtts_keyfile=None,
                 *args,
                 **kw):
        host, port = broker_ep.split(":")
        self._broker_host = host
        self._broker_port = int(port)

        self.topic_pre = topic_pre
        self.topic_index_location = topic_index_location
        self.topic_index_device = topic_index_device
        self.fiware_service = fiware_service
        self.broker_user = broker_user
        self.broker_user_pw = broker_user_pw
        self.mqtts_enabled = mqtts_enabled
        self.mqtts_ca_certs = mqtts_ca_certs or None
        self.mqtts_certfile = mqtts_certfile or None
        self.mqtts_keyfile = mqtts_keyfile or None

        super(mqttConnector, self).__init__(*args, **kw)

    def _on_register(self):
        def on_connect(*_):
            def callback(*args):
                (_, _, message) = args
                self.logger.info(
                    'Received message on topic %s' % message.topic)
                self._handle_data(message.topic, message.payload)

            topics = ['%s/#' % self.topic_pre]

            for topic in topics:
                self.client.message_callback_add(topic, callback)

            self.client.subscribe([(topic, 1) for topic in topics])

        self.client.on_connect = on_connect

        # TODO(rst): this needs to be handled more general and from config
        self.client.username_pw_set(self.broker_user, self.broker_user_pw)
        if self.mqtts_enabled:
            self.client.tls_set(
                ca_certs=self.mqtts_ca_certs,
                certfile=self.mqtts_certfile,
                keyfile=self.mqtts_keyfile)
            self.client.tls_insecure_set(True)
        self.client.connect(self._broker_host, self._broker_port)
        # TODO let gevent handle this
        self.client.loop_forever()

    def _on_shutdown(self):
        self.client.disconnect()

    def _get_target_container(self, location, device, sensor):
        try:
            return self._sensor_containers[(location, device, sensor)]
        except KeyError:
            try:
                device_cnt = self._device_containers[(location, device)]
            except KeyError:
                try:
                    location_cnt = self._location_containers[location]
                except KeyError:
                    location_cnt = self.create_container(None, location)
                    self._location_containers[location] = location_cnt
                device_cnt = self.create_container(
                    location_cnt, device, labels=["openmtc:device"])
                self._device_containers[(location, device)] = device_cnt
            openmtc_id = "%s/%s/%s" % (
                (self.fiware_service + '~' if self.fiware_service else '') +
                location, device, sensor)
            labels = ['openmtc:sensor_data', 'openmtc:id:%s' % openmtc_id]
            sensor_cnt = self.create_container(
                device_cnt, sensor, labels=labels)
            self._sensor_containers[(location, device, sensor)] = sensor_cnt
            return sensor_cnt

    def _handle_data(self, topic, payload):
        # get location and device
        try:
            location = topic.split('/')[self.topic_index_location]
            device = topic.split('/')[self.topic_index_device]
        except (AttributeError, ValueError):
            self.logger.error("Topic '%s' not valid. Dropping." % topic)
            return

        # check payload
        try:
            readings = json_decode(
                base64decode(json_decode(payload)['m2m:cin']['con']).decode('utf-8'))
        except (ValueError, KeyError, TypeError):
            self.logger.error('Damaged payload; discarding')
            return

        # push data
        for _, values in groupby(readings, key=lambda x: x['n']):
            sensor_cnt = self._get_target_container(location, device, 'number')
            for value in sorted(values, key=lambda x: x['t']):
                self.push_content(sensor_cnt, [value])
