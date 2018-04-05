import re
from flask import Flask, Response, request
from gevent import wsgi

from openmtc_app.onem2m import ResourceManagementXAE
from orion_api import OrionAPI


class OrionContextBroker(ResourceManagementXAE):
    def __init__(self,
                 orion_host="http://localhost:1026",
                 orion_api="v2",
                 labels=["openmtc:sensor_data"],
                 accumulate_address="http://localhost:8080",
                 *args,
                 **kw):
        super(OrionContextBroker, self).__init__(*args, **kw)
        if isinstance(labels, basestring):
            self.labels = {labels}
        elif hasattr(labels, '__iter__'):
            self.labels = set(labels)
        else:
            self.labels = None
        self._entity_names = {}
        self._subscriptions = {}
        self.logger.critical(accumulate_address)
        self.orion_api = OrionAPI(
            orion_host=orion_host,
            api_version=orion_api,
            accumulate_endpoint="{}/accumulate".format(accumulate_address))

        # Subscription Sink for OCB
        self.app = Flask(__name__)
        self.app.add_url_rule(
            '/accumulate',
            'process_notification',
            self.process_notification,
            methods=["POST"])
        accumulate_ip, accumulate_port = accumulate_address.split('//')[
            1].split(':')
        self.server = wsgi.WSGIServer(("0.0.0.0", int(accumulate_port)),
                                      self.app)
        self.server.start()

    def process_notification(self):
        self.logger.debug("Got from Subscription {}".format(request.json))
        actuator = self.get_resource(
            self._subscriptions[request.json["subscriptionId"]])
        self.push_content(actuator, request.json["data"][0]["cmd"]["value"])
        return Response(status=200, headers={})

    def _on_register(self):
        self._discover_openmtc_ipe_entities()

    def _sensor_filter(self, sensor_info):
        if self.labels:
            return len(self.labels.intersection(
                sensor_info['sensor_labels'])) > 0
        else:
            return True

    def _get_entity_name(self, sensor_info):
        device_type = "sensor" if sensor_info.get("sensor_labels",
                                                  None) else "actuator"
        try:
            id_label = filter(
                lambda x: (x.startswith('openmtc:id:')),
                sensor_info['{}_labels'.format(device_type)]).pop()
            cse_id, dev_id = re.sub('^openmtc:id:', '',
                                    id_label).split('/')[:2]
        except (IndexError, ValueError):
            cse_id = sensor_info['cse_id']
            dev_id = sensor_info['dev_name']
        try:
            f_s, e_pre = cse_id.split('~', 1)
        except ValueError:
            f_s = ''
            e_pre = cse_id
        return re.sub('[\W]', '_', f_s), '%s-%s' % (e_pre, dev_id)

    def _sensor_data_cb(self, sensor_info, sensor_data):
        try:
            fiware_service, entity_name = self._entity_names[sensor_info['ID']]
        except KeyError:
            self._entity_names[sensor_info['ID']] = self._get_entity_name(
                sensor_info)
            fiware_service, entity_name = self._entity_names[sensor_info['ID']]
            self.orion_api.create_entity(
                entity_name, fiware_service=fiware_service)
        self.orion_api.update_attributes(
            entity_name, sensor_data, fiware_service=fiware_service)

    def _new_actuator(self, actuator_info):
        try:
            fiware_service, entity_name = self._entity_names[actuator_info[
                'ID']]
        except KeyError:
            self._entity_names[actuator_info['ID']] = self._get_entity_name(
                actuator_info)
            fiware_service, entity_name = self._entity_names[actuator_info[
                'ID']]
        self.logger.info("Create new Entity {} on Fiware Service {}".format(
            entity_name, fiware_service))
        self.orion_api.create_entity(
            entity_name, fiware_service=fiware_service)
        data_dummy = {
            'v': "none",
            'bn': "none",
            'n': "cmd",
            'u': "none",
            't': "none"
        }
        self.orion_api.update_attributes(
            entity_name, data_dummy, fiware_service=fiware_service)

        subscriptionId = self.orion_api.subscribe(
            entity_name, fiware_service=fiware_service)
        self._subscriptions[subscriptionId] = actuator_info['ID']
